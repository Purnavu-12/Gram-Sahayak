export interface RetryConfig {
  maxAttempts: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableErrors: string[];
}

export class RetryPolicy {
  private defaultConfig: RetryConfig = {
    maxAttempts: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
    retryableErrors: ['ECONNREFUSED', 'ETIMEDOUT', 'ENOTFOUND', 'ENETUNREACH'],
  };

  constructor(private config: Partial<RetryConfig> = {}) {
    this.config = { ...this.defaultConfig, ...config };
  }

  async execute<T>(fn: () => Promise<T>, context?: string): Promise<T> {
    let lastError: Error | undefined;
    let delay = this.config.initialDelay!;

    for (let attempt = 1; attempt <= this.config.maxAttempts!; attempt++) {
      try {
        return await fn();
      } catch (error: any) {
        lastError = error;

        // Check if error is retryable
        if (!this.isRetryable(error)) {
          throw error;
        }

        // Don't retry on last attempt
        if (attempt === this.config.maxAttempts) {
          break;
        }

        // Wait before retry with exponential backoff
        await this.sleep(delay);
        delay = Math.min(delay * this.config.backoffMultiplier!, this.config.maxDelay!);
      }
    }

    throw lastError || new Error('Retry failed');
  }

  private isRetryable(error: any): boolean {
    if (!error) return false;

    // Check error code
    if (error.code && this.config.retryableErrors!.includes(error.code)) {
      return true;
    }

    // Check HTTP status codes (5xx errors are retryable)
    if (error.response && error.response.status >= 500) {
      return true;
    }

    // Check for timeout errors
    if (error.message && error.message.includes('timeout')) {
      return true;
    }

    return false;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
