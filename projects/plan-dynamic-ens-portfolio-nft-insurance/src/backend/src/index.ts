import express, { Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { Router } from 'express';
import { PrismaClient } from '@prisma/client';
import { ethers } from 'ethers';
import { CoingeckoAPI } from './coingecko';
import { EtherscanAPI } from './etherscan';
import { AlchemyAPI } from './alchemy';
import { WebSocket } from 'ws';
import { setInterval, clearInterval } from 'timers';

// Prisma Client
const prisma = new PrismaClient();

// Initialize external services
const coingecko = new CoingeckoAPI();
const etherscan = new EtherscanAPI();
const alchemy = new AlchemyAPI();

// Express App Setup
const app = express();
app.use(cors());
app.use(helmet());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev'));

// Logging Middleware
app.use((req: Request, res: Response, next: () => void) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

// Error Handling Middleware
app.use((err: any, req: Request, res: Response, next: () => void) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong' });
});

// Health Check Endpoint
app.get('/health', (req: Request, res: Response) => {
    res.status(200).send('OK');
});

// Routes

// Portfolio Routes
const portfolioRouter = new Router();

portfolioRouter.get('/', async (req: Request, res: Response) => {
    try {
        const portfolios = await prisma.portfolio.findMany();
        res.status(200).json(portfolios);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch portfolios' });
    }
});

portfolioRouter.get('/:id', async (req: Request, res: Response) => {
    try {
        const portfolio = await prisma.portfolio.findUnique({
            where: {
                id: parseInt(req.params.id),
            },
        });
        if (!portfolio) {
            return res.status(404).json({ error: 'Portfolio not found' });
        }
        res.status(200).json(portfolio);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch portfolio' });
    }
});

portfolioRouter.post('/', async (req: Request, res: Response) => {
    try {
        const portfolioData = req.body;
        const newPortfolio = await prisma.portfolio.create({
            data: portfolioData,
        });
        res.status(201).json(newPortfolio);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to create portfolio' });
    }
});

portfolioRouter.put('/:id', async (req: Request, res: Response) => {
    try {
        const portfolioId = parseInt(req.params.id);
        const updateData = req.body;
        const updatedPortfolio = await prisma.portfolio.update({
            where: {
                id: portfolioId,
            },
            data: updateData,
        });
        res.status(200).json(updatedPortfolio);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to update portfolio' });
    }
});

portfolioRouter.delete('/:id', async (req: Request, res: Response) => {
    try {
        const portfolioId = parseInt(req.params.id);
        const deletedPortfolio = await prisma.portfolio.delete({
            where: {
                id: portfolioId,
            },
        });
        res.status(200).json(deletedPortfolio);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to delete portfolio' });
    }
});

app.use(portfolioRouter);

// WebSocket endpoint for real-time updates (example)
const wss = new WebSocketServer({ port: 8081 });

wss.on('connection', ws => {
    console.log('Client connected');

    // Simulate real-time portfolio updates
    setInterval(async () => {
        const portfolio = await prisma.portfolio.findFirst();
        if (portfolio) {
            ws.send(JSON.stringify({ type: 'portfolioUpdate', data: portfolio }));
        }
    }, 5000);

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Graceful Shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down...');
    await prisma.$disconnect();
    process.exit();
});

// Export the app
export default app;