/**
 * Database Query Optimizer
 * Provides query optimization utilities and patterns
 */

export interface QueryMetrics {
  queryTime: number;
  rowsReturned: number;
  indexUsed: boolean;
  cacheHit: boolean;
}

export class QueryOptimizer {
  private queryCache: Map<string, { result: any; timestamp: number }>;
  private queryMetrics: Map<string, QueryMetrics[]>;
  private cacheTTL: number;

  constructor(cacheTTL: number = 60000) {
    this.queryCache = new Map();
    this.queryMetrics = new Map();
    this.cacheTTL = cacheTTL;
  }

  /**
   * Execute query with caching and metrics
   */
  async executeQuery<T>(
    queryKey: string,
    queryFn: () => Promise<T>,
    options: {
      cache?: boolean;
      ttl?: number;
      trackMetrics?: boolean;
    } = {}
  ): Promise<T> {
    const { cache = true, ttl = this.cacheTTL, trackMetrics = true } = options;

    // Check cache first
    if (cache) {
      const cached = this.queryCache.get(queryKey);
      if (cached && Date.now() - cached.timestamp < ttl) {
        if (trackMetrics) {
          this.recordMetric(queryKey, {
            queryTime: 0,
            rowsReturned: 0,
            indexUsed: false,
            cacheHit: true,
          });
        }
        return cached.result;
      }
    }

    // Execute query with timing
    const startTime = performance.now();
    const result = await queryFn();
    const queryTime = performance.now() - startTime;

    // Cache result
    if (cache) {
      this.queryCache.set(queryKey, {
        result,
        timestamp: Date.now(),
      });
    }

    // Record metrics
    if (trackMetrics) {
      this.recordMetric(queryKey, {
        queryTime,
        rowsReturned: Array.isArray(result) ? result.length : 1,
        indexUsed: true, // Assume index used for now
        cacheHit: false,
      });
    }

    return result;
  }

  /**
   * Batch multiple queries for efficiency
   */
  async batchQuery<T>(
    queries: Array<{ key: string; fn: () => Promise<T> }>,
    options: { parallel?: boolean } = {}
  ): Promise<T[]> {
    const { parallel = true } = options;

    if (parallel) {
      return Promise.all(queries.map(q => this.executeQuery(q.key, q.fn)));
    } else {
      const results: T[] = [];
      for (const query of queries) {
        results.push(await this.executeQuery(query.key, query.fn));
      }
      return results;
    }
  }

  /**
   * Invalidate cache for specific query or pattern
   */
  invalidateCache(pattern?: string): void {
    if (!pattern) {
      this.queryCache.clear();
      return;
    }

    const keysToDelete: string[] = [];
    for (const key of this.queryCache.keys()) {
      if (key.includes(pattern)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.queryCache.delete(key));
  }

  /**
   * Get query performance metrics
   */
  getMetrics(queryKey?: string): Map<string, QueryMetrics[]> | QueryMetrics[] | undefined {
    if (queryKey) {
      return this.queryMetrics.get(queryKey);
    }
    return this.queryMetrics;
  }

  /**
   * Get aggregated statistics
   */
  getStats(): {
    totalQueries: number;
    cacheHitRate: number;
    avgQueryTime: number;
    slowQueries: Array<{ key: string; avgTime: number }>;
  } {
    let totalQueries = 0;
    let cacheHits = 0;
    let totalQueryTime = 0;
    const queryAvgTimes: Map<string, number> = new Map();

    for (const [key, metrics] of this.queryMetrics.entries()) {
      totalQueries += metrics.length;
      cacheHits += metrics.filter(m => m.cacheHit).length;
      
      const avgTime = metrics.reduce((sum, m) => sum + m.queryTime, 0) / metrics.length;
      totalQueryTime += avgTime * metrics.length;
      queryAvgTimes.set(key, avgTime);
    }

    const slowQueries = Array.from(queryAvgTimes.entries())
      .map(([key, avgTime]) => ({ key, avgTime }))
      .sort((a, b) => b.avgTime - a.avgTime)
      .slice(0, 10);

    return {
      totalQueries,
      cacheHitRate: totalQueries > 0 ? cacheHits / totalQueries : 0,
      avgQueryTime: totalQueries > 0 ? totalQueryTime / totalQueries : 0,
      slowQueries,
    };
  }

  private recordMetric(queryKey: string, metric: QueryMetrics): void {
    const metrics = this.queryMetrics.get(queryKey) || [];
    metrics.push(metric);
    
    // Keep only last 100 metrics per query
    if (metrics.length > 100) {
      metrics.shift();
    }
    
    this.queryMetrics.set(queryKey, metrics);
  }
}

/**
 * Query builder with optimization hints
 */
export class OptimizedQueryBuilder {
  private conditions: string[];
  private indexes: string[];
  private limit?: number;
  private offset?: number;

  constructor() {
    this.conditions = [];
    this.indexes = [];
  }

  where(condition: string, useIndex?: string): this {
    this.conditions.push(condition);
    if (useIndex) {
      this.indexes.push(useIndex);
    }
    return this;
  }

  paginate(limit: number, offset: number = 0): this {
    this.limit = limit;
    this.offset = offset;
    return this;
  }

  build(): {
    conditions: string[];
    indexes: string[];
    limit?: number;
    offset?: number;
  } {
    return {
      conditions: this.conditions,
      indexes: this.indexes,
      limit: this.limit,
      offset: this.offset,
    };
  }
}

// Global query optimizer instance
export const queryOptimizer = new QueryOptimizer();
