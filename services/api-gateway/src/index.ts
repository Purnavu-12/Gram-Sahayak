import express from 'express';
import rateLimit from 'express-rate-limit';
import { authMiddleware } from './middleware/auth';
import { createProxyRouter } from './routes/proxy';

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

// Rate limiting configuration
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

app.use('/api/', limiter);

// Authentication middleware
app.use('/api/', authMiddleware);

// Proxy routes to microservices
app.use('/api/voice', createProxyRouter('http://voice-engine:3001'));
app.use('/api/dialect', createProxyRouter('http://dialect-detector:8001'));
app.use('/api/schemes', createProxyRouter('http://scheme-matcher:8002'));
app.use('/api/forms', createProxyRouter('http://form-generator:3002'));

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`API Gateway listening on port ${port}`);
});
