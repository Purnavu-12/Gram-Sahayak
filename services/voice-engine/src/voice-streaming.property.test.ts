/**
 * Property-Based Tests for Voice Streaming Service
 * Feature: gram-sahayak
 * 
 * **Validates: Requirements 1.1, 1.3**
 */

import * as fc from 'fast-check';
import { VoiceEngineService } from './voice-engine-service';

describe('Voice Streaming Property Tests', () => {
  /**
   * Property 1: Speech Recognition Accuracy
   * 
   * For any audio input in supported Indian languages, the Voice_Engine should 
   * achieve 95% transcription accuracy under both clean and noisy conditions, 
   * with graceful degradation based on audio quality.
   * 
   * **Validates: Requirements 1.1, 1.3**
   */
  describe('Property 1: Speech Recognition Accuracy', () => {
    it('should maintain 95% confidence threshold for clean audio across all supported languages', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate test data: language, audio quality, duration
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa', 'or'),
            audioQuality: fc.constantFrom('clean', 'noisy'),
            duration: fc.integer({ min: 100, max: 5000 }), // 100ms to 5s
            amplitude: fc.double({ min: 0.3, max: 0.9, noNaN: true }), // Reasonable speech amplitude
            noiseLevel: fc.double({ min: 0.0, max: 0.3, noNaN: true }) // Noise level for noisy condition
          }),
          async ({ language, audioQuality, duration, amplitude, noiseLevel }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);

            try {
              // Generate audio samples based on duration
              const sampleRate = 16000;
              const samples = Math.floor((duration / 1000) * sampleRate);
              const audioChunk = generateAudioChunk(samples, amplitude, audioQuality === 'noisy' ? noiseLevel : 0);

              // Act
              const result = await service.processAudioStream(sessionId, audioChunk);

              // Assert - Property: Confidence should meet accuracy requirements
              // Use actual noiseLevel to determine expected confidence, not the label
              if (noiseLevel < 0.05) {
                // Clean audio (very low noise) should achieve 95% confidence
                expect(result.confidence).toBeGreaterThanOrEqual(0.95);
              } else {
                // Noisy audio should show graceful degradation but still be usable
                // Requirement 1.3: filter ambient sounds and focus on human speech
                expect(result.confidence).toBeGreaterThanOrEqual(0.70);
              }

              // Verify language is correctly set
              expect(result.language).toBe(language);

              // Verify confidence is within valid range
              expect(result.confidence).toBeGreaterThanOrEqual(0);
              expect(result.confidence).toBeLessThanOrEqual(1);

              // Verify timestamp is present
              expect(result.timestamp).toBeInstanceOf(Date);

            } finally {
              // Cleanup
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 100 } // Run 100 iterations as per design document
      );
    });

    it('should handle varying audio chunk sizes with consistent accuracy', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr', 'ta'),
            chunkSize: fc.integer({ min: 160, max: 16000 }), // 10ms to 1s at 16kHz
            amplitude: fc.double({ min: 0.3, max: 0.9, noNaN: true })
          }),
          async ({ language, chunkSize, amplitude }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);

            try {
              // Generate audio chunk
              const audioChunk = generateAudioChunk(chunkSize, amplitude, 0);

              // Act
              const result = await service.processAudioStream(sessionId, audioChunk);

              // Assert - Property: System should handle any valid chunk size
              expect(result).toBeDefined();
              expect(result.confidence).toBeGreaterThanOrEqual(0);
              expect(result.confidence).toBeLessThanOrEqual(1);
              expect(result.language).toBe(language);

            } finally {
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should demonstrate graceful degradation with increasing noise levels', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te'),
            noiseLevel: fc.double({ min: 0.0, max: 0.5, noNaN: true }),
            amplitude: fc.double({ min: 0.4, max: 0.8, noNaN: true })
          }),
          async ({ language, noiseLevel, amplitude }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);

            try {
              // Generate audio with specified noise level
              const samples = 1600; // 100ms at 16kHz
              const audioChunk = generateAudioChunk(samples, amplitude, noiseLevel);

              // Act
              const result = await service.processAudioStream(sessionId, audioChunk);

              // Assert - Property: Confidence should degrade gracefully with noise
              // Higher noise should result in lower confidence, but still functional
              const expectedMinConfidence = Math.max(0.70, 0.95 - (noiseLevel * 0.5));
              
              expect(result.confidence).toBeGreaterThanOrEqual(expectedMinConfidence);
              expect(result.confidence).toBeLessThanOrEqual(1.0);

              // System should still process and return valid results
              expect(result.language).toBe(language);
              expect(result.timestamp).toBeInstanceOf(Date);

            } finally {
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain accuracy across multiple consecutive audio chunks', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            language: fc.constantFrom('hi', 'bn', 'te', 'mr'),
            numChunks: fc.integer({ min: 3, max: 10 }),
            chunkSize: fc.integer({ min: 800, max: 3200 }), // 50ms to 200ms
            amplitude: fc.double({ min: 0.3, max: 0.9, noNaN: true })
          }),
          async ({ language, numChunks, chunkSize, amplitude }) => {
            // Arrange
            const service = new VoiceEngineService();
            const userId = `test-user-${Date.now()}`;
            const sessionId = await service.startVoiceSession(userId, language);

            try {
              const results = [];

              // Act - Process multiple chunks
              for (let i = 0; i < numChunks; i++) {
                const audioChunk = generateAudioChunk(chunkSize, amplitude, 0);
                const result = await service.processAudioStream(sessionId, audioChunk);
                results.push(result);
              }

              // Assert - Property: All chunks should maintain high accuracy
              for (const result of results) {
                expect(result.confidence).toBeGreaterThanOrEqual(0.95);
                expect(result.language).toBe(language);
              }

              // Average confidence should be high
              const avgConfidence = results.reduce((sum, r) => sum + r.confidence, 0) / results.length;
              expect(avgConfidence).toBeGreaterThanOrEqual(0.95);

            } finally {
              await service.endVoiceSession(sessionId);
            }
          }
        ),
        { numRuns: 50 } // Fewer runs due to multiple chunks per test
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
