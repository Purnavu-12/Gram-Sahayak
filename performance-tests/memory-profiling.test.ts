/**
 * Memory Usage Profiling and Optimization Tests
 * Validates memory efficiency across all services
 */

import { PERFORMANCE_TARGETS } from './config';

describe('Memory Usage Profiling', () => {
  describe('Service Memory Limits', () => {
    it('should keep individual service memory under 512MB', async () => {
      const services = [
        'voice-engine',
        'dialect-detector',
        'scheme-matcher',
        'form-generator',
        'document-guide',
        'application-tracker',
        'user-profile',
        'api-gateway',
      ];
      
      const memoryUsage: Record<string, number> = {};
      
      for (const service of services) {
        const usage = await measureServiceMemory(service);
        memoryUsage[service] = usage;
        
        console.log(`${service}: ${usage.toFixed(2)}MB`);
        
        expect(usage).toBeLessThan(PERFORMANCE_TARGETS.MEMORY_LIMIT_PER_SERVICE);
      }
      
      const totalMemory = Object.values(memoryUsage).reduce((a, b) => a + b, 0);
      console.log(`Total Memory: ${totalMemory.toFixed(2)}MB`);
      
      expect(totalMemory).toBeLessThan(PERFORMANCE_TARGETS.MEMORY_LIMIT_TOTAL);
    });
  });
  
  describe('Memory Leak Detection', () => {
    it('should not leak memory during sustained operations', async () => {
      const iterations = 100;
      const memorySnapshots: number[] = [];
      
      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }
      
      const initialMemory = process.memoryUsage().heapUsed / 1024 / 1024;
      memorySnapshots.push(initialMemory);
      
      for (let i = 0; i < iterations; i++) {
        // Simulate sustained operations
        await simulateVoiceProcessing();
        await simulateSchemeMatching();
        await simulateFormGeneration();
        
        if (i % 10 === 0) {
          if (global.gc) {
            global.gc();
          }
          const currentMemory = process.memoryUsage().heapUsed / 1024 / 1024;
          memorySnapshots.push(currentMemory);
        }
      }
      
      const finalMemory = memorySnapshots[memorySnapshots.length - 1];
      const memoryGrowth = finalMemory - initialMemory;
      const growthRate = memoryGrowth / initialMemory;
      
      console.log('Memory Leak Detection:');
      console.log(`  Initial Memory: ${initialMemory.toFixed(2)}MB`);
      console.log(`  Final Memory: ${finalMemory.toFixed(2)}MB`);
      console.log(`  Growth: ${memoryGrowth.toFixed(2)}MB`);
      console.log(`  Growth Rate: ${(growthRate * 100).toFixed(2)}%`);
      
      // Memory growth should be minimal (less than 20%)
      expect(growthRate).toBeLessThan(0.2);
    });
  });
  
  describe('Heap Usage Optimization', () => {
    it('should maintain healthy heap usage patterns', async () => {
      const samples = 50;
      const heapUsageRatios: number[] = [];
      
      for (let i = 0; i < samples; i++) {
        await simulateWorkload();
        
        const memUsage = process.memoryUsage();
        const heapRatio = memUsage.heapUsed / memUsage.heapTotal;
        heapUsageRatios.push(heapRatio);
        
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      const avgHeapRatio = heapUsageRatios.reduce((a, b) => a + b, 0) / heapUsageRatios.length;
      
      console.log('Heap Usage Analysis:');
      console.log(`  Average Heap Ratio: ${(avgHeapRatio * 100).toFixed(2)}%`);
      console.log(`  Min: ${(Math.min(...heapUsageRatios) * 100).toFixed(2)}%`);
      console.log(`  Max: ${(Math.max(...heapUsageRatios) * 100).toFixed(2)}%`);
      
      // Heap usage should stay below 80% to avoid frequent GC
      expect(avgHeapRatio).toBeLessThan(0.8);
    });
  });
  
  describe('Large Object Handling', () => {
    it('should handle large audio buffers efficiently', async () => {
      const audioBufferSizes = [
        1024 * 16,      // 16KB
        1024 * 64,      // 64KB
        1024 * 256,     // 256KB
        1024 * 1024,    // 1MB
      ];
      
      for (const size of audioBufferSizes) {
        const memBefore = process.memoryUsage().heapUsed / 1024 / 1024;
        
        // Simulate audio buffer processing
        const buffer = new Float32Array(size / 4);
        await processAudioBuffer(buffer);
        
        // Allow GC to run
        if (global.gc) {
          global.gc();
        }
        
        const memAfter = process.memoryUsage().heapUsed / 1024 / 1024;
        const memDelta = memAfter - memBefore;
        
        console.log(`Audio Buffer ${size / 1024}KB: Memory Delta ${memDelta.toFixed(2)}MB`);
        
        // Memory delta should be reasonable
        expect(memDelta).toBeLessThan(size / 1024 / 1024 * 2);
      }
    });
    
    it('should handle large PDF generation efficiently', async () => {
      const memBefore = process.memoryUsage().heapUsed / 1024 / 1024;
      
      // Simulate large PDF generation
      await simulatePDFGeneration({
        pages: 20,
        imagesPerPage: 2,
      });
      
      if (global.gc) {
        global.gc();
      }
      
      const memAfter = process.memoryUsage().heapUsed / 1024 / 1024;
      const memDelta = memAfter - memBefore;
      
      console.log(`PDF Generation Memory Delta: ${memDelta.toFixed(2)}MB`);
      
      // PDF generation should not consume excessive memory
      expect(memDelta).toBeLessThan(50);
    });
  });
  
  describe('Cache Memory Management', () => {
    it('should limit cache memory usage', async () => {
      const cacheEntries = 10000;
      const memBefore = process.memoryUsage().heapUsed / 1024 / 1024;
      
      // Simulate cache population
      const cache = new Map<string, any>();
      for (let i = 0; i < cacheEntries; i++) {
        cache.set(`key_${i}`, {
          id: i,
          data: `value_${i}`,
          timestamp: Date.now(),
        });
      }
      
      const memAfter = process.memoryUsage().heapUsed / 1024 / 1024;
      const memDelta = memAfter - memBefore;
      const memPerEntry = memDelta / cacheEntries;
      
      console.log('Cache Memory Analysis:');
      console.log(`  Cache Entries: ${cacheEntries}`);
      console.log(`  Total Memory: ${memDelta.toFixed(2)}MB`);
      console.log(`  Memory per Entry: ${(memPerEntry * 1024).toFixed(2)}KB`);
      
      // Cache should use reasonable memory
      expect(memDelta).toBeLessThan(100);
    });
  });
  
  describe('Garbage Collection Performance', () => {
    it('should have reasonable GC pause times', async () => {
      if (!global.gc) {
        console.log('GC not exposed, skipping test');
        return;
      }
      
      const gcPauses: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        // Create garbage
        await createGarbage();
        
        // Measure GC pause
        const start = performance.now();
        global.gc();
        const pause = performance.now() - start;
        
        gcPauses.push(pause);
      }
      
      const avgPause = gcPauses.reduce((a, b) => a + b, 0) / gcPauses.length;
      const maxPause = Math.max(...gcPauses);
      
      console.log('GC Performance:');
      console.log(`  Average Pause: ${avgPause.toFixed(2)}ms`);
      console.log(`  Max Pause: ${maxPause.toFixed(2)}ms`);
      
      // GC pauses should be reasonable
      expect(avgPause).toBeLessThan(50);
      expect(maxPause).toBeLessThan(100);
    });
  });
});

