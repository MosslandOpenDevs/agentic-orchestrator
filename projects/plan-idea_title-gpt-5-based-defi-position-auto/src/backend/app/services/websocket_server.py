import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import aioredis  # Use aioredis for asynchronous Redis
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, websocket_url: str, redis_host: str = "localhost", redis_port: int = 6379,
                 redis_db: int = 0, rate_limit_interval: int = 1, rate_limit_max: int = 10,
                 retry_attempts: int = 3, retry_delay: float = 1):
        self.websocket_url = websocket_url
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.rate_limit_interval = rate_limit_interval
        self.rate_limit_max = rate_limit_max
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.connected_clients = {}  # Store connected clients (client_id: websocket_object)
        self.rate_limits = {}  # Rate limiting per client
        self.redis_client = None
        self.logger = logging.getLogger(__name__)

        try:
            self.redis_client = aioredis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)
        except RedisError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def connect(self, client_id: str):
        """Connects to the WebSocket server."""
        try:
            # Simulate WebSocket connection (replace with actual WebSocket connection logic)
            self.logger.info(f"Connecting to WebSocket server for client: {client_id}")
            # Placeholder for WebSocket connection
            # await websocket.connect(self.websocket_url)
            self.connected_clients[client_id] = client_id  # Store client ID for now
            self.rate_limits[client_id] = 0
            self.logger.info(f"Client {client_id} connected successfully.")
        except Exception as e:
            self.logger.error(f"Error connecting to WebSocket for client {client_id}: {e}")
            self.disconnect(client_id)

    async def disconnect(self, client_id: str):
        """Disconnects from the WebSocket server."""
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
            self.rate_limits.pop(client_id, None)
            self.logger.info(f"Client {client_id} disconnected.")

    async def send_message(self, client_id: str, message: Any):
        """Sends a message to a connected client."""
        if client_id not in self.connected_clients:
            self.logger.warning(f"Client {client_id} not connected.")
            return

        # Rate limiting
        if self.rate_limits.get(client_id, 0) >= self.rate_limit_max:
            self.logger.warning(f"Rate limit exceeded for client {client_id}.")
            await asyncio.sleep(self.rate_limit_interval)
            self.rate_limits[client_id] = 0

        # Simulate sending message (replace with actual WebSocket sending logic)
        # await self.connected_clients[client_id].send(message)
        self.logger.info(f"Sent message to client {client_id}: {message}")

    async def receive_message(self, client_id: str):
        """Simulates receiving a message from a client."""
        # Placeholder for message receiving logic
        # message = await self.connected_clients[client_id].recv()
        self.logger.info(f"Received message from client {client_id}: {message}")
        return message

    async def handle_client(self, client_id: str):
        """Handles a single client connection."""
        try:
            # Simulate client activity
            for _ in range(5):
                message = await self.receive_message(client_id)
                if message:
                    await self.send_message(client_id, f"Received: {message}")
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
        finally:
            await self.disconnect(client_id)

    async def run(self):
        """Runs the WebSocket service."""
        # Simulate client connections
        # await asyncio.gather(*(self.connect(f"client-{i}") for i in range(5)))

        # Example usage:
        client_task1 = asyncio.create_task(self.handle_client("client-1"))
        client_task2 = asyncio.create_task(self.handle_client("client-2"))

        await asyncio.sleep(10)  # Run for 10 seconds
        client_task1.cancel()
        client_task2.cancel()
        await asyncio.gather(client_task1, client_task2, return_exceptions=True)

if __name__ == '__main__':
    # Example usage with environment variables
    websocket_url = os.environ.get("WEBSOCKET_URL", "ws://localhost:8000")
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    redis_db = int(os.environ.get("REDIS_DB", 0))
    rate_limit_interval = int(os.environ.get("RATE_LIMIT_INTERVAL", 1))
    rate_limit_max = int(os.environ.get("RATE_LIMIT_MAX", 10))
    retry_attempts = int(os.environ.get("RETRY_ATTEMPTS", 3))
    retry_delay = float(os.environ.get("RETRY_DELAY", 1))

    ws_service = WebSocketService(websocket_url, redis_host, redis_port, redis_db,
                                  rate_limit_interval, rate_limit_max, retry_attempts, retry_delay)
    try:
        asyncio.run(ws_service.run())
    except Exception as e:
        print(f"An error occurred: {e}")