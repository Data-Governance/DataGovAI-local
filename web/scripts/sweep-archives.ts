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

import { mkdirSync, writeFileSync } from "node:fs";
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

async function main() {
  const dir = path.resolve(
    (flag("dir") ?? path.join(os.homedir(), "grs-corpus", "archives-grs")).replace(
      /^~(?=\/)/,
      os.homedir(),
    ),
  );
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
  for (const d of docs) {
    const dispAuth = d.grsItemDispAuth;
    if (!dispAuth || !/^GRS-\d+$/.test(dispAuth)) {
      console.warn(`Skip ${d.id}: unexpected disposition authority "${dispAuth}"`);
      continue;
    }
    const name = `${slug(d.grsItemTitle ?? d.id)}-(${dispAuth}).md`;
    writeFileSync(path.join(dir, name), seriesMarkdown(d));
    written++;
  }
  console.log(`Wrote ${written} series file(s) to ${dir}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