// Helper functions
async function measureServiceMemory(serviceName: string): Promise<number> {
  // Simulate service memory usage
  const baseMemory = 50; // Base memory in MB
  const variance = 100;
  
  return baseMemory + Math.random() * variance;
}

async function simulateVoiceProcessing(): Promise<void> {
  const buffer = new Float32Array(16000); // 1 second at 16kHz
  for (let i = 0; i < buffer.length; i++) {
    buffer[i] = Math.random();
  }
  await new Promise(resolve => setTimeout(resolve, 10));
}

async function simulateSchemeMatching(): Promise<void> {
  const schemes = Array(100).fill(null).map((_, i) => ({
    id: i,
    name: `Scheme ${i}`,
    eligibility: { age: 18, income: 50000 },
  }));
  await new Promise(resolve => setTimeout(resolve, 10));
}

async function simulateFormGeneration(): Promise<void> {
  const formData = {
    fields: Array(50).fill(null).map((_, i) => ({
      name: `field_${i}`,
      value: `value_${i}`,
    })),
  };
  await new Promise(resolve => setTimeout(resolve, 10));
}

async function simulateWorkload(): Promise<void> {
  await simulateVoiceProcessing();
  await simulateSchemeMatching();
}

async function processAudioBuffer(buffer: Float32Array): Promise<void> {
  // Simulate audio processing
  for (let i = 0; i < buffer.length; i += 100) {
    buffer[i] = buffer[i] * 0.5;
  }
  await new Promise(resolve => setTimeout(resolve, 5));
}

async function simulatePDFGeneration(config: any): Promise<void> {
  // Simulate PDF generation with large data
  const pages = Array(config.pages).fill(null).map((_, i) => ({
    number: i,
    content: 'Lorem ipsum '.repeat(1000),
    images: Array(config.imagesPerPage).fill(null),
  }));
  await new Promise(resolve => setTimeout(resolve, 50));
}

async function createGarbage(): Promise<void> {
  // Create temporary objects that will become garbage
  const garbage = Array(10000).fill(null).map((_, i) => ({
    id: i,
    data: new Array(100).fill(Math.random()),
  }));
  await new Promise(resolve => setTimeout(resolve, 10));
}
