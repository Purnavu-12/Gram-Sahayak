import { DistributedTracer, Span } from '../services/distributed-tracing';

describe('DistributedTracer', () => {
  let tracer: DistributedTracer;

  beforeEach(() => {
    tracer = new DistributedTracer('test-service');
  });

  describe('Trace Creation', () => {
    it('should start a new trace with unique IDs', () => {
      // Act
      const span = tracer.startTrace('test-operation', { userId: 'user123' });

      // Assert
      expect(span.traceId).toBeDefined();
      expect(span.spanId).toBeDefined();
      expect(span.operationName).toBe('test-operation');
      expect(span.serviceName).toBe('test-service');
      expect(span.tags.userId).toBe('user123');
      expect(span.status).toBe('pending');
    });

    it('should create child spans with parent relationship', () => {
      // Arrange
      const parentSpan = tracer.startTrace('parent-operation');

      // Act
      const childSpan = tracer.startSpan('child-operation', parentSpan);

      // Assert
      expect(childSpan.traceId).toBe(parentSpan.traceId);
      expect(childSpan.parentSpanId).toBe(parentSpan.spanId);
      expect(childSpan.spanId).not.toBe(parentSpan.spanId);
    });

    it('should generate unique span IDs for multiple children', () => {
      // Arrange
      const parentSpan = tracer.startTrace('parent-operation');

      // Act
      const child1 = tracer.startSpan('child-1', parentSpan);
      const child2 = tracer.startSpan('child-2', parentSpan);

      // Assert
      expect(child1.spanId).not.toBe(child2.spanId);
      expect(child1.traceId).toBe(child2.traceId);
    });
  });

  describe('Span Lifecycle', () => {
    it('should finish span successfully', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');
      const startTime = span.startTime;

      // Act
      tracer.finishSpan(span, 'success');

      // Assert
      expect(span.endTime).toBeDefined();
      expect(span.duration).toBeDefined();
      expect(span.duration).toBeGreaterThanOrEqual(0);
      expect(span.status).toBe('success');
    });

    it('should finish span with error', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');
      const error = new Error('Test error');

      // Act
      tracer.finishSpan(span, 'error', error);

      // Assert
      expect(span.status).toBe('error');
      expect(span.error).toBeDefined();
      expect(span.error?.message).toBe('Test error');
      expect(span.tags.error).toBe(true);
    });

    it('should calculate duration correctly', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');

      // Wait a bit
      const delay = 10;
      const start = Date.now();
      while (Date.now() - start < delay) {
        // Busy wait
      }

      // Act
      tracer.finishSpan(span, 'success');

      // Assert
      expect(span.duration).toBeGreaterThanOrEqual(delay);
    });
  });

  describe('Span Logging', () => {
    it('should add logs to span', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');

      // Act
      tracer.log(span, 'info', 'Test log message', { key: 'value' });

      // Assert
      expect(span.logs).toHaveLength(1);
      expect(span.logs[0].level).toBe('info');
      expect(span.logs[0].message).toBe('Test log message');
      expect(span.logs[0].fields?.key).toBe('value');
    });

    it('should support multiple log levels', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');

      // Act
      tracer.log(span, 'info', 'Info message');
      tracer.log(span, 'warn', 'Warning message');
      tracer.log(span, 'error', 'Error message');
      tracer.log(span, 'debug', 'Debug message');

      // Assert
      expect(span.logs).toHaveLength(4);
      expect(span.logs[0].level).toBe('info');
      expect(span.logs[1].level).toBe('warn');
      expect(span.logs[2].level).toBe('error');
      expect(span.logs[3].level).toBe('debug');
    });

    it('should timestamp logs correctly', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');
      const beforeLog = Date.now();

      // Act
      tracer.log(span, 'info', 'Test message');

      // Assert
      const afterLog = Date.now();
      expect(span.logs[0].timestamp).toBeGreaterThanOrEqual(beforeLog);
      expect(span.logs[0].timestamp).toBeLessThanOrEqual(afterLog);
    });
  });

  describe('Span Tags', () => {
    it('should set tags on span', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');

      // Act
      tracer.setTags(span, {
        userId: 'user123',
        requestId: 'req456',
        environment: 'test',
      });

      // Assert
      expect(span.tags.userId).toBe('user123');
      expect(span.tags.requestId).toBe('req456');
      expect(span.tags.environment).toBe('test');
    });

    it('should merge tags without overwriting service name', () => {
      // Arrange
      const span = tracer.startTrace('test-operation', { initialTag: 'value' });

      // Act
      tracer.setTags(span, { newTag: 'newValue' });

      // Assert
      expect(span.tags['service.name']).toBe('test-service');
      expect(span.tags.initialTag).toBe('value');
      expect(span.tags.newTag).toBe('newValue');
    });
  });

  describe('Trace Context Propagation', () => {
    it('should generate trace context header', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');

      // Act
      const context = tracer.getTraceContext(span);

      // Assert
      expect(context).toContain(span.traceId);
      expect(context).toContain(span.spanId);
      expect(context).toMatch(/^[a-f0-9]+:[a-f0-9]+:0:1$/);
    });

    it('should include parent span ID in context', () => {
      // Arrange
      const parentSpan = tracer.startTrace('parent-operation');
      const childSpan = tracer.startSpan('child-operation', parentSpan);

      // Act
      const context = tracer.getTraceContext(childSpan);

      // Assert
      expect(context).toContain(childSpan.traceId);
      expect(context).toContain(childSpan.spanId);
      expect(context).toContain(parentSpan.spanId);
    });

    it('should extract trace context from header', () => {
      // Arrange
      const traceHeader = 'abc123:def456:ghi789:1';

      // Act
      const context = tracer.extractTraceContext(traceHeader);

      // Assert
      expect(context).not.toBeNull();
      expect(context?.traceId).toBe('abc123');
      expect(context?.spanId).toBe('def456');
      expect(context?.parentSpanId).toBe('ghi789');
    });

    it('should handle invalid trace headers', () => {
      // Arrange
      const invalidHeaders = ['invalid', '', 'abc:'];

      // Act & Assert
      for (const header of invalidHeaders) {
        const context = tracer.extractTraceContext(header);
        expect(context).toBeNull();
      }
    });

    it('should continue trace from extracted context', () => {
      // Arrange
      const originalSpan = tracer.startTrace('original-operation');
      const context = tracer.getTraceContext(originalSpan);
      const extracted = tracer.extractTraceContext(context);

      // Act
      const continuedSpan = tracer.continueTrace('continued-operation', extracted!, {
        continued: true,
      });

      // Assert
      expect(continuedSpan.traceId).toBe(originalSpan.traceId);
      expect(continuedSpan.parentSpanId).toBe(originalSpan.spanId);
      expect(continuedSpan.tags.continued).toBe(true);
    });
  });

  describe('Trace Retrieval', () => {
    it('should retrieve all spans for a trace', () => {
      // Arrange
      const parentSpan = tracer.startTrace('parent-operation');
      const child1 = tracer.startSpan('child-1', parentSpan);
      const child2 = tracer.startSpan('child-2', parentSpan);

      // Act
      const traceSpans = tracer.getTraceSpans(parentSpan.traceId);

      // Assert
      expect(traceSpans).toHaveLength(3);
      expect(traceSpans.map(s => s.spanId)).toContain(parentSpan.spanId);
      expect(traceSpans.map(s => s.spanId)).toContain(child1.spanId);
      expect(traceSpans.map(s => s.spanId)).toContain(child2.spanId);
    });

    it('should retrieve span by ID', () => {
      // Arrange
      const span = tracer.startTrace('test-operation');

      // Act
      const retrieved = tracer.getSpan(span.spanId);

      // Assert
      expect(retrieved).toBeDefined();
      expect(retrieved?.spanId).toBe(span.spanId);
      expect(retrieved?.operationName).toBe('test-operation');
    });

    it('should return undefined for non-existent span', () => {
      // Act
      const retrieved = tracer.getSpan('non-existent-id');

      // Assert
      expect(retrieved).toBeUndefined();
    });
  });

  describe('Jaeger Format Conversion', () => {
    it('should convert span to Jaeger format', () => {
      // Arrange
      const span = tracer.startTrace('test-operation', { userId: 'user123' });
      tracer.log(span, 'info', 'Test log');
      tracer.finishSpan(span, 'success');

      // Act - Access private method through any
      const jaegerSpan = (tracer as any).convertToJaegerFormat(span);

      // Assert
      expect(jaegerSpan.traceIdLow).toBe(span.traceId);
      expect(jaegerSpan.spanId).toBe(span.spanId);
      expect(jaegerSpan.operationName).toBe('test-operation');
      expect(jaegerSpan.tags).toBeDefined();
      expect(jaegerSpan.logs).toBeDefined();
    });
  });

  describe('Memory Management', () => {
    it('should clean up old spans', () => {
      // Arrange
      const span1 = tracer.startTrace('operation-1');
      tracer.finishSpan(span1, 'success');

      // Manually set old end time
      span1.endTime = Date.now() - 7200000; // 2 hours ago

      const span2 = tracer.startTrace('operation-2');
      tracer.finishSpan(span2, 'success');

      // Act
      tracer.cleanup(3600000); // Clean up spans older than 1 hour

      // Assert
      expect(tracer.getSpan(span1.spanId)).toBeUndefined();
      expect(tracer.getSpan(span2.spanId)).toBeDefined();
    });
  });

  describe('Distributed Tracing Scenarios', () => {
    it('should trace request across multiple services', () => {
      // Arrange - API Gateway starts trace
      const gatewaySpan = tracer.startTrace('api-gateway-request', {
        'http.method': 'POST',
        'http.path': '/api/conversation/start',
      });

      // Act - Voice Engine receives request
      const voiceTracer = new DistributedTracer('voice-engine');
      const context = tracer.getTraceContext(gatewaySpan);
      const extracted = voiceTracer.extractTraceContext(context);
      const voiceSpan = voiceTracer.continueTrace('transcribe-audio', extracted!);

      // Dialect Detector receives request
      const dialectTracer = new DistributedTracer('dialect-detector');
      const dialectContext = voiceTracer.getTraceContext(voiceSpan);
      const dialectExtracted = dialectTracer.extractTraceContext(dialectContext);
      const dialectSpan = dialectTracer.continueTrace('detect-dialect', dialectExtracted!);

      // Assert - All spans share same trace ID
      expect(voiceSpan.traceId).toBe(gatewaySpan.traceId);
      expect(dialectSpan.traceId).toBe(gatewaySpan.traceId);

      // Assert - Parent-child relationships
      expect(voiceSpan.parentSpanId).toBe(gatewaySpan.spanId);
      expect(dialectSpan.parentSpanId).toBe(voiceSpan.spanId);
    });

    it('should trace complete conversation flow', () => {
      // Arrange
      const conversationSpan = tracer.startTrace('conversation-flow', {
        userId: 'user123',
      });

      // Act - Simulate conversation stages
      const dialectSpan = tracer.startSpan('dialect-detection', conversationSpan);
      tracer.log(dialectSpan, 'info', 'Detected Hindi dialect');
      tracer.finishSpan(dialectSpan, 'success');

      const profileSpan = tracer.startSpan('profile-collection', conversationSpan);
      tracer.log(profileSpan, 'info', 'Loaded user profile');
      tracer.finishSpan(profileSpan, 'success');

      const schemeSpan = tracer.startSpan('scheme-matching', conversationSpan);
      tracer.log(schemeSpan, 'info', 'Found 5 eligible schemes');
      tracer.finishSpan(schemeSpan, 'success');

      tracer.finishSpan(conversationSpan, 'success');

      // Assert
      const allSpans = tracer.getTraceSpans(conversationSpan.traceId);
      expect(allSpans).toHaveLength(4);
      expect(allSpans.every(s => s.status === 'success')).toBe(true);
    });
  });
});
