import { config } from "dotenv";
import { createAmazonBedrock } from "@ai-sdk/amazon-bedrock";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { fromNodeProviderChain } from "@aws-sdk/credential-providers";

// Same guard as db/client.ts: scripts import this module before their own
// dotenv call runs, so load env here if it hasn't been loaded yet.
if (!process.env.LLM_PROVIDER) {
  config({ path: ".env.local" });
  config();
}

/**
 * Provider switch: LLM_PROVIDER=bedrock (default) or ollama.
 *
 * bedrock — AWS Bedrock, SigV4 via the standard AWS credential chain
 * (env keys, shared profile, or instance role).
 *
 * ollama — local Ollama through its OpenAI-compatible /v1 endpoint.
 * Deadline fallback while Bedrock model access is pending.
 */
export const LLM_PROVIDER =
  process.env.LLM_PROVIDER === "ollama" ? "ollama" : "bedrock";

export const bedrock = createAmazonBedrock({
  region: process.env.AWS_REGION ?? "us-east-1",
  credentialProvider: fromNodeProviderChain(),
});

const OLLAMA_BASE_URL =
  process.env.OLLAMA_BASE_URL ?? "http://localhost:11434";

export const ollama = createOpenAICompatible({
  name: "ollama",
  baseURL: `${OLLAMA_BASE_URL}/v1`,
});

export const PRIMARY_MODEL_ID =
  LLM_PROVIDER === "ollama"
    ? (process.env.OLLAMA_CHAT_MODEL ?? "llama3.1:8b")
    : (process.env.BEDROCK_MODEL_ID ??
      "anthropic.claude-3-haiku-20240307-v1:0");

export const PRIMARY_MODEL =
  LLM_PROVIDER === "ollama"
    ? ollama(PRIMARY_MODEL_ID)
    : bedrock(PRIMARY_MODEL_ID);

export const TEMPERATURE = 0.2;
