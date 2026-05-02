import express, { Request, Response, Router } from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { PrismaClient } from '@prisma/client';
import { OpenAI } from 'openai';
import http from 'http';
import { WebSocketServer } from 'ws';

const app = express();
const port = process.env.PORT || 3000;

// Prisma Client
const prisma = new PrismaClient();

// CORS Configuration
app.use(cors());

// JSON Body Parser
app.use(bodyParser.json());

// Request Logging
app.use((req: Request, res: Response, next: any) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

// Error Handling Middleware
app.use((err: any, req: Request, res: Response, next: any) => {
    console.error(err.stack);
    res.status(500).send({ error: 'Something broke!' });
});

// Graceful Shutdown Handling
process.on('SIGINT', () => {
    console.log('Shutting down gracefully...');
    prisma.$disconnect()
        .then(() => {
            console.log('Disconnected from database.');
            process.exit(0);
        })
        .catch(err => {
            console.error('Error disconnecting from database:', err);
            process.exit(1);
        });
});

// Health Check Endpoint
app.get('/health', (req: Request, res: Response) => {
    res.status(200).send('OK');
});

// OpenAI Configuration
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

// Routes

// Example Route
app.get('/', (req: Request, res: Response) => {
    res.send('Hello World!');
});

// Example NFT Route (Placeholder)
app.post('/nft', async (req: Request, res: Response) => {
    try {
        const { prompt } = req.body;

        // Generate image using OpenAI
        const imageResponse = await openai.images.generate({
            prompt: prompt,
            n: 1,
            size: '512x512',
        });

        const imageUrl = imageResponse.data[0].url;

        // Store image URL and prompt in the database (example)
        const newNFT = await prisma.nft.create({
            data: {
                prompt: prompt,
                imageUrl: imageUrl,
            },
        });

        res.status(201).json(newNFT);
    } catch (error) {
        console.error('Error creating NFT:', error);
        res.status(500).json({ error: 'Failed to create NFT' });
    }
});

// WebSocket Server
const ws = new WebSocketServer({ port: process.env.PORT || 3001 });

ws.on('connection', (ws: WebSocket, req: http.IncomingMessage) => {
    console.log('Client connected via WebSocket');

    ws.on('message', async (data: string) => {
        console.log('Received message from client:', data);
        try {
            const parsedData = JSON.parse(data);
            // Handle incoming messages (e.g., update UI)
            console.log('Parsed data:', parsedData);
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected via WebSocket');
    });
});

// Start the server
app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});