import { Request, Response, NextFunction } from 'express';

export function requestLogger(req: Request, _res: Response, next: NextFunction): void {
  const start = Date.now();

  _res.on('finish', () => {
    const duration = Date.now() - start;
    if (duration > 1000) {
      console.log(
        `[Gateway] Slow request: ${req.method} ${req.originalUrl} - ${duration}ms (${_res.statusCode})`
      );
    }
  });

  next();
}
