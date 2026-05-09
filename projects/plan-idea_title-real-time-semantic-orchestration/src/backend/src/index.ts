import express, { Express, Request, Response, Router } from 'express';
import cors from 'cors';
import morgan from 'morgan';
import { OpenAI } from 'openai';
import { WebSocketServer } from 'ws';
import { Client } from 'websocket';
import { Configuration, Signer } from 'ethers';
import { Polygon } from 'ethers.js';
import * as dotenv from 'dotenv';
dotenv.config();

// Configuration
const port = process.env.PORT || 3000;
const openaiApiKey = process.env.OPENAI_API_KEY || 'YOUR_OPENAI_API_KEY';
const polygonMaticApiKey = process.env.POLYGON_MATIC_API_KEY || 'YOUR_POLYGON_MATIC_API_KEY';

// Initialize OpenAI
const openai = new OpenAI({ apiKey: openaiApiKey });

// Initialize Polygon
const polygon = new Polygon(polygonMaticApiKey);

// Create Express app
const app: Express = express();
app.use(cors());
app.use(express.json());
app.use(morgan('combined'));

// Error handling middleware
app.use((err: any, req: Request, res: Response, next: () => void) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong' });
});

// Request logging middleware
app.use((req: Request, res: Response, next: () => void) => {
  console.log(`${req.method} ${req.url}`);
  next();
});

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.status(200).send('OK');
});

// Example API endpoint
app.get('/api/hello', async (req: Request, res: Response) => {
  try {
    const completion = await openai.completions.create({
      model: 'text-davinci-003',
      prompt: 'Write a short story about a friendly AI.',
      max_tokens: 150,
    });
    res.json({ message: completion.choices[0].text });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to get completion' });
  }
});

// WebSocket server
const wss = new WebSocketServer({ port });

wss.on('connection', ws => {
  console.log('Client connected');

  ws.on('message', async event => {
    const message = event.data;
    console.log('Received message:', message);

    try {
      const response = await openai.completions.create({
        model: 'text-davinci-003',
        prompt: `Respond to the following message: ${message}`,
        max_tokens: 50,
      });
      ws.send(response.choices[0].text);
    } catch (error) {
      console.error(error);
      ws.send('Error from OpenAI');
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Graceful shutdown handling
process.on('SIGINT', () => {
  console.log('Shutting down...');
  wss.close(() => {
    console.log('WebSocket server closed');
  });
  process.exit();
});

// Start the server
app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});