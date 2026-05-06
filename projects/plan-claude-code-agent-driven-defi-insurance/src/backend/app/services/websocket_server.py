import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import aioredis
import aiohttp
from aioredis.exceptions import RedisError

# Configuration Constants
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds
DEFAULT_RATE_LIMIT_MAX = 10  # requests
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 1  # seconds

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, rate_limit_window: int = DEFAULT_RATE_LIMIT_WINDOW,
                 rate_limit_max: int = DEFAULT_RATE_LIMIT_MAX,
                 retry_count: int = DEFAULT_RETRY_COUNT,
                 retry_delay: int = DEFAULT_RETRY_DELAY):
        self.url = url
        self.rate_limit_window = rate_limit_window
        self.rate_limit_max = rate_limit_max
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.request_queue = deque()
        self.lock = asyncio.Lock()
        self.redis_client = None
        self.session = None
        self.cache = {}  # Simple in-memory cache

    def connect(self):
        """Connects to the WebSocket server."""
        try:
            self.redis_client = aioredis.from_url(os.environ.get("REDIS_URL", "redis://localhost"), decode_responses=True)
            self.session = aiohttp.ClientSession()
            logging.info(f"Connected to WebSocket server at {self.url}")
        except RedisError as e:
            logging.error(f"Error connecting to Redis: {e}")
            raise

    def disconnect(self):
        """Disconnects from the WebSocket server."""
        if self.redis_client:
            try:
                self.redis_client.close()
                logging.info("Disconnected from Redis.")
            except RedisError as e:
                logging.error(f"Error disconnecting from Redis: {e}")
        if self.session:
            self.session.close()
            logging.info("Disconnected from WebSocket session.")

    def send_message(self, message: str) -> bool:
        """Sends a message to the WebSocket server with rate limiting and retry logic."""
        with self.lock:
            if len(self.request_queue) >= self.rate_limit_max:
                logging.warning("Rate limit exceeded. Message dropped.")
                return False

            self.request_queue.append(message)
            # Simulate a transient failure for testing
            # time.sleep(0.1)  # Simulate network latency
            
            for attempt in range(self.retry_count):
                try:
                    async with self.session.post(self.url, data=message.encode(), allow_redirects=True) as response:
                        if response.status == 200:
                            logging.debug(f"Message sent successfully: {message}")
                            return True
                        else:
                            logging.warning(f"Failed to send message: {message}, Status code: {response.status}, Content: {await response.text()}")
                            break  # Exit retry loop on failure
                except aiohttp.ClientError as e:
                    logging.error(f"Aiohttp ClientError: {e}")
                    if attempt == self.retry_count - 1:
                        logging.warning(f"Max retries reached for message: {message}")
                        return False
                    time.sleep(self.retry_delay)
            return False

    def get_data(self, key: str) -> Optional[str]:
        """Retrieves data from the cache."""
        try:
            return self.cache.get(key)
        except Exception as e:
            logging.error(f"Error retrieving data from cache: {e}")
            return None

    def set_data(self, key: str, value: str):
        """Sets data in the cache."""
        self.cache[key] = value

    async def run(self):
        """Main asynchronous loop for handling messages."""
        await self.connect()
        while True:
            if not self.request_queue:
                await asyncio.sleep(1)  # Wait for messages
                continue

            message = self.request_queue.popleft()
            self.send_message(message)
            await asyncio.sleep(0.1)  # Adjust sleep time as needed

async def main():
    # Example Usage
    ws_service = WebSocketService(url="ws://localhost:8000")  # Replace with your WebSocket URL
    ws_service.connect()
    
    # Simulate sending messages
    for i in range(5):
        await ws_service.send_message(f"Message {i}")
        await asyncio.sleep(0.5)

    ws_service.disconnect()

if __name__ == "__main__":
    asyncio.run(main())