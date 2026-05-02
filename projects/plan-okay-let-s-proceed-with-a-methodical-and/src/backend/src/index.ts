import express, { Express, Request, Response, Router } from 'express';
import cors from 'cors';
import morgan from 'morgan';
import { PrismaClient } from '@prisma/client';
import { OpenAI } from 'openai';
import http from 'http';
import { WebSocketServer } from 'ws';

const app: Express = express();
const port = process.env.PORT || 3000;

// Prisma Client
const prisma = new PrismaClient();

// Middleware
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Error Handling Middleware
app.use((err: any, req: Request, res: Response, next: () => void) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Request Logging Middleware
app.use((req: Request, res: Response, next: () => void) => {
  console.log(`${req.method} ${req.url}`);
  next();
});

// Graceful Shutdown Handling
process.on('SIGINT', () => {
  console.log('Shutting down gracefully...');
  prisma.$disconnect()
    .then(() => console.log('Disconnected from database'))
    .catch((err) => console.error('Error disconnecting from database', err));
});

// Environment Variable Configuration
require('dotenv').config();

// Health Check Endpoint
app.get('/health', (req: Request, res: Response) => {
  res.status(200).send('OK');
});

// Routes

// Dummy Route
app.get('/', (req: Request, res: Response) => {
  res.send('Hello, World!');
});

// OpenAI API Integration
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

app.post('/generate-art', async (req: Request, res: Response) => {
  try {
    const prompt = req.body.prompt;
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    const response = await openai.images.generate({
      prompt: prompt,
      n: 1,
      size: '512x512',
      response_format: 'url',
    });

    const imageUrl = response.data[0].url;
    res.status(200).json({ imageUrl });
  } catch (error) {
    console.error('OpenAI Error:', error);
    res.status(500).json({ error: 'Failed to generate art' });
  }
});

// WebSocket Support
const wss = new WebSocketServer({ port: process.env.WS_PORT || 8080 });

wss.on('connection', ws => {
  console.log('Client connected');

  ws.on('message', message => {
    console.log('Received message:', message.toString());
    // Handle messages here (e.g., send updates)
    ws.send('Message received from server!');
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Start the server
const server = app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});