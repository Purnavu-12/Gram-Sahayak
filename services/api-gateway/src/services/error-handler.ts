/**
 * Comprehensive Error Handling and Recovery Service
 * 
 * Provides centralized error handling, recovery strategies, and fallback mechanisms
 * for the conversation flow across all microservices.
 */

import { ConversationState, ConversationStage } from './conversation-orchestrator';
import { Span, DistributedTracer } from './distributed-tracing';

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum ErrorCategory {
  NETWORK = 'network',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  RATE_LIMIT = 'rate_limit',
  DATA_CORRUPTION = 'data_corruption',
  TIMEOUT = 'timeout',
  UNKNOWN = 'unknown',
}

export interface ErrorContext {
  errorId: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  message: string;
  originalError: Error;
  service?: string;
  operation?: string;
  timestamp: Date;
  conversationState?: ConversationState;
  metadata?: Record<string, any>;
}

export interface RecoveryStrategy {
  name: string;
  canRecover: (error: ErrorContext) => boolean;
  recover: (error: ErrorContext, state: ConversationState) => Promise<RecoveryResult>;
  maxRetries: number;
}

export interface RecoveryResult {
  success: boolean;
  message: string;
  newState?: ConversationState;
  fallbackResponse?: any;
  shouldRetry?: boolean;
  retryDelay?: number;
}

export class ErrorHandler {
  private recoveryStrategies: RecoveryStrategy[] = [];
  private errorLog: ErrorContext[] = [];
  private readonly MAX_ERROR_LOG_SIZE = 1000;

  constructor() {
    this.initializeRecoveryStrategies();
  }

  private initializeRecoveryStrategies(): void {
    // Network error recovery
    this.recoveryStrategies.push({
      name: 'network-retry',
      canRecover: (error) => error.category === ErrorCategory.NETWORK,
      recover: async (error, state) => {
        return {
          success: true,
          message: 'Network issue detected. Retrying...',
          shouldRetry: true,
          retryDelay: 2000,
        };
      },
      maxRetries: 3,
    });

    // Service unavailable recovery
    this.recoveryStrategies.push({
      name: 'service-fallback',
      canRecover: (error) => error.category === ErrorCategory.SERVICE_UNAVAILABLE,
      recover: async (error, state) => {
        // Use cached data or offline mode
        return {
          success: true,
          message: 'Service temporarily unavailable. Using cached data.',
          fallbackResponse: await this.getCachedResponse(error, state),
        };
      },
      maxRetries: 2,
    });

    // Timeout recovery
    this.recoveryStrategies.push({
      name: 'timeout-retry',
      canRecover: (error) => error.category === ErrorCategory.TIMEOUT,
      recover: async (error, state) => {
        return {
          success: true,
          message: 'Request timed out. Retrying with extended timeout...',
          shouldRetry: true,
          retryDelay: 5000,
        };
      },
      maxRetries: 2,
    });

    // Validation error recovery
    this.recoveryStrategies.push({
      name: 'validation-prompt',
      canRecover: (error) => error.category === ErrorCategory.VALIDATION,
      recover: async (error, state) => {
        return {
          success: true,
          message: 'Invalid input detected. Prompting user for correction.',
          fallbackResponse: {
            text: 'I did not understand that. Could you please rephrase?',
            requiresUserInput: true,
          },
        };
      },
      maxRetries: 1,
    });

    // Rate limit recovery
    this.recoveryStrategies.push({
      name: 'rate-limit-backoff',
      canRecover: (error) => error.category === ErrorCategory.RATE_LIMIT,
      recover: async (error, state) => {
        return {
          success: true,
          message: 'Rate limit reached. Backing off...',
          shouldRetry: true,
          retryDelay: 10000,
        };
      },
      maxRetries: 1,
    });

    // Authentication error recovery
    this.recoveryStrategies.push({
      name: 'auth-refresh',
      canRecover: (error) => error.category === ErrorCategory.AUTHENTICATION,
      recover: async (error, state) => {
        // Attempt to refresh authentication
        return {
          success: true,
          message: 'Authentication expired. Refreshing...',
          shouldRetry: true,
          retryDelay: 1000,
        };
      },
      maxRetries: 1,
    });

    // Data corruption recovery
    this.recoveryStrategies.push({
      name: 'data-reset',
      canRecover: (error) => error.category === ErrorCategory.DATA_CORRUPTION,
      recover: async (error, state) => {
        // Reset to last known good state
        const newState = await this.resetToSafeState(state);
        return {
          success: true,
          message: 'Data corruption detected. Resetting to safe state.',
          newState,
          fallbackResponse: {
            text: 'I encountered an issue. Let me start from the last checkpoint.',
          },
        };
      },
      maxRetries: 1,
    });
  }

