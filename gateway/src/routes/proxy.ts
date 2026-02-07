import { Router, Request, Response } from 'express';
import { createProxyMiddleware, Options } from 'http-proxy-middleware';

export function proxyRoutes(backendUrl: string): Router {
  const router = Router();

  const proxyOptions: Options = {
    target: backendUrl,
    changeOrigin: true,
    timeout: 300000,      // 5 minutes for long-running AI queries
    proxyTimeout: 300000,
    // Express strips the /api prefix before passing to this middleware,
    // but Django expects /api/ in the URL — re-add it.
    pathRewrite: { '^/': '/api/' },
    on: {
      proxyReq: (proxyReq, req: any) => {
        // Re-serialize the body that express.json() already consumed.
        // Without this, POST/PUT/PATCH requests hang because the proxy
        // tries to pipe a stream that has already been drained.
        if (req.body && Object.keys(req.body).length > 0) {
          const bodyData = JSON.stringify(req.body);
          proxyReq.setHeader('Content-Type', 'application/json');
          proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData).toString());
          proxyReq.write(bodyData);
        }

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
