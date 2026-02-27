/**
 * Bedrock Integration Module
 * Central export for all Bedrock integration components
 */

export { BedrockAgentWrapper } from './bedrock-agent-wrapper';
export { FallbackHandler } from './fallback-handler';
export { GuardrailsIntegration } from './guardrails-integration';
export { BedrockMetricsCollector } from './metrics-collector';
export { ResponseValidator } from './response-validator';
export { KBIngestionPipeline } from './kb-ingestion-pipeline';
export { loadBedrockConfig, validateBedrockConfig } from './bedrock-config';
