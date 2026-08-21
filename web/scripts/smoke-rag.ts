import { config } from "dotenv";
config({ path: ".env.local" });
config();

import { generateText } from "ai";
import { PRIMARY_MODEL } from "../src/lib/ai/model";
import { buildSystemPrompt } from "../src/lib/ai/system-prompt";
import { formatRetrievedChunks, retrieveContext } from "../src/lib/rag/retrieve";

const DEFAULT_QUERIES = [
  "What is the retention period for council minutes?",
  "How long should we keep employee personnel files?",
  "What are the disposition requirements for audit records?",
  "What is the retention schedule for legal case files?",
];

async function runOne(query: string, generate: boolean) {
  const retrieved = await retrieveContext(query, 5);
  console.log("Q:", query);
  console.log(
    "  retrieved:",
    retrieved.map((r) => r.sourceId).join(", ") || "(none)",
  );
  if (!generate) return retrieved.length > 0;
  const { text } = await generateText({
    model: PRIMARY_MODEL,
    system: buildSystemPrompt(formatRetrievedChunks(retrieved)),
    prompt: query,
    temperature: 0.2,
  });
  console.log("  answer:", text.slice(0, 240).replace(/\s+/g, " "));
  return retrieved.length > 0;
}

async function main() {
  const generate = process.argv.includes("--generate");
  const extra = process.argv.slice(2).filter((a) => !a.startsWith("--"));
  const queries = extra.length ? extra : DEFAULT_QUERIES;
  let ok = true;
  for (const q of queries) {
    const hit = await runOne(q, generate);
    if (!hit) ok = false;
  }
  if (!ok) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
