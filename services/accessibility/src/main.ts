/**
 * Accessibility Service Main Entry Point
 * HTTP server for accessibility features
 */

import express from 'express';
import apiRouter from './api';

const app = express();
const PORT = process.env.PORT || 3006;

// Middleware
app.use(express.json());

// CORS for development
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  
  next();
});

// Routes
app.use('/api/accessibility', apiRouter);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Gram Sahayak Accessibility Service',
    version: '1.0.0',
    status: 'running'
  });
});

// Start server
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Accessibility Service running on port ${PORT}`);
  });
}

export default app;
