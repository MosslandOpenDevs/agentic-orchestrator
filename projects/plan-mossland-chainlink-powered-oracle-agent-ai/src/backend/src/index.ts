import express, { Express, Request, Response, Router } from 'express';
import cors from 'cors';
import { json } from 'express';
import morgan from 'morgan';
import { PrismaClient } from '@prisma/client';
import OpenAI from 'openai';
import WebSocket from 'ws';
import { ChainlinkDataFeed } from './types';

const app: Express = express();
const prisma = new PrismaClient();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(json());
app.use(morgan('dev'));

// Environment variable configuration
require('dotenv').config();

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.status(200).send('OK');
});

// WebSocket endpoint
const wss = new WebSocket.Server({ port: process.env.WS_PORT || 8080 });

wss.on('connection', ws => {
  console.log('Client connected');

  ws.on('message', async message => {
    try {
      const data = JSON.parse(message);
      if (data.type === 'update') {
        // Handle updates from the backend (e.g., portfolio changes)
        console.log('Received update:', data);
        // Send the update back to the client
        ws.send(JSON.stringify({ type: 'update', data }));
      }
    } catch (error) {
      console.error('Error processing WebSocket message:', error);
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Routes
const router: Router = Router();

router.get('/data', async (req: Request, res: Response) => {
  try {
    const chainlinkData: ChainlinkDataFeed | null = await prisma.chainlinkDataFeed.findFirst({
      where: {
        name: 'BTC-USD',
      },
    });

    if (chainlinkData) {
      res.json(chainlinkData);
    } else {
      res.status(404).json({ message: 'Chainlink data not found' });
    }
  } catch (error) {
    console.error('Error fetching Chainlink data:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

router.post('/analyze', async (req: Request, res: Response) => {
  const { strategy, assets } = req.body;

  if (!strategy || !assets) {
    return res.status(400).json({ message: 'Strategy and assets are required' });
  }

  try {
    // Simulate OpenAI API call
    const response = await openai.Completion.create({
      engine: 'text-davinci-003',
      prompt: `Analyze the following investment strategy: ${strategy}.  Consider these assets: ${assets}.  Provide a recommendation for allocation.`,
      max_tokens: 150,
    });

    res.json({ analysis: response.choices[0].text });
  } catch (error) {
    console.error('Error calling OpenAI API:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

app.use(router);

// Graceful shutdown handling
process.on('SIGINT', () => {
  console.log('Shutting down gracefully...');
  prisma.$disconnect()
    .then(() => console.log('Disconnected from Prisma'))
    .catch(err => console.error('Error disconnecting from Prisma', err));
  process.exit();
});

// Start the server
app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});