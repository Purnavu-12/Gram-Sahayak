/**
 * Bedrock Metrics Collector
 * Tracks API calls, latency, costs, fallbacks, and guardrails activity
 * Validates: Requirements 11.1-11.7
 */

import { BedrockMetrics, LatencyStats } from '../types/bedrock';

export class BedrockMetricsCollector {
  private latencies: Map<string, number[]> = new Map();
  private metrics: BedrockMetrics = {
    apiCalls: { total: 0, byModel: {}, byStatus: {} },
    latency: {
      average: 0,
      p50: 0,
      p95: 0,
      p99: 0,
      byModel: {},
    },
    costs: { total: 0, byModel: {}, inputTokens: 0, outputTokens: 0 },
    fallbacks: { total: 0, byService: {}, byReason: {} },
    guardrails: {
      totalChecks: 0,
      piiDetections: 0,
      blockedRequests: 0,
      falsePositives: 0,
    },
    knowledgeBase: {
      queries: 0,
      averageResults: 0,
      averageRelevanceScore: 0,
    },
  };

  /**
   * Record an API call
   * Validates: Requirement 11.1, 11.3
   */
  recordApiCall(model: string, status: 'success' | 'error', latencyMs: number): void {
    this.metrics.apiCalls.total++;
    this.metrics.apiCalls.byModel[model] = (this.metrics.apiCalls.byModel[model] || 0) + 1;
    this.metrics.apiCalls.byStatus[status] = (this.metrics.apiCalls.byStatus[status] || 0) + 1;

    // Track latency
    if (!this.latencies.has(model)) {
      this.latencies.set(model, []);
    }
    this.latencies.get(model)!.push(latencyMs);
    this.updateLatencyStats();
  }

  /**
   * Record cost for a request
   * Validates: Requirement 11.2
   */
  recordCost(model: string, inputTokens: number, outputTokens: number): void {
    // Approximate costs per 1000 tokens
    const costRates: Record<string, { input: number; output: number }> = {
      claude: { input: 0.003, output: 0.015 },
      'claude-haiku': { input: 0.00025, output: 0.00125 },
      'nova-pro': { input: 0.0008, output: 0.0032 },
      'titan-embeddings': { input: 0.0001, output: 0 },
    };

    const rate = costRates[model] || { input: 0.001, output: 0.005 };
    const cost = (inputTokens / 1000) * rate.input + (outputTokens / 1000) * rate.output;

    this.metrics.costs.total += cost;
    this.metrics.costs.byModel[model] = (this.metrics.costs.byModel[model] || 0) + cost;
    this.metrics.costs.inputTokens += inputTokens;
    this.metrics.costs.outputTokens += outputTokens;
  }

  /**
   * Record a fallback event
   * Validates: Requirement 11.4
   */
  recordFallback(service: string, reason: string): void {
    this.metrics.fallbacks.total++;
    this.metrics.fallbacks.byService[service] =
      (this.metrics.fallbacks.byService[service] || 0) + 1;
    this.metrics.fallbacks.byReason[reason] =
      (this.metrics.fallbacks.byReason[reason] || 0) + 1;
  }

  /**
   * Record guardrails activity
   * Validates: Requirement 11.5
   */
  recordGuardrailsCheck(piiDetected: boolean, blocked: boolean): void {
    this.metrics.guardrails.totalChecks++;
    if (piiDetected) this.metrics.guardrails.piiDetections++;
    if (blocked) this.metrics.guardrails.blockedRequests++;
  }

  recordGuardrailsFalsePositive(): void {
    this.metrics.guardrails.falsePositives++;
  }

  /**
   * Record Knowledge Base query
   */
  recordKBQuery(resultCount: number, avgRelevance: number): void {
    const prev = this.metrics.knowledgeBase;
    const totalQueries = prev.queries + 1;
    prev.averageResults =
      (prev.averageResults * prev.queries + resultCount) / totalQueries;
    prev.averageRelevanceScore =
      (prev.averageRelevanceScore * prev.queries + avgRelevance) / totalQueries;
    prev.queries = totalQueries;
  }

  /**
   * Get current metrics
   */
  getMetrics(): BedrockMetrics {
    return JSON.parse(JSON.stringify(this.metrics));
  }