  /**
   * Handle an error with automatic recovery
   */
  async handleError(
    error: Error,
    state: ConversationState,
    service?: string,
    operation?: string,
    span?: Span
  ): Promise<RecoveryResult> {
    // Create error context
    const errorContext = this.createErrorContext(error, state, service, operation);

    // Log error
    this.logError(errorContext);

    // Log to distributed tracing
    if (span) {
      const tracer = new DistributedTracer();
      tracer.log(span, 'error', errorContext.message, {
        errorId: errorContext.errorId,
        category: errorContext.category,
        severity: errorContext.severity,
      });
    }

    // Attempt recovery
    const recoveryResult = await this.attemptRecovery(errorContext, state);

    // Update error count in state
    if (state.metadata) {
      state.metadata.errorCount = (state.metadata.errorCount || 0) + 1;
    }

    return recoveryResult;
  }

  private createErrorContext(
    error: Error,
    state: ConversationState,
    service?: string,
    operation?: string
  ): ErrorContext {
    const category = this.categorizeError(error);
    const severity = this.determineSeverity(category, state);

    return {
      errorId: this.generateErrorId(),
      category,
      severity,
      message: error.message,
      originalError: error,
      service,
      operation,
      timestamp: new Date(),
      conversationState: state,
      metadata: {
        stack: error.stack,
        errorCount: state.metadata?.errorCount || 0,
      },
    };
  }

  private categorizeError(error: Error): ErrorCategory {
    const message = error.message.toLowerCase();

    if (message.includes('network') || message.includes('econnrefused')) {
      return ErrorCategory.NETWORK;
    }
    if (message.includes('timeout')) {
      return ErrorCategory.TIMEOUT;
    }
    if (message.includes('unavailable') || message.includes('503')) {
      return ErrorCategory.SERVICE_UNAVAILABLE;
    }
    if (message.includes('validation') || message.includes('invalid')) {
      return ErrorCategory.VALIDATION;
    }
    if (message.includes('auth') || message.includes('401') || message.includes('403')) {
      return ErrorCategory.AUTHENTICATION;
    }
    if (message.includes('rate limit') || message.includes('429')) {
      return ErrorCategory.RATE_LIMIT;
    }
    if (message.includes('corrupt') || message.includes('malformed')) {
      return ErrorCategory.DATA_CORRUPTION;
    }

    return ErrorCategory.UNKNOWN;
  }

  private determineSeverity(category: ErrorCategory, state: ConversationState): ErrorSeverity {
    const errorCount = state.metadata?.errorCount || 0;

    // Critical if too many errors
    if (errorCount > 5) {
      return ErrorSeverity.CRITICAL;
    }

    // Category-based severity
    switch (category) {
      case ErrorCategory.DATA_CORRUPTION:
        return ErrorSeverity.CRITICAL;
      case ErrorCategory.AUTHENTICATION:
        return ErrorSeverity.HIGH;
      case ErrorCategory.SERVICE_UNAVAILABLE:
        return ErrorSeverity.HIGH;
      case ErrorCategory.NETWORK:
        return ErrorSeverity.MEDIUM;
      case ErrorCategory.TIMEOUT:
        return ErrorSeverity.MEDIUM;
      case ErrorCategory.VALIDATION:
        return ErrorSeverity.LOW;
      case ErrorCategory.RATE_LIMIT:
        return ErrorSeverity.MEDIUM;
      default:
        return ErrorSeverity.MEDIUM;
    }
  }

