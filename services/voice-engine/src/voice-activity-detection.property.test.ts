/**
 * Property-Based Tests for Voice Activity Detection
 * Feature: gram-sahayak
 * 
 * **Validates: Requirements 1.5**
 */

import * as fc from 'fast-check';
import { VoiceActivityDetector, VADState, VADResult, SpeechSegment } from './voice-activity-detection';

describe('Voice Activity Detection Property Tests', () => {
  /**
   * Property 2: Voice Activity Detection
   * 
   * For any speech input with pauses, the Voice_Engine should correctly identify 
   * speech boundaries and wait for completion before processing, maintaining 
   * conversation flow.
   * 
   * **Validates: Requirements 1.5**
   */
  describe('Property 2: Voice Activity Detection', () => {
    it('should correctly identify speech boundaries for any valid pause pattern', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            // Speech segment parameters
            speechDuration: fc.integer({ min: 200, max: 3000 }), // 200ms to 3s
            speechEnergy: fc.double({ min: 0.05, max: 0.5 }), // Clear speech energy
            
            // Pause parameters
            pauseDuration: fc.integer({ min: 100, max: 2000 }), // 100ms to 2s
            pauseEnergy: fc.double({ min: 0.0, max: 0.005 }), // Very low energy for pauses
            
            // Configuration
            silenceThreshold: fc.integer({ min: 300, max: 800 }), // Silence detection threshold
            speechThreshold: fc.integer({ min: 50, max: 150 }) // Minimum speech duration
          }),
          async ({ speechDuration, speechEnergy, pauseDuration, pauseEnergy, silenceThreshold, speechThreshold }) => {
            // Arrange
            const vad = new VoiceActivityDetector({
              sampleRate: 16000,
              frameDuration: 30,
              energyThreshold: 0.01,
              silenceDuration: silenceThreshold,
              speechDuration: speechThreshold
            });

            let speechStartEvents = 0;
            let speechEndEvents = 0;
            let segmentsEmitted: SpeechSegment[] = [];

            vad.on('speech:start', () => speechStartEvents++);
            vad.on('speech:end', () => speechEndEvents++);
            vad.on('speech:segment', (segment: SpeechSegment) => segmentsEmitted.push(segment));

            // Act - Simulate speech with pause
            const frameDuration = 30; // ms
            const framesPerMs = 16000 / 1000; // samples per ms
            const samplesPerFrame = Math.floor(frameDuration * framesPerMs);
            
            let currentTime = Date.now();
            
            // Generate speech frames
            const speechFrames = Math.ceil(speechDuration / frameDuration);
            for (let i = 0; i < speechFrames; i++) {
              const audioData = generateAudioFrame(samplesPerFrame, speechEnergy);
              vad.processFrame(audioData, currentTime);
              currentTime += frameDuration;
            }

            // Generate pause frames
            const pauseFrames = Math.ceil(pauseDuration / frameDuration);
            for (let i = 0; i < pauseFrames; i++) {
              const audioData = generateAudioFrame(samplesPerFrame, pauseEnergy);
              vad.processFrame(audioData, currentTime);
              currentTime += frameDuration;
            }

            // Add extra frames to ensure state transition completes and segment is emitted
            // The VAD needs to transition from SPEECH_ACTIVE -> SPEECH_END -> SILENCE
            for (let i = 0; i < 3; i++) {
              const finalFrame = generateAudioFrame(samplesPerFrame, pauseEnergy);
              vad.processFrame(finalFrame, currentTime);
              currentTime += frameDuration;
            }

            // Assert - Property: VAD should correctly identify speech boundaries
            
            // 1. Speech start should be detected if speech duration exceeds threshold
            if (speechDuration >= speechThreshold) {
              expect(speechStartEvents).toBeGreaterThanOrEqual(1);
            }
            
            // 2. If pause is significantly longer than threshold, speech end should be detected
            // Need extra margin because of energy smoothing (history of 10 frames)
            const effectiveSilenceThreshold = silenceThreshold + (frameDuration * 10);
            if (pauseDuration > effectiveSilenceThreshold && speechDuration >= speechThreshold) {
              expect(speechEndEvents).toBeGreaterThanOrEqual(1);
              
              // 3. Complete segment should be emitted
              expect(segmentsEmitted.length).toBeGreaterThanOrEqual(1);
              
              if (segmentsEmitted.length > 0) {
                const segment = segmentsEmitted[0];
                
                // 4. Segment duration should approximately match speech duration
                const durationTolerance = frameDuration * 5; // Allow 5 frames tolerance
                expect(segment.duration).toBeGreaterThanOrEqual(speechDuration - durationTolerance);
                expect(segment.duration).toBeLessThanOrEqual(speechDuration + pauseDuration + durationTolerance);
                
                // 5. Segment should have audio data
                expect(segment.audioData.length).toBeGreaterThan(0);
                
                // 6. Segment timestamps should be valid
                expect(segment.endTime).toBeGreaterThan(segment.startTime);
              }
            }
            
            // 7. VAD should return to appropriate state after processing
            const finalState = vad.getState();
            expect([VADState.SILENCE, VADState.SPEECH_END, VADState.SPEECH_ACTIVE, VADState.SPEECH_START]).toContain(finalState);

            // Cleanup
            vad.removeAllListeners();
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should wait for speech completion before processing across varying pause patterns', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            // Multiple speech segments with pauses
            segments: fc.array(
              fc.record({
                speechDuration: fc.integer({ min: 150, max: 1000 }),
                speechEnergy: fc.double({ min: 0.05, max: 0.4 }),
                pauseAfter: fc.integer({ min: 50, max: 1500 })
              }),
              { minLength: 2, maxLength: 5 }
            ),
            silenceThreshold: fc.integer({ min: 400, max: 700 })
          }),
          async ({ segments, silenceThreshold }) => {
            // Arrange
            const vad = new VoiceActivityDetector({
              sampleRate: 16000,
              frameDuration: 30,
              energyThreshold: 0.01,
              silenceDuration: silenceThreshold,
              speechDuration: 100
            });

            const detectedSegments: SpeechSegment[] = [];
            vad.on('speech:segment', (segment: SpeechSegment) => {
              detectedSegments.push(segment);
            });

            // Act - Process multiple speech segments with pauses
            const frameDuration = 30;
            const samplesPerFrame = Math.floor((frameDuration / 1000) * 16000);
            let currentTime = Date.now();

            for (const segment of segments) {
              // Speech
              const speechFrames = Math.ceil(segment.speechDuration / frameDuration);
              for (let i = 0; i < speechFrames; i++) {
                const audioData = generateAudioFrame(samplesPerFrame, segment.speechEnergy);
                vad.processFrame(audioData, currentTime);
                currentTime += frameDuration;
              }

              // Pause
              const pauseFrames = Math.ceil(segment.pauseAfter / frameDuration);
              for (let i = 0; i < pauseFrames; i++) {
                const audioData = generateAudioFrame(samplesPerFrame, 0.001);
                vad.processFrame(audioData, currentTime);
                currentTime += frameDuration;
              }
            }

            // Final silence to ensure last segment is emitted
            for (let i = 0; i < 30; i++) {
              const audioData = generateAudioFrame(samplesPerFrame, 0.001);
              vad.processFrame(audioData, currentTime);
              currentTime += frameDuration;
            }

            // Assert - Property: VAD waits for completion before processing
            
            // 1. Number of detected segments should be reasonable
            // Segments with pauses >= threshold should create separate segments
            // But consecutive segments with pauses < threshold may merge
            const segmentsWithLongPause = segments.filter(s => s.pauseAfter >= silenceThreshold).length;
            
            // We should have at least some segments detected if there were long pauses
            if (segmentsWithLongPause > 0) {
              expect(detectedSegments.length).toBeGreaterThan(0);
            }
            
            // Total segments should not exceed input segments
            expect(detectedSegments.length).toBeLessThanOrEqual(segments.length);

            // 2. Each detected segment should be complete
            for (const detectedSegment of detectedSegments) {
              expect(detectedSegment.duration).toBeGreaterThan(0);
              expect(detectedSegment.audioData.length).toBeGreaterThan(0);
              expect(detectedSegment.endTime).toBeGreaterThan(detectedSegment.startTime);
            }

            // 3. Segments should not overlap (proper boundary detection)
            for (let i = 1; i < detectedSegments.length; i++) {
              expect(detectedSegments[i].startTime).toBeGreaterThanOrEqual(
                detectedSegments[i - 1].endTime
              );
            }

            // Cleanup
            vad.removeAllListeners();
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain conversation flow by correctly handling mid-sentence pauses', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            // Short pauses that should NOT end speech
            shortPauseDuration: fc.integer({ min: 50, max: 300 }),
            // Long pause that SHOULD end speech
            longPauseDuration: fc.integer({ min: 600, max: 1200 }),
            speechEnergy: fc.double({ min: 0.05, max: 0.5 }),
            speechDuration: fc.integer({ min: 200, max: 800 })
          }),
          async ({ shortPauseDuration, longPauseDuration, speechEnergy, speechDuration }) => {
            // Arrange
            const silenceThreshold = 500;
            const vad = new VoiceActivityDetector({
              sampleRate: 16000,
              frameDuration: 30,
              energyThreshold: 0.01,
              silenceDuration: silenceThreshold,
              speechDuration: 100
            });

            let speechEndCount = 0;
            const segments: SpeechSegment[] = [];
            
            vad.on('speech:end', () => speechEndCount++);
            vad.on('speech:segment', (segment: SpeechSegment) => segments.push(segment));

            // Act - Simulate speech with short pause (mid-sentence) then long pause (end)
            const frameDuration = 30;
            const samplesPerFrame = Math.floor((frameDuration / 1000) * 16000);
            let currentTime = Date.now();

            // First speech segment
            const frames1 = Math.ceil(speechDuration / frameDuration);
            for (let i = 0; i < frames1; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, speechEnergy), currentTime);
              currentTime += frameDuration;
            }

            // Short pause (should NOT end speech if < silenceThreshold)
            const shortPauseFrames = Math.ceil(shortPauseDuration / frameDuration);
            for (let i = 0; i < shortPauseFrames; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, 0.001), currentTime);
              currentTime += frameDuration;
            }

            // Continue speech after short pause
            const frames2 = Math.ceil(speechDuration / frameDuration);
            for (let i = 0; i < frames2; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, speechEnergy), currentTime);
              currentTime += frameDuration;
            }

            // Long pause (should end speech)
            const longPauseFrames = Math.ceil(longPauseDuration / frameDuration);
            for (let i = 0; i < longPauseFrames; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, 0.001), currentTime);
              currentTime += frameDuration;
            }

            // Extra frames to ensure state transition completes
            for (let i = 0; i < 3; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, 0.001), currentTime);
              currentTime += frameDuration;
            }

            // Assert - Property: Conversation flow is maintained
            
            // 1. Short pause should NOT end speech (if < threshold)
            if (shortPauseDuration < silenceThreshold) {
              // Speech should continue as one segment
              expect(segments.length).toBeLessThanOrEqual(1);
              
              if (segments.length === 1) {
                // The segment should include both speech parts
                const totalSpeechDuration = speechDuration * 2 + shortPauseDuration;
                const tolerance = frameDuration * 4;
                expect(segments[0].duration).toBeGreaterThanOrEqual(totalSpeechDuration - tolerance);
              }
            }

            // 2. Long pause should end speech (eventually)
            // Note: Need extra margin for energy smoothing
            const effectiveSilenceThreshold = silenceThreshold + (frameDuration * 10);
            if (longPauseDuration > effectiveSilenceThreshold) {
              expect(speechEndCount).toBeGreaterThanOrEqual(1);
            }

            // 3. Final state should be appropriate
            const finalState = vad.getState();
            expect([VADState.SILENCE, VADState.SPEECH_END, VADState.SPEECH_ACTIVE]).toContain(finalState);

            // Cleanup
            vad.removeAllListeners();
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should correctly identify speech boundaries with varying energy levels', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            // Varying speech energy (simulating volume changes)
            energyLevels: fc.array(
              fc.double({ min: 0.02, max: 0.5 }),
              { minLength: 3, maxLength: 10 }
            ),
            frameDuration: fc.constantFrom(10, 20, 30), // Valid frame durations
            pauseDuration: fc.integer({ min: 500, max: 1000 })
          }),
          async ({ energyLevels, frameDuration, pauseDuration }) => {
            // Arrange
            const vad = new VoiceActivityDetector({
              sampleRate: 16000,
              frameDuration,
              energyThreshold: 0.01,
              silenceDuration: 500,
              speechDuration: 100
            });

            let speechDetected = false;
            let segmentEmitted = false;

            vad.on('speech:start', () => { speechDetected = true; });
            vad.on('speech:segment', () => { segmentEmitted = true; });

            // Act - Process frames with varying energy
            const samplesPerFrame = Math.floor((frameDuration / 1000) * 16000);
            let currentTime = Date.now();

            // Speech with varying energy
            for (const energy of energyLevels) {
              const audioData = generateAudioFrame(samplesPerFrame, energy);
              vad.processFrame(audioData, currentTime);
              currentTime += frameDuration;
            }

            // Pause to end speech
            const pauseFrames = Math.ceil(pauseDuration / frameDuration);
            for (let i = 0; i < pauseFrames; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, 0.001), currentTime);
              currentTime += frameDuration;
            }

            // Extra frames to ensure state transition
            for (let i = 0; i < 3; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, 0.001), currentTime);
              currentTime += frameDuration;
            }

            // Assert - Property: VAD handles varying energy levels
            
            // 1. Speech should be detected if energy levels are sufficient
            // With smoothing, need multiple frames above threshold
            const avgEnergy = energyLevels.reduce((a, b) => a + b, 0) / energyLevels.length;
            const hasSignificantEnergy = avgEnergy > 0.015;
            
            if (hasSignificantEnergy) {
              expect(speechDetected).toBe(true);
              
              // 2. Segment should be emitted after sufficient pause if speech was detected
              // AND speech duration meets the minimum threshold
              const totalSpeechDuration = (energyLevels.length - 1) * frameDuration;
              if (pauseDuration > 500 + (frameDuration * 10) && totalSpeechDuration >= 100) {
                expect(segmentEmitted).toBe(true);
              }
            }

            // 3. VAD should be in appropriate final state
            const finalState = vad.getState();
            expect([VADState.SILENCE, VADState.SPEECH_END, VADState.SPEECH_ACTIVE, VADState.SPEECH_START]).toContain(finalState);

            // Cleanup
            vad.removeAllListeners();
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle edge cases: very short speech and very long pauses', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            speechDuration: fc.integer({ min: 50, max: 200 }), // Very short speech
            pauseDuration: fc.integer({ min: 1000, max: 5000 }), // Very long pause
            speechEnergy: fc.double({ min: 0.05, max: 0.5, noNaN: true }) // Ensure no NaN
          }),
          async ({ speechDuration, pauseDuration, speechEnergy }) => {
            // Arrange
            const vad = new VoiceActivityDetector({
              sampleRate: 16000,
              frameDuration: 30,
              energyThreshold: 0.01,
              silenceDuration: 500,
              speechDuration: 50 // Lower threshold for short speech
            });

            const events: string[] = [];
            vad.on('speech:start', () => events.push('start'));
            vad.on('speech:end', () => events.push('end'));
            vad.on('speech:segment', () => events.push('segment'));

            // Act
            const frameDuration = 30;
            const samplesPerFrame = Math.floor((frameDuration / 1000) * 16000);
            let currentTime = Date.now();

            // Very short speech
            const speechFrames = Math.ceil(speechDuration / frameDuration);
            for (let i = 0; i < speechFrames; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, speechEnergy), currentTime);
              currentTime += frameDuration;
            }

            // Very long pause
            const pauseFrames = Math.ceil(pauseDuration / frameDuration);
            for (let i = 0; i < pauseFrames; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, 0.001), currentTime);
              currentTime += frameDuration;
            }

            // Extra frames to ensure state transition
            for (let i = 0; i < 3; i++) {
              vad.processFrame(generateAudioFrame(samplesPerFrame, 0.001), currentTime);
              currentTime += frameDuration;
            }

            // Assert - Property: Edge cases are handled correctly
            
            // Calculate the actual speech duration as seen by VAD
            const actualSpeechDuration = (speechFrames - 1) * frameDuration;
            
            // 1. Even very short speech should be detected if above minimum duration
            if (speechDuration >= 50 && speechEnergy > 0.01) {
              expect(events).toContain('start');
            }

            // 2. Very long pause should definitely end speech if speech was detected
            // AND speech was long enough to not be treated as a false start
            if (events.includes('start') && actualSpeechDuration >= 50) {
              expect(events).toContain('end');
              expect(events).toContain('segment');
            }

            // 3. Event order should be logical
            const startIndex = events.indexOf('start');
            const endIndex = events.indexOf('end');
            if (startIndex !== -1 && endIndex !== -1) {
              expect(endIndex).toBeGreaterThan(startIndex);
            }

            // Cleanup
            vad.removeAllListeners();
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});

/**
 * Helper function to generate audio frame for testing
 * @param samples - Number of audio samples
 * @param energy - Signal energy level (0-1)
 * @returns ArrayBuffer containing audio data
 */
function generateAudioFrame(samples: number, energy: number): ArrayBuffer {
  const buffer = new ArrayBuffer(samples * 2); // 16-bit samples
  const view = new Int16Array(buffer);

  for (let i = 0; i < samples; i++) {
    // Generate signal with speech-like characteristics
    const frequency = 150 + Math.sin(i / 50) * 50; // 100-200 Hz (typical speech)
    const t = i / 16000; // Time in seconds
    const signal = Math.sin(2 * Math.PI * frequency * t) * energy;

    // Add slight randomness for realism
    const noise = (Math.random() - 0.5) * 0.01 * energy;
    const value = (signal + noise) * 32768;

    view[i] = Math.max(-32768, Math.min(32767, Math.round(value)));
  }

  return buffer;
}
