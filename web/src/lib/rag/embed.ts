import { embed, embedMany } from "ai";

/**
 * Voyage embeddings via Vercel AI Gateway. Plain "provider/model" strings
 * route through the Gateway using the same automatic runtime auth as
 * streamText — no manual OIDC/API-key handling needed.
 */
const EMBEDDING_MODEL = "voyage/voyage-3-large";

export async function embedTexts(texts: string[]): Promise<number[][]> {
  if (texts.length === 0) return [];
  const { embeddings } = await embedMany({
    model: EMBEDDING_MODEL,
    values: texts,
  });
  return embeddings;
}

export async function embedSingle(text: string): Promise<number[]> {
  const { embedding } = await embed({
    model: EMBEDDING_MODEL,
    value: text,
  });
  return embedding;
}
