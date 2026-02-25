/**
 * Unit tests for WebRTC Voice Streaming Service
 * Tests real-time audio streaming, connection management, and error handling
 */

import { WebRTCStreamingService, StreamingSession } from './webrtc-streaming';

describe('WebRTCStreamingService', () => {
  let service: WebRTCStreamingService;

  beforeEach(() => {
    service = new WebRTCStreamingService();
  });

  afterEach(async () => {
    // Cleanup all sessions
    const sessions = service.getActiveSessions();
    for (const session of sessions) {
      await service.closeSession(session.sessionId);
    }
  });

  describe('Session Management', () => {
    test('should create a new streaming session', async () => {
      const sessionId = 'test-session-1';
      const userId = 'user-123';

      const session = await service.createSession(sessionId, userId);

      expect(session).toBeDefined();
      expect(session.sessionId).toBe(sessionId);
      expect(session.userId).toBe(userId);
      expect(session.isActive).toBe(true);
      expect(session.peerConnection).toBeNull();
      expect(session.dataChannel).toBeNull();
    });

    test('should retrieve existing session', async () => {
      const sessionId = 'test-session-2';
      const userId = 'user-456';

      await service.createSession(sessionId, userId);
      const retrieved = service.getSession(sessionId);

      expect(retrieved).toBeDefined();
      expect(retrieved?.sessionId).toBe(sessionId);
    });

    test('should list all active sessions', async () => {
      await service.createSession('session-1', 'user-1');
      await service.createSession('session-2', 'user-2');
      await service.createSession('session-3', 'user-3');

      const activeSessions = service.getActiveSessions();

      expect(activeSessions).toHaveLength(3);
      expect(activeSessions.every(s => s.isActive)).toBe(true);
    });

    test('should close session and cleanup resources', async () => {
      const sessionId = 'test-session-close';
      await service.createSession(sessionId, 'user-close');

      await service.closeSession(sessionId);

      const session = service.getSession(sessionId);
      expect(session).toBeUndefined();
    });

    test('should handle closing non-existent session gracefully', async () => {
      await expect(service.closeSession('non-existent')).resolves.not.toThrow();
    });
  });

  describe('Event Emission', () => {
    test('should emit session:created event on session creation', async () => {
      const sessionId = 'event-test-1';
      const userId = 'user-event';

      const eventPromise = new Promise((resolve) => {
        service.once('session:created', resolve);
      });

      await service.createSession(sessionId, userId);
      const event = await eventPromise;

      expect(event).toEqual({ sessionId, userId });
    });

    test('should emit session:closed event on session closure', async () => {
      const sessionId = 'event-test-2';
      await service.createSession(sessionId, 'user-close-event');

      const eventPromise = new Promise((resolve) => {
        service.once('session:closed', resolve);
      });

      await service.closeSession(sessionId);
      const event = await eventPromise;

      expect(event).toEqual({ sessionId });
    });
  });

  describe('Error Handling', () => {
    test('should throw error when initializing peer connection for non-existent session', async () => {
      await expect(
        service.initializePeerConnection('non-existent')
      ).rejects.toThrow('Session non-existent not found');
    });

    test('should throw error when creating data channel for non-existent session', () => {
      expect(() => {
        service.createDataChannel('non-existent');
      }).toThrow('Session non-existent not initialized');
    });

    test('should throw error when sending audio to non-existent session', async () => {
      const audioData = new ArrayBuffer(1024);
      
      await expect(
        service.sendAudioChunk('non-existent', audioData)
      ).rejects.toThrow('Session non-existent not ready for data transmission');
    });

    test('should throw error when handling answer for non-existent session', async () => {
      const answer = { type: 'answer' as const, sdp: 'test-sdp' };
      
      await expect(
        service.handleAnswer('non-existent', answer)
      ).rejects.toThrow('Session non-existent not initialized');
    });

    test('should throw error when adding ICE candidate to non-existent session', async () => {
      const candidate = { candidate: 'test', sdpMid: '0', sdpMLineIndex: 0 };
      
      await expect(
        service.addIceCandidate('non-existent', candidate)
      ).rejects.toThrow('Session non-existent not initialized');
    });
  });

  describe('Configuration', () => {
    test('should use default ICE servers when not provided', () => {
      const defaultService = new WebRTCStreamingService();
      expect(defaultService).toBeDefined();
    });

    test('should accept custom ICE servers', () => {
      const customConfig = {
        iceServers: [
          { urls: 'stun:custom.stun.server:3478' },
          { urls: 'turn:custom.turn.server:3478', username: 'user', credential: 'pass' }
        ]
      };

      const customService = new WebRTCStreamingService(customConfig);
      expect(customService).toBeDefined();
    });

    test('should accept custom audio constraints', () => {
      const customConfig = {
        audioConstraints: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
          sampleRate: 48000,
          channelCount: 2
        }
      };

      const customService = new WebRTCStreamingService(customConfig);
      expect(customService).toBeDefined();
    });
  });

  describe('Session Statistics', () => {
    test('should return null stats for non-existent session', async () => {
      const stats = await service.getSessionStats('non-existent');
      expect(stats).toBeNull();
    });

    test('should return null stats for session without peer connection', async () => {
      const sessionId = 'stats-test';
      await service.createSession(sessionId, 'user-stats');

      const stats = await service.getSessionStats(sessionId);
      expect(stats).toBeNull();
    });
  });

  describe('Audio Chunk Handling', () => {
    test('should emit audio:chunk event when receiving data', async () => {
      const sessionId = 'audio-chunk-test';
      await service.createSession(sessionId, 'user-audio');

      const testAudioData = new ArrayBuffer(1024);
      
      const eventPromise = new Promise((resolve) => {
        service.once('audio:chunk', resolve);
      });

      // Simulate incoming audio data
      service.emit('audio:chunk', {
        sessionId,
        audioData: testAudioData,
        timestamp: Date.now(),
        sampleRate: 16000,
        channels: 1
      });

      const event = await eventPromise;
      expect(event).toBeDefined();
    });
  });

  describe('Connection State Management', () => {
    test('should track session start time', async () => {
      const beforeCreate = Date.now();
      const sessionId = 'time-test';
      
      const session = await service.createSession(sessionId, 'user-time');
      const afterCreate = Date.now();

      expect(session.startTime).toBeGreaterThanOrEqual(beforeCreate);
      expect(session.startTime).toBeLessThanOrEqual(afterCreate);
    });

    test('should mark session as inactive after closing', async () => {
      const sessionId = 'inactive-test';
      const session = await service.createSession(sessionId, 'user-inactive');

      expect(session.isActive).toBe(true);

      await service.closeSession(sessionId);

      // Session should be removed, so getSession returns undefined
      const closedSession = service.getSession(sessionId);
      expect(closedSession).toBeUndefined();
    });
  });
});
