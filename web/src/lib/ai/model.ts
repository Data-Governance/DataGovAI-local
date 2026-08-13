/** All model calls use AI Gateway `provider/model` strings. */

export const PRIMARY_MODEL = "openai/gpt-4o-mini" as const;

export const FALLBACK_MODELS = [
  "openai/gpt-4o-mini",
  "anthropic/claude-haiku-4.5",
  "google/gemini-2.5-flash",
] as const;

export const TEMPERATURE = 0.2;
