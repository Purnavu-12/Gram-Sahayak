/**
 * Integration tests for Offline Voice Processing with Voice Engine
 * Tests the integration between offline processor and voice engine service
 */

import { VoiceEngineService } from './voice-engine-service';

describe('Offline Voice Processing Integration', () => {
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

  describe('Offline Mode Availability', () => {
    it('should check offline mode availability', () => {
      const isAvailable = voiceEngine.isOfflineModeAvailable('hi');
      expect(typeof isAvailable).toBe('boolean');
    });

    it('should return false for uncached languages', () => {
      const isAvailable = voiceEngine.isOfflineModeAvailable('unknown-lang');
      expect(isAvailable).toBe(false);
    });

    it('should return true after caching model', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      const modelData = new ArrayBuffer(1024);
      
      await offlineProcessor.cacheModel('ta', undefined, modelData, '1.0.0');
      
      const isAvailable = voiceEngine.isOfflineModeAvailable('ta');
      expect(isAvailable).toBe(true);
    });
  });

  describe('Online/Offline Switching', () => {
    it('should switch to offline mode', () => {
      voiceEngine.setOnlineStatus(false);
      const syncStatus = voiceEngine.getSyncStatus();
      expect(syncStatus).toBeDefined();
    });

    it('should switch back to online mode', () => {
      voiceEngine.setOnlineStatus(false);
      voiceEngine.setOnlineStatus(true);
      const syncStatus = voiceEngine.getSyncStatus();
      expect(syncStatus).toBeDefined();
    });

    it('should handle offline audio processing when model is cached', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      const modelData = new ArrayBuffer(1024);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');

      voiceEngine.setOnlineStatus(false);

      const audioChunk = new ArrayBuffer(512);
      const result = await voiceEngine.processAudioStream(sessionId, audioChunk);

      expect(result).toBeDefined();
      expect(result.isOffline).toBe(true);
    });

    it('should handle offline processing failure gracefully', async () => {
      voiceEngine.setOnlineStatus(false);

      const audioChunk = new ArrayBuffer(512);
      const result = await voiceEngine.processAudioStream(sessionId, audioChunk);

      expect(result).toBeDefined();
      expect(result.confidence).toBe(0);
      expect(result.isOffline).toBe(true);
    });
  });

  describe('Sync Status', () => {
    it('should get sync status', () => {
      const status = voiceEngine.getSyncStatus();
      expect(status).toBeDefined();
      expect(status).toHaveProperty('lastSyncTime');
      expect(status).toHaveProperty('pendingOperations');
      expect(status).toHaveProperty('isSyncing');
      expect(status).toHaveProperty('syncErrors');
    });

    it('should track sync operations', async () => {
      voiceEngine.setOnlineStatus(true);
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      
      await offlineProcessor.syncWithCloud();
      
      const status = voiceEngine.getSyncStatus();
      expect(status.lastSyncTime).not.toBeNull();
    });
  });

  describe('Offline Processor Access', () => {
    it('should provide access to offline processor', () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      expect(offlineProcessor).toBeDefined();
      expect(typeof offlineProcessor.cacheModel).toBe('function');
      expect(typeof offlineProcessor.cacheScheme).toBe('function');
    });

    it('should allow caching models through offline processor', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      const modelData = new ArrayBuffer(2048);
      
      await offlineProcessor.cacheModel('te', undefined, modelData, '1.0.0');
      
      const versions = offlineProcessor.getCachedModelVersions();
      expect(versions.some(v => v.language === 'te')).toBe(true);
    });

    it('should allow caching schemes through offline processor', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      
      const scheme = {
        schemeId: 'TEST-SCHEME',
        name: { en: 'Test Scheme', hi: 'परीक्षण योजना' },
        description: { en: 'Test', hi: 'परीक्षण' },
        eligibilityCriteria: { age: { min: 18, max: 60 } },
        cachedAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      };
      
      await offlineProcessor.cacheScheme(scheme);
      
      const cached = await offlineProcessor.getCachedScheme('TEST-SCHEME');
      expect(cached).not.toBeNull();
      expect(cached?.schemeId).toBe('TEST-SCHEME');
    });
  });

  describe('Multiple Sessions with Offline Mode', () => {
    it('should handle multiple sessions in offline mode', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      const modelData = new ArrayBuffer(1024);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');
      await offlineProcessor.cacheModel('ta', undefined, modelData, '1.0.0');

      voiceEngine.setOnlineStatus(false);

      const session1 = await voiceEngine.startVoiceSession('user1', 'hi');
      const session2 = await voiceEngine.startVoiceSession('user2', 'ta');

      const audioChunk = new ArrayBuffer(512);
      
      const result1 = await voiceEngine.processAudioStream(session1, audioChunk);
      const result2 = await voiceEngine.processAudioStream(session2, audioChunk);

      expect(result1.isOffline).toBe(true);
      expect(result2.isOffline).toBe(true);
      expect(result1.language).toBe('hi');
      expect(result2.language).toBe('ta');

      await voiceEngine.endVoiceSession(session1);
      await voiceEngine.endVoiceSession(session2);
    });
  });

  describe('Fallback Mechanisms', () => {
    it('should fallback to offline when connection fails', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      const modelData = new ArrayBuffer(1024);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');

      // Simulate connection failure
      voiceEngine.setOnlineStatus(false);

      const audioChunk = new ArrayBuffer(512);
      const result = await voiceEngine.processAudioStream(sessionId, audioChunk);

      expect(result.isOffline).toBe(true);
    });

    it('should return error result when offline model not available', async () => {
      voiceEngine.setOnlineStatus(false);

      const audioChunk = new ArrayBuffer(512);
      const result = await voiceEngine.processAudioStream(sessionId, audioChunk);

      expect(result.confidence).toBe(0);
      expect(result.isOffline).toBe(true);
    });
  });

  describe('Cache Management Integration', () => {
    it('should manage cache through voice engine', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      
      // Cache multiple models
      const modelData = new ArrayBuffer(1024);
      await offlineProcessor.cacheModel('hi', undefined, modelData, '1.0.0');
      await offlineProcessor.cacheModel('ta', undefined, modelData, '1.1.0');
      await offlineProcessor.cacheModel('te', undefined, modelData, '1.2.0');

      const versions = offlineProcessor.getCachedModelVersions();
      expect(versions.length).toBeGreaterThanOrEqual(3);
    });

    it('should clear expired cache', async () => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      
      const expiredScheme = {
        schemeId: 'EXPIRED',
        name: { en: 'Expired' },
        description: { en: 'Expired' },
        eligibilityCriteria: {},
        cachedAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
        expiresAt: new Date(Date.now() - 1000)
      };

      await offlineProcessor.cacheScheme(expiredScheme);
      await offlineProcessor.clearExpiredCache();

      const cached = await offlineProcessor.getCachedScheme('EXPIRED');
      expect(cached).toBeNull();
    });
  });

  describe('Event Handling', () => {
    it('should emit events during offline operations', (done) => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      
      offlineProcessor.once('network:offline', () => {
        done();
      });

      voiceEngine.setOnlineStatus(false);
    });

    it('should emit sync events', (done) => {
      const offlineProcessor = voiceEngine.getOfflineProcessor();
      
      offlineProcessor.once('sync:completed', () => {
        done();
      });

      voiceEngine.setOnlineStatus(true);
      offlineProcessor.syncWithCloud();
    });
  });
});
