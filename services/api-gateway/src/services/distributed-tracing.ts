/**
 * Distributed Tracing Service
 * 
 * Provides distributed tracing capabilities for debugging multi-service flows
 * using OpenTelemetry with Jaeger backend.
 */

export interface TraceContext {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  serviceName: string;
  operationName: string;
  startTime: number;
  tags: Record<string, any>;
  logs: TraceLog[];
}

export interface TraceLog {
  timestamp: number;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  fields?: Record<string, any>;
}

export interface Span {
  spanId: string;
  traceId: string;
  parentSpanId?: string;
  serviceName: string;
  operationName: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  tags: Record<string, any>;
  logs: TraceLog[];
  status: 'success' | 'error' | 'pending';
  error?: {
    message: string;
    stack?: string;
  };
}

export class DistributedTracer {
  private spans: Map<string, Span> = new Map();
  private readonly jaegerEndpoint: string;
  private readonly serviceName: string;

  constructor(serviceName: string = 'api-gateway') {
    this.serviceName = serviceName;
    this.jaegerEndpoint = process.env.JAEGER_ENDPOINT || 'http://localhost:14268/api/traces';
  }

  /**
   * Start a new trace
   */
  startTrace(operationName: string, tags: Record<string, any> = {}): Span {
    const traceId = this.generateTraceId();
    const spanId = this.generateSpanId();

    const span: Span = {
      spanId,
      traceId,
      serviceName: this.serviceName,
      operationName,
      startTime: Date.now(),
      tags: {
        ...tags,
        'service.name': this.serviceName,
      },
      logs: [],
      status: 'pending',
    };

    this.spans.set(spanId, span);
    return span;
  }

  /**
   * Start a child span
   */
  startSpan(
    operationName: string,
    parentSpan: Span,
    tags: Record<string, any> = {}
  ): Span {
    const spanId = this.generateSpanId();

    const span: Span = {
      spanId,
      traceId: parentSpan.traceId,
      parentSpanId: parentSpan.spanId,
      serviceName: this.serviceName,
      operationName,
      startTime: Date.now(),
      tags: {
        ...tags,
        'service.name': this.serviceName,
      },
      logs: [],
      status: 'pending',
    };

    this.spans.set(spanId, span);
    return span;
  }

  /**
   * Finish a span
   */
  finishSpan(span: Span, status: 'success' | 'error' = 'success', error?: Error): void {
    span.endTime = Date.now();
    span.duration = span.endTime - span.startTime;
    span.status = status;

    if (error) {
      span.error = {
        message: error.message,
        stack: error.stack,
      };
      span.tags['error'] = true;
      span.tags['error.message'] = error.message;
    }

    // Send to Jaeger
    this.sendToJaeger(span);
  }

  /**
   * Add a log to a span
   */
  log(
    span: Span,
    level: 'info' | 'warn' | 'error' | 'debug',
    message: string,
    fields?: Record<string, any>
  ): void {
    span.logs.push({
      timestamp: Date.now(),
      level,
      message,
      fields,
    });
  }

  /**
   * Add tags to a span
   */
  setTags(span: Span, tags: Record<string, any>): void {
    span.tags = { ...span.tags, ...tags };
  }

  /**
   * Get trace context for propagation
   */
  getTraceContext(span: Span): string {
    // Format: traceId:spanId:parentSpanId:flags
    return `${span.traceId}:${span.spanId}:${span.parentSpanId || '0'}:1`;
  }

