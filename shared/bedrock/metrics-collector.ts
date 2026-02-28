/**
 * Metrics Collector
 * 
 * Collects and exposes metrics for Bedrock API usage in Prometheus format.
 */

export interface MetricEntry {
  name: string;
  value: number;
  labels: Record<string, string>;
  timestamp: number;
}

export class MetricsCollector {
  private metrics: Map<string, MetricEntry[]> = new Map();
  private maxEntriesPerMetric: number;

  constructor(maxEntriesPerMetric: number = 10000) {
    this.maxEntriesPerMetric = maxEntriesPerMetric;
  }

  /**
   * Record a metric value.
   */
  record(name: string, value: number, labels: Record<string, string> = {}): void {
    const entries = this.metrics.get(name) || [];
    entries.push({
      name,
      value,
      labels,
      timestamp: Date.now(),
    });
    // Evict oldest entries if exceeding max
    if (entries.length > this.maxEntriesPerMetric) {
      entries.splice(0, entries.length - this.maxEntriesPerMetric);
    }
    this.metrics.set(name, entries);
  }

  /**
   * Record API latency.
   */
  recordLatency(operation: string, latencyMs: number, modelId: string): void {
    this.record('bedrock_api_latency_ms', latencyMs, { operation, model_id: modelId });
  }

  /**
   * Record token usage.
   */
  recordTokenUsage(inputTokens: number, outputTokens: number, modelId: string): void {
    this.record('bedrock_input_tokens', inputTokens, { model_id: modelId });
    this.record('bedrock_output_tokens', outputTokens, { model_id: modelId });
  }

  /**
   * Record an API error.
   */
  recordError(operation: string, errorType: string): void {
    this.record('bedrock_api_errors', 1, { operation, error_type: errorType });
  }

  /**
   * Get all metrics in Prometheus text format.
   */
  getPrometheusMetrics(): string {
    const lines: string[] = [];

    for (const [name, entries] of this.metrics) {
      for (const entry of entries) {
        const labelStr = Object.entries(entry.labels)
          .map(([k, v]) => `${k}="${String(v).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')}"`)
          .join(',');
        lines.push(`${name}{${labelStr}} ${entry.value}`);
      }
    }

    return lines.join('\n');
  }

  /**
   * Get metrics summary.
   */
  getSummary(): Record<string, number> {
    const summary: Record<string, number> = {};
    for (const [name, entries] of this.metrics) {
      summary[name] = entries.reduce((sum, e) => sum + e.value, 0);
    }
    return summary;
  }

  /**
   * Reset all metrics.
   */
  reset(): void {
    this.metrics.clear();
  }
}
