import { sql } from "drizzle-orm";

import { db } from "@/lib/db/client";
import { logger } from "@/lib/logger";

import type { RetrievedChunk } from "./context-format";
import { formatRetrievedChunks, sanitizeChunk } from "./context-format";
import { embedSingle } from "./embed";
import { rerank } from "./rerank";

export type { RetrievedChunk } from "./context-format";
export { formatRetrievedChunks } from "./context-format";

function dedupeById<T extends { id: string }>(rows: T[]): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const r of rows) {
    if (seen.has(r.id)) continue;
    seen.add(r.id);
    out.push(r);
  }
  return out;
}

/**
 * Hybrid vector + full-text retrieval for Utah GRS chunks.
 * Failures degrade to [] so chat can still respond (without citations).
 */
export async function retrieveContext(
  query: string,
  k = 5,
): Promise<RetrievedChunk[]> {
  if (!process.env.DATABASE_URL) {
    return [];
  }

  try {
    const embedding = await embedSingle(query);
    for (const x of embedding) {
      if (!Number.isFinite(x)) throw new Error("Invalid embedding value");
    }
    const vec = embedding.join(",");

    const vectorRows = await db.execute(sql.raw(`
      SELECT id::text as id, content, source_id as "sourceId", title, page_start as "pageStart"
      FROM document_chunks
      ORDER BY embedding <=> '[${vec}]'::vector
      LIMIT 20
    `));

    const kwRows = await db.execute(sql`
      SELECT id::text as id, content, source_id as "sourceId", title, page_start as "pageStart"
      FROM document_chunks
      WHERE to_tsvector('english', content) @@ plainto_tsquery('english', ${query})
      ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', ${query})) DESC
      LIMIT 20
    `);

    type Row = RetrievedChunk;
    const merged = dedupeById([
      ...(vectorRows.rows as unknown as Row[]),
      ...(kwRows.rows as unknown as Row[]),
    ]);

    if (!merged.length) return [];

    const reranked = await rerank(
      query,
      merged.map((m) => m.content),
    );
    return reranked
      .sort((a, b) => b.score - a.score)
      .slice(0, k)
      .map((r) => merged[r.index])
      .filter(Boolean)
      .map(sanitizeChunk)
      .filter((c) => c.content.length >= 40);
  } catch (err) {
    logger.warn({ err }, "rag.retrieve_failed");
    return [];
  }
}
