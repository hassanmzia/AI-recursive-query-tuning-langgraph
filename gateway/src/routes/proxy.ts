import { Router, Request, Response } from 'express';
import { createProxyMiddleware, Options } from 'http-proxy-middleware';

export function proxyRoutes(backendUrl: string): Router {
  const router = Router();

  const proxyOptions: Options = {
    target: backendUrl,
    changeOrigin: true,
    timeout: 300000,      // 5 minutes for long-running AI queries
    proxyTimeout: 300000,
    on: {
      proxyReq: (proxyReq, req: any) => {
        // Forward session ID header
        if (req.headers['x-session-id']) {
          proxyReq.setHeader('X-Session-Id', req.headers['x-session-id']);
        }
      },
      error: (err, req, res: any) => {
        console.error('[Gateway] Proxy error:', err.message);
        if (!res.headersSent) {
          res.status(502).json({
            error: 'Backend service unavailable',
            message: err.message,
          });
        }
      },
    },
  };

  // Proxy all /api routes to backend
  router.use('/', createProxyMiddleware(proxyOptions));

  return router;
}
