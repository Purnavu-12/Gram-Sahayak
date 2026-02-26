import { HealthMonitor } from '../services/health-monitor';
import { CircuitBreaker, CircuitState } from '../services/circuit-breaker';
import { RetryPolicy } from '../services/retry-policy';
import { LoadBalancer, LoadBalancingStrategy, ServiceInstance } from '../services/load-balancer';

describe('Microservices Integration', () => {
  describe('Health Monitor', () => {
    it('should check service health', async () => {
      const monitor = new HealthMonitor();
      const health = await monitor.checkServiceHealth({
        name: 'test-service',
        url: 'http://localhost:9999/health',
      });

      expect(health).toBeDefined();
      expect(health.name).toBe('test-service');
      expect(health.status).toBeDefined();
      expect(health.lastChecked).toBeInstanceOf(Date);
    });

    it('should cache health check results', async () => {
      const monitor = new HealthMonitor();
      
      // First check
      await monitor.checkServiceHealth({
        name: 'test-service',
        url: 'http://localhost:9999/health',
      });

      // Get cached result
      const cached = monitor.getCachedHealth('test-service');
      expect(cached).toBeDefined();
      expect(cached?.name).toBe('test-service');
    });
  });

  describe('Circuit Breaker', () => {
    it('should start in CLOSED state', () => {
      const breaker = new CircuitBreaker('test-service');
      expect(breaker.getState()).toBe(CircuitState.CLOSED);
    });

    it('should open after failure threshold', async () => {
      const breaker = new CircuitBreaker('test-service', {
        failureThreshold: 3,
        successThreshold: 2,
        timeout: 1000,
        resetTimeout: 5000,
      });

      const failingFn = async () => {
        throw new Error('Service error');
      };

      // Trigger failures
      for (let i = 0; i < 3; i++) {
        try {
          await breaker.execute(failingFn);
        } catch (error) {
          // Expected
        }
      }

      expect(breaker.getState()).toBe(CircuitState.OPEN);
    });

    it('should transition to HALF_OPEN after reset timeout', async () => {
      const breaker = new CircuitBreaker('test-service', {
        failureThreshold: 2,
        successThreshold: 1,
        timeout: 1000,
        resetTimeout: 100, // Short timeout for testing
      });

      const failingFn = async () => {
        throw new Error('Service error');
      };

      // Open the circuit
      for (let i = 0; i < 2; i++) {
        try {
          await breaker.execute(failingFn);
        } catch (error) {
          // Expected
        }
      }

      expect(breaker.getState()).toBe(CircuitState.OPEN);

      // Wait for reset timeout
      await new Promise(resolve => setTimeout(resolve, 150));

      // Next attempt should transition to HALF_OPEN
      try {
        await breaker.execute(failingFn);
      } catch (error) {
        // Expected
      }

      // State should be OPEN again after failure in HALF_OPEN
      expect(breaker.getState()).toBe(CircuitState.OPEN);
    });

    it('should close after success threshold in HALF_OPEN', async () => {
      const breaker = new CircuitBreaker('test-service', {
        failureThreshold: 2,
        successThreshold: 2,
        timeout: 1000,
        resetTimeout: 100,
      });

      const failingFn = async () => {
        throw new Error('Service error');
      };

      const successFn = async () => {
        return 'success';
      };

      // Open the circuit
      for (let i = 0; i < 2; i++) {
        try {
          await breaker.execute(failingFn);
        } catch (error) {
          // Expected
        }
      }

      expect(breaker.getState()).toBe(CircuitState.OPEN);

      // Wait for reset timeout
      await new Promise(resolve => setTimeout(resolve, 150));

      // Execute successful requests
      for (let i = 0; i < 2; i++) {
        await breaker.execute(successFn);
      }

      expect(breaker.getState()).toBe(CircuitState.CLOSED);
    });
  });

  describe('Retry Policy', () => {
    it('should retry on retryable errors', async () => {
      const policy = new RetryPolicy({
        maxAttempts: 3,
        initialDelay: 10,
        maxDelay: 100,
        backoffMultiplier: 2,
      });

      let attempts = 0;
      const fn = async () => {
        attempts++;
        if (attempts < 3) {
          const error: any = new Error('Connection refused');
          error.code = 'ECONNREFUSED';
          throw error;
        }
        return 'success';
      };

      const result = await policy.execute(fn);
      expect(result).toBe('success');
      expect(attempts).toBe(3);
    });

    it('should not retry on non-retryable errors', async () => {
      const policy = new RetryPolicy({
        maxAttempts: 3,
        initialDelay: 10,
      });

      let attempts = 0;
      const fn = async () => {
        attempts++;
        throw new Error('Bad request');
      };

      await expect(policy.execute(fn)).rejects.toThrow('Bad request');
      expect(attempts).toBe(1);
    });

    it('should use exponential backoff', async () => {
      const policy = new RetryPolicy({
        maxAttempts: 3,
        initialDelay: 100,
        maxDelay: 1000,
        backoffMultiplier: 2,
      });

      const startTime = Date.now();
      let attempts = 0;

      const fn = async () => {
        attempts++;
        const error: any = new Error('Timeout');
        error.code = 'ETIMEDOUT';
        throw error;
      };

      try {
        await policy.execute(fn);
      } catch (error) {
        // Expected
      }

      const duration = Date.now() - startTime;
      expect(attempts).toBe(3);
      // Should take at least 100ms (first delay) + 200ms (second delay) = 300ms
      expect(duration).toBeGreaterThanOrEqual(300);
    });
  });

  describe('Load Balancer', () => {
    it('should distribute requests using round robin', () => {
      const lb = new LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN);

      const instances: ServiceInstance[] = [
        { url: 'http://service1:3000', healthy: true, weight: 1, activeConnections: 0 },
        { url: 'http://service2:3000', healthy: true, weight: 1, activeConnections: 0 },
        { url: 'http://service3:3000', healthy: true, weight: 1, activeConnections: 0 },
      ];

      instances.forEach(i => lb.registerInstance('test-service', i));

      const selected = [];
      for (let i = 0; i < 6; i++) {
        const instance = lb.getNextInstance('test-service');
        selected.push(instance?.url);
      }

      // Should cycle through instances
      expect(selected[0]).toBe('http://service1:3000');
      expect(selected[1]).toBe('http://service2:3000');
      expect(selected[2]).toBe('http://service3:3000');
      expect(selected[3]).toBe('http://service1:3000');
      expect(selected[4]).toBe('http://service2:3000');
      expect(selected[5]).toBe('http://service3:3000');
    });

    it('should skip unhealthy instances', () => {
      const lb = new LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN);

      const instances: ServiceInstance[] = [
        { url: 'http://service1:3000', healthy: true, weight: 1, activeConnections: 0 },
        { url: 'http://service2:3000', healthy: false, weight: 1, activeConnections: 0 },
        { url: 'http://service3:3000', healthy: true, weight: 1, activeConnections: 0 },
      ];

      instances.forEach(i => lb.registerInstance('test-service', i));

      const selected = [];
      for (let i = 0; i < 4; i++) {
        const instance = lb.getNextInstance('test-service');
        selected.push(instance?.url);
      }

      // Should only select healthy instances
      expect(selected).not.toContain('http://service2:3000');
      expect(selected[0]).toBe('http://service1:3000');
      expect(selected[1]).toBe('http://service3:3000');
    });

    it('should use least connections strategy', () => {
      const lb = new LoadBalancer(LoadBalancingStrategy.LEAST_CONNECTIONS);

      const instances: ServiceInstance[] = [
        { url: 'http://service1:3000', healthy: true, weight: 1, activeConnections: 5 },
        { url: 'http://service2:3000', healthy: true, weight: 1, activeConnections: 2 },
        { url: 'http://service3:3000', healthy: true, weight: 1, activeConnections: 8 },
      ];

      instances.forEach(i => lb.registerInstance('test-service', i));

      const instance = lb.getNextInstance('test-service');
      expect(instance?.url).toBe('http://service2:3000');
    });

    it('should track active connections', () => {
      const lb = new LoadBalancer();

      const instance: ServiceInstance = {
        url: 'http://service1:3000',
        healthy: true,
        weight: 1,
        activeConnections: 0,
      };

      lb.registerInstance('test-service', instance);

      lb.incrementConnections('test-service', 'http://service1:3000');
      lb.incrementConnections('test-service', 'http://service1:3000');

      const stats = lb.getStats('test-service');
      expect(stats?.instances[0].activeConnections).toBe(2);

      lb.decrementConnections('test-service', 'http://service1:3000');

      const updatedStats = lb.getStats('test-service');
      expect(updatedStats?.instances[0].activeConnections).toBe(1);
    });
  });
});
