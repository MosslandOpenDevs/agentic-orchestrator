import express, { Request, Response, Router } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { MongoClient } from 'mongodb';
import { WebSocketServer } from 'ws';
import { v4 as uuidv4 } from 'uuid';
import dotenv from 'dotenv';

dotenv.config();

const app: Router = express();
const port = process.env.PORT || 3000;

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));

// Database Configuration
const mongoUri = process.env.MONGO_URI || 'mongodb://localhost:27017';
const dbName = process.env.DB_NAME || 'mossland';

let mongoClient: MongoClient;

async function connectToMongo() {
    try {
        mongoClient = new MongoClient(mongoUri);
        await mongoClient.connect();
        console.log('Connected to MongoDB');
    } catch (error) {
        console.error('Error connecting to MongoDB:', error);
    }
}

connectToMongo();

// Health Check Endpoint
app.get('/health', (req: Request, res: Response) => {
    res.status(200).send('OK');
});

// WebSocket Server
const wss = new WebSocketServer({ port: process.env.WS_PORT || 8080 });

wss.on('connection', ws => {
    console.log('Client connected via WebSocket');

    ws.on('message', async message => {
        try {
            const data = JSON.parse(message);
            console.log('Received message:', data);

            // Handle incoming messages (e.g., from the frontend)
            if (data.type === 'update') {
                // Process and send updates to connected clients
                console.log('Processing update:', data);
            }
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected via WebSocket');
    });
});

// Example API Endpoint (Placeholder)
app.get('/api/mossland-data', async (req: Request, res: Response) => {
    try {
        // Simulate fetching data from the database or external sources
        const data = {
            message: 'Hello from Mossland!',
            timestamp: new Date().toISOString()
        };
        res.json(data);
    } catch (error) {
        console.error('Error fetching data:', error);
        res.status(500).json({ error: 'Failed to fetch data' });
    }
});

// Graceful Shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down...');
    if (mongoClient) {
        try {
            await mongoClient.close();
            console.log('MongoDB connection closed');
        } catch (error) {
            console.error('Error closing MongoDB connection:', error);
        }
    }
    process.exit();
});

// Start the server
app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});