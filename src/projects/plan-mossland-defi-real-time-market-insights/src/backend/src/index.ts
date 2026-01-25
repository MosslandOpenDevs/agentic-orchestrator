import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { Server } from 'socket.io';
import http from 'http';

const app = express();
const server = new http.Server(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

app.use(cors());
app.use(bodyParser.json());

// Environment variables
const PORT = process.env.PORT || 3000;

// Middleware for request logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} - ${req.url}`);
  next();
});

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.send({ status: 'OK' });
});

// WebSocket support
io.on('connection', (socket) => {
  console.log('a user connected');
  socket.on('disconnect', () => {
    console.log('user disconnected');
  });
});

const gracefulShutdown = async () => {
  await new Promise<void>((resolve, reject) => {
    server.close((err: NodeJS.ErrnoException | null) => {
      if (err) {
        reject(err);
      } else {
        resolve();
      }
    });
  });
};

// Graceful shutdown handling
process.on('SIGINT', async () => {
  await gracefulShutdown();
  process.exit(0);
});

server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});