  /**
   * Export metrics in Prometheus format
   * Validates: Requirement 11.6
   */
  toPrometheusFormat(): string {
    const lines: string[] = [];

    // API calls
    lines.push('# HELP bedrock_api_calls_total Total number of Bedrock API calls');
    lines.push('# TYPE bedrock_api_calls_total counter');
    for (const [model, count] of Object.entries(this.metrics.apiCalls.byModel)) {
      lines.push(`bedrock_api_calls_total{model="${model}"} ${count}`);
    }

    // Latency
    lines.push('# HELP bedrock_api_latency_ms API call latency in milliseconds');
    lines.push('# TYPE bedrock_api_latency_ms gauge');
    lines.push(`bedrock_api_latency_ms{quantile="0.5"} ${this.metrics.latency.p50}`);
    lines.push(`bedrock_api_latency_ms{quantile="0.95"} ${this.metrics.latency.p95}`);
    lines.push(`bedrock_api_latency_ms{quantile="0.99"} ${this.metrics.latency.p99}`);

    // Costs
    lines.push('# HELP bedrock_cost_usd_total Total cost in USD');
    lines.push('# TYPE bedrock_cost_usd_total counter');
    for (const [model, cost] of Object.entries(this.metrics.costs.byModel)) {
      lines.push(`bedrock_cost_usd_total{model="${model}"} ${cost.toFixed(4)}`);
    }

    // Fallbacks
    lines.push('# HELP bedrock_fallback_total Total number of fallback invocations');
    lines.push('# TYPE bedrock_fallback_total counter');
    for (const [service, count] of Object.entries(this.metrics.fallbacks.byService)) {
      lines.push(`bedrock_fallback_total{service="${service}"} ${count}`);
    }

    // Guardrails
    lines.push('# HELP bedrock_guardrails_pii_detections_total PII detections');
    lines.push('# TYPE bedrock_guardrails_pii_detections_total counter');
    lines.push(
      `bedrock_guardrails_pii_detections_total ${this.metrics.guardrails.piiDetections}`
    );

    return lines.join('\n');
  }

  /**
   * Check if fallback rate exceeds alert threshold
   * Validates: Requirement 11.7
   */
  shouldAlert(): boolean {
    if (this.metrics.apiCalls.total === 0) return false;
    const fallbackRate = (this.metrics.fallbacks.total / this.metrics.apiCalls.total) * 100;
    return fallbackRate > 20;
  }

  private updateLatencyStats(): void {
    const allLatencies: number[] = [];
    for (const latencyList of this.latencies.values()) {
      allLatencies.push(...latencyList);
    }

    if (allLatencies.length === 0) return;

    allLatencies.sort((a, b) => a - b);
    const len = allLatencies.length;

    this.metrics.latency.average =
      allLatencies.reduce((a, b) => a + b, 0) / len;
    this.metrics.latency.p50 = allLatencies[Math.floor(len * 0.5)] || 0;
    this.metrics.latency.p95 = allLatencies[Math.floor(len * 0.95)] || 0;
    this.metrics.latency.p99 = allLatencies[Math.floor(len * 0.99)] || 0;

    // Per-model stats
    for (const [model, latencyList] of this.latencies.entries()) {
      this.metrics.latency.byModel[model] = this.calculateLatencyStats(latencyList);
    }
  }

  private calculateLatencyStats(values: number[]): LatencyStats {
    if (values.length === 0) {
      return { count: 0, average: 0, min: 0, max: 0, p50: 0, p95: 0, p99: 0 };
    }

    const sorted = [...values].sort((a, b) => a - b);
    const len = sorted.length;

    return {
      count: len,
      average: sorted.reduce((a, b) => a + b, 0) / len,
      min: sorted[0],
      max: sorted[len - 1],
      p50: sorted[Math.floor(len * 0.5)] || 0,
      p95: sorted[Math.floor(len * 0.95)] || 0,
      p99: sorted[Math.floor(len * 0.99)] || 0,
    };
  }

  /**
   * Reset all metrics
   */
  reset(): void {
    this.latencies.clear();
    this.metrics = {
      apiCalls: { total: 0, byModel: {}, byStatus: {} },
      latency: { average: 0, p50: 0, p95: 0, p99: 0, byModel: {} },
      costs: { total: 0, byModel: {}, inputTokens: 0, outputTokens: 0 },
      fallbacks: { total: 0, byService: {}, byReason: {} },
      guardrails: {
        totalChecks: 0,
        piiDetections: 0,
        blockedRequests: 0,
        falsePositives: 0,
      },
      knowledgeBase: {
        queries: 0,
        averageResults: 0,
        averageRelevanceScore: 0,
      },
    };
  }
}
