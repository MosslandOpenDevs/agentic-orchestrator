import { WebSocket } from 'ws';
import { RateLimiterRedis } from 'rate-limiter-flexible';
import Redis from 'ioredis';
import { logger } from './logger';
import { Config, WebSocketConfig } from './config';

export class WebSocketService {
  private wss: WebSocket | null = null;
  private redis: Redis | null = null;
  private config: WebSocketConfig;

  constructor(config: Config) {
    this.config = config.websocket;

    this.redis = new Redis({
      host: this.config.redisHost,
      port: this.config.redisPort,
    });

    if (!this.redis) {
      logger.error('Redis connection failed.');
    }
  }

  public async connect(): Promise<void> {
    try {
      this.wss = new WebSocket(this.config.wsUrl);

      this.wss.onopen = () => {
        logger.info('WebSocket connection opened.');
      };

      this.wss.onmessage = async (event) => {
        try {
          const message = event.data;
          logger.debug(`Received message: ${message}`);
          // Implement message processing logic here
        } catch (error) {
          logger.error('Error processing WebSocket message:', error);
        }
      };

      this.wss.onclose = (code, reason) => {
        logger.warn(`WebSocket connection closed: ${code} - ${reason}`);
        // Implement reconnection logic here
      };

      this.wss.onerror = (error) => {
        logger.error('WebSocket error:', error);
      };
    } catch (error) {
      logger.error('Failed to connect to WebSocket server:', error);
      this.wss = null;
    }
  }

  public async disconnect(): Promise<void> {
    if (this.wss) {
      try {
        this.wss.close();
      } catch (error) {
        logger.error('Error closing WebSocket connection:', error);
      }
      this.wss = null;
    }
  }

  public async sendMessage(message: any): Promise<boolean> {
    if (!this.wss || !this.wss.readyState === WebSocket.OPEN) {
      logger.warn('WebSocket not connected. Cannot send message.');
      return false;
    }

    try {
      const success = await this.wss.send(message);
      logger.debug(`Sent message: ${message}, success: ${success}`);
      return success;
    } catch (error) {
      logger.error('Error sending message:', error);
      return false;
    }
  }

  public async receiveMessage(): Promise<any> {
    if (!this.wss || !this.wss.readyState === WebSocket.OPEN) {
      logger.warn('WebSocket not connected. Cannot receive message.');
      return null;
    }

    try {
      return new Promise((resolve, reject) => {
        this.wss.onmessage = (event) => {
          resolve(event.data);
          this.wss.removeListener('onmessage', this.wss.onmessage); // Clean up listener
        };
        this.wss.onerror = (error) => {
          reject(error);
          this.wss.removeListener('onerror', this.wss.onerror); // Clean up listener
        };
      });
    } catch (error) {
      logger.error('Error receiving message:', error);
      return null;
    }
  }

  async cleanup() {
    if (this.redis) {
      await this.redis.quit();
      this.redis = null;
    }
  }
}