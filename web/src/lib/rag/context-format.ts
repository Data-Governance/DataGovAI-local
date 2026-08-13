export type RetrievedChunk = {
  id: string;
  content: string;
  sourceId: string;
  title: string;
  pageStart: number | null;
};

export function formatRetrievedChunks(chunks: RetrievedChunk[]): string {
  if (!chunks.length) return "";
  const lines = chunks.map(
    (c) =>
      `[${c.sourceId}] ${c.title}${c.pageStart != null ? ` (p. ${c.pageStart})` : ""}\n${c.content}`,
  );
  return `<retrieved_context>\n${lines.join("\n\n")}\n</retrieved_context>`;
}

export function sanitizeChunk(chunk: RetrievedChunk): RetrievedChunk {
  return {
    ...chunk,
    title: chunk.title.replace(/\s+/g, " ").trim(),
    content: chunk.content.replace(/\s+/g, " ").trim(),
  };
}
