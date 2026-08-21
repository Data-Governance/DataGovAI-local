import { embed, embedMany } from "ai";

import { LLM_PROVIDER, bedrock, ollama } from "@/lib/ai/model";

/**
 * Embeddings follow LLM_PROVIDER:
 *
 * bedrock — amazon.titan-embed-text-v2:0 (1024 dims by default).
 * ollama  — mxbai-embed-large (1024 dims; do NOT swap in nomic-embed-text,
 *           it outputs 768).
 *
 * Both match the vector(1024) column on document_chunks, so no schema
 * change either way. Switching the embedding model (including switching
 * providers) requires re-ingesting every document — embedding spaces
 * don't mix.
 */
const EMBEDDING_MODEL =
  LLM_PROVIDER === "ollama"
    ? ollama.textEmbeddingModel(
        process.env.OLLAMA_EMBED_MODEL ?? "mxbai-embed-large",
      )
    : bedrock.embedding(
        process.env.BEDROCK_EMBEDDING_MODEL_ID ??
          "amazon.titan-embed-text-v2:0",
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