  private async attemptRecovery(
    error: ErrorContext,
    state: ConversationState
  ): Promise<RecoveryResult> {
    // Find applicable recovery strategies
    const strategies = this.recoveryStrategies.filter(s => s.canRecover(error));

    if (strategies.length === 0) {
      return this.getDefaultRecovery(error, state);
    }

    // Try each strategy
    for (const strategy of strategies) {
      try {
        const result = await strategy.recover(error, state);
        if (result.success) {
          console.log(`Recovery successful using strategy: ${strategy.name}`);
          return result;
        }
      } catch (recoveryError) {
        console.error(`Recovery strategy ${strategy.name} failed:`, recoveryError);
      }
    }

    // All strategies failed
    return this.getDefaultRecovery(error, state);
  }

  private getDefaultRecovery(error: ErrorContext, state: ConversationState): RecoveryResult {
    // Provide user-friendly fallback
    return {
      success: false,
      message: 'Unable to recover from error',
      fallbackResponse: {
        text: this.getUserFriendlyErrorMessage(error, state),
        error: {
          code: error.category,
          recoverable: error.severity !== ErrorSeverity.CRITICAL,
        },
      },
    };
  }

  private getUserFriendlyErrorMessage(error: ErrorContext, state: ConversationState): string {
    const language = state.detectedLanguage || 'en';

    // In a real implementation, this would use proper i18n
    switch (error.category) {
      case ErrorCategory.NETWORK:
        return 'I am having trouble connecting. Please check your internet connection.';
      case ErrorCategory.SERVICE_UNAVAILABLE:
        return 'The service is temporarily unavailable. Please try again in a few minutes.';
      case ErrorCategory.TIMEOUT:
        return 'The request is taking too long. Please try again.';
      case ErrorCategory.VALIDATION:
        return 'I did not understand that. Could you please rephrase?';
      case ErrorCategory.AUTHENTICATION:
        return 'Your session has expired. Please log in again.';
      case ErrorCategory.RATE_LIMIT:
        return 'Too many requests. Please wait a moment and try again.';
      case ErrorCategory.DATA_CORRUPTION:
        return 'I encountered a data issue. Let me start fresh.';
      default:
        return 'I encountered an unexpected error. Please try again.';
    }
  }

  private async getCachedResponse(error: ErrorContext, state: ConversationState): Promise<any> {
    // In a real implementation, this would fetch from cache
    return {
      text: 'Using cached information...',
      cached: true,
    };
  }

  private async resetToSafeState(state: ConversationState): Promise<ConversationState> {
    // Reset to a safe checkpoint
    return {
      ...state,
      currentStage: ConversationStage.PROFILE_COLLECTION,
      metadata: {
        ...state.metadata,
        errorCount: 0,
        retryCount: 0,
      },
    };
  }

  private logError(error: ErrorContext): void {
    this.errorLog.push(error);

    // Maintain log size
    if (this.errorLog.length > this.MAX_ERROR_LOG_SIZE) {
      this.errorLog.shift();
    }

    // Log to console
    console.error('[ERROR]', {
      id: error.errorId,
      category: error.category,
      severity: error.severity,
      message: error.message,
      service: error.service,
      operation: error.operation,
    });
  }

  private generateErrorId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get error statistics
   */
  getErrorStats(): {
    total: number;
    byCategory: Record<ErrorCategory, number>;
    bySeverity: Record<ErrorSeverity, number>;
    recentErrors: ErrorContext[];
  } {
    const byCategory: Record<ErrorCategory, number> = {} as any;
    const bySeverity: Record<ErrorSeverity, number> = {} as any;

    for (const error of this.errorLog) {
      byCategory[error.category] = (byCategory[error.category] || 0) + 1;
      bySeverity[error.severity] = (bySeverity[error.severity] || 0) + 1;
    }

    return {
      total: this.errorLog.length,
      byCategory,
      bySeverity,
      recentErrors: this.errorLog.slice(-10),
    };
  }

  /**
   * Clear error log
   */
  clearErrorLog(): void {
    this.errorLog = [];
  }
}

// Global error handler instance
export const globalErrorHandler = new ErrorHandler();
