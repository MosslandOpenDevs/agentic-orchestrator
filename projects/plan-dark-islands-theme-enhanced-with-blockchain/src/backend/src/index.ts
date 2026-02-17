import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { Server } from 'ws';
import http from 'http';

const app = express();
const server = http.createServer(app);
const wss = new Server({ server });

app.use(cors());
app.use(bodyParser.json());

// Graceful shutdown handling
function gracefulShutdown(signal: string) {
    console.log(`Received ${signal} signal, shutting down gracefully.`);
    wss.clients.forEach(client => client.close());
    server.close(() => process.exit(0));
}

process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));

// Environment variable configuration
const PORT = process.env.PORT || 3000;

app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.error(err.stack);
    res.status(500).send({ error: 'Something broke!' });
});

// Request logging
app.use((req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

// Health check endpoint
app.get('/health', (req: express.Request, res: express.Response) => {
    res.send({ status: 'ok' });
});

wss.on('connection', ws => {
    ws.on('message', message => console.log(`Received: ${message}`));
    ws.on('close', () => console.log('Client disconnected'));
});

server.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});