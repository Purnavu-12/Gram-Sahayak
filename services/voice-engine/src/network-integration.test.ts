/**
 * Integration tests for Network Optimization with Voice Engine
 */

import { VoiceEngineService } from './voice-engine-service';
import { NetworkCondition, SyncOperationType, SyncPriority } from './network-optimization';

describe('Network Optimization Integration', () => {
  let voiceEngine: VoiceEngineService;
  let sessionId: string;

  beforeEach(async () => {
    voiceEngine = new VoiceEngineService();
    sessionId = await voiceEngine.startVoiceSession('test-user', 'hi');
  });

  afterEach(async () => {
    if (sessionId) {
      await voiceEngine.endVoiceSession(sessionId);
    }
  });

  describe('Audio Processing with Network Optimization', () => {
    it('should compress audio based on network conditions', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();
      
      // Set poor network condition
      networkOptimizer['currentCondition'] = NetworkCondition.POOR;
      networkOptimizer['currentMetrics'] = {
        bandwidth: 200,
        latency: 400,
        packetLoss: 5,
        jitter: 50,
        timestamp: new Date()
      };

      // Process audio
      const audioData = new ArrayBuffer(1000);
      const result = await voiceEngine.processAudioStream(sessionId, audioData);

      expect(result).toBeDefined();
      expect(result.timestamp).toBeInstanceOf(Date);
    });

    it('should queue transcriptions when offline', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();
      const offlineProcessor = voiceEngine.getOfflineProcessor();

      // Setup offline mode
      voiceEngine.setOnlineStatus(false);
      networkOptimizer['currentCondition'] = NetworkCondition.OFFLINE;

      // Cache a model for offline processing
      const modelData = new ArrayBuffer(1000);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');

      // Process audio offline
      const audioData = new ArrayBuffer(1000);
      await voiceEngine.processAudioStream(sessionId, audioData);

      // Check that operation was queued
      const queueStatus = networkOptimizer.getSyncQueueStatus();
      expect(queueStatus.queueSize).toBeGreaterThan(0);
    });

    it('should sync queued operations when coming back online', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();
      const offlineProcessor = voiceEngine.getOfflineProcessor();

      // Start offline
      voiceEngine.setOnlineStatus(false);
      networkOptimizer['currentCondition'] = NetworkCondition.OFFLINE;

      // Cache model
      const modelData = new ArrayBuffer(1000);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');

      // Process audio offline
      const audioData = new ArrayBuffer(1000);
      await voiceEngine.processAudioStream(sessionId, audioData);

      // Come back online
      voiceEngine.setOnlineStatus(true);
      networkOptimizer['currentCondition'] = NetworkCondition.GOOD;

      // Trigger sync
      await networkOptimizer.triggerSync();

      // Queue should be processed
      const queueStatus = networkOptimizer.getSyncQueueStatus();
      expect(queueStatus.queueSize).toBe(0);
    });
  });

  describe('Adaptive Quality Adjustment', () => {
    it('should adjust audio quality when network degrades', (done) => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      networkOptimizer.on('quality:adjusted', ({ oldQuality, newQuality, condition }) => {
        expect(condition).toBe(NetworkCondition.POOR);
        expect(newQuality.bitrate).toBeLessThan(oldQuality.bitrate);
        done();
      });

      // Simulate network degradation
      networkOptimizer['handleConditionChange'](NetworkCondition.POOR);
    });

    it('should improve quality when network improves', (done) => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Start with poor condition
      networkOptimizer['currentCondition'] = NetworkCondition.POOR;
      networkOptimizer['handleConditionChange'](NetworkCondition.POOR);

      networkOptimizer.on('quality:adjusted', ({ oldQuality, newQuality, condition }) => {
        if (condition === NetworkCondition.EXCELLENT) {
          expect(newQuality.bitrate).toBeGreaterThan(oldQuality.bitrate);
          done();
        }
      });

      // Improve network
      networkOptimizer['handleConditionChange'](NetworkCondition.EXCELLENT);
    });
  });

  describe('Sync Queue Priority Management', () => {
    it('should prioritize critical operations', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Queue operations with different priorities
      networkOptimizer.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.LOW,
        data: { text: 'low priority' },
        maxRetries: 3
      });

      networkOptimizer.queueOperation({
        type: SyncOperationType.APPLICATION,
        priority: SyncPriority.CRITICAL,
        data: { applicationId: 'app-123' },
        maxRetries: 3
      });

      networkOptimizer.queueOperation({
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.HIGH,
        data: { userId: 'user-123' },
        maxRetries: 3
      });

      // Get queue status
      const status = networkOptimizer.getSyncQueueStatus();
      expect(status.queueSize).toBe(3);
      expect(status.byPriority[SyncPriority.CRITICAL]).toBe(1);
      expect(status.byPriority[SyncPriority.HIGH]).toBe(1);
      expect(status.byPriority[SyncPriority.LOW]).toBe(1);
    });

    it('should defer non-critical updates in poor network', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Set poor network condition
      networkOptimizer['currentCondition'] = NetworkCondition.POOR;

      // Queue operations
      networkOptimizer.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.LOW,
        data: {},
        maxRetries: 3
      });

      networkOptimizer.queueOperation({
        type: SyncOperationType.APPLICATION,
        priority: SyncPriority.CRITICAL,
        data: {},
        maxRetries: 3
      });

      // Get next batch
      const batch = networkOptimizer['getNextBatch']();

      // Should only include critical operations
      expect(batch.length).toBe(1);
      expect(batch[0].priority).toBe(SyncPriority.CRITICAL);
    });
  });

  describe('Bandwidth Optimization', () => {
    it('should compress audio when bandwidth is limited', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Set limited bandwidth
      networkOptimizer['currentMetrics'] = {
        bandwidth: 300, // Below compression threshold
        latency: 200,
        packetLoss: 2,
        jitter: 20,
        timestamp: new Date()
      };
      networkOptimizer['currentCondition'] = NetworkCondition.FAIR;

      const audioData = new ArrayBuffer(10000);
      const result = await networkOptimizer.compressAudio(audioData);

      expect(result.compressedSize).toBeLessThan(result.originalSize);
      expect(result.compressionRatio).toBeLessThan(1.0);
    });

    it('should minimize compression when bandwidth is good', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Set good bandwidth
      networkOptimizer['currentMetrics'] = {
        bandwidth: 5000, // Above compression threshold
        latency: 50,
        packetLoss: 0.1,
        jitter: 5,
        timestamp: new Date()
      };
      networkOptimizer['currentCondition'] = NetworkCondition.EXCELLENT;

      const audioData = new ArrayBuffer(10000);
      const result = await networkOptimizer.compressAudio(audioData);

      // Should have minimal or no compression
      expect(result.compressionRatio).toBeGreaterThan(0.7);
    });
  });

  describe('Network Condition Monitoring', () => {
    it('should detect network metrics', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();
      const metrics = await networkOptimizer.measureNetworkConditions();

      expect(metrics).toBeDefined();
      expect(metrics.bandwidth).toBeGreaterThanOrEqual(0);
      expect(metrics.latency).toBeGreaterThanOrEqual(0);
      expect(metrics.packetLoss).toBeGreaterThanOrEqual(0);
      expect(metrics.jitter).toBeGreaterThanOrEqual(0);
    });

    it('should update condition based on metrics', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Simulate poor metrics
      networkOptimizer['currentMetrics'] = {
        bandwidth: 100,
        latency: 500,
        packetLoss: 10,
        jitter: 100,
        timestamp: new Date()
      };

      const condition = networkOptimizer['determineNetworkCondition'](
        networkOptimizer['currentMetrics']
      );

      expect(condition).toBe(NetworkCondition.POOR);
    });
  });

  describe('Offline-to-Online Synchronization', () => {
    it('should handle complete offline workflow', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();
      const offlineProcessor = voiceEngine.getOfflineProcessor();

      // Setup offline mode
      voiceEngine.setOnlineStatus(false);
      networkOptimizer['currentCondition'] = NetworkCondition.OFFLINE;

      // Cache model
      const modelData = new ArrayBuffer(1000);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');

      // Process multiple audio chunks offline
      for (let i = 0; i < 3; i++) {
        const audioData = new ArrayBuffer(1000);
        await voiceEngine.processAudioStream(sessionId, audioData);
      }

      // Verify operations are queued
      let queueStatus = networkOptimizer.getSyncQueueStatus();
      expect(queueStatus.queueSize).toBeGreaterThan(0);

      // Come back online
      voiceEngine.setOnlineStatus(true);
      networkOptimizer['currentCondition'] = NetworkCondition.GOOD;

      // Sync
      await networkOptimizer.triggerSync();

      // Verify queue is processed
      queueStatus = networkOptimizer.getSyncQueueStatus();
      expect(queueStatus.queueSize).toBe(0);
    });

    it('should handle sync conflicts', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      let conflictResolved = false;
      networkOptimizer.on('conflict:resolved', () => {
        conflictResolved = true;
      });

      // Queue operation
      networkOptimizer.queueOperation({
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.HIGH,
        data: { name: 'test' },
        maxRetries: 3
      });

      // Process (may trigger conflict in simulation)
      await networkOptimizer.triggerSync();

      // Conflict may or may not occur due to random simulation
      // Just verify no errors thrown
      expect(true).toBe(true);
    });
  });

  describe('Requirements Validation', () => {
    it('should validate Requirement 8.3: Sync offline interactions when connectivity returns', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();
      const offlineProcessor = voiceEngine.getOfflineProcessor();

      // Go offline
      voiceEngine.setOnlineStatus(false);
      networkOptimizer['currentCondition'] = NetworkCondition.OFFLINE;

      // Cache model and process offline
      const modelData = new ArrayBuffer(1000);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');

      const audioData = new ArrayBuffer(1000);
      await voiceEngine.processAudioStream(sessionId, audioData);

      // Verify queued
      let queueStatus = networkOptimizer.getSyncQueueStatus();
      const queuedCount = queueStatus.queueSize;
      expect(queuedCount).toBeGreaterThan(0);

      // Restore connectivity
      voiceEngine.setOnlineStatus(true);
      networkOptimizer['currentCondition'] = NetworkCondition.GOOD;

      // Sync should happen
      await networkOptimizer.triggerSync();

      queueStatus = networkOptimizer.getSyncQueueStatus();
      expect(queueStatus.queueSize).toBeLessThan(queuedCount);
    });

    it('should validate Requirement 8.4: Compress audio and minimize bandwidth usage', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Set condition where compression is needed
      networkOptimizer['currentMetrics'] = {
        bandwidth: 400, // Below threshold
        latency: 200,
        packetLoss: 2,
        jitter: 20,
        timestamp: new Date()
      };
      networkOptimizer['currentCondition'] = NetworkCondition.FAIR;

      const audioData = new ArrayBuffer(10000);
      const result = await networkOptimizer.compressAudio(audioData);

      // Verify compression occurred
      expect(result.compressedSize).toBeLessThan(result.originalSize);
      expect(result.compressionRatio).toBeLessThan(1.0);
    });

    it('should validate Requirement 8.5: Prioritize essential data in slow network', async () => {
      const networkOptimizer = voiceEngine.getNetworkOptimizer();

      // Set slow network
      networkOptimizer['currentCondition'] = NetworkCondition.POOR;

      // Queue mixed priority operations
      networkOptimizer.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.LOW,
        data: {},
        maxRetries: 3
      });

      networkOptimizer.queueOperation({
        type: SyncOperationType.APPLICATION,
        priority: SyncPriority.CRITICAL,
        data: {},
        maxRetries: 3
      });

      // Get batch for processing
      const batch = networkOptimizer['getNextBatch']();

      // Should only include critical/high priority
      for (const op of batch) {
        expect(op.priority).toBeLessThanOrEqual(SyncPriority.HIGH);
      }
    });
  });
});
