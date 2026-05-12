import { WebSocket } from 'ws';
import { WsOptions, WebSocketClient } from 'ws';
import { Logger } from 'ts-logging';
import { RateLimiter } from 'rate-limiter-flexible';
import { v4 as uuidv4 } from 'uuid';

Logger.setLevel('info');

interface WebSocketMessage {
    id: string;
    type: string;
    data: any;
}

interface WebSocketServiceConfig {
    wsUrl: string;
    retryInterval?: number;
    maxRetries?: number;
    rateLimitInterval?: number;
    rateLimitMax?: number;
}

export class WebSocketService {
    private ws: WebSocket | null = null;
    private rateLimiter: RateLimiter;
    private cache: { [key: string]: any } = {};
    private logger = Logger.createDefaultLogger('WebSocketService');

    constructor(config: WebSocketServiceConfig) {
        this.wsUrl = config.wsUrl;
        this.retryInterval = config.retryInterval || 5000;
        this.maxRetries = config.maxRetries || 3;
        this.rateLimitInterval = config.rateLimitInterval || 1000;
        this.rateLimitMax = config.rateLimitMax || 100;

        this.rateLimiter = new RateLimiter({
            limiter: RateLimiter.slidingWindow,
            windowMs: this.rateLimitInterval,
            max: this.rateLimitMax,
        });

        this.logger.info(`WebSocketService initialized for ${this.wsUrl}`);
    }

    private async connect(): Promise<void> {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                this.logger.info('WebSocket connection opened');
            };

            this.ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data) as WebSocketMessage;
                    this.logger.debug(`Received message: ${JSON.stringify(message)}`);
                    this.handleMessage(message);
                } catch (error) {
                    this.logger.error(`Error parsing message: ${error}`);
                }
            };

            this.ws.onclose = (event) => {
                this.logger.info(`WebSocket connection closed with code ${event.code}, message: ${event.reason}`);
            };

            this.ws.onerror = (error) => {
                this.logger.error(`WebSocket error: ${error}`);
            };
        } catch (error) {
            this.logger.error(`Failed to connect to WebSocket: ${error}`);
        }
    }

    private async disconnect(): Promise<void> {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.logger.info('WebSocket connection closed');
        }
    }

    private async send(type: string, data: any): Promise<void> {
        if (!this.rateLimiter.shouldYield()) {
            this.logger.warn('Rate limit exceeded');
            return;
        }

        try {
            const message: WebSocketMessage = {
                id: uuidv4(),
                type: type,
                data: data,
            };
            await this.ws?.send(JSON.stringify(message));
            this.logger.debug(`Sent message: ${JSON.stringify(message)}`);
        } catch (error) {
            this.logger.error(`Error sending message: ${error}`);
        }
    }

    private handleMessage(message: WebSocketMessage): void {
        switch (message.type) {
            case 'data':
                // Handle data messages
                break;
            case 'status':
                // Handle status messages
                break;
            default:
                this.logger.warn(`Unknown message type: ${message.type}`);
        }
    }

    async connectWebSocket(): Promise<void> {
        try {
            await this.connect();
        } catch (error) {
            this.logger.error(`Failed to connect WebSocket: ${error}`);
        }
    }

    async disconnectWebSocket(): Promise<void> {
        try {
            await this.disconnect();
        } catch (error) {
            this.logger.error(`Failed to disconnect WebSocket: ${error}`);
        }
    }

    async sendData(data: any): Promise<void> {
        await this.send('data', data);
    }
}