import { WebSocket } from 'ws';
import { Logger } from 'winston';
import { RateLimiterRedis } from 'rate-limiter-redis';
import { createClient } from 'redis';
import { injectable, inject } from 'tsyringe';

// Configure logging
const logger = Logger({ level: 'info' });

interface WebSocketOptions {
  url: string;
  retryInterval: number;
  maxRetries: number;
  rateLimit: {
    windowMs: number;
    max: number;
  };
}

@injectable()
export class WebSocketService {
  private wss: WebSocket | null = null;
  private redisClient: any = null;
  private rateLimiter: RateLimiterRedis | null = null;
  private options: WebSocketOptions;

  constructor(options: WebSocketOptions) {
    this.options = options;

    // Initialize Redis Client
    this.redisClient = createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379',
    });

    this.redisClient.on('error', (err) => {
      logger.error('Redis connection error:', err);
    });

    this.redisClient.connect().then(() => {
      logger.info('Connected to Redis');
    });

    // Initialize Rate Limiter
    this.rateLimiter = new RateLimiterRedis({
      store: this.redisClient,
      keyPrefix: 'websocket:',
      windowMs: this.options.rateLimit.windowMs,
      max: this.options.rateLimit.max,
    });

    // Logging setup
    logger.info('WebSocketService initialized');
  }

  async connect(): Promise<void> {
    if (this.wss) {
      return;
    }

    try {
      this.wss = new WebSocket(this.options.url);

      this.wss.onopen = () => {
        logger.info('WebSocket connection opened');
      };

      this.wss.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          logger.info('Received message:', message);
        } catch (error) {
          logger.error('Error parsing WebSocket message:', error);
        }
      };

      this.wss.onclose = (code, reason) => {
        logger.info(`WebSocket connection closed: ${code} - ${reason}`);
        // Implement reconnection logic here if needed
      };

      this.wss.onerror = (error) => {
        logger.error('WebSocket error:', error);
      };

    } catch (error) {
      logger.error('Error connecting to WebSocket server:', error);
      this.wss = null;
    }
  }

  async disconnect(): Promise<void> {
    if (!this.wss) {
      return;
    }

    try {
      if (this.wss.readyState === WebSocket.CLOSING) {
        // Give it a moment to close gracefully
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      this.wss.close();
      this.wss = null;
      logger.info('WebSocket connection closed');
    } catch (error) {
      logger.error('Error disconnecting from WebSocket server:', error);
    }
  }

  async send(message: any): Promise<boolean> {
    try {
      if (!this.wss || !this.wss.readyState === WebSocket.OPEN) {
        logger.warn('WebSocket not connected, cannot send message');
        return false;
      }

      // Rate limiting
      const limit = await this.rateLimiter.fetch({ key: 'message' });
      if (limit < 0) {
        logger.warn('Rate limit exceeded, cannot send message');
        return false;
      }

      this.wss.send(JSON.stringify(message));
      logger.info('Sent message:', message);
      return true;
    } catch (error) {
      logger.error('Error sending message:', error);
      return false;
    }
  }
}