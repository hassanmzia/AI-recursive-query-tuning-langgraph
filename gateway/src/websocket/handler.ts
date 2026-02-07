import { Server as HttpServer } from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import { v4 as uuidv4 } from 'uuid';
import http from 'http';

interface ClientInfo {
  id: string;
  sessionId: string;
  ws: WebSocket;
  connectedAt: Date;
}

const clients = new Map<string, ClientInfo>();

export function setupWebSocket(server: HttpServer, backendUrl: string): void {
  const wss = new WebSocketServer({
    server,
    path: '/ws',
  });

  console.log('[Gateway] WebSocket server initialized on /ws');

  wss.on('connection', (ws: WebSocket, req) => {
    const clientId = uuidv4();
    const urlParams = new URL(req.url || '/', `http://${req.headers.host}`);
    const sessionId = urlParams.searchParams.get('session_id') || 'default';

    const clientInfo: ClientInfo = {
      id: clientId,
      sessionId,
      ws,
      connectedAt: new Date(),
    };
    clients.set(clientId, clientInfo);

    console.log(`[WS] Client connected: ${clientId} (session: ${sessionId})`);

    // Send connection confirmation
    ws.send(JSON.stringify({
      type: 'connected',
      clientId,
      sessionId,
    }));

    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        handleMessage(clientInfo, message, backendUrl);
      } catch (err) {
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Invalid message format',
        }));
      }
    });

    ws.on('close', () => {
      clients.delete(clientId);
      console.log(`[WS] Client disconnected: ${clientId}`);
    });

    ws.on('error', (err) => {
      console.error(`[WS] Client error ${clientId}:`, err.message);
      clients.delete(clientId);
    });

    // Heartbeat
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.ping();
      } else {
        clearInterval(heartbeat);
      }
    }, 30000);
  });
}

function handleMessage(client: ClientInfo, message: any, backendUrl: string): void {
  const { type } = message;

  switch (type) {
    case 'execute_query':
      handleExecuteQuery(client, message, backendUrl);
      break;
    case 'ping':
      client.ws.send(JSON.stringify({ type: 'pong' }));
      break;
    default:
      client.ws.send(JSON.stringify({
        type: 'error',
        message: `Unknown message type: ${type}`,
      }));
  }
}

function handleExecuteQuery(client: ClientInfo, message: any, backendUrl: string): void {
  const { query, workflow_type = 'recursive_qa', max_iterations = 5 } = message;

  if (!query) {
    client.ws.send(JSON.stringify({
      type: 'error',
      message: 'Query is required',
    }));
    return;
  }

  // Notify client that processing has started
  client.ws.send(JSON.stringify({
    type: 'workflow_started',
    query,
    workflow_type,
  }));

  // Forward to backend API
  const postData = JSON.stringify({
    query,
    workflow_type,
    max_iterations,
    session_id: client.sessionId,
  });

  const url = new URL(`${backendUrl}/api/agents/execute/`);

  const options: http.RequestOptions = {
    hostname: url.hostname,
    port: url.port,
    path: url.pathname,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData),
    },
    timeout: 300000,
  };

  const req = http.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
      try {
        const result = JSON.parse(data);
        if (res.statusCode && res.statusCode >= 400) {
          client.ws.send(JSON.stringify({
            type: 'error',
            message: result.error || 'Backend error',
            details: result,
          }));
        } else {
          client.ws.send(JSON.stringify({
            type: 'workflow_completed',
            ...result,
          }));
        }
      } catch {
        client.ws.send(JSON.stringify({
          type: 'error',
          message: 'Failed to parse backend response',
        }));
      }
    });
  });

  req.on('error', (err) => {
    console.error('[WS] Backend request error:', err.message);
    client.ws.send(JSON.stringify({
      type: 'error',
      message: 'Backend service unavailable',
    }));
  });

  req.on('timeout', () => {
    req.destroy();
    client.ws.send(JSON.stringify({
      type: 'error',
      message: 'Backend request timed out',
    }));
  });

  req.write(postData);
  req.end();
}
