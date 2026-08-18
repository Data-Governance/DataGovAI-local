import { createAmazonBedrock } from "@ai-sdk/amazon-bedrock";
import { fromNodeProviderChain } from "@aws-sdk/credential-providers";

/**
 * All model calls go to AWS Bedrock. Auth is SigV4 via the standard AWS
 * credential chain (env keys, shared profile, or instance role).
 */
export const bedrock = createAmazonBedrock({
  region: process.env.AWS_REGION ?? "us-east-1",
  credentialProvider: fromNodeProviderChain(),
});

export const PRIMARY_MODEL_ID =
  process.env.BEDROCK_MODEL_ID ?? "anthropic.claude-3-haiku-20240307-v1:0";

export const PRIMARY_MODEL = bedrock(PRIMARY_MODEL_ID);

export const TEMPERATURE = 0.2;
