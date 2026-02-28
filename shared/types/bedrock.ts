/**
 * AWS Bedrock Type Definitions
 * 
 * Shared types for Bedrock integration across services.
 */

export interface BedrockModelConfig {
  modelId: string;
  maxTokens: number;
  temperature: number;
  topP: number;
}

export interface BedrockInferenceResult {
  text: string;
  confidence: number;
  modelId: string;
  latencyMs: number;
  tokenUsage: {
    input: number;
    output: number;
  };
}

export interface BedrockKBQueryResult {
  answer: string;
  sources: Array<{
    uri: string;
    relevanceScore: number;
    excerpt: string;
  }>;
  latencyMs: number;
}

export interface BedrockGuardrailResult {
  allowed: boolean;
  blockedReason?: string;
  piiDetected: boolean;
  redactedText?: string;
}
