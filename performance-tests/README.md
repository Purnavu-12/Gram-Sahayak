# Performance Testing and Optimization Suite

This directory contains comprehensive performance tests and optimization utilities for the Gram Sahayak system.

## Performance Targets

### Voice Recognition
- **Latency Target**: Sub-500ms for speech-to-text processing
- **P95 Latency**: < 500ms
- **P99 Latency**: < 600ms
- **Concurrent Processing**: Support 1000+ simultaneous voice streams

### System Load
- **Concurrent Users**: 10,000+ users
- **Throughput**: 1,000+ requests/second
- **Error Rate**: < 1% under normal load, < 5% under spike load

### Database Performance
- **Simple Queries**: < 50ms (P95)
- **Complex Queries**: < 200ms (P95)
- **Cache Hit Rate**: > 80%

### Memory Usage
- **Per Service**: < 512MB
- **Total System**: < 4GB
- **Memory Growth**: < 20% over sustained operations

## Test Suites

### 1. Voice Latency Tests (`voice-latency.test.ts`)
Tests voice recognition performance under various conditions:
- Short utterance processing
- Long conversation handling
- Concurrent voice processing
- Voice Activity Detection (VAD) latency
- End-to-end voice pipeline

**Run:**
```bash
npm test -- voice-latency.test.ts
```

### 2. Load Testing (`load-testing.test.ts`)
Validates system scalability with 10,000+ concurrent users:
- Ramp-up load test (gradual increase to 10K users)
- Sustained load test (maintain 10K users for 10 minutes)
- Spike load test (sudden traffic spike to 15K users)
- Service-specific load tests

**Run:**
```bash
npm test -- load-testing.test.ts
```

**Note:** Load tests have extended timeouts (up to 12 minutes). Run separately from other tests.

### 3. Database Optimization Tests (`database-optimization.test.ts`)
Tests database query performance and caching:
- Simple query performance
- Complex scheme matching queries
- Graph traversal optimization
- Index effectiveness
- Query batching
- Connection pool performance
- Cache hit rate validation
- Cache performance impact

**Run:**
```bash
npm test -- database-optimization.test.ts
```

### 4. Memory Profiling Tests (`memory-profiling.test.ts`)
Validates memory efficiency:
- Per-service memory limits
- Memory leak detection
- Heap usage patterns
- Large object handling (audio buffers, PDFs)
- Cache memory management
- Garbage collection performance

**Run:**
```bash
npm test -- memory-profiling.test.ts --expose-gc
```

**Note:** Use `--expose-gc` flag to enable garbage collection testing.

## Optimization Utilities

### Cache Manager (`shared/performance/cache-manager.ts`)
Centralized caching with multiple strategies:
- **LRU** (Least Recently Used) - Default for most data
- **LFU** (Least Frequently Used) - For access pattern optimization
- **FIFO** (First In First Out) - For simple queue-based caching

**Specialized Caches:**
- `SchemeCacheManager` - 24-hour TTL for scheme data
- `UserProfileCacheManager` - 30-minute TTL for user profiles

**Usage:**
```typescript
import { schemeCache, userProfileCache } from '@/shared/performance/cache-manager';

// Cache scheme data
await schemeCache.setScheme('scheme_123', schemeData);
const scheme = await schemeCache.getScheme('scheme_123');

// Cache user profile
await userProfileCache.setUserProfile('user_456', profileData);
const profile = await userProfileCache.getUserProfile('user_456');

// Get cache statistics
const stats = schemeCache.getStats();
console.log(`Cache hit rate: ${(stats.hitRate * 100).toFixed(2)}%`);
```

### Query Optimizer (`shared/performance/query-optimizer.ts`)
Database query optimization with caching and metrics:

**Features:**
- Query result caching with configurable TTL
- Query batching for efficiency
- Performance metrics tracking
- Slow query identification

**Usage:**
```typescript
import { queryOptimizer } from '@/shared/performance/query-optimizer';

// Execute query with caching
const result = await queryOptimizer.executeQuery(
  'user:profile:123',
  async () => await db.getUserProfile('123'),
  { cache: true, ttl: 60000 }
);

// Batch multiple queries
const results = await queryOptimizer.batchQuery([
  { key: 'scheme:1', fn: () => db.getScheme('1') },
  { key: 'scheme:2', fn: () => db.getScheme('2') },
], { parallel: true });

// Get performance statistics
const stats = queryOptimizer.getStats();
console.log(`Cache hit rate: ${(stats.cacheHitRate * 100).toFixed(2)}%`);
console.log(`Avg query time: ${stats.avgQueryTime.toFixed(2)}ms`);
```

### Performance Monitor (`shared/performance/performance-monitor.ts`)
Real-time performance monitoring and metrics:

**Features:**
- Operation timing with start/end
- Async operation measurement
- Service-level metrics aggregation
- Percentile calculations (P50, P95, P99)
- Memory usage tracking

**Usage:**
```typescript
import { performanceMonitor, Measure } from '@/shared/performance/performance-monitor';

// Manual timing
performanceMonitor.startTimer('voice:processing');
await processVoice(audio);
const duration = performanceMonitor.endTimer('voice:processing');

// Automatic measurement
const result = await performanceMonitor.measure(
  'scheme:matching',
  async () => await matchSchemes(userProfile)
);

// Using decorator
class VoiceService {
  @Measure('voice:stt')
  async speechToText(audio: Buffer): Promise<string> {
    // Implementation
  }
}

// Get statistics
const stats = performanceMonitor.getStats('voice:processing');
console.log(`P95 latency: ${stats.p95.toFixed(2)}ms`);

// Get service metrics
const serviceMetrics = performanceMonitor.getServiceMetrics('voice');
console.log(`Throughput: ${serviceMetrics.throughput.toFixed(2)} req/s`);
```

## Running All Performance Tests

### Quick Test (Simulated)
```bash
npm test -- performance-tests/
```

### Full Load Test (Extended)
```bash
npm test -- performance-tests/ --testTimeout=720000
```

### With Memory Profiling
```bash
node --expose-gc node_modules/.bin/jest performance-tests/
```

## Optimization Strategies Implemented

### 1. Voice Recognition Optimization
- **Audio Preprocessing**: Noise reduction and normalization before STT
- **Streaming Processing**: Process audio chunks in real-time
- **Model Caching**: Keep frequently used language models in memory
- **Batch Processing**: Group multiple audio chunks for efficiency

### 2. Database Query Optimization
- **Indexing**: Proper indexes on frequently queried fields
  - User ID, Scheme ID, State, District
  - Composite indexes for multi-criteria queries
- **Query Caching**: Cache frequent queries with appropriate TTL
- **Connection Pooling**: Reuse database connections
- **Query Batching**: Combine multiple queries when possible

### 3. Caching Strategy
- **Multi-Level Caching**:
  - L1: In-memory cache (fastest, limited size)
  - L2: Redis cache (shared across services)
  - L3: Database (source of truth)
- **Cache Warming**: Pre-populate cache with hot data
- **Smart Invalidation**: Invalidate only affected cache entries

### 4. Memory Optimization
- **Streaming**: Process large files in chunks
- **Buffer Pooling**: Reuse audio buffers
- **Lazy Loading**: Load data only when needed
- **Garbage Collection**: Proper cleanup of temporary objects

### 5. Load Balancing
- **Round Robin**: Distribute requests evenly
- **Health Checks**: Route away from unhealthy instances
- **Circuit Breakers**: Prevent cascade failures
- **Rate Limiting**: Protect services from overload

## Performance Monitoring in Production

### Metrics to Track
1. **Latency Metrics**
   - P50, P95, P99 response times
   - Voice recognition latency
   - Database query times

2. **Throughput Metrics**
   - Requests per second
   - Concurrent users
   - Voice streams processed

3. **Error Metrics**
   - Error rate by service
   - Timeout rate
   - Circuit breaker trips

4. **Resource Metrics**
   - CPU usage per service
   - Memory usage and growth
   - Database connection pool utilization
   - Cache hit rates

### Alerting Thresholds
- Voice latency P95 > 500ms
- Error rate > 1%
- Memory usage > 80% of limit
- Cache hit rate < 70%
- Database query P95 > 200ms

## Continuous Optimization

### Regular Tasks
1. **Weekly**: Review slow query logs and optimize
2. **Monthly**: Analyze cache hit rates and adjust TTLs
3. **Quarterly**: Load test with increased targets
4. **Ongoing**: Monitor production metrics and tune

### Performance Regression Prevention
- Run performance tests in CI/CD pipeline
- Set performance budgets for critical paths
- Alert on performance degradation
- Regular profiling of production workloads

## Troubleshooting

### High Latency
1. Check cache hit rates
2. Review database query performance
3. Check for memory pressure (GC pauses)
4. Verify network latency between services

### High Memory Usage
1. Check for memory leaks (use profiler)
2. Review cache sizes
3. Check for large object retention
4. Monitor GC frequency and pause times

### Low Throughput
1. Check CPU utilization
2. Review connection pool sizes
3. Check for blocking operations
4. Verify load balancer configuration

## References

- [Performance Targets](./config.ts)
- [Cache Manager](../shared/performance/cache-manager.ts)
- [Query Optimizer](../shared/performance/query-optimizer.ts)
- [Performance Monitor](../shared/performance/performance-monitor.ts)