  /**
   * Extract trace context from header
   */
  extractTraceContext(traceHeader: string): {
    traceId: string;
    spanId: string;
    parentSpanId?: string;
  } | null {
    try {
      const parts = traceHeader.split(':');
      if (parts.length < 2) return null;

      return {
        traceId: parts[0],
        spanId: parts[1],
        parentSpanId: parts[2] !== '0' ? parts[2] : undefined,
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * Create a span from extracted context
   */
  continueTrace(
    operationName: string,
    traceContext: { traceId: string; spanId: string; parentSpanId?: string },
    tags: Record<string, any> = {}
  ): Span {
    const spanId = this.generateSpanId();

    const span: Span = {
      spanId,
      traceId: traceContext.traceId,
      parentSpanId: traceContext.spanId,
      serviceName: this.serviceName,
      operationName,
      startTime: Date.now(),
      tags: {
        ...tags,
        'service.name': this.serviceName,
      },
      logs: [],
      status: 'pending',
    };

    this.spans.set(spanId, span);
    return span;
  }

  /**
   * Get all spans for a trace
   */
  getTraceSpans(traceId: string): Span[] {
    return Array.from(this.spans.values()).filter(span => span.traceId === traceId);
  }

  /**
   * Get span by ID
   */
  getSpan(spanId: string): Span | undefined {
    return this.spans.get(spanId);
  }

  /**
   * Send span to Jaeger
   */
  private async sendToJaeger(span: Span): Promise<void> {
    try {
      // Convert to Jaeger format
      const jaegerSpan = this.convertToJaegerFormat(span);

      // In production, this would send to Jaeger via HTTP or UDP
      // For now, we'll just log it
      if (process.env.NODE_ENV !== 'test') {
        console.log('[TRACE]', JSON.stringify(jaegerSpan, null, 2));
      }

      // Optionally send to Jaeger endpoint
      if (process.env.JAEGER_ENABLED === 'true') {
        await this.sendToJaegerEndpoint(jaegerSpan);
      }
    } catch (error) {
      console.error('Error sending trace to Jaeger:', error);
    }
  }

  private convertToJaegerFormat(span: Span): any {
    return {
      traceIdLow: span.traceId,
      traceIdHigh: '0',
      spanId: span.spanId,
      parentSpanId: span.parentSpanId || '0',
      operationName: span.operationName,
      references: span.parentSpanId
        ? [
            {
              refType: 'CHILD_OF',
              traceIdLow: span.traceId,
              traceIdHigh: '0',
              spanId: span.parentSpanId,
            },
          ]
        : [],
      flags: 1,
      startTime: span.startTime * 1000, // microseconds
      duration: span.duration ? span.duration * 1000 : 0,
      tags: Object.entries(span.tags).map(([key, value]) => ({
        key,
        type: typeof value === 'string' ? 'string' : 'bool',
        value: String(value),
      })),
      logs: span.logs.map(log => ({
        timestamp: log.timestamp * 1000,
        fields: [
          { key: 'event', type: 'string', value: log.message },
          { key: 'level', type: 'string', value: log.level },
          ...(log.fields
            ? Object.entries(log.fields).map(([key, value]) => ({
                key,
                type: 'string',
                value: String(value),
              }))
            : []),
        ],
      })),
      processId: 'p1',
      warnings: null,
    };
  }

  private async sendToJaegerEndpoint(jaegerSpan: any): Promise<void> {
    try {
      const response = await fetch(this.jaegerEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: [
            {
              process: {
                serviceName: this.serviceName,
                tags: [],
              },
              spans: [jaegerSpan],
            },
          ],
        }),
      });

      if (!response.ok) {
        console.error('Failed to send trace to Jaeger:', response.statusText);
      }
    } catch (error) {
      console.error('Error sending to Jaeger endpoint:', error);
    }
  }

  private generateTraceId(): string {
    return this.generateId(16);
  }

  private generateSpanId(): string {
    return this.generateId(8);
  }

  private generateId(length: number): string {
    const chars = '0123456789abcdef';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
  }

  /**
   * Clean up old spans (memory management)
   */
  cleanup(maxAge: number = 3600000): void {
    const now = Date.now();
    for (const [spanId, span] of this.spans.entries()) {
      if (span.endTime && now - span.endTime > maxAge) {
        this.spans.delete(spanId);
      }
    }
  }
}

// Global tracer instance
export const globalTracer = new DistributedTracer();

/**
 * Middleware to add tracing to Express routes
 */
export function tracingMiddleware(serviceName: string) {
  const tracer = new DistributedTracer(serviceName);

  return (req: any, res: any, next: any) => {
    // Extract trace context from headers
    const traceHeader = req.headers['x-trace-context'];
    let span: Span;

    if (traceHeader) {
      const context = tracer.extractTraceContext(traceHeader);
      if (context) {
        span = tracer.continueTrace(`${req.method} ${req.path}`, context, {
          'http.method': req.method,
          'http.url': req.url,
          'http.path': req.path,
        });
      } else {
        span = tracer.startTrace(`${req.method} ${req.path}`, {
          'http.method': req.method,
          'http.url': req.url,
          'http.path': req.path,
        });
      }
    } else {
      span = tracer.startTrace(`${req.method} ${req.path}`, {
        'http.method': req.method,
        'http.url': req.url,
        'http.path': req.path,
      });
    }

    // Attach span to request
    req.span = span;
    req.tracer = tracer;

    // Add trace context to response headers
    res.setHeader('x-trace-context', tracer.getTraceContext(span));

    // Finish span when response is sent
    const originalSend = res.send;
    res.send = function (data: any) {
      tracer.setTags(span, {
        'http.status_code': res.statusCode,
      });

      const status = res.statusCode >= 400 ? 'error' : 'success';
      tracer.finishSpan(span, status);

      return originalSend.call(this, data);
    };

    next();
  };
}
