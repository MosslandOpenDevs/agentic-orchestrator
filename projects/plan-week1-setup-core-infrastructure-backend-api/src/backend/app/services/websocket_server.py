import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import aioredis  # Use aioredis for Redis
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, redis_host: str = os.environ.get("REDIS_HOST", "localhost"),
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 ws_url: str = os.environ.get("WS_URL", "ws://localhost:8000"),
                 rate_limit_interval: int = 1,  # seconds
                 retry_count: int = 3,
                 retry_delay: float = 0.5):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.ws_url = ws_url
        self.rate_limit_interval = rate_limit_interval
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.connected_clients: Dict[str, asyncio.WebSocketClient] = {}
        self.client_lock = asyncio.Lock()
        self.redis_client = None
        self.last_activity_time = time.time()

    async def connect(self):
        try:
            self.redis_client = aioredis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)
            await self.redis_client.ping()
            logging.info("Connected to Redis.")
        except RedisError as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        if self.redis_client:
            try:
                await self.redis_client.close()
                logging.info("Disconnected from Redis.")
            except RedisError as e:
                logging.error(f"Error closing Redis connection: {e}")

    async def send_message(self, client: asyncio.WebSocketClient, message: str):
        try:
            await client.send(message)
            logging.debug(f"Sent message to {client.id}: {message}")
        except Exception as e:
            logging.error(f"Error sending message to client {client.id}: {e}")

    async def receive_message(self, client: asyncio.WebSocketClient):
        try:
            async for msg in client:
                if msg:
                    logging.debug(f"Received message from {client.id}: {msg}")
                    # Process message here - could include rate limiting, caching, etc.
                    await self.process_message(client, msg)
        except Exception as e:
            logging.error(f"Error receiving message from client {client.id}: {e}")
        finally:
            await self.disconnect_client(client)

    async def connect_client(self, client: asyncio.WebSocketClient):
        with self.client_lock:
            self.connected_clients[client.id] = client
            logging.info(f"Client {client.id} connected.")

    async def disconnect_client(self, client: asyncio.WebSocketClient):
        with self.client_lock:
            if client.id in self.connected_clients:
                del self.connected_clients[client.id]
                logging.info(f"Client {client.id} disconnected.")

    async def process_message(self, client: asyncio.WebSocketClient, message: str):
        # Example processing - could be expanded with rate limiting, caching, etc.
        # This is just a placeholder.
        await self.send_message(client, f"Received: {message}")

    async def run(self):
        await self.connect()
        try:
            # Example WebSocket client connection
            ws_client = await asyncio.wrap_future(
                asyncio.open_connection(
                    "localhost", 8000
                )
            )
            await self.connect_client(ws_client)
            await self.receive_message(ws_client)

        finally:
            await self.disconnect()

if __name__ == "__main__":
    service = WebSocketService()
    asyncio.run(service.run())