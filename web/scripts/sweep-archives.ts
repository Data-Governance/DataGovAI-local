/**
 * Sweep Utah State Archives GRS retention series from the AXAEM Solr
 * endpoint into a corpus directory as one markdown doc per series, named
 * `<title-slug>-(GRS-<n>).md` so ingest's parseSource picks up the series
 * id. Re-runs are idempotent: each series overwrites its own file.
 *
 *   npm run sweep:archives
 *   npm run sweep:archives -- --dir ~/grs-corpus/archives-grs
 *
 * Weekly job: sweep first, then re-ingest the corpus (ingest re-embeds
 * per source id, delete-then-insert).
 */
import { config } from "dotenv";
config({ path: ".env.local" });
config();

import { mkdirSync, readdirSync, unlinkSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";

const SOLR_URL =
  process.env.ARCHIVES_SOLR_URL ??
  "https://axaemarchives.utah.gov/solr/axaem/GRSItem";

type GrsDoc = {
  id: string;
  grsItemDispAuth?: string;
  grsItemLocalId?: string;
  grsItemTitle?: string;
  grsItemDescription?: string;
  grsItemRetention?: string;
  grsItemClassification?: string;
  grsItemCategories?: string[];
  grsItemSchedType?: string;
  grsItemRevision?: string;
  grsItemStatus?: string;
  grsItemApprovedBy?: string;
  grsItemDateApproved?: string;
  grsItemAppraisalSentence?: string;
};

const FIELDS = [
  "id",
  "grsItemDispAuth",
  "grsItemLocalId",
  "grsItemTitle",
  "grsItemDescription",
  "grsItemRetention",
  "grsItemClassification",
  "grsItemCategories",
  "grsItemSchedType",
  "grsItemRevision",
  "grsItemStatus",
  "grsItemApprovedBy",
  "grsItemDateApproved",
  "grsItemAppraisalSentence",
].join(",");

function flag(name: string): string | undefined {
  const args = process.argv.slice(2);
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : undefined;
}

function slug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60)
    .replace(/-+$/, "");
}

function seriesMarkdown(d: GrsDoc): string {
  const dispAuth = d.grsItemDispAuth ?? d.id;
  const title = d.grsItemTitle ?? "Untitled series";
  const facts: string[] = [];
  facts.push(
    `Utah General Retention Schedule series ${dispAuth}` +
      (d.grsItemLocalId ? ` (local id ${d.grsItemLocalId})` : "") +
      (d.grsItemSchedType ? `, ${d.grsItemSchedType}` : "") +
      (d.grsItemRevision ? `, revision ${d.grsItemRevision}` : "") +
      (d.grsItemStatus ? `, status ${d.grsItemStatus}` : "") +
      `. Title: ${title}.`,
  );
  if (d.grsItemCategories?.length) {
    facts.push(`Categories: ${d.grsItemCategories.join(", ")}.`);
  }
  if (d.grsItemClassification) {
    facts.push(`Classification: ${d.grsItemClassification}.`);
  }
  if (d.grsItemApprovedBy || d.grsItemDateApproved) {
    facts.push(
      `Approved by ${d.grsItemApprovedBy ?? "the State Records Committee"}` +
        (d.grsItemDateApproved ? ` on ${d.grsItemDateApproved}` : "") +
        `.`,
    );
  }

  const parts = [`# ${title} (${dispAuth})`, facts.join(" ")];
  if (d.grsItemDescription) {
    parts.push(`Description of ${dispAuth}: ${d.grsItemDescription}`);
  }
  if (d.grsItemRetention) {
    parts.push(
      `Retention and disposition for ${dispAuth} (${title}): ${d.grsItemRetention}` +
        (d.grsItemAppraisalSentence ? ` ${d.grsItemAppraisalSentence}` : ""),
    );
  }
  return parts.join("\n\n") + "\n";
}

