import { embed, embedMany } from "ai";

import { bedrock } from "@/lib/ai/model";

/**
 * Titan embeddings via AWS Bedrock. titan-embed-text-v2 outputs 1024
 * dimensions by default, matching the vector(1024) column on
 * document_chunks. Changing the embedding model requires re-ingesting
 * every document — embedding spaces don't mix.
 */
const EMBEDDING_MODEL = bedrock.embedding(
  process.env.BEDROCK_EMBEDDING_MODEL_ID ?? "amazon.titan-embed-text-v2:0",
);

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
