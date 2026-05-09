import express, { Express, Request, Response, Router } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { Routes } from './routes';
import { WebSocket } from './websocket';
import { config } from './config';
import { errorHandler, requestLogger, healthCheck } from './middlewares';
import { WebSocketHandler } from './websocketHandler';

const app: Express = express();

// Middleware setup
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));

// Logging
app.use(requestLogger);

// Routes
app.use('/api', Routes);

// WebSocket
const ws = new WebSocket(app);

// Error handling
app.use(errorHandler);

// Health check
app.get('/health', healthCheck);

// Graceful shutdown
import gracefulShutdown from './gracefulShutdown';
gracefulShutdown(app);

export default app;

// config.ts
export const config = {
  port: process.env.PORT || 3000,
  environment: process.env.NODE_ENV || 'development',
  databaseUrl: process.env.DATABASE_URL || '',
  apiKey: process.env.API_KEY || '',
  claudeApiKey: process.env.CLAUDE_API_KEY || '',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  loggingLevel: process.env.LOGGING_LEVEL || 'dev',
  // Add other configuration options here
};

// routes.ts
import Router, { Router as ExpressRouter } from 'express';

const router: ExpressRouter = new Router();

// Dummy API route for demonstration
router.get('/hello', (req: Request, res: Response) => {
  res.json({ message: 'Hello from Mossland!' });
});

export const Routes = router;

// websocket.ts
import { WebSocketServer } from 'ws';
import { config } from './config';

const wss = new WebSocketServer({ port: config.port });

wss.on('connection', ws => {
  console.log('Client connected');

  ws.on('message', message => {
    console.log(`Received message from client: ${message}`);
    // Handle incoming messages here
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

export { wss };

// websocketHandler.ts
import { WebSocket } from 'ws';

export class WebSocketHandler {
  private ws: WebSocket;

  constructor(ws: WebSocket) {
    this.ws = ws;
  }

  public send(message: any) {
    this.ws.send(JSON.stringify(message));
  }

  public close() {
    this.ws.close();
  }
}

// middlewares/errorHandler.ts
import { Response, Request, NextFunction } from 'express';

export const errorHandler = (err: any, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!', stack: err.stack });
};

// middlewares/requestLogger.ts
import { Request, Response, NextFunction } from 'express';
import { config } from '../config';

interface LoggedRequest extends Request {
  log: (message: string, ...args: any[]) => void;
}

export const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  const log = (message: string, ...args: any[]) => {
    console.log(`[${config.environment}] ${new Date().toISOString()} - ${req.method} ${req.url} - ${message}`);
    if (args.length > 0) {
      console.log(...args);
    }
  };

  req['log'] = log;
  next();
};

// middlewares/healthCheck.ts
import { Request, Response } from 'express';

export const healthCheck = (req: Request, res: Response) => {
  res.status(200).json({ status: 'healthy', version: '1.0.0' });
};

// gracefulShutdown.ts
import { app } from '../app';
import { config } from '../config';

const gracefulShutdown = (app: any) => {
  process.on('SIGINT', () => {
    console.log('Shutting down gracefully...');
    app.close(() => {
      console.log('Server closed.');
      process.exit(0);
    });
  });

  process.on('SIGTERM', () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    app.close(() => {
      console.log('Server closed.');
      process.exit(0);
    });
  });
};