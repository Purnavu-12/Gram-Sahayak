/**
 * Bedrock Integration Type Definitions
 * Defines all interfaces for AWS Bedrock model integration
 */

// --- Configuration Types ---

export interface BedrockConfig {
  enabled: boolean;
  region: string;
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
  };
  models: {
    claude: {
      modelId: string;
      fallbackModelId: string;
      maxTokens: number;
      temperature: number;
    };
    novaPro: {
      sttModelId: string;
      ttsModelId: string;
      supportedLanguages: string[];
    };
    titanEmbeddings: {
      modelId: string;
      dimensions: number;
    };
  };
  guardrails: {
    policyId: string;
    policyVersion: string;
    enabledDetectors: string[];
  };
  knowledgeBase: {
    kbId: string;
    dataSourceId: string;
    maxResults: number;
  };
  fallback: {
    timeout: number;
    retries: number;
    circuitBreakerThreshold: number;
    circuitBreakerWindow: number;
  };
  monitoring: {
    enableMetrics: boolean;
    enableTracing: boolean;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
  };
}

// --- Claude Model Types ---

export interface ClaudeConfig {
  modelId: string;
  maxTokens: number;
  temperature: number;
  systemPrompt?: string;
}

export interface ClaudeResponse {
  content: string;
  stopReason: string;
  usage: {
    inputTokens: number;
    outputTokens: number;
  };
  confidence?: number;
}

// --- Nova Pro Types ---

export interface TranscriptionResult {
  transcription: string;
  confidence: number;
  language: 'hi' | 'en';
  duration: number;
  latency: number;
}

export interface TTSResult {
  audio: ArrayBuffer;
  format: string;
  sampleRate: number;
  duration: number;
  latency: number;
}

// --- Knowledge Base Types ---

export interface KBFilter {
  key: string;
  operator: '<=' | '>=' | '=' | '!=' | 'contains';
  value: string | number | boolean;
}

export interface KBResult {
  content: string;
  metadata: Record<string, any>;
  score: number;
  sourceLocation: string;
}

export interface KBSchemeResult {
  schemeName: string;
  description: string;
  eligibilityCriteria: string;
  benefits: string;
  relevanceScore: number;
  language: 'hi' | 'en';
}

export interface SchemeData {
  schemeId: string;
  name: {
    en: string;
    hi: string;
  };
  description: {
    en: string;
    hi: string;
  };
  eligibility: {
    ageMin?: number;
    ageMax?: number;
    incomeMax?: number;
    caste?: string[];
    gender?: string[];
    state?: string[];
    district?: string[];
  };
  benefits: {
    en: string;
    hi: string;
  };
  applicationProcess: {
    en: string;
    hi: string;
  };
}

export interface IngestionResult {
  successCount: number;
  failureCount: number;
  errors: IngestionError[];
  duration: number;
}

export interface IngestionError {
  schemeId: string;
  error: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// --- Guardrails Types ---

export interface GuardrailsResult {
  action: 'ALLOWED' | 'BLOCKED';
  outputText: string;
  piiDetections: PIIDetection[];
  assessments: Assessment[];
}

export interface PIIDetection {
  type: string;
  match: string;
  startOffset: number;
  endOffset: number;
}

export interface Assessment {
  topicPolicy: string;
  action: string;
}

export interface PIIRedactionResult {
  redactedText: string;
  detections: PIIDetection[];
  action: 'ALLOWED' | 'BLOCKED';
  confidence: number;
}

export interface PIIContext {
  originalText: string;
  redactedText: string;
  detections: PIIDetection[];
  timestamp: Date;
}

// --- Fallback Types ---

export interface FallbackOptions {
  timeout: number;
  retries: number;
  retryDelay: number;
  circuitBreakerThreshold: number;
  circuitBreakerWindow: number;
}

export interface FallbackResult<T> {
  data: T;
  source: 'primary' | 'fallback';
  latency: number;
  attempts: number;
}

export interface FallbackMetrics {
  totalRequests: number;
  primarySuccesses: number;
  primaryFailures: number;
  fallbackSuccesses: number;
  fallbackFailures: number;
  averageLatency: number;
}

// --- Monitoring Types ---

export interface BedrockMetrics {
  apiCalls: {
    total: number;
    byModel: Record<string, number>;
    byStatus: Record<string, number>;
  };
  latency: {
    average: number;
    p50: number;
    p95: number;
    p99: number;
    byModel: Record<string, LatencyStats>;
  };
  costs: {
    total: number;
    byModel: Record<string, number>;
    inputTokens: number;
    outputTokens: number;
  };
  fallbacks: {
    total: number;
    byService: Record<string, number>;
    byReason: Record<string, number>;
  };
  guardrails: {
    totalChecks: number;
    piiDetections: number;
    blockedRequests: number;
    falsePositives: number;
  };
  knowledgeBase: {
    queries: number;
    averageResults: number;
    averageRelevanceScore: number;
  };
}

export interface LatencyStats {
  count: number;
  average: number;
  min: number;
  max: number;
  p50: number;
  p95: number;
  p99: number;
}

// --- Service Status Types ---

export interface BedrockServiceStatus {
  enabled: boolean;
  available: boolean;
  lastCheck: Date;
  fallbackActive: boolean;
}

export interface BedrockHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: Record<string, {
    available: boolean;
    latency: number;
    lastCheck: Date;
  }>;
  credentials: {
    valid: boolean;
    expiresAt?: Date;
  };
}

// --- Enhanced User Profile ---

export interface EnhancedUserProfile {
  bedrockMetadata?: {
    extractionConfidence: number;
    extractionModel: string;
    extractionTimestamp: Date;
    piiRedacted: boolean;
  };
}

// --- Response Validation Types ---

export interface ResponseValidation {
  valid: boolean;
  errors: string[];
  confidence: number;
}
