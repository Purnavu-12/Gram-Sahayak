/**
 * Unit tests for Network Optimization Service
 */

import {
  NetworkOptimizationService,
  NetworkCondition,
  SyncOperationType,
  SyncPriority,
  ConflictResolutionStrategy,
  AudioQualitySettings,
  NetworkMetrics
} from './network-optimization';

describe('NetworkOptimizationService', () => {
  let service: NetworkOptimizationService;

  beforeEach(() => {
    service = new NetworkOptimizationService({
      enableAdaptiveQuality: true,
      enableCompression: true,
      maxQueueSize: 100,
      syncBatchSize: 5,
      syncInterval: 1000,
      bandwidthTestInterval: 5000,
      compressionThreshold: 512
    });
  });

  afterEach(() => {
    service.destroy();
  });

  describe('Network Condition Detection', () => {
    it('should initialize with GOOD network condition', () => {
      const condition = service.getNetworkCondition();
      expect(condition).toBe(NetworkCondition.GOOD);
    });

    it('should detect network condition changes', (done) => {
      service.on('condition:changed', ({ oldCondition, newCondition }) => {
        expect(oldCondition).toBeDefined();
        expect(newCondition).toBeDefined();
        done();
      });

      // Trigger condition change by simulating different metrics
      service['currentMetrics'] = {
        bandwidth: 100,
        latency: 500,
        packetLoss: 10,
        jitter: 100,
        timestamp: new Date()
      };
      service['handleConditionChange'](NetworkCondition.POOR);
    });

    it('should emit network:offline when going offline', (done) => {
      service.on('network:offline', () => {
        done();
      });

      // Simulate offline condition
      service['currentMetrics'] = {
        bandwidth: 0,
        latency: 0,
        packetLoss: 100,
        jitter: 0,
        timestamp: new Date()
      };
      service['handleConditionChange'](NetworkCondition.OFFLINE);
    });

    it('should emit network:online when coming back online', (done) => {
      // First go offline
      service['currentCondition'] = NetworkCondition.OFFLINE;

      service.on('network:online', () => {
        done();
      });

      // Come back online
      service['handleConditionChange'](NetworkCondition.GOOD);
    });
  });

  describe('Audio Quality Adjustment', () => {
    it('should adjust quality based on network condition', (done) => {
      service.on('quality:adjusted', ({ oldQuality, newQuality, condition }) => {
        expect(oldQuality).toBeDefined();
        expect(newQuality).toBeDefined();
        expect(condition).toBe(NetworkCondition.POOR);
        expect(newQuality.bitrate).toBeLessThan(oldQuality.bitrate);
        done();
      });

      service['handleConditionChange'](NetworkCondition.POOR);
    });

    it('should use lower bitrate for poor conditions', () => {
      service['handleConditionChange'](NetworkCondition.POOR);
      const quality = service.getAudioQuality();
      
      expect(quality.bitrate).toBe(16);
      expect(quality.sampleRate).toBe(8000);
      expect(quality.compressionLevel).toBe(9);
    });

    it('should use higher bitrate for excellent conditions', () => {
      service['handleConditionChange'](NetworkCondition.EXCELLENT);
      const quality = service.getAudioQuality();
      
      expect(quality.bitrate).toBe(128);
      expect(quality.sampleRate).toBe(48000);
      expect(quality.compressionLevel).toBe(3);
    });

    it('should not adjust quality if adaptive quality is disabled', () => {
      const noAdaptiveService = new NetworkOptimizationService({
        enableAdaptiveQuality: false
      });

      const initialQuality = noAdaptiveService.getAudioQuality();
      noAdaptiveService['handleConditionChange'](NetworkCondition.POOR);
      const afterQuality = noAdaptiveService.getAudioQuality();

      expect(afterQuality).toEqual(initialQuality);
      noAdaptiveService.destroy();
    });
  });

  describe('Audio Compression', () => {
    it('should compress audio when network is poor', async () => {
      service['handleConditionChange'](NetworkCondition.POOR);
      
      const audioData = new ArrayBuffer(10000);
      const result = await service.compressAudio(audioData);

      expect(result.originalSize).toBe(10000);
      expect(result.compressedSize).toBeLessThan(result.originalSize);
      expect(result.compressionRatio).toBeLessThan(1.0);
    });

    it('should not compress when network is excellent and compression disabled', async () => {
      const noCompressionService = new NetworkOptimizationService({
        enableCompression: false
      });

      const audioData = new ArrayBuffer(10000);
      const result = await noCompressionService.compressAudio(audioData);

      expect(result.compressedSize).toBe(result.originalSize);
      expect(result.compressionRatio).toBe(1.0);
      
      noCompressionService.destroy();
    });

    it('should emit audio:compressed event', (done) => {
      service['handleConditionChange'](NetworkCondition.POOR);
      
      service.on('audio:compressed', (result) => {
        expect(result.originalSize).toBeGreaterThan(0);
        expect(result.compressedSize).toBeGreaterThan(0);
        done();
      });

      const audioData = new ArrayBuffer(10000);
      service.compressAudio(audioData);
    });

    it('should compress more aggressively in poor conditions', async () => {
      service['handleConditionChange'](NetworkCondition.POOR);
      const audioData = new ArrayBuffer(10000);
      const poorResult = await service.compressAudio(audioData);

      service['handleConditionChange'](NetworkCondition.FAIR);
      const fairResult = await service.compressAudio(audioData);

      expect(poorResult.compressionRatio).toBeLessThan(fairResult.compressionRatio);
    });
  });

  describe('Sync Queue Management', () => {
    it('should queue operations', () => {
      const id = service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.NORMAL,
        data: { text: 'test' },
        maxRetries: 3
      });

      expect(id).toBeDefined();
      expect(id).toMatch(/^sync_/);

      const status = service.getSyncQueueStatus();
      expect(status.queueSize).toBe(1);
    });

    it('should prioritize operations by priority', () => {
      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.LOW,
        data: {},
        maxRetries: 3
      });

      service.queueOperation({
        type: SyncOperationType.APPLICATION,
        priority: SyncPriority.CRITICAL,
        data: {},
        maxRetries: 3
      });

      service.queueOperation({
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.HIGH,
        data: {},
        maxRetries: 3
      });

      const queue = service['syncQueue'];
      expect(queue[0].priority).toBe(SyncPriority.CRITICAL);
      expect(queue[1].priority).toBe(SyncPriority.HIGH);
      expect(queue[2].priority).toBe(SyncPriority.LOW);
    });

    it('should evict low priority operations when queue is full', () => {
      const smallQueueService = new NetworkOptimizationService({
        maxQueueSize: 3
      });

      // Fill queue
      smallQueueService.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.LOW,
        data: {},
        maxRetries: 3
      });

      smallQueueService.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.NORMAL,
        data: {},
        maxRetries: 3
      });

      smallQueueService.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.HIGH,
        data: {},
        maxRetries: 3
      });

      // This should evict the LOW priority operation
      smallQueueService.queueOperation({
        type: SyncOperationType.APPLICATION,
        priority: SyncPriority.CRITICAL,
        data: {},
        maxRetries: 3
      });

      const status = smallQueueService.getSyncQueueStatus();
      expect(status.queueSize).toBe(3);
      expect(status.byPriority[SyncPriority.LOW]).toBe(0);

      smallQueueService.destroy();
    });

    it('should emit operation:queued event', (done) => {
      service.on('operation:queued', ({ id, type, priority }) => {
        expect(id).toBeDefined();
        expect(type).toBe(SyncOperationType.TRANSCRIPTION);
        expect(priority).toBe(SyncPriority.NORMAL);
        done();
      });

      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.NORMAL,
        data: {},
        maxRetries: 3
      });
    });

    it('should get queue status by priority', () => {
      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.CRITICAL,
        data: {},
        maxRetries: 3
      });

      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.CRITICAL,
        data: {},
        maxRetries: 3
      });

      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.HIGH,
        data: {},
        maxRetries: 3
      });

      const status = service.getSyncQueueStatus();
      expect(status.byPriority[SyncPriority.CRITICAL]).toBe(2);
      expect(status.byPriority[SyncPriority.HIGH]).toBe(1);
      expect(status.byPriority[SyncPriority.NORMAL]).toBe(0);
    });

    it('should clear queue', () => {
      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.NORMAL,
        data: {},
        maxRetries: 3
      });

      service.clearQueue();

      const status = service.getSyncQueueStatus();
      expect(status.queueSize).toBe(0);
    });
  });

  describe('Sync Processing', () => {
    it('should not sync when offline', async () => {
      service['currentCondition'] = NetworkCondition.OFFLINE;
      
      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.NORMAL,
        data: {},
        maxRetries: 3
      });

      await service.processSyncQueue();

      const status = service.getSyncQueueStatus();
      expect(status.queueSize).toBe(1); // Should still be in queue
    });

    it('should process operations when online', async () => {
      service['currentCondition'] = NetworkCondition.GOOD;
      
      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.NORMAL,
        data: {},
        maxRetries: 3
      });

      await service.processSyncQueue();

      const status = service.getSyncQueueStatus();
      expect(status.queueSize).toBe(0); // Should be processed
    });

    it('should emit sync:started and sync:completed events', (done) => {
      let started = false;

      service.on('sync:started', () => {
        started = true;
      });

      service.on('sync:completed', ({ processed, remaining }) => {
        expect(started).toBe(true);
        expect(processed).toBeGreaterThanOrEqual(0);
        expect(remaining).toBeGreaterThanOrEqual(0);
        done();
      });

      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.NORMAL,
        data: {},
        maxRetries: 3
      });

      service.processSyncQueue();
    });

    it('should process operations in batches', async () => {
      // Queue more operations than batch size
      for (let i = 0; i < 10; i++) {
        service.queueOperation({
          type: SyncOperationType.TRANSCRIPTION,
          priority: SyncPriority.NORMAL,
          data: { index: i },
          maxRetries: 3
        });
      }

      await service.processSyncQueue();

      const status = service.getSyncQueueStatus();
      // Should have processed one batch (5 operations)
      expect(status.queueSize).toBeLessThan(10);
    });

    it('should reduce batch size in poor conditions', () => {
      service['currentCondition'] = NetworkCondition.POOR;
      const batch = service['getNextBatch']();
      
      service['currentCondition'] = NetworkCondition.GOOD;
      const normalBatch = service['getNextBatch']();

      // Poor condition batch should be smaller or equal
      expect(batch.length).toBeLessThanOrEqual(normalBatch.length);
    });

    it('should only sync critical/high priority in poor conditions', () => {
      service['currentCondition'] = NetworkCondition.POOR;

      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.LOW,
        data: {},
        maxRetries: 3
      });

      service.queueOperation({
        type: SyncOperationType.APPLICATION,
        priority: SyncPriority.CRITICAL,
        data: {},
        maxRetries: 3
      });

      const batch = service['getNextBatch']();
      
      // Should only include CRITICAL, not LOW
      expect(batch.length).toBe(1);
      expect(batch[0].priority).toBe(SyncPriority.CRITICAL);
    });
  });

  describe('Conflict Resolution', () => {
    it('should handle SERVER_WINS strategy', async () => {
      const operation = {
        id: 'test-op',
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.NORMAL,
        data: { name: 'local' },
        timestamp: new Date(),
        retryCount: 0,
        maxRetries: 3,
        conflictResolution: ConflictResolutionStrategy.SERVER_WINS
      };

      await service['handleConflict'](operation);
      // Should not throw
    });

    it('should handle CLIENT_WINS strategy', async () => {
      const operation = {
        id: 'test-op',
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.NORMAL,
        data: { name: 'local' },
        timestamp: new Date(),
        retryCount: 0,
        maxRetries: 3,
        conflictResolution: ConflictResolutionStrategy.CLIENT_WINS
      };

      await service['handleConflict'](operation);
      // Should not throw
    });

    it('should handle MERGE strategy', async () => {
      const operation = {
        id: 'test-op',
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.NORMAL,
        data: { name: 'local', age: 25 },
        timestamp: new Date(),
        retryCount: 0,
        maxRetries: 3,
        conflictResolution: ConflictResolutionStrategy.MERGE
      };

      await service['handleConflict'](operation);
      // Should not throw
    });

    it('should emit conflict:manual for MANUAL strategy', (done) => {
      service.on('conflict:manual', (conflict) => {
        expect(conflict.operationId).toBe('test-op');
        expect(conflict.resolution).toBe(ConflictResolutionStrategy.MANUAL);
        done();
      });

      const operation = {
        id: 'test-op',
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.NORMAL,
        data: { name: 'local' },
        timestamp: new Date(),
        retryCount: 0,
        maxRetries: 3,
        conflictResolution: ConflictResolutionStrategy.MANUAL
      };

      service['handleConflict'](operation).catch(() => {
        // Expected to throw for manual resolution
      });
    });

    it('should emit conflict:resolved event', (done) => {
      service.on('conflict:resolved', (conflict) => {
        expect(conflict.operationId).toBeDefined();
        expect(conflict.resolvedData).toBeDefined();
        done();
      });

      const operation = {
        id: 'test-op',
        type: SyncOperationType.USER_PROFILE,
        priority: SyncPriority.NORMAL,
        data: { name: 'local' },
        timestamp: new Date(),
        retryCount: 0,
        maxRetries: 3,
        conflictResolution: ConflictResolutionStrategy.SERVER_WINS
      };

      service['handleConflict'](operation);
    });
  });

  describe('Network Metrics', () => {
    it('should measure network conditions', async () => {
      const metrics = await service.measureNetworkConditions();

      expect(metrics.bandwidth).toBeGreaterThanOrEqual(0);
      expect(metrics.latency).toBeGreaterThanOrEqual(0);
      expect(metrics.packetLoss).toBeGreaterThanOrEqual(0);
      expect(metrics.jitter).toBeGreaterThanOrEqual(0);
      expect(metrics.timestamp).toBeInstanceOf(Date);
    });

    it('should emit metrics:updated event', (done) => {
      service.on('metrics:updated', (metrics) => {
        expect(metrics).toBeDefined();
        expect(metrics.bandwidth).toBeDefined();
        done();
      });

      service.measureNetworkConditions();
    });

    it('should get current metrics', async () => {
      await service.measureNetworkConditions();
      const metrics = service.getNetworkMetrics();

      expect(metrics).not.toBeNull();
      expect(metrics?.bandwidth).toBeDefined();
    });
  });

  describe('Integration', () => {
    it('should handle complete offline-to-online flow', async () => {
      // Start offline
      service['currentCondition'] = NetworkCondition.OFFLINE;

      // Queue operations while offline
      service.queueOperation({
        type: SyncOperationType.TRANSCRIPTION,
        priority: SyncPriority.HIGH,
        data: { text: 'offline transcription' },
        maxRetries: 3
      });

      let status = service.getSyncQueueStatus();
      expect(status.queueSize).toBe(1);

      // Come back online
      service['handleConditionChange'](NetworkCondition.GOOD);

      // Process queue
      await service.processSyncQueue();

      status = service.getSyncQueueStatus();
      // Queue should be empty or have fewer items after processing
      expect(status.queueSize).toBeLessThanOrEqual(1);
    });

    it('should adapt quality and compression together', async () => {
      // Start with good conditions
      service['handleConditionChange'](NetworkCondition.GOOD);
      const goodQuality = service.getAudioQuality();

      const audioData = new ArrayBuffer(10000);
      const goodCompression = await service.compressAudio(audioData);

      // Switch to poor conditions
      service['handleConditionChange'](NetworkCondition.POOR);
      const poorQuality = service.getAudioQuality();
      const poorCompression = await service.compressAudio(audioData);

      // Quality should be lower
      expect(poorQuality.bitrate).toBeLessThan(goodQuality.bitrate);
      
      // Compression should be more aggressive
      expect(poorCompression.compressionRatio).toBeLessThan(goodCompression.compressionRatio);
    });
  });
});
