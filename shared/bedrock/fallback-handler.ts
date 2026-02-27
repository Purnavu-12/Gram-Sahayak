/**
 * Fallback Handler for Bedrock Integration
 * Manages graceful degradation from Bedrock to existing implementations
 * Validates: Requirements 1.5, 1.6, 1.7, 7.1-7.7
 */

import { FallbackOptions, FallbackResult, FallbackMetrics } from '../types/bedrock';

export interface CircuitBreakerState {
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failureCount: number;
  successCount: number;
  lastFailureTime?: Date;
  nextAttemptTime?: Date;
}

export class FallbackHandler {
  private metrics: FallbackMetrics = {
    totalRequests: 0,
    primarySuccesses: 0,
    primaryFailures: 0,
    fallbackSuccesses: 0,
    fallbackFailures: 0,
    averageLatency: 0,
  };

  private circuitStates: Map<string, CircuitBreakerState> = new Map();
  private fallbackLog: Array<{
    timestamp: Date;
    serviceId: string;
    error: string;
    fallbackDestination: string;
    latency: number;
  }> = [];

  private defaultOptions: FallbackOptions = {
    timeout: 3000,
    retries: 2,
    retryDelay: 100,
    circuitBreakerThreshold: 50,
    circuitBreakerWindow: 60,
  };

  constructor(private options?: Partial<FallbackOptions>) {
    if (options) {
      this.defaultOptions = { ...this.defaultOptions, ...options };
    }
  }

  /**
   * Execute with automatic fallback on failure
   * Validates: Requirements 1.5, 1.6, 7.1, 7.2
   */
  async executeWithFallback<T>(
    primary: () => Promise<T>,
    fallback: () => Promise<T>,
    options?: Partial<FallbackOptions>,
    serviceId: string = 'default'
  ): Promise<FallbackResult<T>> {
    const opts = { ...this.defaultOptions, ...options };
    const startTime = Date.now();
    this.metrics.totalRequests++;

    // Check circuit breaker
    const circuitState = this.getCircuitState(serviceId);
    if (circuitState.state === 'OPEN') {
      if (circuitState.nextAttemptTime && Date.now() < circuitState.nextAttemptTime.getTime()) {
        // Circuit is open, go directly to fallback
        return this.executeFallback(fallback, startTime, serviceId, 'circuit_open');
      }
      // Try half-open
      circuitState.state = 'HALF_OPEN';
    }

    // Try primary with timeout and retries
    let lastError: Error | undefined;
    for (let attempt = 0; attempt <= opts.retries; attempt++) {
      try {
        const result = await this.executeWithTimeout(primary, opts.timeout);
        const latency = Date.now() - startTime;

        // Success - update circuit breaker
        this.onPrimarySuccess(serviceId);
        this.metrics.primarySuccesses++;
        this.updateAverageLatency(latency);

        return {
          data: result,
          source: 'primary',
          latency,
          attempts: attempt + 1,
        };
      } catch (error: any) {
        lastError = error;
        if (attempt < opts.retries) {
          await this.delay(opts.retryDelay * Math.pow(2, attempt));
        }
      }
    }

    // Primary failed - update circuit breaker and try fallback
    this.onPrimaryFailure(serviceId);
    this.metrics.primaryFailures++;

    return this.executeFallback(
      fallback,
      startTime,
      serviceId,
      lastError?.message || 'unknown_error'
    );
  }

  /**
   * Execute with model tier fallback
   * Validates: Requirement 1.7
   * Sequence: Claude 3.5 Sonnet → Claude 3 Haiku → Existing
   */
  async executeWithModelTierFallback<T>(
    primaryModel: () => Promise<T>,
    fallbackModel: () => Promise<T>,
    existingImpl: () => Promise<T>,
    serviceId: string = 'claude'
  ): Promise<FallbackResult<T>> {
    const startTime = Date.now();
    this.metrics.totalRequests++;

    // Try primary model (Claude 3.5 Sonnet)
    try {
      const result = await this.executeWithTimeout(primaryModel, this.defaultOptions.timeout);
      this.metrics.primarySuccesses++;
      this.onPrimarySuccess(serviceId);
      return {
        data: result,
        source: 'primary',
        latency: Date.now() - startTime,
        attempts: 1,
      };
    } catch {
      // Primary model failed
    }

    // Try fallback model (Claude 3 Haiku)
    try {
      const result = await this.executeWithTimeout(fallbackModel, this.defaultOptions.timeout);
      this.logFallbackEvent(serviceId, 'primary_model_failed', 'fallback_model');
      return {
        data: result,
        source: 'fallback',
        latency: Date.now() - startTime,
        attempts: 2,
      };
    } catch {
      // Fallback model failed
    }

    // Fall through to existing implementation
    return this.executeFallback(existingImpl, startTime, serviceId, 'all_models_failed');
  }

