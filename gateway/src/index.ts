import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { createServer } from 'http';
import { setupWebSocket } from './websocket/handler';
import { proxyRoutes } from './routes/proxy';
import { healthRoutes } from './routes/health';
import { rateLimiter } from './middleware/rateLimiter';
import { requestLogger } from './middleware/requestLogger';

const app = express();
const PORT = parseInt(process.env.PORT || '3083', 10);
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8042';

// Security middleware
app.use(helmet({
  crossOriginResourcePolicy: { policy: 'cross-origin' },
  contentSecurityPolicy: false,
}));

// CORS configuration
app.use(cors({
  origin: [
    `http://${process.env.HOST_IP || '172.168.1.95'}:${process.env.FRONTEND_PORT || '3082'}`,
    'http://localhost:3082',
    'http://127.0.0.1:3082',
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Session-Id'],
}));

// Body parsing
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Logging
app.use(morgan('combined'));
app.use(requestLogger);

// Rate limiting
app.use('/api/', rateLimiter);

// Routes
app.use('/api/health', healthRoutes);
app.use('/api', proxyRoutes(BACKEND_URL));

// Create HTTP server
const server = createServer(app);

// Setup WebSocket
setupWebSocket(server, BACKEND_URL);

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[Gateway] API Gateway running on port ${PORT}`);
  console.log(`[Gateway] Backend URL: ${BACKEND_URL}`);
  console.log(`[Gateway] WebSocket enabled`);
});

export default app;
