/**
 * Performance Monitoring Utility
 * Tracks and reports performance metrics across services
 */

import { performance } from 'perf_hooks';

export interface PerformanceMetric {
  name: string;
  duration: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface ServiceMetrics {
  requestCount: number;
  errorCount: number;
  avgLatency: number;
  p50Latency: number;
  p95Latency: number;
  p99Latency: number;
  throughput: number;
  memoryUsage: {
    heapUsed: number;
    heapTotal: number;
    rss: number;
  };
}

export class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric[]>;
  private activeTimers: Map<string, number>;
  private windowSize: number;

  constructor(windowSize: number = 1000) {
    this.metrics = new Map();
    this.activeTimers = new Map();
    this.windowSize = windowSize;
  }

  /**
   * Start timing an operation
   */
  startTimer(name: string): void {
    this.activeTimers.set(name, performance.now());
  }

  /**
   * End timing and record metric
   */
  endTimer(name: string, metadata?: Record<string, any>): number {
    const startTime = this.activeTimers.get(name);
    if (!startTime) {
      console.warn(`No active timer found for: ${name}`);
      return 0;
    }

    const duration = performance.now() - startTime;
    this.activeTimers.delete(name);

    this.recordMetric({
      name,
      duration,
      timestamp: Date.now(),
      metadata,
    });

    return duration;
  }

  /**
   * Measure async operation
   */
  async measure<T>(
    name: string,
    fn: () => Promise<T>,
    metadata?: Record<string, any>
  ): Promise<T> {
    const startTime = performance.now();
    try {
      const result = await fn();
      const duration = performance.now() - startTime;
      
      this.recordMetric({
        name,
        duration,
        timestamp: Date.now(),
        metadata: { ...metadata, success: true },
      });
      
      return result;
    } catch (error) {
      const duration = performance.now() - startTime;
      
      this.recordMetric({
        name,
        duration,
        timestamp: Date.now(),
        metadata: { ...metadata, success: false, error: String(error) },
      });
      
      throw error;
    }
  }

  /**
   * Record a metric manually
   */
  recordMetric(metric: PerformanceMetric): void {
    const metrics = this.metrics.get(metric.name) || [];
    metrics.push(metric);

    // Keep only recent metrics within window
    if (metrics.length > this.windowSize) {
      metrics.shift();
    }

    this.metrics.set(metric.name, metrics);
  }

  /**
   * Get metrics for a specific operation
   */
  getMetrics(name: string): PerformanceMetric[] {
    return this.metrics.get(name) || [];
  }

  /**
   * Get aggregated statistics for an operation
   */
  getStats(name: string): {
    count: number;
    mean: number;
    p50: number;
    p95: number;
    p99: number;
    min: number;
    max: number;
  } | null {
    const metrics = this.metrics.get(name);
    if (!metrics || metrics.length === 0) {
      return null;
    }

    const durations = metrics.map(m => m.duration).sort((a, b) => a - b);
    const sum = durations.reduce((a, b) => a + b, 0);

    return {
      count: durations.length,
      mean: sum / durations.length,
      p50: durations[Math.floor(durations.length * 0.5)],
      p95: durations[Math.floor(durations.length * 0.95)],
      p99: durations[Math.floor(durations.length * 0.99)],
      min: durations[0],
      max: durations[durations.length - 1],
    };
  }

  /**
   * Get service-level metrics
   */
  getServiceMetrics(serviceName: string): ServiceMetrics {
    const allMetrics = Array.from(this.metrics.entries())
      .filter(([name]) => name.startsWith(serviceName))
      .flatMap(([_, metrics]) => metrics);

    if (allMetrics.length === 0) {
      return this.getEmptyMetrics();
    }

    const durations = allMetrics.map(m => m.duration).sort((a, b) => a - b);
    const errors = allMetrics.filter(m => m.metadata?.success === false).length;
    const sum = durations.reduce((a, b) => a + b, 0);

    // Calculate time window for throughput
    const timestamps = allMetrics.map(m => m.timestamp);
    const timeWindow = (Math.max(...timestamps) - Math.min(...timestamps)) / 1000; // seconds

    const memUsage = process.memoryUsage();

    return {
      requestCount: allMetrics.length,
      errorCount: errors,
      avgLatency: sum / durations.length,
      p50Latency: durations[Math.floor(durations.length * 0.5)],
      p95Latency: durations[Math.floor(durations.length * 0.95)],
      p99Latency: durations[Math.floor(durations.length * 0.99)],
      throughput: timeWindow > 0 ? allMetrics.length / timeWindow : 0,
      memoryUsage: {
        heapUsed: memUsage.heapUsed / 1024 / 1024,
        heapTotal: memUsage.heapTotal / 1024 / 1024,
        rss: memUsage.rss / 1024 / 1024,
      },
    };
  }

  /**
   * Get all service metrics
   */
  getAllServiceMetrics(): Map<string, ServiceMetrics> {
    const services = new Set<string>();
    
    for (const name of this.metrics.keys()) {
      const serviceName = name.split(':')[0];
      services.add(serviceName);
    }

    const result = new Map<string, ServiceMetrics>();
    for (const service of services) {
      result.set(service, this.getServiceMetrics(service));
    }

    return result;
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics.clear();
    this.activeTimers.clear();
  }

  /**
   * Clear metrics for specific operation
   */
  clearMetrics(name: string): void {
    this.metrics.delete(name);
  }

  /**
   * Export metrics for analysis
   */
  exportMetrics(): {
    timestamp: number;
    metrics: Record<string, PerformanceMetric[]>;
    stats: Record<string, any>;
  } {
    const stats: Record<string, any> = {};
    
    for (const name of this.metrics.keys()) {
      stats[name] = this.getStats(name);
    }

    return {
      timestamp: Date.now(),
      metrics: Object.fromEntries(this.metrics),
      stats,
    };
  }

  private getEmptyMetrics(): ServiceMetrics {
    const memUsage = process.memoryUsage();
    
    return {
      requestCount: 0,
      errorCount: 0,
      avgLatency: 0,
      p50Latency: 0,
      p95Latency: 0,
      p99Latency: 0,
      throughput: 0,
      memoryUsage: {
        heapUsed: memUsage.heapUsed / 1024 / 1024,
        heapTotal: memUsage.heapTotal / 1024 / 1024,
        rss: memUsage.rss / 1024 / 1024,
      },
    };
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

/**
 * Decorator for measuring method performance
 */
export function Measure(metricName?: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;
    const name = metricName || `${target.constructor.name}.${propertyKey}`;

    descriptor.value = async function (...args: any[]) {
      return performanceMonitor.measure(name, () => originalMethod.apply(this, args));
    };

    return descriptor;
  };
}