  private async executeFallback<T>(
    fallback: () => Promise<T>,
    startTime: number,
    serviceId: string,
    reason: string
  ): Promise<FallbackResult<T>> {
    try {
      const result = await fallback();
      const latency = Date.now() - startTime;

      this.metrics.fallbackSuccesses++;
      this.logFallbackEvent(serviceId, reason, 'existing_implementation');
      this.updateAverageLatency(latency);

      return {
        data: result,
        source: 'fallback',
        latency,
        attempts: this.defaultOptions.retries + 1,
      };
    } catch (error: any) {
      this.metrics.fallbackFailures++;
      throw new Error(`Both primary and fallback failed for ${serviceId}: ${error.message}`);
    }
  }

  private async executeWithTimeout<T>(fn: () => Promise<T>, timeout: number): Promise<T> {
    return Promise.race([
      fn(),
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), timeout)
      ),
    ]);
  }

  private onPrimarySuccess(serviceId: string): void {
    const state = this.getCircuitState(serviceId);
    if (state.state === 'HALF_OPEN') {
      state.successCount++;
      if (state.successCount >= 2) {
        state.state = 'CLOSED';
        state.failureCount = 0;
        state.successCount = 0;
      }
    } else {
      state.failureCount = 0;
    }
  }

  private onPrimaryFailure(serviceId: string): void {
    const state = this.getCircuitState(serviceId);
    state.failureCount++;
    state.lastFailureTime = new Date();
    state.successCount = 0;

    const threshold = this.defaultOptions.circuitBreakerThreshold;
    // Open circuit after exceeding the configured failure count threshold
    if (state.failureCount >= Math.max(threshold / 10, 5)) {
      state.state = 'OPEN';
      state.nextAttemptTime = new Date(Date.now() + this.defaultOptions.circuitBreakerWindow * 1000);
    }
  }

  private logFallbackEvent(serviceId: string, error: string, destination: string): void {
    this.fallbackLog.push({
      timestamp: new Date(),
      serviceId,
      error,
      fallbackDestination: destination,
      latency: 0,
    });

    console.warn(`[FallbackHandler] ${serviceId}: ${error} → ${destination}`);
  }

  getCircuitState(serviceId: string): CircuitBreakerState {
    if (!this.circuitStates.has(serviceId)) {
      this.circuitStates.set(serviceId, {
        state: 'CLOSED',
        failureCount: 0,
        successCount: 0,
      });
    }
    return this.circuitStates.get(serviceId)!;
  }

  resetCircuit(serviceId: string): void {
    this.circuitStates.set(serviceId, {
      state: 'CLOSED',
      failureCount: 0,
      successCount: 0,
    });
  }

  getMetrics(): FallbackMetrics {
    return { ...this.metrics };
  }

  getFallbackLog() {
    return [...this.fallbackLog];
  }

  /**
   * Check if fallback rate exceeds alert threshold (20%)
   * Validates: Requirement 11.7
   */
  shouldAlert(): boolean {
    if (this.metrics.totalRequests === 0) return false;
    const fallbackRate = (this.metrics.primaryFailures / this.metrics.totalRequests) * 100;
    return fallbackRate > 20;
  }

  private updateAverageLatency(latency: number): void {
    const total = this.metrics.primarySuccesses + this.metrics.fallbackSuccesses;
    if (total <= 1) {
      this.metrics.averageLatency = latency;
    } else {
      this.metrics.averageLatency =
        (this.metrics.averageLatency * (total - 1) + latency) / total;
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
