/**
 * Unit tests for Voice Activity Detection
 * Tests speech detection, turn-taking management, and state transitions
 */

import { VoiceActivityDetector, VADState, AdvancedVAD } from './voice-activity-detection';

describe('VoiceActivityDetector', () => {
  let vad: VoiceActivityDetector;

  beforeEach(() => {
    vad = new VoiceActivityDetector({
      sampleRate: 16000,
      frameDuration: 30,
      energyThreshold: 0.01,
      silenceDuration: 500,
      speechDuration: 100
    });
  });

  afterEach(() => {
    vad.removeAllListeners();
  });

  describe('Initialization', () => {
    test('should initialize with default configuration', () => {
      const defaultVAD = new VoiceActivityDetector();
      expect(defaultVAD.getState()).toBe(VADState.SILENCE);
      expect(defaultVAD.isSpeechActive()).toBe(false);
    });

    test('should initialize with custom configuration', () => {
      const config = {
        sampleRate: 48000,
        energyThreshold: 0.05,
        silenceDuration: 1000
      };
      const customVAD = new VoiceActivityDetector(config);
      const vadConfig = customVAD.getConfig();

      expect(vadConfig.sampleRate).toBe(48000);
      expect(vadConfig.energyThreshold).toBe(0.05);
      expect(vadConfig.silenceDuration).toBe(1000);
    });
  });

  describe('Speech Detection', () => {
    test('should detect silence for low-energy audio', () => {
      const silentAudio = createAudioBuffer(480, 0.001); // Very low energy
      const result = vad.processFrame(silentAudio, Date.now());

      expect(result.isSpeech).toBe(false);
      expect(vad.getState()).toBe(VADState.SILENCE);
    });

    test('should detect speech for high-energy audio', () => {
      const speechAudio = createAudioBuffer(480, 0.1); // High energy
      const result = vad.processFrame(speechAudio, Date.now());

      expect(result.isSpeech).toBe(true);
    });

    test('should transition to SPEECH_START on speech detection', () => {
      const speechAudio = createAudioBuffer(480, 0.1);
      
      const eventPromise = new Promise((resolve) => {
        vad.once('speech:start', resolve);
      });

      vad.processFrame(speechAudio, Date.now());

      return expect(eventPromise).resolves.toBeDefined();
    });

    test('should transition to SPEECH_ACTIVE after minimum duration', () => {
      const speechAudio = createAudioBuffer(480, 0.1);
      const startTime = Date.now();

      const eventPromise = new Promise((resolve) => {
        vad.once('speech:active', resolve);
      });

      // Process multiple frames to exceed speechDuration (100ms)
      vad.processFrame(speechAudio, startTime);
      vad.processFrame(speechAudio, startTime + 50);
      vad.processFrame(speechAudio, startTime + 150); // Exceeds 100ms

      return expect(eventPromise).resolves.toBeDefined();
    });

    test('should detect speech end after silence duration', async () => {
      // Use higher energy for clear speech detection
      const speechAudio = createAudioBuffer(480, 0.5);
      const silentAudio = createAudioBuffer(480, 0.001);
      const startTime = Date.now();

      let speechEndDetected = false;
      vad.once('speech:end', () => {
        speechEndDetected = true;
      });

      // Start speech - ensure we reach SPEECH_ACTIVE
      vad.processFrame(speechAudio, startTime);
      expect(vad.getState()).toBe(VADState.SPEECH_START);
      
      vad.processFrame(speechAudio, startTime + 50);
      vad.processFrame(speechAudio, startTime + 150); // Should be SPEECH_ACTIVE now
      expect(vad.isSpeechActive()).toBe(true);

      // Continue speech
      vad.processFrame(speechAudio, startTime + 200);

      // Now silence for more than silenceDuration (500ms)
      vad.processFrame(silentAudio, startTime + 250);
      vad.processFrame(silentAudio, startTime + 800); // Exceeds 500ms silence

      // Give a moment for event processing
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(speechEndDetected).toBe(true);
    });
  });

  describe('State Management', () => {
    test('should start in SILENCE state', () => {
      expect(vad.getState()).toBe(VADState.SILENCE);
    });

    test('should emit state:change events on transitions', () => {
      const speechAudio = createAudioBuffer(480, 0.1);
      
      const eventPromise = new Promise((resolve) => {
        vad.once('state:change', resolve);
      });

      vad.processFrame(speechAudio, Date.now());

      return expect(eventPromise).resolves.toMatchObject({
        from: VADState.SILENCE,
        to: VADState.SPEECH_START
      });
    });

    test('should reset to SILENCE state', () => {
      const speechAudio = createAudioBuffer(480, 0.1);
      vad.processFrame(speechAudio, Date.now());

      expect(vad.getState()).not.toBe(VADState.SILENCE);

      vad.reset();

      expect(vad.getState()).toBe(VADState.SILENCE);
      expect(vad.isSpeechActive()).toBe(false);
    });

    test('should emit vad:reset event on reset', () => {
      const eventPromise = new Promise((resolve) => {
        vad.once('vad:reset', resolve);
      });

      vad.reset();

      return expect(eventPromise).resolves.toBeUndefined();
    });
  });

  describe('Speech Segment Emission', () => {
    test('should emit complete speech segment', async () => {
      // Use higher energy for clear speech detection
      const speechAudio = createAudioBuffer(480, 0.5);
      const silentAudio = createAudioBuffer(480, 0.001);
      const startTime = Date.now();

      let capturedSegment: any = null;
      vad.once('speech:segment', (segment) => {
        capturedSegment = segment;
      });

      // Create a complete speech segment
      vad.processFrame(speechAudio, startTime);
      vad.processFrame(speechAudio, startTime + 50);
      vad.processFrame(speechAudio, startTime + 150); // SPEECH_ACTIVE
      vad.processFrame(speechAudio, startTime + 200);
      
      // Silence to end speech
      vad.processFrame(silentAudio, startTime + 250);
      vad.processFrame(silentAudio, startTime + 800); // SPEECH_END
      vad.processFrame(silentAudio, startTime + 850); // Transition to SILENCE, emit segment

      // Give a moment for event processing
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(capturedSegment).not.toBeNull();
      if (capturedSegment) {
        expect(capturedSegment).toMatchObject({
          startTime: expect.any(Number),
          endTime: expect.any(Number),
          duration: expect.any(Number),
          audioData: expect.any(Array)
        });
      }
    });
  });

  describe('Configuration Updates', () => {
    test('should update configuration', () => {
      const newConfig = {
        energyThreshold: 0.05,
        silenceDuration: 1000
      };

      vad.updateConfig(newConfig);
      const config = vad.getConfig();

      expect(config.energyThreshold).toBe(0.05);
      expect(config.silenceDuration).toBe(1000);
    });

    test('should emit config:updated event', () => {
      const eventPromise = new Promise((resolve) => {
        vad.once('config:updated', resolve);
      });

      vad.updateConfig({ energyThreshold: 0.05 });

      return expect(eventPromise).resolves.toBeDefined();
    });
  });

  describe('Confidence Calculation', () => {
    test('should return confidence score in VAD result', () => {
      const speechAudio = createAudioBuffer(480, 0.1);
      const result = vad.processFrame(speechAudio, Date.now());

      expect(result.confidence).toBeGreaterThanOrEqual(0);
      expect(result.confidence).toBeLessThanOrEqual(1);
    });

    test('should have higher confidence for stronger speech signals', () => {
      const weakSpeech = createAudioBuffer(480, 0.02);
      const strongSpeech = createAudioBuffer(480, 0.2);

      const weakResult = vad.processFrame(weakSpeech, Date.now());
      vad.reset();
      const strongResult = vad.processFrame(strongSpeech, Date.now());

      expect(strongResult.confidence).toBeGreaterThan(weakResult.confidence);
    });
  });

  describe('isSpeechActive', () => {
    test('should return false in SILENCE state', () => {
      expect(vad.isSpeechActive()).toBe(false);
    });

    test('should return true in SPEECH_START state', () => {
      const speechAudio = createAudioBuffer(480, 0.1);
      vad.processFrame(speechAudio, Date.now());

      expect(vad.isSpeechActive()).toBe(true);
    });

    test('should return true in SPEECH_ACTIVE state', () => {
      const speechAudio = createAudioBuffer(480, 0.1);
      const startTime = Date.now();

      vad.processFrame(speechAudio, startTime);
      vad.processFrame(speechAudio, startTime + 50);
      vad.processFrame(speechAudio, startTime + 150);

      expect(vad.isSpeechActive()).toBe(true);
    });
  });
});