function expandHome(p: string): string {
  return p.replace(/^~(?=\/|$)/, os.homedir());
}

/**
 * Output directory: --dir wins, else <GRSBOT_CORPUS_DIR>/archives-grs, else
 * ~/grs-corpus/archives-grs. GRSBOT_CORPUS_DIR is the whole corpus root that
 * ingest is pointed at (`npm run ingest -- --pdf $GRSBOT_CORPUS_DIR`), so the
 * sweep keeps its own subdirectory under it.
 */
function outputDir(): string {
  const explicit = flag("dir");
  if (explicit) return path.resolve(expandHome(explicit));
  const root = expandHome(
    process.env.GRSBOT_CORPUS_DIR || path.join(os.homedir(), "grs-corpus"),
  );
  return path.resolve(path.join(root, "archives-grs"));
}

async function main() {
  const dir = outputDir();
  mkdirSync(dir, { recursive: true });

  const url = `${SOLR_URL}?wt=json&rows=1000&facet=off&hl=off&fl=${encodeURIComponent(FIELDS)}`;
  console.log(`Fetching ${url}`);
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Solr request failed: ${res.status} ${res.statusText}`);
  }
  const data = (await res.json()) as {
    response: { numFound: number; docs: GrsDoc[] };
  };
  const docs = data.response.docs;
  console.log(`numFound=${data.response.numFound}, received=${docs.length}`);
  if (docs.length < data.response.numFound) {
    console.warn(
      `WARNING: received fewer docs than numFound — raise rows above ${docs.length}`,
    );
  }

  let written = 0;
  const writtenNames = new Set<string>();
  for (const d of docs) {
    const dispAuth = d.grsItemDispAuth;
    if (!dispAuth || !/^GRS-\d+$/.test(dispAuth)) {
      console.warn(`Skip ${d.id}: unexpected disposition authority "${dispAuth}"`);
      continue;
    }
    const name = `${slug(d.grsItemTitle ?? d.id)}-(${dispAuth}).md`;
    writeFileSync(path.join(dir, name), seriesMarkdown(d));
    writtenNames.add(name);
    written++;
  }
  console.log(`Wrote ${written} series file(s) to ${dir}`);

  pruneStaleSeriesFiles(dir, writtenNames, written);
}

/**
 * Delete series files left behind by an EARLIER sweep that this sweep did not
 * rewrite. A series' file name embeds its title slug, so a title change in the
 * Archives catalog produces a NEW file and orphans the old one — and both
 * carry the same `(GRS-<n>)` id. ingest.ts keys on that id with
 * delete-then-insert and walks files in sort order, so whichever name sorts
 * later wins the row: a stale file can silently overwrite the fresh one and
 * regress a citation's retention text after a sweep that reported success.
 *
 * Safety, in order:
 *  - Only runs after the Solr fetch succeeded (a failed fetch throws above and
 *    never reaches here), so a bad request can never empty the corpus.
 *  - Refuses to prune when this sweep wrote nothing, so a degenerate but
 *    HTTP-200 response (zero docs) also cannot empty the corpus.
 *  - Only considers files matching this script's own naming convention
 *    (`*-(GRS-<n>).md`). Hand-dropped PDFs, notes, the weekly job's
 *    `.last-sweep` stamp, and anything else in the corpus are never touched.
 */
function pruneStaleSeriesFiles(
  dir: string,
  writtenNames: Set<string>,
  written: number,
): void {
  if (written === 0) {
    console.warn("Nothing written — skipping prune so the corpus is never emptied.");
    return;
  }

  const owned = /-\(GRS-\d+\)\.md$/i;
  let removed = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isFile()) continue;
    if (!owned.test(entry.name)) continue;
    if (writtenNames.has(entry.name)) continue;
    unlinkSync(path.join(dir, entry.name));
    console.log(`Pruned stale series file: ${entry.name}`);
    removed++;
  }
  console.log(`Pruned ${removed} stale series file(s).`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
