import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional
from collections import deque
from ratelimit import RateLimitException
import aiohttp

# Configuration Constants
DEFAULT_RATE_LIMIT = 10  # Requests per second
MAX_RETRIES = 3
RETRY_DELAY = 1  # Seconds
CACHE_TTL = 60  # Seconds

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, rate_limit: int = DEFAULT_RATE_LIMIT):
        self.url = url
        self.rate_limit = rate_limit
        self.connected = False
        self.ws = None
        self.cache = {}  # Simple in-memory cache
        self.lock = asyncio.Lock()  # For thread-safe caching and rate limiting
        self.message_queue = deque()  # Queue for messages to be sent

    def _log(self, level: str, message: str):
        logging.log(level, message)

    async def _connect(self):
        try:
            async with aiohttp.ClientSession() as session:
                self.ws = await session.ws_connect(self.url)
                self._log(logging.INFO, f"Connected to WebSocket server at {self.url}")
                self.connected = True
        except aiohttp.ClientError as e:
            self._log(logging.ERROR, f"Failed to connect to WebSocket server: {e}")
            self.connected = False
            raise

    async def _disconnect(self):
        if self.ws:
            try:
                await self.ws.close()
                self._log(logging.INFO, "Disconnected from WebSocket server.")
                self.connected = False
            except Exception as e:
                self._log(logging.ERROR, f"Error during disconnection: {e}")
            finally:
                self.ws = None

    async def _send_message(self, message: str):
        if not self.connected:
            self._log(logging.WARNING, "Attempted to send message, but not connected.")
            return

        try:
            await self.ws.send(message)
            self._log(logging.DEBUG, f"Sent message: {message}")
        except Exception as e:
            self._log(logging.ERROR, f"Error sending message: {e}")

    async def _receive_message(self):
        try:
            message = await self.ws.recv()
            self._log(logging.DEBUG, f"Received message: {message}")
            return message
        except Exception as e:
            self._log(logging.ERROR, f"Error receiving message: {e}")
            return None

    async def _rate_limited_send(self, message: str):
        try:
            await asyncio.sleep(0.1)  # Allow rate limiting to work
            await self._send_message(message)
        except RateLimitException:
            self._log(logging.WARNING, "Rate limit exceeded. Retrying...")
            await asyncio.sleep(0.5)  # Exponential backoff
            await self._rate_limited_send(message)

    async def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            if key in self.cache:
                if time.time() - self.cache[key]['timestamp'] < CACHE_TTL:
                    self._log(logging.DEBUG, f"Data retrieved from cache for key: {key}")
                    return self.cache[key]['data']
                else:
                    self._log(logging.INFO, f"Cache expired for key: {key}. Removing.")
                    del self.cache[key]
            return None

    def _set_cached_data(self, key: str, data: Dict[str, Any]):
        with self.lock:
            self.cache[key] = {'data': data, 'timestamp': time.time()}

    async def run(self):
        try:
            await self._connect()
            while self.connected:
                # Check message queue
                if self.message_queue:
                    message = self.message_queue.popleft()
                    await self._rate_limited_send(message)
                await asyncio.sleep(0.1)  # Check every 100ms
        except Exception as e:
            self._log(logging.ERROR, f"An unexpected error occurred: {e}")
        finally:
            await self._disconnect()

    def send_message(self, message: str):
        asyncio.create_task(self._rate_limited_send(message))
        self.message_queue.append(message)

    def receive_message(self):
        return asyncio.create_task(self._receive_message())

    def clear_message_queue(self):
        self.message_queue = deque()