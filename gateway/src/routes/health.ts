import { Router, Request, Response } from 'express';
import http from 'http';

const router = Router();

router.get('/', (_req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    service: 'rqt-gateway',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

router.get('/backend', (_req: Request, res: Response) => {
  const backendUrl = process.env.BACKEND_URL || 'http://backend:8042';

  const healthReq = http.get(`${backendUrl}/api/health/`, (backendRes) => {
    let data = '';
    backendRes.on('data', (chunk) => { data += chunk; });
    backendRes.on('end', () => {
      try {
        res.json({
          gateway: 'healthy',
          backend: JSON.parse(data),
        });
      } catch {
        res.json({
          gateway: 'healthy',
          backend: { status: 'unknown', raw: data },
        });
      }
    });
  });

  healthReq.on('error', (err) => {
    res.status(503).json({
      gateway: 'healthy',
      backend: { status: 'unreachable', error: err.message },
    });
  });

  healthReq.setTimeout(5000, () => {
    healthReq.destroy();
    res.status(503).json({
      gateway: 'healthy',
      backend: { status: 'timeout' },
    });
  });
});

export const healthRoutes = router;
