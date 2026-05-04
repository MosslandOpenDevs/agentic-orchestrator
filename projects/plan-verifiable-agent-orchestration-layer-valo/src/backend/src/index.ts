import express, { Express, Request, Response, Router } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { WebSocketServer } from 'ws';
import { WebSocket } from 'ws';
import { Config } from './config';
import { logger } from './utils/logger';
import { healthCheck } from './routes/health';
import { agentReceiptsRouter } from './routes/agentReceipts';
import { errorMiddleware } from './middleware/error';
import { requestLoggingMiddleware } from './middleware/requestLogging';
import { gracefulShutdown } from './utils/gracefulShutdown';

export class App {
    private app: Express;
    private server: WebSocketServer;
    private port: number;
    private config: Config;

    constructor(config: Config) {
        this.config = config;
        this.app = express();
        this.app.use(helmet());
        this.app.use(cors());
        this.app.use(express.json());
        this.app.use(morgan('combined', { stream: logger.stream }));

        this.app.use('/health', healthCheck);
        this.app.use('/agentReceipts', agentReceiptsRouter);

        this.app.use(errorMiddleware);

        this.setupGracefulShutdown();

        this.port = this.config.port;
    }

    private setupGracefulShutdown() {
        process.on('SIGINT', () => {
            logger.info('Received SIGINT (Ctrl+C).');
            gracefulShutdown(this.app);
        });

        process.on('SIGTERM', () => {
            logger.info('Received SIGTERM.');
            gracefulShutdown(this.app);
        });
    }

    public listen(): Express {
        this.app.listen(this.port, () => {
            logger.info(`Server listening on port ${this.port}`);
        });
        return this.app;
    }

    public getWebSocketServer(): WebSocketServer {
        this.server = new WebSocketServer({ port: this.config.wsPort || this.port });

        this.server.on('connection', (ws: WebSocket, req: Request) => {
            logger.info('Client connected via WebSocket');

            ws.on('message', (data: string) => {
                logger.info(`Received message from client: ${data}`);
                ws.send(`Server received: ${data}`);
            });

            ws.on('close', () => {
                logger.info('Client disconnected via WebSocket');
            });
        });

        return this.server;
    }
}

// Example usage (for demonstration purposes - not part of the core App class)
if (require.main === module) {
    const config = new Config();
    const app = new App(config);
    const server = app.getWebSocketServer();
    const expressApp = app.listen();

    // Keep the process alive (for demonstration)
    setInterval(() => {
        // Do something to prevent the process from exiting
    }, 5000);
}

// config.ts
export class Config {
    public port: number;
    public wsPort: number;
    // Add other configuration options here
}

// utils/logger.ts
import 'winston';

const logger = winston.createLogger({
    level: 'info',
    format: Winston.formats.combine([
        Winston.formats.timestamp(),
        Winston.formats.json(),
    ]),
    transports: [
        new Winston.transports.Console(),
        new Winston.transports.File({ filename: 'app.log' }),
    ],
});

export { logger };

// utils/gracefulShutdown.ts
import { app } from '../app';

async function gracefulShutdown(app: Express) {
    return new Promise((resolve, reject) => {
        app.close(() => {
            logger.info('Server shut down gracefully');
            resolve();
        });
    });
}

export { gracefulShutdown };

// routes/health.ts
import express from 'express';

export const healthCheck = express.Router();

healthCheck.get('/', (req, res) => {
    res.status(200).json({ status: 'healthy', version: '1.0.0' });
});

// routes/agentReceipts.ts
import express from 'express';

export const agentReceiptsRouter = express.Router();

agentReceiptsRouter.get('/', (req, res) => {
    res.status(200).json({ message: 'Agent Receipts data' });
});

// middleware/error.ts
import { logger } from '../utils/logger';

export const errorMiddleware = (err: any, req: any, res: any, next: any) => {
    logger.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
};

// middleware/requestLogging.ts
import { logger } from '../utils/logger';

export const requestLoggingMiddleware = (req: any, res: any, next: any) => {
    const start = Date.now();
    logger.info(`[${req.method}] ${req.url}`);
    next();
    const end = Date.now();
    logger.info(`[${req.method}] ${req.url} - Request took ${end - start}ms`);
};