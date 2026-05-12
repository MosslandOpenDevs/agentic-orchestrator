import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional
from collections import deque
import aioredis
import aiohttp
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
DEFAULT_RATE_LIMIT = 10  # Requests per second
CACHE_TTL = 60  # Cache expiration time in seconds
MAX_CACHE_SIZE = 100

# Environment variable names
WEBSOCKET_SERVER_URL = "WEBSOCKET_SERVER_URL"
RATE_LIMIT_KEY = "rate_limit"
CACHE_KEY_PREFIX = "cache:"


class WebSocketService:
    def __init__(self, server_url: str, rate_limit: int = DEFAULT_RATE_LIMIT):
        self.server_url = server_url
        self.rate_limit = rate_limit
        self.connected = False
        self.loop = asyncio.get_event_loop()
        self.cache = {}
        self.cache_queue = deque()
        self.redis_client = None
        self.rate_limit_lock = asyncio.Lock()
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    async def connect(self):
        try:
            reader, writer = await asyncio.open_connection(
                self.loop, aiohttp.ClientSession(), self.server_url, timeout=10
            )
            self.writer = writer
            self.reader = reader
            self.connected = True
            logging.info(f"Connected to WebSocket server: {self.server_url}")
        except asyncio.TimeoutError:
            logging.error(f"Connection to WebSocket server timed out.")
            self.connected = False
            return False
        except Exception as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            self.connected = False
            return False
        return True

    async def disconnect(self):
        if self.connected:
            try:
                self.writer.close()
                await self.writer.wait_closed()
                self.connected = False
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting from WebSocket server: {e}")

    async def send_message(self, message: str) -> bool:
        if not self.connected:
            logging.warning("Not connected to WebSocket server. Cannot send message.")
            return False

        await self.rate_limit_acquire()
        try:
            await self.writer.write(message.encode())
            await self.writer.drain()
            logging.debug(f"Sent message: {message}")
            return True
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False
        finally:
            await self.rate_limit_release()

    async def receive_message(self) -> Optional[str]:
        try:
            data = await self.reader.readline()
            if data:
                message = data.decode().strip()
                logging.debug(f"Received message: {message}")
                return message
            else:
                return None
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    async def rate_limit_acquire(self):
        async with self.rate_limit_lock:
            start_time = time.time()
            while self.retry_count < self.max_retries:
                try:
                    # Simulate rate limiting with Redis
                    if self.redis_client:
                        rate = await self.redis_client.get(RATE_LIMIT_KEY)
                        if rate is None:
                            rate = 1
                        else:
                            rate = int(rate)
                        if rate > 0:
                            await self.redis_client.set(RATE_LIMIT_KEY, rate - 1, ex=1)
                            return
                        else:
                            await asyncio.sleep(0.1)
                    else:
                        await asyncio.sleep(0.1)
                    self.retry_count += 1
                    await asyncio.sleep(0.1)
                except RedisError as e:
                    logging.error(f"Redis error during rate limiting: {e}")
                    await asyncio.sleep(self.retry_delay)
            logging.warning("Rate limit exceeded.")

    async def rate_limit_release(self):
        async with self.rate_limit_lock:
            await self.redis_client.delete(RATE_LIMIT_KEY)

    async def setup_redis(self):
        try:
            self.redis_client = aioredis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)))
            await self.redis_client.ping()
            logging.info("Connected to Redis.")
        except aioredis.exceptions.ConnectionError as e:
            logging.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def teardown_redis(self):
        if self.redis_client:
            try:
                await self.redis_client.close()
                logging.info("Disconnected from Redis.")
            except Exception as e:
                logging.error(f"Error disconnecting from Redis: {e}")

    async def run(self):
        await self.setup_redis()
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            await self.teardown_redis()


if __name__ == '__main__':
    # Example Usage (replace with your actual WebSocket server URL)
    ws_service = WebSocketService(server_url="ws://localhost:8000")
    asyncio.run(ws_service.run())