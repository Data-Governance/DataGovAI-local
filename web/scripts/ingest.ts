/**
 * Ingest Utah GRS PDFs from data/raw into Postgres document_chunks.
 *
 *   npm run ingest -- --limit 20
 *   npm run ingest -- --pdf ../data/raw/council-minutes-(GRS-19978).pdf
 */
import { config } from "dotenv";
config({ path: ".env.local" });
config();

import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { eq, sql } from "drizzle-orm";
import { PDFParse } from "pdf-parse";

import { db } from "../src/lib/db/client";
import { documentChunks } from "../src/lib/db/schema";
import { embedTexts } from "../src/lib/rag/embed";

function chunkDeterministicId(
  sourceId: string,
  index: number,
  body: string,
): string {
  const h = createHash("sha256")
    .update(sourceId)
    .update("\0")
    .update(String(index))
    .update("\0")
    .update(body)
    .digest();
  const b = Buffer.from(h.subarray(0, 16));
  b[6] = (b[6]! & 0x0f) | 0x40;
  b[8] = (b[8]! & 0x3f) | 0x80;
  const hex = b.toString("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20, 32)}`;
}

function vectorSql(embedding: number[]) {
  for (const x of embedding) {
    if (!Number.isFinite(x)) throw new Error("Non-finite embedding value");
  }
  return sql.raw(`'[${embedding.join(",")}]'::vector`);
}

function parseSource(fileName: string): { sourceId: string; title: string } {
  const stem = fileName.replace(/\.pdf$/i, "");
  const match = stem.match(/\(GRS-(\d+)\)/i);
  const sourceId = match ? `GRS-${match[1]}` : stem.slice(0, 80);
  const title = stem.replace(/-\(GRS-\d+\)$/i, "").replace(/-/g, " ");
  return { sourceId, title };
}

function chunkText(fullText: string, maxChunks = 40): string[] {
  const paras = fullText
    .split(/\n\s*\n+/)
    .map((p) => p.replace(/\s+/g, " ").trim())
    .filter((p) => p.length > 40);

  const chunks: string[] = [];
  let buf = "";

  function flush() {
    const t = buf.trim();
    if (t.length >= 120) chunks.push(t);
    buf = "";
  }

  for (const p of paras) {
    if (buf.length + p.length + 2 > 1600) {
      flush();
      if (chunks.length >= maxChunks) break;
    }
    buf = buf ? `${buf}\n\n${p}` : p;
  }
  flush();
  return chunks.slice(0, maxChunks);
}

function flag(name: string): string | undefined {
  const args = process.argv.slice(2);
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : undefined;
}

async function ingestPdf(pdfPath: string) {
  const fileName = path.basename(pdfPath);
  const { sourceId, title } = parseSource(fileName);
  const buffer = readFileSync(pdfPath);
  const parser = new PDFParse({ data: buffer });
  const { text } = await parser.getText();
  if (!text || text.trim().length < 80) {
    console.warn(`Skip ${fileName}: extracted text too short`);
    return 0;
  }

  const bodies = chunkText(text);
  if (!bodies.length) {
    console.warn(`Skip ${fileName}: no chunks`);
    return 0;
  }

  console.log(`${sourceId} (${title}): ${bodies.length} chunks`);
  await db.delete(documentChunks).where(eq(documentChunks.sourceId, sourceId));
  const embeddings = await embedTexts(bodies);

  const rows = bodies.map((body, i) => {
    const embedding = embeddings[i]!;
    if (embedding.length !== 1024) {
      throw new Error(`Expected 1024-dim embedding, got ${embedding.length}`);
    }
    return {
      id: chunkDeterministicId(sourceId, i, body),
      sourceId,
      title,
      content: body,
      pageStart: null,
      pageEnd: null,
      metadata: { fileName },
      embedding: vectorSql(embedding),
    };
  });

  const ROWS = 25;
  for (let i = 0; i < rows.length; i += ROWS) {
    await db.insert(documentChunks).values(rows.slice(i, i + ROWS));
  }
  return bodies.length;
}

async function main() {
  if (!process.env.DATABASE_URL) {
    console.error("DATABASE_URL is required");
    process.exit(1);
  }

  const single = flag("pdf");
  const limit = Number(flag("limit") ?? "20");
  const rawDir = path.resolve(process.cwd(), "..", "data", "raw");

  const files: string[] = [];
  if (single) {
    const resolved = path.resolve(single);
    if (!existsSync(resolved)) {
      console.error(`File not found: ${resolved}`);
      process.exit(1);
    }
    files.push(resolved);
  } else {
    if (!existsSync(rawDir)) {
      console.error(`Missing ${rawDir}`);
      process.exit(1);
    }
    const preferred = [
      "council-minutes-(GRS-19978).pdf",
      "ordinances-and-resolutions-(GRS-28604).pdf",
      "accounting-audit-reports-(GRS-7695).pdf",
      "performance-audit-records-(GRS-28265).pdf",
      "annual-reports-(GRS-15859).pdf",
      "telephone-bills-(GRS-12287).pdf",
      "billing-files-(GRS-82607).pdf",
      "purchase-requisition-files-(GRS-24815).pdf",
      "personnel-files-for-full-time-salaried-employees-(GRS-19374).pdf",
      "personnel-files-for-part-time-employees-(GRS-19375).pdf",
      "legal-case-files-(GRS-11284).pdf",
      "deposits-with-the-treasurer-(GRS-8369).pdf",
      "general-plan-(GRS-29269).pdf",
    ];
    for (const name of preferred) {
      const p = path.join(rawDir, name);
      if (existsSync(p)) files.push(p);
    }
    if (files.length < limit) {
      const extra = readdirSync(rawDir)
        .filter((f) => f.toLowerCase().endsWith(".pdf"))
        .map((f) => path.join(rawDir, f))
        .filter((p) => !files.includes(p));
      files.push(...extra.slice(0, Math.max(0, limit - files.length)));
    }
    files.splice(limit);
  }

  console.log(`Ingesting ${files.length} PDF(s)`);
  let total = 0;
  for (const f of files) {
    try {
      total += await ingestPdf(f);
    } catch (e) {
      console.error(`Failed ${path.basename(f)}:`, e);
    }
  }
  console.log(`Done. ${total} chunks inserted.`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
