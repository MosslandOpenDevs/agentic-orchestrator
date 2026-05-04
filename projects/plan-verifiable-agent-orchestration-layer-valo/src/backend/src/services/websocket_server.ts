import { WsOptions, WebSocket } from 'ws';
import { Logger } from 'ts-logging';

const logger = Logger.getLogger(__filename);

interface WebSocketServiceOptions {
  url: string;
  retryIntervalMs?: number;
  maxRetries?: number;
  rateLimitIntervalMs?: number;
  rateLimitRequests?: number;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private rateLimitTimeout: NodeJS.Timeout | null = null;

  constructor(private options: WebSocketServiceOptions) {
    logger.debug(`WebSocketService initialized with options: ${JSON.stringify(options)}`);
  }

  public async connect(): Promise<void> {
    try {
      this.ws = new WebSocket(this.options.url);

      this.ws.onopen = () => {
        logger.info('WebSocket connection opened.');
      };

      this.ws.onmessage = async (event) => {
        try {
          const message = event.data;
          logger.debug(`Received message: ${message}`);
          // Handle incoming messages here - implement your logic
        } catch (error) {
          logger.error('Error processing WebSocket message:', error);
        }
      };

      this.ws.onclose = (code, reason) => {
        logger.warn(`WebSocket connection closed with code ${code}, reason: ${reason}`);
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
        }

        this.reconnectTimeout = setTimeout(() => {
          logger.info('Reconnecting WebSocket...');
          this.connect();
        }, this.options.retryIntervalMs || 5000);
      };

      this.ws.onerror = (error) => {
        logger.error('WebSocket error:', error);
      };
    } catch (error) {
      logger.error('Error connecting to WebSocket:', error);
      this.ws = null;
    }
  }

  public async disconnect(): Promise<void> {
    if (this.ws) {
      try {
        this.ws.close();
        this.ws = null;
        logger.info('WebSocket connection closed.');
      } catch (error) {
        logger.error('Error closing WebSocket connection:', error);
      }
    }
  }

  public async send(message: any): Promise<void> {
    if (!this.ws) {
      logger.error('WebSocket connection not established.');
      return;
    }

    try {
      await this.ws.send(message);
      logger.debug(`Sent message: ${message}`);
    } catch (error) {
      logger.error('Error sending message to WebSocket:', error);
    }
  }

  public async rateLimit(): Promise<void> {
    if (this.rateLimitTimeout) {
      clearTimeout(this.rateLimitTimeout);
    }

    this.rateLimitTimeout = setTimeout(async () => {
      logger.info('Rate limit reset.');
      this.rateLimitTimeout = null;
    }, this.options.rateLimitIntervalMs || 1000);
  }
}