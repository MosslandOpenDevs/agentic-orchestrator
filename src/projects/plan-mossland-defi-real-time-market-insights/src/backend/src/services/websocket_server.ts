import WebSocket from 'ws';
import { RateLimiterMemory } from 'rate-limiter-flexible';

const WS_URL = process.env.WS_SERVER_URL || 'wss://example.com/socket';
const RATE_LIMIT = parseInt(process.env.RATE_LIMIT || '10');
const RETRY_DELAY_MS = parseInt(process.env.RETRY_DELAY_MS || '5000');

class WebSocketService {
  private ws: WebSocket | null = null;
  private rateLimiter: RateLimiterMemory;

  constructor() {
    this.rateLimiter = new RateLimiterMemory({
      points: RATE_LIMIT,
      duration: 1, // per second
    });
    this.connect();
  }

  private connect(): void {
    this.ws = new WebSocket(WS_URL);
    this.ws.on('open', () => console.log('Connected to WebSocket server'));
    this.ws.on('message', (data) => console.log(`Received message: ${data}`));
    this.ws.on('error', (err) => console.error('WebSocket error:', err));
    this.ws.on('close', () => {
      console.log('Connection closed, attempting reconnect...');
      setTimeout(() => this.connect(), RETRY_DELAY_MS);
    });
  }

  public async sendMessage(message: string): Promise<void> {
    try {
      await this.rateLimiter.consume(1);
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ message }));
      } else {
        console.error('WebSocket is not open');
      }
    } catch (err) {
      if (err instanceof Error) {
        console.error(`Rate limit exceeded: ${err.message}`);
      }
    }
  }

  public close(): void {
    if (this.ws) {
      this.ws.close();
    }
  }
}

const wsService = new WebSocketService();

// Example usage
wsService.sendMessage('Hello, WebSocket!').then(() => console.log('Message sent'));