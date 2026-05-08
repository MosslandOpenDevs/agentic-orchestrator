import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import aioredis
import websockets
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
DEFAULT_RATE_LIMIT = 10  # Requests per second
CACHE_TTL = 60  # Cache expiration time in seconds
MAX_CACHE_SIZE = 100

# Environment Variable Names
WEBSOCKET_SERVER_URI = "WEBSOCKET_SERVER_URI"
RATE_LIMIT_KEY = "rate_limit"
CACHE_KEY_PREFIX = "cache:"

class WebSocketService:
    def __init__(self, server_uri: str, rate_limit: int = DEFAULT_RATE_LIMIT):
        self.server_uri = server_uri
        self.rate_limit = rate_limit
        self.rate_limit_queue = deque()
        self.cache = {}
        self.redis_client = None
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds

    def connect(self):
        try:
            self.redis_client = aioredis.from_url(os.environ.get(WEBSOCKET_SERVER_URI, "ws://localhost:8765"))
            logging.info("Connected to Redis.")
        except RedisError as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise

    def disconnect(self):
        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None
            logging.info("Disconnected from Redis.")

    def _rate_limit(self, client_id: str) -> bool:
        """
        Implements rate limiting using Redis.
        """
        try:
            count = self.redis_client.get(RATE_LIMIT_KEY).decode(errors='ignore')
            if not count:
                self.redis_client.set(RATE_LIMIT_KEY, "1", ex=self.rate_limit)
                return True
            else:
                count = int(count) + 1
                if count > self.rate_limit:
                    count = 1
                self.redis_client.set(RATE_LIMIT_KEY, str(count), ex=self.rate_limit)
                return True
        except RedisError as e:
            logging.error(f"Rate limit error: {e}")
            return False

    def _cache_get(self, key: str) -> Optional[str]:
        """
        Retrieves data from the cache.
        """
        if key in self.cache:
            if time.time() - self.cache[key]['timestamp'] < CACHE_TTL:
                logging.debug(f"Cache hit for key: {key}")
                return self.cache[key]['value']
            else:
                logging.debug(f"Cache expired for key: {key}")
                del self.cache[key]
        return None

    def _cache_set(self, key: str, value: str, timestamp: float) -> None:
        """
        Sets data in the cache.
        """
        self.cache[key] = {'value': value, 'timestamp': timestamp}

    def handle_websocket(self, websocket: websockets.WebSocketClient, client_id: str):
        """
        Handles a single WebSocket connection.
        """
        logging.info(f"Client connected: {client_id}")
        self.rate_limit(client_id)

        try:
            while True:
                message = await websocket.recv()
                logging.info(f"Received message from {client_id}: {message}")

                # Simulate some processing
                processed_message = f"Processed: {message}"

                # Cache the processed message
                key = f"message:{client_id}"
                if self._cache_get(key):
                    processed_message = self._cache_get(key)
                else:
                    self._cache_set(key, processed_message, time.time())

                await websocket.send(processed_message)

        except websockets.exceptions.ConnectionClosedError as e:
            logging.warning(f"Connection closed for {client_id}: {e}")
        except Exception as e:
            logging.error(f"Error handling connection for {client_id}: {e}")
        finally:
            self.rate_limit(client_id)
            logging.info(f"Client disconnected: {client_id}")

    def start(self):
        """
        Starts the WebSocket server.
        """
        self.connect()
        try:
            async def accept_client():
                async for websocket, client_id in self.redis_client.bgetall(RATE_LIMIT_KEY).items():
                    if client_id:
                        await self.handle_websocket(websocket, client_id)

            asyncio.create_task(accept_client())
        except RedisError as e:
            logging.error(f"Redis error during server startup: {e}")
        finally:
            self.disconnect()

    def stop(self):
        """
        Stops the WebSocket server.
        """
        self.disconnect()

if __name__ == '__main__':
    # Example usage
    service = WebSocketService(server_uri="ws://localhost:8765")
    service.start()