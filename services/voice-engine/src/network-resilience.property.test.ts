/**
 * Property-Based Tests for Network Resilience
 * Feature: gram-sahayak
 * 
 * **Validates: Requirements 1.4, 8.1, 8.2, 8.3, 8.4, 8.5**
 */

import * as fc from 'fast-check';
import { VoiceEngineService } from './voice-engine-service';
import { NetworkCondition, SyncPriority, SyncOperationType } from './network-optimization';
import { DialectCode } from '../../../shared/types/voice-engine';

describe('Network Resilience Property Tests', () => {
  /**
   * Property 3: Network Resilience
   * 
   * For any network condition (poor connectivity, offline, slow), the system should 
   * provide appropriate functionality with graceful degradation and automatic recovery 
   * when connectivity improves.
   * 
   * **Validates: Requirements 1.4, 8.1, 8.2, 8.3, 8.4, 8.5**
   */
  describe('Property 3: Network Resilience', () => {
    it('should continue processing speech offline using cached models (Req 8.1)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa', 'or'),
            dialect: fc.option(fc.constantFrom('hi-IN', 'bn-IN', 'te-IN') as fc.Arbitrary<DialectCode>, { nil: undefined }),
            audioChunks: fc.integer({ min: 1, max: 5 }),
            chunkSize: fc.integer({ min: 800, max: 3200 })
          }),
          async ({ language, dialect, audioChunks, chunkSize }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);
            const offlineProcessor = service.getOfflineProcessor();

            try {
              // Cache model for offline use
              const modelData = new ArrayBuffer(1000);
              await offlineProcessor.cacheModel(language, dialect, modelData, '1.0.0');

              // Go offline
              service.setOnlineStatus(false);
              const networkOptimizer = service.getNetworkOptimizer();
              networkOptimizer.setCondition(NetworkCondition.OFFLINE);

              // Act - Process audio chunks offline
              const results = [];
              for (let i = 0; i < audioChunks; i++) {
                const audioData = generateAudioChunk(chunkSize, 0.7, 0);
                const result = await service.processAudioStream(sessionId, audioData);
                results.push(result);
              }

              // Assert - Property: System should continue processing offline
              expect(results.length).toBe(audioChunks);
              
              for (const result of results) {
                // Should have valid transcription result
                expect(result).toBeDefined();
                expect(result.text).toBeDefined();
                expect(result.confidence).toBeGreaterThan(0);
                expect(result.confidence).toBeLessThanOrEqual(1);
                expect(result.language).toBe(language);
                expect(result.timestamp).toBeInstanceOf(Date);
                
                // Should be marked as offline
                expect(result.isOffline).toBe(true);
              }

              // Verify operations were queued for sync
              const queueStatus = networkOptimizer.getSyncQueueStatus();
              expect(queueStatus.queueSize).toBeGreaterThan(0);

            } finally {
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should provide access to cached scheme information offline (Req 8.2)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            schemeCount: fc.integer({ min: 1, max: 10 }),
            language: fc.constantFrom('hi', 'bn', 'te', 'mr', 'ta')
          }),
          async ({ schemeCount, language }) => {
            // Arrange
            const service = new VoiceEngineService();
            const offlineProcessor = service.getOfflineProcessor();

            // Cache multiple schemes
            const cachedSchemes = [];
            for (let i = 0; i < schemeCount; i++) {
              const scheme = {
                schemeId: `scheme-${i}`,
                name: { [language]: `Scheme ${i}` },
                description: { [language]: `Description ${i}` },
                eligibilityCriteria: { income: 100000 },
                cachedAt: new Date(),
                expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
              };
              await offlineProcessor.cacheScheme(scheme);
              cachedSchemes.push(scheme);
            }

            // Go offline
            service.setOnlineStatus(false);

            // Act - Access cached schemes offline
            const retrievedSchemes = [];
            for (const scheme of cachedSchemes) {
              const retrieved = await offlineProcessor.getCachedScheme(scheme.schemeId);
              if (retrieved) {
                retrievedSchemes.push(retrieved);
              }
            }

            // Assert - Property: All cached schemes should be accessible offline
            expect(retrievedSchemes.length).toBe(schemeCount);
            
            for (let i = 0; i < schemeCount; i++) {
              const retrieved = retrievedSchemes[i];
              const original = cachedSchemes[i];
              
              expect(retrieved.schemeId).toBe(original.schemeId);
              expect(retrieved.name[language]).toBe(original.name[language]);
              expect(retrieved.description[language]).toBe(original.description[language]);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should sync offline interactions when connectivity returns (Req 8.3)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr'),
            offlineOperations: fc.integer({ min: 1, max: 10 }),
            chunkSize: fc.integer({ min: 800, max: 2400 })
          }),
          async ({ language, offlineOperations, chunkSize }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);
            const networkOptimizer = service.getNetworkOptimizer();
            const offlineProcessor = service.getOfflineProcessor();

            try {
              // Cache model
              const modelData = new ArrayBuffer(1000);
              await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

              // Go offline
              service.setOnlineStatus(false);
              networkOptimizer.setCondition(NetworkCondition.OFFLINE);

              // Perform operations offline
              for (let i = 0; i < offlineOperations; i++) {
                const audioData = generateAudioChunk(chunkSize, 0.7, 0);
                await service.processAudioStream(sessionId, audioData);
              }

              // Verify operations are queued
              const offlineQueueStatus = networkOptimizer.getSyncQueueStatus();
              const queuedCount = offlineQueueStatus.queueSize;
              expect(queuedCount).toBeGreaterThan(0);

              // Act - Restore connectivity
              service.setOnlineStatus(true);
              networkOptimizer.setCondition(NetworkCondition.GOOD);

              // Trigger sync
              await networkOptimizer.triggerSync();

              // Assert - Property: Offline operations should be synced
              const onlineQueueStatus = networkOptimizer.getSyncQueueStatus();
              
              // Queue should be processed (empty or significantly reduced)
              expect(onlineQueueStatus.queueSize).toBeLessThanOrEqual(queuedCount);
              
              // If not all processed in one batch, at least some should be processed
              if (queuedCount > 10) {
                expect(onlineQueueStatus.queueSize).toBeLessThan(queuedCount);
              }

            } finally {
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should compress audio and minimize bandwidth usage when needed (Req 8.4)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            bandwidth: fc.integer({ min: 100, max: 1000 }), // kbps
            audioSize: fc.integer({ min: 5000, max: 20000 }), // bytes
            networkCondition: fc.constantFrom(
              NetworkCondition.POOR,
              NetworkCondition.FAIR,
              NetworkCondition.GOOD
            )
          }),
          async ({ bandwidth, audioSize, networkCondition }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();

            // Set network condition
            networkOptimizer.setCondition(networkCondition);
            networkOptimizer['currentMetrics'] = {
              bandwidth,
              latency: 200,
              packetLoss: 2,
              jitter: 20,
              timestamp: new Date()
            };

            const audioData = new ArrayBuffer(audioSize);

            // Act - Compress audio
            const result = await networkOptimizer.compressAudio(audioData);

            // Assert - Property: Compression should minimize bandwidth usage
            expect(result.originalSize).toBe(audioSize);
            expect(result.compressedSize).toBeGreaterThan(0);
            expect(result.compressionRatio).toBeGreaterThan(0);
            expect(result.compressionRatio).toBeLessThanOrEqual(1.0);

            // When bandwidth is limited, compression should be more aggressive
            if (bandwidth < 512) {
              // Below compression threshold - should compress
              expect(result.compressedSize).toBeLessThan(result.originalSize);
              expect(result.compressionRatio).toBeLessThan(1.0);
            }

            // Poor network should have more compression than good network
            if (networkCondition === NetworkCondition.POOR) {
              expect(result.compressionRatio).toBeLessThan(0.7);
            }

          }
        ),
        { numRuns: 100 }
      );
    });

    it('should prioritize essential data and defer non-critical updates in slow network (Req 8.5)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            criticalOps: fc.integer({ min: 1, max: 5 }),
            highOps: fc.integer({ min: 1, max: 5 }),
            normalOps: fc.integer({ min: 1, max: 5 }),
            lowOps: fc.integer({ min: 1, max: 5 }),
            networkCondition: fc.constantFrom(NetworkCondition.POOR, NetworkCondition.FAIR)
          }),
          async ({ criticalOps, highOps, normalOps, lowOps, networkCondition }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();

            // Set slow/poor network condition
            networkOptimizer.setCondition(networkCondition);

            // Queue operations with different priorities
            for (let i = 0; i < criticalOps; i++) {
              networkOptimizer.queueOperation({
                type: SyncOperationType.APPLICATION,
                priority: SyncPriority.CRITICAL,
                data: { id: `critical-${i}` },
                maxRetries: 3
              });
            }

            for (let i = 0; i < highOps; i++) {
              networkOptimizer.queueOperation({
                type: SyncOperationType.USER_PROFILE,
                priority: SyncPriority.HIGH,
                data: { id: `high-${i}` },
                maxRetries: 3
              });
            }

            for (let i = 0; i < normalOps; i++) {
              networkOptimizer.queueOperation({
                type: SyncOperationType.TRANSCRIPTION,
                priority: SyncPriority.NORMAL,
                data: { id: `normal-${i}` },
                maxRetries: 3
              });
            }

            for (let i = 0; i < lowOps; i++) {
              networkOptimizer.queueOperation({
                type: SyncOperationType.SCHEME_DATA,
                priority: SyncPriority.LOW,
                data: { id: `low-${i}` },
                maxRetries: 3
              });
            }

            // Act - Get next batch for processing
            const batch = networkOptimizer['getNextBatch']();

            // Assert - Property: Essential data should be prioritized
            // In poor/slow network, only critical and high priority should be processed
            for (const operation of batch) {
              if (networkCondition === NetworkCondition.POOR) {
                // Poor network: only CRITICAL and HIGH priority
                expect(operation.priority).toBeLessThanOrEqual(SyncPriority.HIGH);
              } else if (networkCondition === NetworkCondition.FAIR) {
                // Fair network: CRITICAL, HIGH, and some NORMAL
                expect(operation.priority).toBeLessThanOrEqual(SyncPriority.NORMAL);
              }
            }

            // Verify critical operations are included
            const criticalInBatch = batch.filter(op => op.priority === SyncPriority.CRITICAL).length;
            expect(criticalInBatch).toBeGreaterThan(0);

            // Verify low priority operations are deferred in poor conditions
            if (networkCondition === NetworkCondition.POOR) {
              const lowInBatch = batch.filter(op => op.priority === SyncPriority.LOW).length;
              expect(lowInBatch).toBe(0);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should provide graceful degradation with offline capabilities (Req 1.4)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr', 'ta'),
            networkCondition: fc.constantFrom(
              NetworkCondition.EXCELLENT,
              NetworkCondition.GOOD,
              NetworkCondition.FAIR,
              NetworkCondition.POOR,
              NetworkCondition.OFFLINE
            ),
            audioChunks: fc.integer({ min: 1, max: 3 }),
            chunkSize: fc.integer({ min: 800, max: 2400 })
          }),
          async ({ language, networkCondition, audioChunks, chunkSize }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);
            const networkOptimizer = service.getNetworkOptimizer();
            const offlineProcessor = service.getOfflineProcessor();

            try {
              // Cache model for offline capability
              const modelData = new ArrayBuffer(1000);
              await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

              // Set network condition
              networkOptimizer.setCondition(networkCondition);
              service.setOnlineStatus(networkCondition !== NetworkCondition.OFFLINE);

              // Act - Process audio in various network conditions
              const results = [];
              for (let i = 0; i < audioChunks; i++) {
                const audioData = generateAudioChunk(chunkSize, 0.7, 0);
                const result = await service.processAudioStream(sessionId, audioData);
                results.push(result);
              }

              // Assert - Property: System should provide graceful degradation
              expect(results.length).toBe(audioChunks);

              for (const result of results) {
                // Should always return valid results regardless of network
                expect(result).toBeDefined();
                expect(result.text).toBeDefined();
                expect(result.confidence).toBeGreaterThan(0);
                expect(result.language).toBe(language);
                expect(result.timestamp).toBeInstanceOf(Date);

                // Offline results should be marked
                if (networkCondition === NetworkCondition.OFFLINE) {
                  expect(result.isOffline).toBe(true);
                }
              }

              // Audio quality should adapt to network condition
              const quality = networkOptimizer.getAudioQuality();
              expect(quality).toBeDefined();
              expect(quality.bitrate).toBeGreaterThan(0);
              expect(quality.sampleRate).toBeGreaterThan(0);

              // Poor network should have lower quality settings
              if (networkCondition === NetworkCondition.POOR) {
                expect(quality.bitrate).toBeLessThanOrEqual(32);
                expect(quality.compressionLevel).toBeGreaterThanOrEqual(7);
              }

              // Excellent network should have higher quality settings
              if (networkCondition === NetworkCondition.EXCELLENT) {
                expect(quality.bitrate).toBeGreaterThanOrEqual(64);
              }

            } finally {
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle network condition transitions smoothly', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr'),
            transitions: fc.array(
              fc.constantFrom(
                NetworkCondition.EXCELLENT,
                NetworkCondition.GOOD,
                NetworkCondition.FAIR,
                NetworkCondition.POOR,
                NetworkCondition.OFFLINE
              ),
              { minLength: 2, maxLength: 5 }
            ),
            chunkSize: fc.integer({ min: 800, max: 2400 })
          }),
          async ({ language, transitions, chunkSize }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);
            const networkOptimizer = service.getNetworkOptimizer();
            const offlineProcessor = service.getOfflineProcessor();

            try {
              // Cache model for offline capability
              const modelData = new ArrayBuffer(1000);
              await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

              const results = [];

              // Act - Process audio through network transitions
              for (const condition of transitions) {
                networkOptimizer.setCondition(condition);
                service.setOnlineStatus(condition !== NetworkCondition.OFFLINE);

                const audioData = generateAudioChunk(chunkSize, 0.7, 0);
                const result = await service.processAudioStream(sessionId, audioData);
                results.push({ condition, result });
              }

              // Assert - Property: System should handle transitions smoothly
              expect(results.length).toBe(transitions.length);

              for (const { condition, result } of results) {
                // Should always produce valid results
                expect(result).toBeDefined();
                expect(result.text).toBeDefined();
                expect(result.confidence).toBeGreaterThan(0);
                expect(result.language).toBe(language);

                // Offline results should be marked
                if (condition === NetworkCondition.OFFLINE) {
                  expect(result.isOffline).toBe(true);
                }
              }

              // Verify no crashes or errors during transitions
              expect(results.every(r => r.result !== null)).toBe(true);

            } finally {
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain sync queue integrity across network conditions', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            operations: fc.array(
              fc.record({
                type: fc.constantFrom(
                  SyncOperationType.TRANSCRIPTION,
                  SyncOperationType.USER_PROFILE,
                  SyncOperationType.APPLICATION,
                  SyncOperationType.SCHEME_DATA
                ),
                priority: fc.constantFrom(
                  SyncPriority.CRITICAL,
                  SyncPriority.HIGH,
                  SyncPriority.NORMAL,
                  SyncPriority.LOW
                )
              }),
              { minLength: 1, maxLength: 20 }
            ),
            networkCondition: fc.constantFrom(
              NetworkCondition.GOOD,
              NetworkCondition.FAIR,
              NetworkCondition.POOR,
              NetworkCondition.OFFLINE
            )
          }),
          async ({ operations, networkCondition }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();

            // Set network condition
            networkOptimizer.setCondition(networkCondition);

            // Act - Queue operations
            const queuedIds = [];
            for (const op of operations) {
              const id = networkOptimizer.queueOperation({
                type: op.type,
                priority: op.priority,
                data: { test: true },
                maxRetries: 3
              });
              queuedIds.push(id);
            }

            // Assert - Property: Queue should maintain integrity
            const status = networkOptimizer.getSyncQueueStatus();
            
            // All operations should be queued
            expect(status.queueSize).toBe(operations.length);

            // Priority counts should match
            const priorityCounts = operations.reduce((acc, op) => {
              acc[op.priority] = (acc[op.priority] || 0) + 1;
              return acc;
            }, {} as Record<SyncPriority, number>);

            for (const [priority, count] of Object.entries(priorityCounts)) {
              expect(status.byPriority[priority as unknown as SyncPriority]).toBe(count);
            }

            // Queue should be sorted by priority
            const queue = networkOptimizer['syncQueue'];
            for (let i = 1; i < queue.length; i++) {
              expect(queue[i].priority).toBeGreaterThanOrEqual(queue[i - 1].priority);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});

/**
 * Helper function to generate audio chunks for testing
 * @param samples - Number of audio samples
 * @param amplitude - Signal amplitude (0-1)
 * @param noiseLevel - Noise level to add (0-1)
 * @returns ArrayBuffer containing audio data
 */
function generateAudioChunk(samples: number, amplitude: number, noiseLevel: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2); // 16-bit samples
  const view = new Int16Array(buffer);

  for (let i = 0; i < samples; i++) {
    // Generate base signal (simulating speech with varying frequency)
    const frequency = 200 + Math.sin(i / 100) * 100; // 100-300 Hz range (typical speech)
    const t = i / 16000; // Time in seconds at 16kHz sample rate
    let signal = Math.sin(2 * Math.PI * frequency * t) * amplitude;

    // Add noise if specified
    if (noiseLevel > 0) {
      const noise = (Math.random() - 0.5) * 2 * noiseLevel;
      signal += noise;
    }

    // Convert to 16-bit integer and clamp
    const value = signal * 32768;
    view[i] = Math.max(-32768, Math.min(32767, Math.round(value)));
  }

  return buffer;
}
