import { VoiceEngineService } from './voice-engine-service';

describe('VoiceEngineService', () => {
  let service: VoiceEngineService;

  beforeEach(() => {
    service = new VoiceEngineService();
  });

  describe('startVoiceSession', () => {
    it('should create a new session with valid userId', async () => {
      const userId = 'user123';
      const sessionId = await service.startVoiceSession(userId);

      expect(sessionId).toBeDefined();
      expect(sessionId).toContain(userId);
    });

    it('should accept optional preferred language', async () => {
      const userId = 'user123';
      const preferredLanguage = 'hi';
      const sessionId = await service.startVoiceSession(userId, preferredLanguage);

      expect(sessionId).toBeDefined();
    });
  });

  describe('endVoiceSession', () => {
    it('should return session summary for valid session', async () => {
      const userId = 'user123';
      const sessionId = await service.startVoiceSession(userId);
      const summary = await service.endVoiceSession(sessionId);

      expect(summary).toBeDefined();
      expect(summary.sessionId).toBe(sessionId);
      expect(summary.duration).toBeGreaterThanOrEqual(0);
      expect(summary.totalUtterances).toBe(0);
    });

    it('should throw error for invalid session', async () => {
      await expect(service.endVoiceSession('invalid-session')).rejects.toThrow('Session not found');
    });
  });

  describe('processAudioStream', () => {
    it('should process audio chunk for valid session', async () => {
      const userId = 'user123';
      const sessionId = await service.startVoiceSession(userId, 'hi');
      const audioChunk = new ArrayBuffer(1024);

      const result = await service.processAudioStream(sessionId, audioChunk);

      expect(result).toBeDefined();
      expect(result.confidence).toBeGreaterThanOrEqual(0);
      expect(result.confidence).toBeLessThanOrEqual(1);
      expect(result.language).toBe('hi');
    });

    it('should throw error for invalid session', async () => {
      const audioChunk = new ArrayBuffer(1024);
      await expect(service.processAudioStream('invalid-session', audioChunk)).rejects.toThrow('Session not found');
    });
  });
});
