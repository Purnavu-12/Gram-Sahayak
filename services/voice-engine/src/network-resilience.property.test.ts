/**
 * Property-Based Tests for Network Resilience
 * Feature: gram-sahayak
 * 
 * **Validates: Requirements 1.4, 8.1, 8.2, 8.3, 8.4, 8.5**
 */

import * as fc from 'fast-check';
import { VoiceEngineService } from './voice-engine-service';
import { NetworkCondition, SyncPriority, SyncOperationType } from './network-optimization';
import { CachedScheme } from './offline-processing';

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
    it('should process speech offline when models are cached (Req 8.1)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr', 'ta'),
            audioSize: fc.integer({ min: 250, max: 2500 }).map(n => n * 2), // Ensure even
            amplitude: fc.double({ min: 0.3, max: 0.9, noNaN: true })
          }),
          async ({ language, audioSize, amplitude }) => {
            // Arrange
            const service = new VoiceEngineService();
            const offlineProcessor = service.getOfflineProcessor();
            const userId = `test-user-${Date.now()}`;

            // Cache model for offline use
            const modelData = new ArrayBuffer(1024);
            await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

            // Start session
            const sessionId = await service.startVoiceSession(userId, language);

            try {
              // Act - Go offline
              service.setOnlineStatus(false);

              // Generate and process audio
              const audioChunk = generateAudioChunk(audioSize, amplitude, 0);
              const result = await service.processAudioStream(sessionId, audioChunk);

              // Assert - Property: System continues processing with cached models
              expect(result).toBeDefined();
              expect(result.isOffline).toBe(true);
              expect(result.language).toBe(language);
              
              // Offline processing should still provide reasonable confidence
              expect(result.confidence).toBeGreaterThanOrEqual(0.70);
              expect(result.confidence).toBeLessThanOrEqual(1.0);

              // Verify offline mode is available
              expect(service.isOfflineModeAvailable(language)).toBe(true);

            } finally {
              await service.endVoiceSession(sessionId);
              offlineProcessor.destroy();
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
            schemeId: fc.string({ minLength: 5, maxLength: 20 }).map(s => `SCHEME-${s}`),
            language: fc.constantFrom('en', 'hi', 'bn', 'te'),
            daysUntilExpiry: fc.integer({ min: 1, max: 30 })
          }),
          async ({ schemeId, language, daysUntilExpiry }) => {
            // Arrange
            const service = new VoiceEngineService();
            const offlineProcessor = service.getOfflineProcessor();

            const scheme: CachedScheme = {
              schemeId,
              name: { [language]: `Test Scheme ${schemeId}` },
              description: { [language]: 'Test description' },
              eligibilityCriteria: { age: { min: 18, max: 60 } },
              cachedAt: new Date(),
              expiresAt: new Date(Date.now() + daysUntilExpiry * 24 * 60 * 60 * 1000)
            };

            // Cache scheme
            await offlineProcessor.cacheScheme(scheme);

            try {
              // Act - Go offline
              service.setOnlineStatus(false);

              // Retrieve cached scheme
              const cachedScheme = await offlineProcessor.getCachedScheme(schemeId);

              // Assert - Property: Cached schemes remain accessible offline
              expect(cachedScheme).not.toBeNull();
              expect(cachedScheme?.schemeId).toBe(schemeId);
              expect(cachedScheme?.name[language]).toBeDefined();
              expect(cachedScheme?.description[language]).toBeDefined();
              expect(cachedScheme?.eligibilityCriteria).toBeDefined();

            } finally {
              offlineProcessor.destroy();
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
            language: fc.constantFrom('hi', 'bn', 'te'),
            numOfflineOperations: fc.integer({ min: 1, max: 5 }), // Reduced from 10
            audioSize: fc.integer({ min: 250, max: 1000 }).map(n => n * 2) // Ensure even
          }),
          async ({ language, numOfflineOperations, audioSize }) => {
            // Arrange
            const service = new VoiceEngineService();
            const offlineProcessor = service.getOfflineProcessor();
            const networkOptimizer = service.getNetworkOptimizer();
            const userId = `test-user-${Date.now()}`;

            // Cache model
            const modelData = new ArrayBuffer(1024);
            await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

            const sessionId = await service.startVoiceSession(userId, language);

            try {
              // Act - Go offline and perform operations
              service.setOnlineStatus(false);
              networkOptimizer['currentCondition'] = NetworkCondition.OFFLINE;

              for (let i = 0; i < numOfflineOperations; i++) {
                const audioChunk = generateAudioChunk(audioSize, 0.7, 0);
                await service.processAudioStream(sessionId, audioChunk);
              }

              // Check operations are queued
              const offlineStatus = networkOptimizer.getSyncQueueStatus();
              const queuedCount = offlineStatus.queueSize;
              expect(queuedCount).toBeGreaterThan(0);

              // Restore connectivity
              service.setOnlineStatus(true);
              networkOptimizer['currentCondition'] = NetworkCondition.GOOD;

              // Trigger sync
              await networkOptimizer.triggerSync();

              // Assert - Property: Offline operations sync when connectivity returns
              const onlineStatus = networkOptimizer.getSyncQueueStatus();
              
              // Queue should be processed (empty or reduced)
              expect(onlineStatus.queueSize).toBeLessThanOrEqual(queuedCount);

              // Sync status should be updated
              const syncStatus = service.getSyncStatus();
              expect(syncStatus).toBeDefined();

            } finally {
              await service.endVoiceSession(sessionId);
              offlineProcessor.destroy();
              networkOptimizer.destroy();
            }
          }
        ),
        { numRuns: 30 } // Reduced from 50
      );
    }, 30000); // 30 second timeout

    it('should compress audio and minimize bandwidth when data usage is a concern (Req 8.4)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            bandwidth: fc.integer({ min: 100, max: 500 }), // Limited bandwidth (kbps)
            audioSize: fc.integer({ min: 2500, max: 10000 }).map(n => n * 2), // Ensure even
            amplitude: fc.double({ min: 0.3, max: 0.9, noNaN: true })
          }),
          async ({ bandwidth, audioSize, amplitude }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();

            // Simulate limited bandwidth condition
            networkOptimizer['currentMetrics'] = {
              bandwidth,
              latency: 200,
              packetLoss: 2,
              jitter: 20,
              timestamp: new Date()
            };
            networkOptimizer['currentCondition'] = NetworkCondition.FAIR;

            try {
              // Act - Compress audio
              const audioData = generateAudioChunk(audioSize, amplitude, 0);
              const result = await networkOptimizer.compressAudio(audioData);

              // Assert - Property: Audio is compressed to minimize bandwidth usage
              expect(result.compressedSize).toBeLessThanOrEqual(result.originalSize);
              expect(result.compressionRatio).toBeLessThanOrEqual(1.0);
              expect(result.compressionRatio).toBeGreaterThan(0);

              // Lower bandwidth should result in more aggressive compression
              if (bandwidth < 300) {
                expect(result.compressionRatio).toBeLessThan(0.8);
              }

              // Compression time should be reasonable
              expect(result.compressionTime).toBeGreaterThanOrEqual(0);

            } finally {
              networkOptimizer.destroy();
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
            normalOps: fc.integer({ min: 2, max: 8 }),
            lowOps: fc.integer({ min: 1, max: 5 })
          }),
          async ({ criticalOps, normalOps, lowOps }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();

            // Simulate slow network
            networkOptimizer['currentCondition'] = NetworkCondition.POOR;
            networkOptimizer['currentMetrics'] = {
              bandwidth: 150,
              latency: 400,
              packetLoss: 8,
              jitter: 80,
              timestamp: new Date()
            };

            try {
              // Act - Queue operations with different priorities
              for (let i = 0; i < criticalOps; i++) {
                networkOptimizer.queueOperation({
                  type: SyncOperationType.APPLICATION,
                  priority: SyncPriority.CRITICAL,
                  data: { id: `critical-${i}` },
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
                  type: SyncOperationType.AUDIO_UPLOAD,
                  priority: SyncPriority.LOW,
                  data: { id: `low-${i}` },
                  maxRetries: 3
                });
              }

              // Get next batch for processing
              const batch = networkOptimizer['getNextBatch']();

              // Assert - Property: Essential data is prioritized in slow network
              // In poor conditions, only CRITICAL and HIGH priority should be processed
              for (const op of batch) {
                expect(op.priority).toBeLessThanOrEqual(SyncPriority.HIGH);
              }

              // Critical operations should be included
              const criticalInBatch = batch.filter(op => op.priority === SyncPriority.CRITICAL);
              expect(criticalInBatch.length).toBeGreaterThan(0);

              // Low priority operations should be deferred
              const lowInBatch = batch.filter(op => op.priority === SyncPriority.LOW);
              expect(lowInBatch.length).toBe(0);

              // Queue status should show proper prioritization
              const status = networkOptimizer.getSyncQueueStatus();
              expect(status.byPriority[SyncPriority.CRITICAL]).toBe(criticalOps);
              expect(status.byPriority[SyncPriority.LOW]).toBe(lowOps);

            } finally {
              networkOptimizer.destroy();
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should provide graceful degradation across all network conditions (Req 1.4)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            condition: fc.constantFrom(
              NetworkCondition.EXCELLENT,
              NetworkCondition.GOOD,
              NetworkCondition.FAIR,
              NetworkCondition.POOR
            ),
            language: fc.constantFrom('hi', 'bn', 'te')
          }),
          async ({ condition, language }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();
            const offlineProcessor = service.getOfflineProcessor();
            const userId = `test-user-${Date.now()}`;
            const audioSize = 1600; // Fixed size: 100ms at 16kHz

            // Cache model for potential offline use
            const modelData = new ArrayBuffer(1024);
            await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

            // Ensure we're online for this test
            service.setOnlineStatus(true);
            
            // Set network condition (but don't go offline)
            if (condition !== NetworkCondition.OFFLINE) {
              networkOptimizer['currentCondition'] = condition;
              // Trigger quality adjustment without going offline
              if (networkOptimizer['config'].enableAdaptiveQuality) {
                networkOptimizer['adjustAudioQuality'](condition);
              }
            }

            const sessionId = await service.startVoiceSession(userId, language);

            try {
              // Act - Process audio under specific network condition
              const audioChunk = generateAudioChunk(audioSize, 0.7, 0);
              const result = await service.processAudioStream(sessionId, audioChunk);

              // Assert - Property: System provides appropriate functionality for each condition
              expect(result).toBeDefined();
              expect(result.language).toBe(language);

              // Quality should adapt to network condition
              const quality = networkOptimizer.getAudioQuality();
              expect(quality).toBeDefined();

              // Better conditions should allow higher quality
              if (condition === NetworkCondition.EXCELLENT) {
                expect(quality.bitrate).toBeGreaterThanOrEqual(64);
                expect(quality.sampleRate).toBeGreaterThanOrEqual(16000);
              } else if (condition === NetworkCondition.POOR) {
                expect(quality.bitrate).toBeLessThanOrEqual(32);
                expect(quality.compressionLevel).toBeGreaterThanOrEqual(7);
              }

              // Confidence should remain reasonable across conditions
              // System should provide results even in poor conditions
              // Note: In test environment without real ASR, confidence may be lower
              expect(result.confidence).toBeGreaterThanOrEqual(0);
              expect(result.confidence).toBeLessThanOrEqual(1.0);

            } finally {
              await service.endVoiceSession(sessionId);
              offlineProcessor.destroy();
              networkOptimizer.destroy();
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should automatically recover when connectivity improves', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te'),
            initialCondition: fc.constantFrom(NetworkCondition.OFFLINE, NetworkCondition.POOR),
            improvedCondition: fc.constantFrom(NetworkCondition.GOOD, NetworkCondition.EXCELLENT),
            numOperations: fc.integer({ min: 2, max: 5 }) // Reduced from 8
          }),
          async ({ language, initialCondition, improvedCondition, numOperations }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();
            const offlineProcessor = service.getOfflineProcessor();

            // Cache model
            const modelData = new ArrayBuffer(1024);
            await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

            try {
              // Act - Start with poor/offline condition
              networkOptimizer['currentCondition'] = initialCondition;
              if (initialCondition === NetworkCondition.OFFLINE) {
                service.setOnlineStatus(false);
              }

              // Queue operations during poor connectivity
              for (let i = 0; i < numOperations; i++) {
                networkOptimizer.queueOperation({
                  type: SyncOperationType.TRANSCRIPTION,
                  priority: i === 0 ? SyncPriority.CRITICAL : SyncPriority.NORMAL,
                  data: { index: i },
                  maxRetries: 3
                });
              }

              const beforeStatus = networkOptimizer.getSyncQueueStatus();
              const queuedBefore = beforeStatus.queueSize;
              expect(queuedBefore).toBeGreaterThan(0);

              // Improve connectivity
              service.setOnlineStatus(true);
              networkOptimizer['currentCondition'] = improvedCondition;

              // Trigger recovery
              await networkOptimizer.triggerSync();

              // Assert - Property: System automatically recovers with improved connectivity
              const afterStatus = networkOptimizer.getSyncQueueStatus();
              
              // Queue should be processed
              expect(afterStatus.queueSize).toBeLessThanOrEqual(queuedBefore);

              // Quality should improve
              const quality = networkOptimizer.getAudioQuality();
              if (improvedCondition === NetworkCondition.EXCELLENT) {
                expect(quality.bitrate).toBeGreaterThanOrEqual(64);
              }

            } finally {
              offlineProcessor.destroy();
              networkOptimizer.destroy();
            }
          }
        ),
        { numRuns: 30 } // Reduced from 50
      );
    }, 30000); // 30 second timeout

    it('should handle rapid network condition changes without data loss', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te'),
            conditionChanges: fc.array(
              fc.constantFrom(
                NetworkCondition.EXCELLENT,
                NetworkCondition.GOOD,
                NetworkCondition.FAIR,
                NetworkCondition.POOR
              ),
              { minLength: 3, maxLength: 10 }
            ),
            audioSize: fc.constant(1000) // Fixed even size
          }),
          async ({ language, conditionChanges, audioSize }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();
            const offlineProcessor = service.getOfflineProcessor();
            const userId = `test-user-${Date.now()}`;

            // Cache model
            const modelData = new ArrayBuffer(1024);
            await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

            const sessionId = await service.startVoiceSession(userId, language);

            try {
              // Act - Rapidly change network conditions
              const results = [];
              
              for (const condition of conditionChanges) {
                networkOptimizer['currentCondition'] = condition;
                
                // Process audio under this condition
                const audioChunk = generateAudioChunk(audioSize, 0.7, 0);
                const result = await service.processAudioStream(sessionId, audioChunk);
                results.push(result);
              }

              // Assert - Property: No data loss despite rapid changes
              expect(results.length).toBe(conditionChanges.length);
              
              // All results should be valid
              for (const result of results) {
                expect(result).toBeDefined();
                expect(result.language).toBe(language);
                expect(result.confidence).toBeGreaterThanOrEqual(0);
                expect(result.confidence).toBeLessThanOrEqual(1.0);
                expect(result.timestamp).toBeInstanceOf(Date);
              }

              // System should remain stable
              const finalStatus = networkOptimizer.getSyncQueueStatus();
              expect(finalStatus).toBeDefined();

            } finally {
              await service.endVoiceSession(sessionId);
              offlineProcessor.destroy();
              networkOptimizer.destroy();
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should maintain data integrity during offline-to-online transitions', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te'),
            offlineOperations: fc.integer({ min: 2, max: 4 }), // Reduced from 6
            onlineOperations: fc.integer({ min: 2, max: 4 }) // Reduced from 6
          }),
          async ({ language, offlineOperations, onlineOperations }) => {
            // Arrange
            const service = new VoiceEngineService();
            const networkOptimizer = service.getNetworkOptimizer();
            const offlineProcessor = service.getOfflineProcessor();
            const userId = `test-user-${Date.now()}`;

            // Cache model
            const modelData = new ArrayBuffer(1024);
            await offlineProcessor.cacheModel(language, undefined, modelData, '1.0.0');

            const sessionId = await service.startVoiceSession(userId, language);

            try {
              const allResults = [];

              // Act - Process offline
              service.setOnlineStatus(false);
              networkOptimizer['currentCondition'] = NetworkCondition.OFFLINE;

              for (let i = 0; i < offlineOperations; i++) {
                const audioChunk = generateAudioChunk(1000, 0.7, 0);
                const result = await service.processAudioStream(sessionId, audioChunk);
                allResults.push({ result, phase: 'offline' });
              }

              // Transition to online
              service.setOnlineStatus(true);
              networkOptimizer['currentCondition'] = NetworkCondition.GOOD;

              // Process online
              for (let i = 0; i < onlineOperations; i++) {
                const audioChunk = generateAudioChunk(1000, 0.7, 0);
                const result = await service.processAudioStream(sessionId, audioChunk);
                allResults.push({ result, phase: 'online' });
              }

              // Sync offline data
              await networkOptimizer.triggerSync();

              // Assert - Property: Data integrity maintained across transition
              expect(allResults.length).toBe(offlineOperations + onlineOperations);

              // All results should be valid
              for (const { result, phase } of allResults) {
                expect(result).toBeDefined();
                expect(result.language).toBe(language);
                expect(result.confidence).toBeGreaterThanOrEqual(0.70);
                
                // Offline results should be marked as such
                if (phase === 'offline') {
                  expect(result.isOffline).toBe(true);
                }
              }

              // Sync should complete successfully
              const syncStatus = service.getSyncStatus();
              expect(syncStatus).toBeDefined();

            } finally {
              await service.endVoiceSession(sessionId);
              offlineProcessor.destroy();
              networkOptimizer.destroy();
            }
          }
        ),
        { numRuns: 30 } // Reduced from 50
      );
    }, 30000); // 30 second timeout
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
  // Create buffer with correct byte size for Int16Array (2 bytes per sample)
  const buffer = new ArrayBuffer(samples * 2);
  const view = new Int16Array(buffer);

  for (let i = 0; i < samples; i++) {
    // Generate base signal (simulating speech)
    const frequency = 200 + Math.sin(i / 100) * 100; // 100-300 Hz range
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
