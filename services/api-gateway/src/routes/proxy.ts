import { Router } from 'express';
import axios from 'axios';
import { CircuitBreakerRegistry } from '../services/circuit-breaker';
import { RetryPolicy } from '../services/retry-policy';

const circuitBreakerRegistry = new CircuitBreakerRegistry();

export function createProxyRouter(targetUrl: string): Router {
  const router = Router();
  const serviceName = new URL(targetUrl).hostname;
  const circuitBreaker = circuitBreakerRegistry.getBreaker(serviceName);
  const retryPolicy = new RetryPolicy();

  router.all('*', async (req, res) => {
    try {
      // Execute with circuit breaker and retry policy
      const response = await circuitBreaker.execute(async () => {
        return await retryPolicy.execute(async () => {
          return await axios({
            method: req.method,
            url: `${targetUrl}${req.path}`,
            data: req.body,
            headers: {
              'Content-Type': 'application/json',
            },
            params: req.query,
            timeout: 30000, // 30 second timeout
          });
        });
      });

      res.status(response.status).json(response.data);
    } catch (error: any) {
      // Check if circuit breaker is open
      if (error.message && error.message.includes('Circuit breaker is OPEN')) {
        return res.status(503).json({ 
          error: 'Service temporarily unavailable',
          service: serviceName,
          retryAfter: 30,
        });
      }

      if (error.response) {
        res.status(error.response.status).json(error.response.data);
      } else {
        res.status(500).json({ 
          error: 'Service unavailable',
          message: error.message,
        });
      }
    }
  });

  return router;
}

export function getCircuitBreakerRegistry(): CircuitBreakerRegistry {
  return circuitBreakerRegistry;
}
