import {
  ErrorHandler,
  ErrorCategory,
  ErrorSeverity,
} from '../services/error-handler';
import { ConversationState, ConversationStage } from '../services/conversation-orchestrator';

describe('ErrorHandler', () => {
  let errorHandler: ErrorHandler;
  let mockState: ConversationState;

  beforeEach(() => {
    errorHandler = new ErrorHandler();
    mockState = {
      sessionId: 'session123',
      userId: 'user123',
      currentStage: ConversationStage.PROFILE_COLLECTION,
      conversationHistory: [],
      metadata: {
        startTime: new Date(),
        lastActivity: new Date(),
        errorCount: 0,
        retryCount: 0,
      },
    };
  });

  describe('Error Categorization', () => {
    it('should categorize network errors', async () => {
      // Arrange
      const error = new Error('Network connection failed: ECONNREFUSED');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.shouldRetry).toBe(true);
      expect(result.message).toContain('Network');
    });

    it('should categorize timeout errors', async () => {
      // Arrange
      const error = new Error('Request timeout after 30 seconds');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.shouldRetry).toBe(true);
      expect(result.retryDelay).toBeGreaterThan(0);
    });

    it('should categorize service unavailable errors', async () => {
      // Arrange
      const error = new Error('Service unavailable: 503');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.success).toBe(true);
      expect(result.fallbackResponse).toBeDefined();
    });

    it('should categorize validation errors', async () => {
      // Arrange
      const error = new Error('Validation failed: invalid input format');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.success).toBe(true);
      expect(result.fallbackResponse?.requiresUserInput).toBe(true);
    });

    it('should categorize authentication errors', async () => {
      // Arrange
      const error = new Error('Authentication failed: 401 Unauthorized');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.shouldRetry).toBe(true);
      expect(result.message).toContain('Authentication');
    });

    it('should categorize rate limit errors', async () => {
      // Arrange
      const error = new Error('Rate limit exceeded: 429 Too Many Requests');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.shouldRetry).toBe(true);
      expect(result.retryDelay).toBeGreaterThanOrEqual(10000);
    });

    it('should categorize data corruption errors', async () => {
      // Arrange
      const error = new Error('Data corruption detected: malformed JSON');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.newState).toBeDefined();
      expect(result.fallbackResponse).toBeDefined();
    });
  });

  describe('Error Severity', () => {
    it('should assign low severity to validation errors', async () => {
      // Arrange
      const error = new Error('Validation error');

      // Act
      await errorHandler.handleError(error, mockState);
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.bySeverity[ErrorSeverity.LOW]).toBeGreaterThan(0);
    });

    it('should assign medium severity to network errors', async () => {
      // Arrange
      const error = new Error('Network error');

      // Act
      await errorHandler.handleError(error, mockState);
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.bySeverity[ErrorSeverity.MEDIUM]).toBeGreaterThan(0);
    });

    it('should assign high severity to authentication errors', async () => {
      // Arrange
      const error = new Error('Authentication failed');

      // Act
      await errorHandler.handleError(error, mockState);
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.bySeverity[ErrorSeverity.HIGH]).toBeGreaterThan(0);
    });

    it('should assign critical severity to data corruption', async () => {
      // Arrange
      const error = new Error('Data corruption detected');

      // Act
      await errorHandler.handleError(error, mockState);
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.bySeverity[ErrorSeverity.CRITICAL]).toBeGreaterThan(0);
    });

    it('should escalate severity after multiple errors', async () => {
      // Arrange
      mockState.metadata.errorCount = 6;
      const error = new Error('Network error');

      // Act
      await errorHandler.handleError(error, mockState);
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.bySeverity[ErrorSeverity.CRITICAL]).toBeGreaterThan(0);
    });
  });

  describe('Recovery Strategies', () => {
    it('should retry network errors', async () => {
      // Arrange
      const error = new Error('Network connection failed');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.shouldRetry).toBe(true);
      expect(result.retryDelay).toBe(2000);
    });

    it('should use cached data for service unavailable', async () => {
      // Arrange
      const error = new Error('Service unavailable');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.fallbackResponse).toBeDefined();
      expect(result.fallbackResponse.cached).toBe(true);
    });

    it('should prompt user for validation errors', async () => {
      // Arrange
      const error = new Error('Invalid input');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.fallbackResponse?.text).toContain('rephrase');
      expect(result.fallbackResponse?.requiresUserInput).toBe(true);
    });

    it('should reset state for data corruption', async () => {
      // Arrange
      const error = new Error('Data corruption');
      mockState.currentStage = ConversationStage.FORM_FILLING;

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.newState).toBeDefined();
      expect(result.newState?.currentStage).toBe(ConversationStage.PROFILE_COLLECTION);
      expect(result.newState?.metadata.errorCount).toBe(0);
    });

    it('should backoff for rate limit errors', async () => {
      // Arrange
      const error = new Error('Rate limit exceeded');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.shouldRetry).toBe(true);
      expect(result.retryDelay).toBeGreaterThanOrEqual(10000);
    });
  });

  describe('User-Friendly Messages', () => {
    it('should provide friendly message for network errors', async () => {
      // Arrange
      const error = new Error('Network error');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      if (!result.success) {
        expect(result.fallbackResponse?.text).toContain('internet connection');
      }
    });

    it('should provide friendly message for timeout errors', async () => {
      // Arrange
      const error = new Error('Timeout');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      if (!result.success) {
        expect(result.fallbackResponse?.text).toContain('taking too long');
      }
    });

    it('should provide friendly message for validation errors', async () => {
      // Arrange
      const error = new Error('Validation failed');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.fallbackResponse?.text).toContain('did not understand');
    });
  });

  describe('Error Logging', () => {
    it('should log errors with context', async () => {
      // Arrange
      const error = new Error('Test error');

      // Act
      await errorHandler.handleError(error, mockState, 'test-service', 'test-operation');
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.total).toBe(1);
      expect(stats.recentErrors[0].service).toBe('test-service');
      expect(stats.recentErrors[0].operation).toBe('test-operation');
    });

    it('should track error statistics by category', async () => {
      // Arrange
      const errors = [
        new Error('Network error'),
        new Error('Network error'),
        new Error('Validation error'),
        new Error('Timeout'),
      ];

      // Act
      for (const error of errors) {
        await errorHandler.handleError(error, mockState);
      }

      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.total).toBe(4);
      expect(stats.byCategory[ErrorCategory.NETWORK]).toBe(2);
      expect(stats.byCategory[ErrorCategory.VALIDATION]).toBe(1);
      expect(stats.byCategory[ErrorCategory.TIMEOUT]).toBe(1);
    });

    it('should maintain recent error history', async () => {
      // Arrange
      const error = new Error('Test error');

      // Act
      await errorHandler.handleError(error, mockState);
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.recentErrors).toHaveLength(1);
      expect(stats.recentErrors[0].message).toBe('Test error');
      expect(stats.recentErrors[0].timestamp).toBeInstanceOf(Date);
    });

    it('should limit error log size', async () => {
      // Arrange
      const error = new Error('Test error');

      // Act - Generate many errors
      for (let i = 0; i < 1100; i++) {
        await errorHandler.handleError(error, mockState);
      }

      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.total).toBeLessThanOrEqual(1000);
    });

    it('should clear error log', async () => {
      // Arrange
      const error = new Error('Test error');
      await errorHandler.handleError(error, mockState);

      // Act
      errorHandler.clearErrorLog();
      const stats = errorHandler.getErrorStats();

      // Assert
      expect(stats.total).toBe(0);
      expect(stats.recentErrors).toHaveLength(0);
    });
  });

  describe('State Updates', () => {
    it('should increment error count in state', async () => {
      // Arrange
      const error = new Error('Test error');
      const initialCount = mockState.metadata.errorCount;

      // Act
      await errorHandler.handleError(error, mockState);

      // Assert
      expect(mockState.metadata.errorCount).toBe(initialCount + 1);
    });

    it('should track multiple errors', async () => {
      // Arrange
      const error = new Error('Test error');

      // Act
      await errorHandler.handleError(error, mockState);
      await errorHandler.handleError(error, mockState);
      await errorHandler.handleError(error, mockState);

      // Assert
      expect(mockState.metadata.errorCount).toBe(3);
    });
  });

  describe('Recovery Result', () => {
    it('should indicate successful recovery', async () => {
      // Arrange
      const error = new Error('Network error');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.success).toBe(true);
      expect(result.message).toBeDefined();
    });

    it('should indicate failed recovery for unknown errors', async () => {
      // Arrange
      const error = new Error('Unknown catastrophic error');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result.fallbackResponse).toBeDefined();
    });

    it('should provide retry information', async () => {
      // Arrange
      const error = new Error('Timeout');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      if (result.shouldRetry) {
        expect(result.retryDelay).toBeGreaterThan(0);
      }
    });
  });

  describe('Edge Cases', () => {
    it('should handle errors with no message', async () => {
      // Arrange
      const error = new Error();

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result).toBeDefined();
      expect(result.fallbackResponse).toBeDefined();
    });

    it('should handle errors with special characters', async () => {
      // Arrange
      const error = new Error('Error: <script>alert("xss")</script>');

      // Act
      const result = await errorHandler.handleError(error, mockState);

      // Assert
      expect(result).toBeDefined();
    });

    it('should handle concurrent error handling', async () => {
      // Arrange
      const errors = Array(10).fill(new Error('Concurrent error'));

      // Act
      const results = await Promise.all(
        errors.map(error => errorHandler.handleError(error, mockState))
      );

      // Assert
      expect(results).toHaveLength(10);
      results.forEach(result => expect(result).toBeDefined());
    });
  });
});
