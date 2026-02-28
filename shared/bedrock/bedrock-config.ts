/**
 * AWS Bedrock Configuration
 * 
 * Centralized configuration for AWS Bedrock integration.
 * All values are loaded from environment variables.
 */

export interface BedrockConfig {
  region: string;
  modelId: string;
  knowledgeBaseId?: string;
  guardrailId?: string;
  guardrailVersion?: string;
  maxTokens: number;
  temperature: number;
  topP: number;
  timeoutMs: number;
  maxRetries: number;
}

export function loadBedrockConfig(): BedrockConfig {
  return {
    region: process.env.AWS_REGION || 'us-east-1',
    modelId: process.env.BEDROCK_MODEL_ID || 'anthropic.claude-3-sonnet-20240229-v1:0',
    knowledgeBaseId: process.env.BEDROCK_KB_ID,
    guardrailId: process.env.BEDROCK_GUARDRAIL_ID,
    guardrailVersion: process.env.BEDROCK_GUARDRAIL_VERSION || 'DRAFT',
    maxTokens: parseInt(process.env.BEDROCK_MAX_TOKENS || '4096', 10),
    temperature: parseFloat(process.env.BEDROCK_TEMPERATURE || '0.7'),
    topP: parseFloat(process.env.BEDROCK_TOP_P || '0.9'),
    timeoutMs: parseInt(process.env.BEDROCK_TIMEOUT_MS || '30000', 10),
    maxRetries: parseInt(process.env.BEDROCK_MAX_RETRIES || '3', 10),
  };
}
