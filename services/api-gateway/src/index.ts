import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { authMiddleware } from './middleware/auth';
import { createProxyRouter, getCircuitBreakerRegistry } from './routes/proxy';
import { HealthMonitor } from './services/health-monitor';
import conversationRouter from './routes/conversation';
import { tracingMiddleware } from './services/distributed-tracing';

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json({ limit: '10mb' })); // Increased limit for audio data

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
}));

app.use(tracingMiddleware('api-gateway'));

// Initialize health monitor
const healthMonitor = new HealthMonitor();

// Rate limiting configuration
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

app.use('/api/', limiter);

// Authentication middleware
app.use('/api/', authMiddleware);

// Conversation orchestration routes (end-to-end flow)
app.use('/api/conversation', conversationRouter);

// Proxy routes to microservices
app.use('/api/voice', createProxyRouter('http://voice-engine:3001'));
app.use('/api/dialect', createProxyRouter('http://dialect-detector:8001'));
app.use('/api/schemes', createProxyRouter('http://scheme-matcher:8002'));
app.use('/api/forms', createProxyRouter('http://form-generator:3002'));
app.use('/api/documents', createProxyRouter('http://document-guide:8003'));
app.use('/api/applications', createProxyRouter('http://application-tracker:8004'));
app.use('/api/profiles', createProxyRouter('http://user-profile:8005'));
app.use('/api/accessibility', createProxyRouter('http://accessibility:3003'));

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Detailed health check endpoint
app.get('/health/detailed', async (req, res) => {
  try {
    const systemHealth = await healthMonitor.checkAllServices();
    res.json(systemHealth);
  } catch (error: any) {
    res.status(500).json({ error: 'Health check failed', message: error.message });
  }
});

// Service-specific health check
app.get('/health/service/:serviceName', async (req, res) => {
  try {
    const serviceHealth = await healthMonitor.getServiceHealth(req.params.serviceName);
    res.json(serviceHealth);
  } catch (error: any) {
    res.status(500).json({ error: 'Health check failed', message: error.message });
  }
});

// Circuit breaker status endpoint
app.get('/circuit-breakers', (req, res) => {
  const registry = getCircuitBreakerRegistry();
  const stats = registry.getAllStats();
  res.json({ circuitBreakers: stats });
});

// Reset circuit breakers (admin endpoint)
app.post('/circuit-breakers/reset', (req, res) => {
  const registry = getCircuitBreakerRegistry();
  registry.resetAll();
  res.json({ message: 'All circuit breakers reset' });
});

app.listen(port, () => {
  console.log(`API Gateway listening on port ${port}`);
});