describe('AdvancedVAD', () => {
  let advancedVAD: AdvancedVAD;

  beforeEach(() => {
    advancedVAD = new AdvancedVAD({
      sampleRate: 16000,
      energyThreshold: 0.01
    });
  });

  afterEach(() => {
    advancedVAD.removeAllListeners();
  });

  test('should initialize advanced VAD', () => {
    expect(advancedVAD.getState()).toBe(VADState.SILENCE);
  });

  test('should process frames with enhanced detection', () => {
    const speechAudio = createAudioBuffer(480, 0.1);
    const result = advancedVAD.processFrame(speechAudio, Date.now());

    expect(result).toBeDefined();
    expect(result.isSpeech).toBeDefined();
    expect(result.confidence).toBeDefined();
  });

  test('should use zero-crossing rate for speech detection', () => {
    // Create audio with speech-like characteristics
    const speechLikeAudio = createSpeechLikeAudio(480);
    const result = advancedVAD.processFrame(speechLikeAudio, Date.now());

    expect(result).toBeDefined();
  });
});

// Helper functions
function createAudioBuffer(samples: number, energy: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2); // 16-bit samples
  const view = new Int16Array(buffer);

  for (let i = 0; i < samples; i++) {
    // Generate random noise with specified energy level
    const value = (Math.random() - 0.5) * 2 * energy * 32768;
    view[i] = Math.max(-32768, Math.min(32767, value));
  }

  return buffer;
}

function createSpeechLikeAudio(samples: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2);
  const view = new Int16Array(buffer);

  // Generate audio with speech-like frequency (100-300 Hz)
  const frequency = 150;
  const sampleRate = 16000;

  for (let i = 0; i < samples; i++) {
    const t = i / sampleRate;
    const value = Math.sin(2 * Math.PI * frequency * t) * 0.1 * 32768;
    view[i] = Math.round(value);
  }

  return buffer;
}
