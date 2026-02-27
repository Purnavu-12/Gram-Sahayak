/**
 * Bedrock Configuration Management
 * Loads and validates Bedrock configuration from environment variables
 */

import { BedrockConfig } from '../types/bedrock';

const DEFAULT_CONFIG: BedrockConfig = {
  enabled: false,
  region: 'us-east-1',
  credentials: {
    accessKeyId: '',
    secretAccessKey: '',
  },
  models: {
    claude: {
      modelId: 'anthropic.claude-3-5-sonnet-20241022-v2:0',
      fallbackModelId: 'anthropic.claude-3-haiku-20240307-v1:0',
      maxTokens: 1000,
      temperature: 0.3,
    },
    novaPro: {
      sttModelId: 'amazon.nova-pro-v1:0',
      ttsModelId: 'amazon.nova-pro-v1:0',
      supportedLanguages: ['hi', 'en'],
    },
    titanEmbeddings: {
      modelId: 'amazon.titan-embed-text-v2:0',
      dimensions: 1024,
    },
  },
  guardrails: {
    policyId: '',
    policyVersion: 'DRAFT',
    enabledDetectors: ['NAME', 'ADDRESS', 'PHONE', 'AADHAAR'],
  },
  knowledgeBase: {
    kbId: '',
    dataSourceId: '',
    maxResults: 3,
  },
  fallback: {
    timeout: 3000,
    retries: 2,
    circuitBreakerThreshold: 50,
    circuitBreakerWindow: 60,
  },
  monitoring: {
    enableMetrics: true,
    enableTracing: true,
    logLevel: 'info',
  },
};

/**
 * Load Bedrock configuration from environment variables with defaults
 */
export function loadBedrockConfig(): BedrockConfig {
  return {
    enabled: process.env.BEDROCK_ENABLED === 'true',
    region: process.env.BEDROCK_REGION || DEFAULT_CONFIG.region,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
      sessionToken: process.env.AWS_SESSION_TOKEN,
    },
    models: {
      claude: {
        modelId: process.env.BEDROCK_CLAUDE_MODEL_ID || DEFAULT_CONFIG.models.claude.modelId,
        fallbackModelId: process.env.BEDROCK_CLAUDE_FALLBACK_MODEL_ID || DEFAULT_CONFIG.models.claude.fallbackModelId,
        maxTokens: parseInt(process.env.BEDROCK_CLAUDE_MAX_TOKENS || '1000', 10),
        temperature: parseFloat(process.env.BEDROCK_CLAUDE_TEMPERATURE || '0.3'),
      },
      novaPro: {
        sttModelId: process.env.BEDROCK_NOVA_PRO_STT_MODEL_ID || DEFAULT_CONFIG.models.novaPro.sttModelId,
        ttsModelId: process.env.BEDROCK_NOVA_PRO_TTS_MODEL_ID || DEFAULT_CONFIG.models.novaPro.ttsModelId,
        supportedLanguages: DEFAULT_CONFIG.models.novaPro.supportedLanguages,
      },
      titanEmbeddings: {
        modelId: process.env.BEDROCK_TITAN_EMBEDDINGS_MODEL_ID || DEFAULT_CONFIG.models.titanEmbeddings.modelId,
        dimensions: parseInt(process.env.BEDROCK_TITAN_DIMENSIONS || '1024', 10),
      },
    },
    guardrails: {
      policyId: process.env.BEDROCK_GUARDRAILS_POLICY_ID || '',
      policyVersion: process.env.BEDROCK_GUARDRAILS_POLICY_VERSION || 'DRAFT',
      enabledDetectors: DEFAULT_CONFIG.guardrails.enabledDetectors,
    },
    knowledgeBase: {
      kbId: process.env.BEDROCK_KB_ID || '',
      dataSourceId: process.env.BEDROCK_KB_DATA_SOURCE_ID || '',
      maxResults: parseInt(process.env.BEDROCK_KB_MAX_RESULTS || '3', 10),
    },
    fallback: {
      timeout: parseInt(process.env.BEDROCK_FALLBACK_TIMEOUT || '3000', 10),
      retries: parseInt(process.env.BEDROCK_FALLBACK_RETRIES || '2', 10),
      circuitBreakerThreshold: parseInt(process.env.BEDROCK_CB_THRESHOLD || '50', 10),
      circuitBreakerWindow: parseInt(process.env.BEDROCK_CB_WINDOW || '60', 10),
    },
    monitoring: {
      enableMetrics: process.env.BEDROCK_METRICS !== 'false',
      enableTracing: process.env.BEDROCK_TRACING !== 'false',
      logLevel: (process.env.BEDROCK_LOG_LEVEL as any) || 'info',
    },
  };
}

/**
 * Validate Bedrock configuration for required fields
 */
export function validateBedrockConfig(config: BedrockConfig): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (config.enabled) {
    if (!config.credentials.accessKeyId) {
      errors.push('AWS_ACCESS_KEY_ID is required when Bedrock is enabled');
    }
    if (!config.credentials.secretAccessKey) {
      errors.push('AWS_SECRET_ACCESS_KEY is required when Bedrock is enabled');
    }
    if (!config.region) {
      errors.push('BEDROCK_REGION is required');
    }
  }

  return { valid: errors.length === 0, errors };
}

export { DEFAULT_CONFIG };
