import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional
from collections import deque
import aioredis
import websockets
import rate_limiter
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
WEBSOCKET_URL = os.environ.get("WEBSOCKET_URL", "ws://localhost:8765")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
RATE_LIMIT_RATE = int(os.environ.get("RATE_LIMIT_RATE", 10))  # Requests per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds
CACHE_TTL = int(os.environ.get("CACHE_TTL", 60))  # Cache expiration in seconds

# Rate limiter
rate_limiter_instance = rate_limiter.RateLimiter(rate=RATE_LIMIT_RATE, window=RATE_LIMIT_WINDOW)

# Redis connection
redis_client = None
try:
    redis_client = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)
except RedisError as e:
    logging.error(f"Failed to connect to Redis: {e}")
    raise

# Cache (using Redis)
cache = {}

# Retry logic
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Message queue (using Redis)
message_queue = deque()

# Callback queue for handling messages
callback_queue = asyncio.Queue()


class WebSocketService:
    def __init__(self):
        self.websocket_url = WEBSOCKET_URL
        self.callbacks: Dict[str, Callable[[str], None]] = {}
        self.retry_count = 0

    async def connect(self):
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                logging.info(f"Connected to WebSocket server at {self.websocket_url}")
                while True:
                    try:
                        message = await websocket.recv()
                        logging.info(f"Received message: {message}")
                        self.process_message(message)
                    except websockets.exceptions.ConnectionClosedError as e:
                        logging.error(f"WebSocket connection closed: {e}")
                        break
                    except Exception as e:
                        logging.error(f"Error receiving message: {e}")
                        break
        except websockets.exceptions.ConnectionRefusedError as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            # Handle connection refused error - potentially retry or log
            raise

    def register_callback(self, message_type: str, callback: Callable[[str], None]):
        self.callbacks[message_type] = callback

    async def process_message(self, message: str):
        if message_type := os.environ.get("MESSAGE_TYPE") and message_type not in self.callbacks:
            logging.warning(f"Message type {message_type} not registered for callback.")
            return

        if message_type := os.environ.get("MESSAGE_TYPE"):
            if message_type in self.callbacks:
                self.callbacks[message_type](message)
            else:
                logging.warning(f"Message type {message_type} not registered.")
        else:
            logging.warning("No message type specified.")

    async def enqueue_message(self, message: str):
        message_queue.append(message)
        logging.info(f"Message enqueued: {message}")

    async def consume_messages(self):
        while True:
            if message_queue:
                message = message_queue.popleft()
                await self.process_message(message)
            else:
                await asyncio.sleep(1)

    async def cleanup(self):
        if redis_client:
            try:
                await redis_client.close()
                logging.info("Redis connection closed.")
            except Exception as e:
                logging.error(f"Error closing Redis connection: {e}")

    async def run(self):
        try:
            asyncio.create_task(self.connect())
            asyncio.create_task(self.consume_messages())
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            await self.cleanup()


if __name__ == "__main__":
    service = WebSocketService()
    asyncio.run(service.run())