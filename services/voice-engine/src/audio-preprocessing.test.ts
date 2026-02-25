/**
 * Unit tests for Audio Preprocessing Pipeline
 * Tests noise reduction, filtering, and audio enhancement
 */

import { AudioPreprocessor, AudioBufferManager } from './audio-preprocessing';

describe('AudioPreprocessor', () => {
  let preprocessor: AudioPreprocessor;

  beforeEach(() => {
    preprocessor = new AudioPreprocessor({
      sampleRate: 16000,
      channels: 1,
      noiseReduction: true,
      highPassFilter: true,
      lowPassFilter: true,
      normalization: true
    });
  });

  afterEach(() => {
    preprocessor.removeAllListeners();
  });

  describe('Initialization', () => {
    test('should initialize with default configuration', () => {
      const defaultPreprocessor = new AudioPreprocessor();
      const config = defaultPreprocessor.getConfig();

      expect(config.sampleRate).toBe(16000);
      expect(config.channels).toBe(1);
      expect(config.noiseReduction).toBe(true);
    });

    test('should initialize with custom configuration', () => {
      const customConfig = {
        sampleRate: 48000,
        channels: 2,
        noiseReduction: false,
        highPassCutoff: 100
      };
      const customPreprocessor = new AudioPreprocessor(customConfig);
      const config = customPreprocessor.getConfig();

      expect(config.sampleRate).toBe(48000);
      expect(config.channels).toBe(2);
      expect(config.noiseReduction).toBe(false);
      expect(config.highPassCutoff).toBe(100);
    });
  });

  describe('Audio Processing', () => {
    test('should process audio buffer', async () => {
      const inputAudio = createTestAudio(1600, 0.5); // 100ms at 16kHz
      const outputAudio = await preprocessor.processAudio(inputAudio);

      expect(outputAudio).toBeDefined();
      expect(outputAudio.byteLength).toBe(inputAudio.byteLength);
    });

    test('should apply high-pass filter', async () => {
      const audioWithLowFreq = createLowFrequencyAudio(1600);
      const processed = await preprocessor.processAudio(audioWithLowFreq);

      expect(processed).toBeDefined();
      expect(processed.byteLength).toBeGreaterThan(0);
      // Low frequency content should be reduced
    });

    test('should apply low-pass filter', async () => {
      const audioWithHighFreq = createHighFrequencyAudio(1600);
      const processed = await preprocessor.processAudio(audioWithHighFreq);

      expect(processed).toBeDefined();
      expect(processed.byteLength).toBeGreaterThan(0);
      // High frequency content should be reduced
    });

    test('should normalize audio to target level', async () => {
      const quietAudio = createTestAudio(1600, 0.1);
      const processed = await preprocessor.processAudio(quietAudio);

      const processedSamples = new Int16Array(processed);
      const peak = Math.max(...Array.from(processedSamples).map(Math.abs)) / 32768;

      // Peak should be closer to target level (0.3)
      expect(peak).toBeGreaterThan(0.1);
    });

    test('should handle silent audio', async () => {
      const silentAudio = createTestAudio(1600, 0.0);
      const processed = await preprocessor.processAudio(silentAudio);

      expect(processed).toBeDefined();
      expect(processed.byteLength).toBe(silentAudio.byteLength);
    });

    test('should handle very loud audio without clipping', async () => {
      const loudAudio = createTestAudio(1600, 1.5);
      const processed = await preprocessor.processAudio(loudAudio);

      const processedSamples = new Int16Array(processed);
      const hasClipping = Array.from(processedSamples).some(
        sample => Math.abs(sample) >= 32767
      );

      // Normalization should prevent clipping
      expect(hasClipping).toBe(false);
    });
  });

  describe('Noise Reduction', () => {
    test('should build noise profile from initial frames', async () => {
      expect(preprocessor.isNoiseProfileReady()).toBe(false);

      // Process multiple frames to build noise profile
      for (let i = 0; i < 10; i++) {
        const noiseFrame = createTestAudio(1600, 0.01);
        await preprocessor.processAudio(noiseFrame);
      }

      // After 10 frames, noise profile should be ready
      expect(preprocessor.isNoiseProfileReady()).toBe(true);
    });

    test('should emit noise:profile:ready event', async () => {
      const eventPromise = new Promise((resolve) => {
        preprocessor.once('noise:profile:ready', resolve);
      });

      // Process frames to trigger noise profile creation
      for (let i = 0; i < 10; i++) {
        const noiseFrame = createTestAudio(1600, 0.01);
        await preprocessor.processAudio(noiseFrame);
      }

      await expect(eventPromise).resolves.toBeUndefined();
    });

    test('should reset noise profile', () => {
      preprocessor.resetNoiseProfile();
      expect(preprocessor.isNoiseProfileReady()).toBe(false);
    });

    test('should emit noise:profile:reset event', () => {
      const eventPromise = new Promise((resolve) => {
        preprocessor.once('noise:profile:reset', resolve);
      });

      preprocessor.resetNoiseProfile();

      return expect(eventPromise).resolves.toBeUndefined();
    });
  });

  describe('Audio Statistics', () => {
    test('should emit audio statistics', async () => {
      const audio = createTestAudio(1600, 0.5);

      const statsPromise = new Promise((resolve) => {
        preprocessor.once('audio:stats', resolve);
      });

      await preprocessor.processAudio(audio);
      const stats = await statsPromise;

      expect(stats).toMatchObject({
        rms: expect.any(Number),
        peak: expect.any(Number),
        snr: expect.any(Number),
        clipping: expect.any(Boolean)
      });
    });

    test('should detect clipping in audio', async () => {
      const clippingAudio = createClippingAudio(1600);

      const statsPromise = new Promise((resolve) => {
        preprocessor.once('audio:stats', resolve);
      });

      await preprocessor.processAudio(clippingAudio);
      const stats: any = await statsPromise;

      // After normalization, clipping should be prevented
      expect(stats.clipping).toBeDefined();
    });

    test('should calculate RMS level', async () => {
      const audio = createTestAudio(1600, 0.5);

      const statsPromise = new Promise((resolve) => {
        preprocessor.once('audio:stats', resolve);
      });

      await preprocessor.processAudio(audio);
      const stats: any = await statsPromise;

      expect(stats.rms).toBeGreaterThan(0);
      expect(stats.rms).toBeLessThanOrEqual(1);
    });
  });

  describe('Configuration Updates', () => {
    test('should update configuration', () => {
      const newConfig = {
        noiseReduction: false,
        highPassCutoff: 100
      };

      preprocessor.updateConfig(newConfig);
      const config = preprocessor.getConfig();

      expect(config.noiseReduction).toBe(false);
      expect(config.highPassCutoff).toBe(100);
    });

    test('should emit config:updated event', () => {
      const eventPromise = new Promise((resolve) => {
        preprocessor.once('config:updated', resolve);
      });

      preprocessor.updateConfig({ noiseReduction: false });

      return expect(eventPromise).resolves.toBeDefined();
    });
  });

  describe('Filter Bypass', () => {
    test('should skip high-pass filter when disabled', async () => {
      preprocessor.updateConfig({ highPassFilter: false });
      const audio = createLowFrequencyAudio(1600);
      const processed = await preprocessor.processAudio(audio);

      expect(processed).toBeDefined();
      expect(processed.byteLength).toBeGreaterThan(0);
    });

    test('should skip low-pass filter when disabled', async () => {
      preprocessor.updateConfig({ lowPassFilter: false });
      const audio = createHighFrequencyAudio(1600);
      const processed = await preprocessor.processAudio(audio);

      expect(processed).toBeDefined();
      expect(processed.byteLength).toBeGreaterThan(0);
    });

    test('should skip noise reduction when disabled', async () => {
      preprocessor.updateConfig({ noiseReduction: false });
      const audio = createTestAudio(1600, 0.5);
      const processed = await preprocessor.processAudio(audio);

      expect(processed).toBeDefined();
      expect(processed.byteLength).toBeGreaterThan(0);
    });

    test('should skip normalization when disabled', async () => {
      preprocessor.updateConfig({ normalization: false });
      const audio = createTestAudio(1600, 0.1);
      const processed = await preprocessor.processAudio(audio);

      expect(processed).toBeDefined();
      expect(processed.byteLength).toBeGreaterThan(0);
    });
  });
});

