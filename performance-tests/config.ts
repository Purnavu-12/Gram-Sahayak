/**
 * Performance Testing Configuration
 * Defines targets and thresholds for Gram Sahayak system performance
 */

export const PERFORMANCE_TARGETS = {
  // Voice recognition latency target (ms)
  VOICE_RECOGNITION_LATENCY: 500,
  
  // Concurrent users target
  CONCURRENT_USERS: 10000,
  
  // Database query thresholds (ms)
  DB_QUERY_SIMPLE: 50,
  DB_QUERY_COMPLEX: 200,
  
  // API response times (ms)
  API_RESPONSE_P50: 100,
  API_RESPONSE_P95: 300,
  API_RESPONSE_P99: 500,
  
  // Memory usage limits (MB)
  MEMORY_LIMIT_PER_SERVICE: 512,
  MEMORY_LIMIT_TOTAL: 4096,
  
  // Cache hit rate targets (%)
  CACHE_HIT_RATE: 80,
  
  // Throughput targets (requests/second)
  THROUGHPUT_MIN: 1000,
};

export const TEST_SCENARIOS = {
  // Voice processing scenarios
  VOICE_SHORT_UTTERANCE: 'short_utterance',
  VOICE_LONG_CONVERSATION: 'long_conversation',
  VOICE_NOISY_ENVIRONMENT: 'noisy_environment',
  
  // Scheme matching scenarios
  SCHEME_SIMPLE_MATCH: 'simple_match',
  SCHEME_COMPLEX_ELIGIBILITY: 'complex_eligibility',
  SCHEME_BULK_SEARCH: 'bulk_search',
  
  // Form generation scenarios
  FORM_SIMPLE: 'simple_form',
  FORM_COMPLEX: 'complex_form',
  FORM_PDF_GENERATION: 'pdf_generation',
  
  // Load testing scenarios
  LOAD_RAMP_UP: 'ramp_up',
  LOAD_SUSTAINED: 'sustained',
  LOAD_SPIKE: 'spike',
};

export interface PerformanceMetrics {
  latency: {
    min: number;
    max: number;
    mean: number;
    p50: number;
    p95: number;
    p99: number;
  };
  throughput: {
    requestsPerSecond: number;
    totalRequests: number;
    duration: number;
  };
  errors: {
    count: number;
    rate: number;
  };
  memory: {
    heapUsed: number;
    heapTotal: number;
    external: number;
    rss: number;
  };
}

export interface LoadTestConfig {
  scenario: string;
  duration: number; // seconds
  rampUpTime: number; // seconds
  targetUsers: number;
  requestsPerUser: number;
}
