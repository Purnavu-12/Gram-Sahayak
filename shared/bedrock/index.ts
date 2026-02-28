/**
 * AWS Bedrock Integration Module
 * 
 * Provides unified access to AWS Bedrock services including:
 * - Foundation model invocation (Claude, Nova Pro, Titan)
 * - Knowledge Base retrieval and generation
 * - Guardrails for PII detection and content filtering
 * - Circuit breaker pattern for resilience
 * - Metrics collection for monitoring
 * - Response validation and sanitization
 */

export { BedrockConfig, loadBedrockConfig } from './bedrock-config';
export { BedrockAgentWrapper, InvokeModelRequest, InvokeModelResponse, RetrieveAndGenerateRequest, RetrieveAndGenerateResponse, Citation } from './bedrock-agent-wrapper';
export { FallbackHandler, CircuitState, CircuitBreakerConfig } from './fallback-handler';
export { GuardrailsIntegration, GuardrailsConfig, PiiDetectionResult } from './guardrails-integration';
export { ResponseValidator, ValidationResult, ValidationConfig } from './response-validator';
export { MetricsCollector, MetricEntry } from './metrics-collector';
export { KBIngestionPipeline, SchemeDocument, IngestionResult } from './kb-ingestion-pipeline';