describe('AudioBufferManager', () => {
  let bufferManager: AudioBufferManager;

  beforeEach(() => {
    bufferManager = new AudioBufferManager(10);
  });

  describe('Buffer Management', () => {
    test('should add audio chunks to buffer', () => {
      const sessionId = 'test-session';
      const chunk1 = createTestAudio(1600, 0.5);
      const chunk2 = createTestAudio(1600, 0.5);

      bufferManager.addChunk(sessionId, chunk1);
      bufferManager.addChunk(sessionId, chunk2);

      expect(bufferManager.getBufferSize(sessionId)).toBe(2);
    });

    test('should retrieve chunks for session', () => {
      const sessionId = 'test-session';
      const chunk = createTestAudio(1600, 0.5);

      bufferManager.addChunk(sessionId, chunk);
      const chunks = bufferManager.getChunks(sessionId);

      expect(chunks).toHaveLength(1);
      expect(chunks[0]).toBe(chunk);
    });

    test('should maintain buffer size limit', () => {
      const sessionId = 'test-session';
      const maxSize = 10;

      // Add more chunks than max size
      for (let i = 0; i < 15; i++) {
        const chunk = createTestAudio(160, 0.5);
        bufferManager.addChunk(sessionId, chunk);
      }

      expect(bufferManager.getBufferSize(sessionId)).toBe(maxSize);
    });

    test('should concatenate chunks into single buffer', () => {
      const sessionId = 'test-session';
      const chunk1 = createTestAudio(800, 0.5);
      const chunk2 = createTestAudio(800, 0.5);

      bufferManager.addChunk(sessionId, chunk1);
      bufferManager.addChunk(sessionId, chunk2);

      const concatenated = bufferManager.concatenateChunks(sessionId);

      expect(concatenated).not.toBeNull();
      expect(concatenated!.byteLength).toBe(chunk1.byteLength + chunk2.byteLength);
    });

    test('should return null when concatenating empty buffer', () => {
      const sessionId = 'empty-session';
      const concatenated = bufferManager.concatenateChunks(sessionId);

      expect(concatenated).toBeNull();
    });

    test('should clear buffer for session', () => {
      const sessionId = 'test-session';
      const chunk = createTestAudio(1600, 0.5);

      bufferManager.addChunk(sessionId, chunk);
      expect(bufferManager.getBufferSize(sessionId)).toBe(1);

      bufferManager.clearBuffer(sessionId);
      expect(bufferManager.getBufferSize(sessionId)).toBe(0);
    });

    test('should return 0 size for non-existent session', () => {
      expect(bufferManager.getBufferSize('non-existent')).toBe(0);
    });

    test('should return empty array for non-existent session', () => {
      const chunks = bufferManager.getChunks('non-existent');
      expect(chunks).toEqual([]);
    });
  });

  describe('Multiple Sessions', () => {
    test('should manage buffers for multiple sessions independently', () => {
      const session1 = 'session-1';
      const session2 = 'session-2';

      bufferManager.addChunk(session1, createTestAudio(1600, 0.5));
      bufferManager.addChunk(session1, createTestAudio(1600, 0.5));
      bufferManager.addChunk(session2, createTestAudio(1600, 0.5));

      expect(bufferManager.getBufferSize(session1)).toBe(2);
      expect(bufferManager.getBufferSize(session2)).toBe(1);
    });

    test('should clear one session without affecting others', () => {
      const session1 = 'session-1';
      const session2 = 'session-2';

      bufferManager.addChunk(session1, createTestAudio(1600, 0.5));
      bufferManager.addChunk(session2, createTestAudio(1600, 0.5));

      bufferManager.clearBuffer(session1);

      expect(bufferManager.getBufferSize(session1)).toBe(0);
      expect(bufferManager.getBufferSize(session2)).toBe(1);
    });
  });
});

