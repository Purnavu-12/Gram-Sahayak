import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { authMiddleware } from './middleware/auth';
import { createProxyRouter, getCircuitBreakerRegistry } from './routes/proxy';
import { HealthMonitor } from './services/health-monitor';
import conversationRouter from './routes/conversation';
import { tracingMiddleware } from './services/distributed-tracing';
import {
  BedrockAgentWrapper,
  FallbackHandler,
  BedrockMetricsCollector,
  loadBedrockConfig,
  validateBedrockConfig,
} from '../../../shared/bedrock';

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

// Initialize Bedrock integration
const bedrockConfig = loadBedrockConfig();
const bedrockValidation = validateBedrockConfig(bedrockConfig);
let bedrockWrapper: BedrockAgentWrapper | null = null;
let bedrockMetrics: BedrockMetricsCollector | null = null;

if (bedrockConfig.enabled && bedrockValidation.valid) {
  bedrockWrapper = new BedrockAgentWrapper(bedrockConfig);
  bedrockMetrics = new BedrockMetricsCollector();
  console.log('API Gateway: Bedrock integration enabled');
} else {
  if (bedrockConfig.enabled && !bedrockValidation.valid) {
    console.warn('API Gateway: Bedrock config invalid, starting with Bedrock disabled:', bedrockValidation.errors);
  }
  console.log('API Gateway: Bedrock integration disabled');
}

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

// Bedrock integration endpoints
app.get('/health/bedrock', async (req, res) => {
  if (!bedrockWrapper) {
    return res.json({
      status: 'disabled',
      message: 'Bedrock integration is not enabled',
    });
  }

  try {
    const health = await bedrockWrapper.checkHealth();
    res.json(health);
  } catch (error: any) {
    res.status(500).json({ error: 'Bedrock health check failed', message: error.message });
  }
});

app.get('/metrics/bedrock', (req, res) => {
  if (!bedrockMetrics) {
    return res.status(404).json({ error: 'Bedrock metrics not available' });
  }

  const format = req.query.format;
  if (format === 'prometheus') {
    res.set('Content-Type', 'text/plain');
    res.send(bedrockMetrics.toPrometheusFormat());
  } else {
    res.json(bedrockMetrics.getMetrics());
  }
});

app.get('/config/bedrock', (req, res) => {
  // Return sanitized config (no credentials)
  const safeConfig = {
    enabled: bedrockConfig.enabled,
    region: bedrockConfig.region,
    models: {
      claude: {
        modelId: bedrockConfig.models.claude.modelId,
        fallbackModelId: bedrockConfig.models.claude.fallbackModelId,
      },
      novaPro: {
        sttModelId: bedrockConfig.models.novaPro.sttModelId,
        ttsModelId: bedrockConfig.models.novaPro.ttsModelId,
      },
      titanEmbeddings: {
        modelId: bedrockConfig.models.titanEmbeddings.modelId,
      },
    },
    knowledgeBase: {
      kbId: bedrockConfig.knowledgeBase.kbId ? '***configured***' : 'not configured',
      maxResults: bedrockConfig.knowledgeBase.maxResults,
    },
    fallback: bedrockConfig.fallback,
    monitoring: bedrockConfig.monitoring,
  };
  res.json(safeConfig);
});

app.listen(port, () => {
  console.log(`API Gateway listening on port ${port}`);
});
