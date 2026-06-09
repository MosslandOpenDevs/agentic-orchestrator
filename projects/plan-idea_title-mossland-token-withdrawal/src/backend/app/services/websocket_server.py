import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
from collections import deque
from urllib.parse import urlparse, parse_qs
import aiohttp
import aioredis
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, websocket_url: str, redis_host: str, redis_port: int, redis_db: int,
                 rate_limit_max_requests: int = 10, rate_limit_window_seconds: int = 5,
                 cache_ttl: int = 60):
        """
        Initializes the WebSocketService.

        Args:
            websocket_url: The URL of the WebSocket server.
            redis_host: Hostname of the Redis server.
            redis_port: Port number of the Redis server.
            redis_db: Database number of the Redis server.
            rate_limit_max_requests: Maximum number of requests allowed within the window.
            rate_limit_window_seconds: Window in seconds for rate limiting.
            cache_ttl: Time-to-live (TTL) for cached data in seconds.
        """
        self.websocket_url = websocket_url
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.rate_limit_max_requests = rate_limit_max_requests
        self.rate_limit_window_seconds = rate_limit_window_seconds
        self.cache_ttl = cache_ttl
        self.redis_client = None
        self.cache = {}
        self.request_counts = {}  # Use a dictionary for rate limiting
        self.lock = asyncio.Lock()
        self.connected_clients = set()

    async def connect(self):
        """
        Establishes a WebSocket connection.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.websocket_url) as ws:
                    self.connected_clients.add(ws)
                    logging.info(f"Connected to WebSocket server at {self.websocket_url}")
                    yield ws
        except aiohttp.ClientError as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            self.disconnect_all()
        finally:
            self.connected_clients.remove(ws)

    async def disconnect_all(self):
        """
        Disconnects all connected clients.
        """
        logging.info("Disconnecting all clients...")
        for ws in self.connected_clients:
            try:
                await ws.close()
            except Exception as e:
                logging.error(f"Error closing WebSocket connection: {e}")
        self.connected_clients.clear()

    async def receive_messages(self, ws):
        """
        Receives messages from the WebSocket server.
        """
        try:
            async for message in ws:
                if message:
                    try:
                        data = json.loads(message)
                        logging.debug(f"Received message: {data}")
                        # Process the message here (e.g., update cache, trigger action)
                        # Example:
                        # self.cache[data['id']] = data['data']
                    except json.JSONDecodeError:
                        logging.warning(f"Received invalid JSON message: {message}")
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
        finally:
            self.connected_clients.remove(ws)

    async def send_message(self, ws, message):
        """
        Sends a message to the WebSocket server.
        """
        try:
            if ws and ws.open:
                await ws.send(message)
                await ws.drain()  # Ensure the message is sent
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    async def rate_limit(self, client_id):
        """
        Implements rate limiting for incoming requests.
        """
        with self.lock:
            if client_id not in self.request_counts:
                self.request_counts[client_id] = 0
            self.request_counts[client_id] += 1
            if self.request_counts[client_id] > self.rate_limit_max_requests:
                wait_time = (self.request_counts[client_id] - self.rate_limit_max_requests) * self.rate_limit_window_seconds / self.rate_limit_max_requests
                await asyncio.sleep(wait_time)
                self.request_counts[client_id] = 1  # Reset count after waiting

    async def run(self):
        """
        Main function to run the WebSocket service.
        """
        try:
            # Initialize Redis connection
            await self.initialize_redis()
            # Create a generator to yield the WebSocket connection
            async for ws in self.connect():
                # Rate limiting and message receiving
                await self.rate_limit(str(id(ws)))
                await self.receive_messages(ws)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            await self.disconnect_all()

    async def initialize_redis(self):
        """
        Initializes the Redis connection.
        """
        try:
            r = aioredis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)
            self.redis_client = r
            # Example: Set a key with a TTL
            # await r.setex('mykey', self.cache_ttl, 'myvalue')
        except Exception as e:
            logging.error(f"Error initializing Redis: {e}")

    async def cleanup(self):
        """
        Closes the Redis connection.
        """
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logging.error(f"Error closing Redis connection: {e}")
            self.redis_client = None


if __name__ == '__main__':
    # Example Usage (replace with your actual WebSocket URL and Redis settings)
    websocket_url = os.environ.get("WEBSOCKET_URL", "ws://localhost:8080")
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    redis_db = int(os.environ.get("REDIS_DB", 0))
    rate_limit_max_requests = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", 10))
    rate_limit_window_seconds = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", 5))
    cache_ttl = int(os.environ.get("CACHE_TTL", 60))

    service = WebSocketService(websocket_url, redis_host, redis_port, redis_db,
                               rate_limit_max_requests, rate_limit_window_seconds, cache_ttl)
    asyncio.run(service.run())