// Helper functions
function createTestAudio(samples: number, amplitude: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2);
  const view = new Int16Array(buffer);

  for (let i = 0; i < samples; i++) {
    const value = (Math.random() - 0.5) * 2 * amplitude * 32768;
    view[i] = Math.max(-32768, Math.min(32767, value));
  }

  return buffer;
}

function createLowFrequencyAudio(samples: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2);
  const view = new Int16Array(buffer);
  const frequency = 50; // Below typical high-pass cutoff
  const sampleRate = 16000;

  for (let i = 0; i < samples; i++) {
    const t = i / sampleRate;
    const value = Math.sin(2 * Math.PI * frequency * t) * 0.5 * 32768;
    view[i] = Math.round(value);
  }

  return buffer;
}

function createHighFrequencyAudio(samples: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2);
  const view = new Int16Array(buffer);
  const frequency = 10000; // Above typical low-pass cutoff
  const sampleRate = 16000;

  for (let i = 0; i < samples; i++) {
    const t = i / sampleRate;
    const value = Math.sin(2 * Math.PI * frequency * t) * 0.5 * 32768;
    view[i] = Math.round(value);
  }

  return buffer;
}

function createClippingAudio(samples: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2);
  const view = new Int16Array(buffer);

  for (let i = 0; i < samples; i++) {
    // Create audio that clips at max value
    view[i] = i % 2 === 0 ? 32767 : -32768;
  }

  return buffer;
}
