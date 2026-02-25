import { Router } from 'express';
import axios from 'axios';

export function createProxyRouter(targetUrl: string): Router {
  const router = Router();

  router.all('*', async (req, res) => {
    try {
      const response = await axios({
        method: req.method,
        url: `${targetUrl}${req.path}`,
        data: req.body,
        headers: {
          'Content-Type': 'application/json',
        },
        params: req.query,
      });

      res.status(response.status).json(response.data);
    } catch (error: any) {
      if (error.response) {
        res.status(error.response.status).json(error.response.data);
      } else {
        res.status(500).json({ error: 'Service unavailable' });
      }
    }
  });

  return router;
}
