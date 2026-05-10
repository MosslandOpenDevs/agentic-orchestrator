import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import aioredis
import aiohttp
from aiohttp import ClientSession
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, session_timeout: int = 60, retry_count: int = 3, retry_delay: float = 1.0, rate_limit: int = 10):
        self.url = url
        self.session_timeout = session_timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.request_count = 0
        self.connected = False
        self.redis_client = None
        self.aiohttp_session = None
        self.message_queue = deque()
        self.lock = asyncio.Lock()

    async def connect(self):
        try:
            self.redis_client = await aioredis.from_url(os.environ.get("REDIS_URL", "redis://localhost"), decode_responses=True)
            self.aiohttp_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout))
            self.connected = True
            logging.info(f"Connected to WebSocket server at {self.url}")
        except RedisError as e:
            logging.error(f"Error connecting to Redis: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        if self.redis_client:
            try:
                await self.redis_client.close()
                self.redis_client = None
            except Exception as e:
                logging.error(f"Error closing Redis connection: {e}")
        if self.aiohttp_session:
            try:
                await self.aiohttp_session.close()
                self.aiohttp_session = None
            except Exception as e:
                logging.error(f"Error closing aiohttp session: {e}")

    async def send_message(self, message: str):
        if not self.connected:
            logging.warning("Not connected to WebSocket server. Message dropped.")
            return

        if self.request_count >= self.rate_limit:
            await asyncio.sleep(1.0)  # Simple rate limiting
            return

        self.request_count += 1
        start_time = time.time()
        try:
            async with self.aiohttp_session.post(self.url, data=message.encode(), headers={'Content-Type': 'text/plain'}) as response:
                if response.status == 200:
                    logging.debug(f"Message sent successfully: {message}")
                else:
                    logging.error(f"Failed to send message: {message}, Status code: {response.status}")
        except aiohttp.ClientError as e:
            logging.error(f"aiohttp error sending message: {e}")
            await self.retry_message(message)
        except Exception as e:
            logging.error(f"Unexpected error sending message: {e}")
            await self.retry_message(message)

    async def receive_message(self):
        try:
            while True:
                try:
                    message = await asyncio.wait_for(self.redis_client.blpop(timeout=1), 1)
                    if message:
                        data = message[1]
                        logging.info(f"Received message: {data}")
                        self.message_queue.append(data)
                        break
                except RedisError as e:
                    logging.error(f"Redis error receiving message: {e}")
                    await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(f"Error receiving message: {e}")

    async def retry_message(self, message: str):
        for i in range(self.retry_count):
            await asyncio.sleep(self.retry_delay * (i + 1))
            try:
                await self.send_message(message)
                return
            except Exception as e:
                logging.warning(f"Retry failed for message {message}: {e}")

    async def run(self):
        await self.connect()
        receiver_task = asyncio.create_task(self.receive_message())
        sender_task = asyncio.create_task(self.send_message("Hello, WebSocket!"))
        await asyncio.gather(receiver_task, sender_task)
        await self.disconnect()

    def get_message_queue(self) -> list:
        with self.lock:
            return list(self.message_queue)