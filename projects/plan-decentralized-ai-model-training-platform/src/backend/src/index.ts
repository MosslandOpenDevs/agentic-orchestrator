import express, { Express, Request, Response, Router } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { MongoClient } from 'mongodb';
import { WebSocketServer } from 'ws';
import { v4 as uuidv4 } from 'uuid';

// Configuration
const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Initialize Express app
const app: Express = express();
app.use(cors());
app.use(helmet());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined'));

// Database connection
const db = new MongoClient(MONGO_URI);
db.connect();

// Middleware
app.use((err: any, req: Request, res: Response, next: any) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something broke!' });
});

// Routes
const router: Router = Router();

router.get('/', (req: Request, res: Response) => {
    res.send('Genesis AI API');
});

router.post('/models', async (req: Request, res: Response) => {
    try {
        const { name, description, modelType, price } = req.body;

        if (!name || !description || !modelType || !price) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        const model = {
            id: uuidv4(),
            name,
            description,
            modelType,
            price,
            createdAt: new Date(),
        };

        const modelResult = await db.db('genesisai').collection('models').insertOne(model);

        res.status(201).json(modelResult.insertedId);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to create model' });
    }
});

router.get('/models', async (req: Request, res: Response) => {
    try {
        const models = await db.db('genesisai').collection('models').find().toArray();
        res.json(models);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to retrieve models' });
    }
});

router.get('/models/:id', async (req: Request, res: Response) => {
    try {
        const id = req.params.id;
        const model = await db.db('genesisai').collection('models').findOne({ id });

        if (!model) {
            return res.status(404).json({ error: 'Model not found' });
        }

        res.json(model);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to retrieve model' });
    }
});

// Health Check Endpoint
router.get('/health', (req: Request, res: Response) => {
    res.status(200).send('OK');
});

// WebSocket Server
const wss = new WebSocketServer({ port: PORT + 1 });

wss.on('connection', ws => {
    console.log('Client connected');

    ws.on('message', message => {
        console.log('Received message:', message.toString());
        ws.send(`Server received: ${message.toString()}`);
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Apply routes
app.use('/', router);

// Graceful Shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down...');
    try {
        await db.close();
        app.close();
    } catch (error) {
        console.error('Error during shutdown:', error);
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Genesis AI API listening on port ${PORT}`);
});