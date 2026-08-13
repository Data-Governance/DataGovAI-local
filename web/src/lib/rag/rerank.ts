import { rerank as aiRerank } from "ai";

import { logger } from "@/lib/logger";

export type RerankResult = { index: number; score: number };

const RERANK_MODEL = "voyage/rerank-2.5";

function mergeOrderFallback(documents: string[]): RerankResult[] {
  return documents.map((_, index) => ({
    index,
    score: 1 - index * 0.001,
  }));
}

/**
 * Voyage rerank-2 via AI Gateway. Any failure (rate limit, timeout, model
 * unavailable) degrades to merge order — reranking is a quality enhancement,
 * never a hard requirement for chat.
 */
export async function rerank(
  query: string,
  documents: string[],
): Promise<RerankResult[]> {
  if (documents.length === 0) return [];
  try {
    const { ranking } = await aiRerank({
      model: RERANK_MODEL,
      documents,
      query,
    });
    return ranking.map((r) => ({ index: r.originalIndex, score: r.score }));
  } catch (err) {
    logger.warn({ err }, "rag.rerank_failed");
    return mergeOrderFallback(documents);
  }
}
