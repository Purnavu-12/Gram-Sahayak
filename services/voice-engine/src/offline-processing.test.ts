/**
 * Unit tests for Offline Voice Processing
 * Tests cached model storage, offline speech recognition, scheme caching, and sync
 */

import { OfflineVoiceProcessor, CachedScheme, ModelVersion } from './offline-processing';

describe('OfflineVoiceProcessor', () => {
  let processor: OfflineVoiceProcessor;

  beforeEach(() => {
    processor = new OfflineVoiceProcessor({
      maxCacheSize: 100 * 1024 * 1024, // 100MB for testing
      syncInterval: 1000, // 1 second for testing
      maxOfflineAge: 24 * 60 * 60 * 1000 // 1 day for testing
    });
  });

  afterEach(() => {
    processor.destroy();
  });

  describe('Model Caching', () => {
    it('should cache a model successfully', async () => {
      const modelData = new ArrayBuffer(1024);
      const language = 'hi';
      const version = '1.0.0';

      await processor.cacheModel(language, undefined, modelData, version);

      const cachedModel = await processor.loadCachedModel(language);
      expect(cachedModel).not.toBeNull();
      expect(cachedModel?.version.language).toBe(language);
      expect(cachedModel?.version.version).toBe(version);
    });

    it('should cache models with dialects', async () => {
      const modelData = new ArrayBuffer(2048);
      const language = 'hi';
      const dialect = 'hi-IN-haryanvi';
      const version = '1.0.0';

      await processor.cacheModel(language, dialect, modelData, version);

      const cachedModel = await processor.loadCachedModel(language, dialect);
      expect(cachedModel).not.toBeNull();
      expect(cachedModel?.version.dialect).toBe(dialect);
    });

    it('should return null for non-existent models', async () => {
      const cachedModel = await processor.loadCachedModel('unknown');
      expect(cachedModel).toBeNull();
    });

    it('should track model versions', async () => {
      const modelData = new ArrayBuffer(1024);
      await processor.cacheModel('hi', undefined, modelData, '1.0.0');
      await processor.cacheModel('ta', undefined, modelData, '1.1.0');

      const versions = processor.getCachedModelVersions();
      expect(versions).toHaveLength(2);
      expect(versions.map(v => v.language)).toContain('hi');
      expect(versions.map(v => v.language)).toContain('ta');
    });

    it('should update last used time when loading model', async () => {
      const modelData = new ArrayBuffer(1024);
      await processor.cacheModel('hi', undefined, modelData, '1.0.0');

      const firstLoad = await processor.loadCachedModel('hi');
      const firstTime = firstLoad?.version.lastUsed.getTime();

      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 10));

      const secondLoad = await processor.loadCachedModel('hi');
      const secondTime = secondLoad?.version.lastUsed.getTime();

      expect(secondTime).toBeGreaterThan(firstTime!);
    });

    it('should evict oldest model when cache is full', async () => {
      // Create processor with small cache
      const smallProcessor = new OfflineVoiceProcessor({
        maxCacheSize: 3000 // Only 3KB
      });

      const modelData1 = new ArrayBuffer(1500);
      const modelData2 = new ArrayBuffer(1500);
      const modelData3 = new ArrayBuffer(1500);

      await smallProcessor.cacheModel('hi', undefined, modelData1, '1.0.0');
      await new Promise(resolve => setTimeout(resolve, 10));
      await smallProcessor.cacheModel('ta', undefined, modelData2, '1.0.0');
      
      // This should evict the first model
      await smallProcessor.cacheModel('te', undefined, modelData3, '1.0.0');

      const hiModel = await smallProcessor.loadCachedModel('hi');
      const taModel = await smallProcessor.loadCachedModel('ta');
      const teModel = await smallProcessor.loadCachedModel('te');

      expect(hiModel).toBeNull(); // Evicted
      expect(taModel).not.toBeNull();
      expect(teModel).not.toBeNull();

      smallProcessor.destroy();
    });
  });

  describe('Offline Speech Processing', () => {
    it('should process speech offline when model is cached', async () => {
      const modelData = new ArrayBuffer(1024);
      await processor.cacheModel('hi', undefined, modelData, '1.0.0');

      const audioData = new ArrayBuffer(512);
      const result = await processor.processOfflineSpeech(audioData, 'hi');

      expect(result).toBeDefined();
      expect(result.language).toBe('hi');
      expect(result.isOffline).toBe(true);
      expect(result.isFinal).toBe(true);
    });

    it('should throw error when model not cached', async () => {
      const audioData = new ArrayBuffer(512);

      await expect(
        processor.processOfflineSpeech(audioData, 'unknown')
      ).rejects.toThrow('No cached model available');
    });

    it('should have lower confidence for offline processing', async () => {
      const modelData = new ArrayBuffer(1024);
      await processor.cacheModel('hi', undefined, modelData, '1.0.0');

      const audioData = new ArrayBuffer(512);
      const result = await processor.processOfflineSpeech(audioData, 'hi');

      // Offline processing typically has slightly lower confidence
      expect(result.confidence).toBeLessThanOrEqual(0.95);
    });
  });

  describe('Scheme Caching', () => {
    it('should cache scheme information', async () => {
      const scheme: CachedScheme = {
        schemeId: 'PM-KISAN',
        name: { en: 'PM-KISAN', hi: 'पीएम-किसान' },
        description: { en: 'Farmer support scheme', hi: 'किसान सहायता योजना' },
        eligibilityCriteria: { landOwnership: true },
        cachedAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      };

      await processor.cacheScheme(scheme);

      const cached = await processor.getCachedScheme('PM-KISAN');
      expect(cached).not.toBeNull();
      expect(cached?.schemeId).toBe('PM-KISAN');
      expect(cached?.name.en).toBe('PM-KISAN');
    });

    it('should return null for non-existent schemes', async () => {
      const cached = await processor.getCachedScheme('NON-EXISTENT');
      expect(cached).toBeNull();
    });

    it('should get all cached schemes', async () => {
      const scheme1: CachedScheme = {
        schemeId: 'SCHEME-1',
        name: { en: 'Scheme 1' },
        description: { en: 'Description 1' },
        eligibilityCriteria: {},
        cachedAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      };

      const scheme2: CachedScheme = {
        schemeId: 'SCHEME-2',
        name: { en: 'Scheme 2' },
        description: { en: 'Description 2' },
        eligibilityCriteria: {},
        cachedAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      };

      await processor.cacheScheme(scheme1);
      await processor.cacheScheme(scheme2);

      const allSchemes = await processor.getAllCachedSchemes();
      expect(allSchemes).toHaveLength(2);
      expect(allSchemes.map(s => s.schemeId)).toContain('SCHEME-1');
      expect(allSchemes.map(s => s.schemeId)).toContain('SCHEME-2');
    });

    it('should detect expired schemes', async () => {
      const expiredScheme: CachedScheme = {
        schemeId: 'EXPIRED',
        name: { en: 'Expired Scheme' },
        description: { en: 'This is expired' },
        eligibilityCriteria: {},
        cachedAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
        expiresAt: new Date(Date.now() - 1000) // Expired 1 second ago
      };

      await processor.cacheScheme(expiredScheme);

      let expiredEventFired = false;
      processor.once('scheme:expired', () => {
        expiredEventFired = true;
      });

      const cached = await processor.getCachedScheme('EXPIRED');
      expect(cached).not.toBeNull(); // Still returns the scheme
      expect(expiredEventFired).toBe(true); // But fires expired event
    });
  });

  describe('Online/Offline Status', () => {
    it('should track online status', () => {
      processor.setOnlineStatus(false);
      expect(processor.isOfflineModeAvailable('hi')).toBe(false);

      processor.setOnlineStatus(true);
      // Status changed but model still not available
      expect(processor.isOfflineModeAvailable('hi')).toBe(false);
    });

    it('should emit events on status change', (done) => {
      let offlineEventFired = false;
      let onlineEventFired = false;

      processor.once('network:offline', () => {
        offlineEventFired = true;
      });

      processor.once('network:online', () => {
        onlineEventFired = true;
        expect(offlineEventFired).toBe(true);
        expect(onlineEventFired).toBe(true);
        done();
      });

      processor.setOnlineStatus(false);
      processor.setOnlineStatus(true);
    });

    it('should check offline mode availability', async () => {
      expect(processor.isOfflineModeAvailable('hi')).toBe(false);

      const modelData = new ArrayBuffer(1024);
      await processor.cacheModel('hi', undefined, modelData, '1.0.0');

      expect(processor.isOfflineModeAvailable('hi')).toBe(true);
      expect(processor.isOfflineModeAvailable('ta')).toBe(false);
    });
  });

  describe('Synchronization', () => {
    it('should track sync status', () => {
      const status = processor.getSyncStatus();
      expect(status).toBeDefined();
      expect(status.lastSyncTime).toBeNull();
      expect(status.pendingOperations).toBe(0);
      expect(status.isSyncing).toBe(false);
    });

    it('should sync with cloud when online', async () => {
      processor.setOnlineStatus(true);

      let syncStarted = false;
      let syncCompleted = false;

      processor.once('sync:started', () => {
        syncStarted = true;
      });

      processor.once('sync:completed', () => {
        syncCompleted = true;
      });

      await processor.syncWithCloud();

      expect(syncStarted).toBe(true);
      expect(syncCompleted).toBe(true);

      const status = processor.getSyncStatus();
      expect(status.lastSyncTime).not.toBeNull();
    });

    it('should not sync when offline', async () => {
      processor.setOnlineStatus(false);

      let syncStarted = false;
      processor.once('sync:started', () => {
        syncStarted = true;
      });

      await processor.syncWithCloud();

      expect(syncStarted).toBe(false);
    });

    it('should not sync when already syncing', async () => {
      processor.setOnlineStatus(true);

      let syncCount = 0;
      processor.on('sync:started', () => {
        syncCount++;
      });

      // Start two syncs simultaneously
      const sync1 = processor.syncWithCloud();
      const sync2 = processor.syncWithCloud();

      await Promise.all([sync1, sync2]);

      // Should only sync once
      expect(syncCount).toBe(1);
    });
  });

  describe('Cache Management', () => {
    it('should clear expired cache entries', async () => {
      // Add an old scheme
      const oldScheme: CachedScheme = {
        schemeId: 'OLD',
        name: { en: 'Old Scheme' },
        description: { en: 'Old' },
        eligibilityCriteria: {},
        cachedAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
        expiresAt: new Date(Date.now() - 1000)
      };

      await processor.cacheScheme(oldScheme);

      let clearedCount = 0;
      processor.once('cache:cleared', ({ clearedCount: count }) => {
        clearedCount = count;
      });

      await processor.clearExpiredCache();

      expect(clearedCount).toBeGreaterThan(0);

      const cached = await processor.getCachedScheme('OLD');
      expect(cached).toBeNull();
    });

    it('should emit events for cache operations', async () => {
      const events: string[] = [];

      processor.on('model:cached', () => events.push('model:cached'));
      processor.on('model:loaded', () => events.push('model:loaded'));
      processor.on('scheme:cached', () => events.push('scheme:cached'));

      const modelData = new ArrayBuffer(1024);
      await processor.cacheModel('hi', undefined, modelData, '1.0.0');
      await processor.loadCachedModel('hi');

      const scheme: CachedScheme = {
        schemeId: 'TEST',
        name: { en: 'Test' },
        description: { en: 'Test' },
        eligibilityCriteria: {},
        cachedAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      };
      await processor.cacheScheme(scheme);

      expect(events).toContain('model:cached');
      expect(events).toContain('model:loaded');
      expect(events).toContain('scheme:cached');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty audio data', async () => {
      const modelData = new ArrayBuffer(1024);
      await processor.cacheModel('hi', undefined, modelData, '1.0.0');

      const emptyAudio = new ArrayBuffer(0);
      const result = await processor.processOfflineSpeech(emptyAudio, 'hi');

      expect(result).toBeDefined();
      expect(result.isOffline).toBe(true);
    });

    it('should handle multiple languages simultaneously', async () => {
      const modelData = new ArrayBuffer(1024);
      
      await Promise.all([
        processor.cacheModel('hi', undefined, modelData, '1.0.0'),
        processor.cacheModel('ta', undefined, modelData, '1.0.0'),
        processor.cacheModel('te', undefined, modelData, '1.0.0')
      ]);

      expect(processor.isOfflineModeAvailable('hi')).toBe(true);
      expect(processor.isOfflineModeAvailable('ta')).toBe(true);
      expect(processor.isOfflineModeAvailable('te')).toBe(true);
    });

    it('should handle rapid status changes', () => {
      for (let i = 0; i < 10; i++) {
        processor.setOnlineStatus(i % 2 === 0);
      }

      // Should end up offline (last value was false for i=9)
      const status = processor.getSyncStatus();
      expect(status).toBeDefined();
    });
  });
});
