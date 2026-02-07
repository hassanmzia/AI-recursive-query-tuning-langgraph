import type { WebSocketMessage } from '../types';

type MessageHandler = (message: WebSocketMessage) => void;

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://172.168.1.95:3083';

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private sessionId: string = 'default';

  connect(sessionId?: string): void {
    if (sessionId) this.sessionId = sessionId;

    const url = `${WS_URL}/ws?session_id=${this.sessionId}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.reconnectAttempts = 0;
        this.emit('connection_status', { type: 'connection_status', connected: true });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.emit(message.type, message);
          this.emit('*', message); // Wildcard handler
        } catch (err) {
          console.error('[WS] Failed to parse message:', err);
        }
      };

      this.ws.onclose = () => {
        console.log('[WS] Disconnected');
        this.emit('connection_status', { type: 'connection_status', connected: false });
        this.attemptReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('[WS] Error:', err);
      };
    } catch (err) {
      console.error('[WS] Failed to connect:', err);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WS] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => this.connect(), delay);
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: Record<string, any>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WS] Not connected, cannot send message');
    }
  }

  executeQuery(query: string, workflowType: string = 'recursive_qa'): void {
    this.send({
      type: 'execute_query',
      query,
      workflow_type: workflowType,
    });
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  private emit(type: string, message: WebSocketMessage): void {
    this.handlers.get(type)?.forEach((handler) => {
      try {
        handler(message);
      } catch (err) {
        console.error('[WS] Handler error:', err);
      }
    });
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
