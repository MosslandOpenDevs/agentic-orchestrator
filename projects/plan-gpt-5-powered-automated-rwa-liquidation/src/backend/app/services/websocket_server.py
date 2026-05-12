import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
from collections import deque
import aioredis  # Use aioredis for asynchronous Redis
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, redis_host: str = os.environ.get("REDIS_HOST", "localhost"),
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 ws_url: str = os.environ.get("WS_URL", "ws://localhost:8765"),
                 rate_limit_interval: int = 1,  # seconds
                 max_rate: int = 10,
                 cache_ttl: int = 60,
                 retry_attempts: int = 3,
                 retry_delay: float = 1):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.ws_url = ws_url
        self.rate_limit_interval = rate_limit_interval
        self.max_rate = max_rate
        self.cache_ttl = cache_ttl
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self.redis = None
        self.ws = None
        self.rate_limit_queue = deque()
        self.connection_map: Dict[str, asyncio.Task] = {}

    async def connect(self):
        try:
            self.redis = await aioredis.from_url(f"redis://{self.redis_host}:{self.redis_port}")
            self.ws = await asyncio.open_connection(self.ws_url)
            self.ws.protocols = [asyncio.Protocol]
            logging.info(f"Connected to WebSocket server at {self.ws_url}")
        except RedisError as e:
            logging.error(f"Error connecting to Redis: {e}")
            raise
        except Exception as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            raise

    async def disconnect(self):
        if self.ws:
            try:
                await self.ws.close()
                await self.ws.wait_closed()
                logging.info("WebSocket connection closed.")
            except Exception as e:
                logging.error(f"Error closing WebSocket connection: {e}")
        if self.redis:
            try:
                await self.redis.close()
                logging.info("Redis connection closed.")
            except Exception as e:
                logging.error(f"Error closing Redis connection: {e}")

    async def send_message(self, message: str):
        try:
            if not self.ws:
                logging.warning("WebSocket connection not established.")
                return

            await self.ws.send(message)
            logging.debug(f"Sent message: {message}")
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    async def receive_message(self):
        try:
            if not self.ws:
                logging.warning("WebSocket connection not established.")
                return None

            return await self.ws.recv()
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    async def run(self):
        try:
            await self.connect()
            while True:
                # Example: Receive messages and send back (replace with your logic)
                received_message = await self.receive_message()
                if received_message:
                    await self.send_message(f"Received: {received_message}")
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Error in WebSocket service: {e}")
        finally:
            await self.disconnect()

    def rate_limit(self, client_id: str):
        """
        Rate limiting logic using Redis.
        """
        now = time.time()
        while len(self.rate_limit_queue) >= self.max_rate:
            wait_time = self.rate_limit_interval - (now - self.rate_limit_queue[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.time()
            self.rate_limit_queue.popleft()

        self.rate_limit_queue.append(now)

    def retry(self, func, *args, **kwargs):
        """
        Retry logic with exponential backoff.
        """
        for attempt in range(self.retry_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                await asyncio.sleep(self.retry_delay * 2 ** attempt)