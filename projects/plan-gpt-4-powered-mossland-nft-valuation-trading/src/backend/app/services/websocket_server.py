import asyncio
import json
import logging
import time
from typing import Callable, Dict, Any, Optional
from collections import deque
import os
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable names
WS_URL = os.environ.get("WS_URL", "ws://localhost:8765")
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 10))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 5))
MAX_CACHE_SIZE = int(os.environ.get("MAX_CACHE_SIZE", 100))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", 0.5))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))

# Global cache (using a deque for LRU)
cache = deque(maxlen=MAX_CACHE_SIZE)
cache_lock = asyncio.Lock()


class WebSocketService:
    def __init__(self):
        self.ws: Optional[asyncio.Client] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.rate_limit_count: int = 0
        self.retry_count: int = 0

    async def connect(self):
        try:
            parsed_url = urlparse(WS_URL)
            ws_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            self.ws = asyncio.ClientProtocol(
                protocol=asyncio.Protocol
                (
                    lambda self: self.connection_opened(self),
                    lambda self, msg: self.connection_closed(self),
                    lambda self: self.connection_data(self),
                )
            )
            await self.ws.connect(ws_url)
            logging.info("Connected to WebSocket server.")
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            raise

    async def disconnect(self):
        if self.ws:
            try:
                await self.ws.disconnect()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Failed to disconnect from WebSocket server: {e}")
            finally:
                self.ws = None

    async def send_message(self, message: Dict[str, Any]):
        if not self.ws:
            logging.warning("WebSocket is not connected. Cannot send message.")
            return

        try:
            await self.ws.send_json(message)
            logging.debug(f"Sent message: {message}")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")
            if self.retry_attempt(e):
                await asyncio.sleep(RETRY_DELAY)
                await self.send_message(message)
            else:
                raise

    async def receive_message(self):
        try:
            message = await self.ws.recv_json()
            logging.debug(f"Received message: {message}")
            await self.process_message(message)
        except Exception as e:
            logging.error(f"Failed to receive message: {e}")
            if self.retry_attempt(e):
                await asyncio.sleep(RETRY_DELAY)
                await self.receive_message()
            else:
                raise

    async def process_message(self, message: Dict[str, Any]):
        # Implement message processing logic here.
        # Example: Store in cache
        with self.cache_lock:
            cache.append(message)
            if len(cache) > MAX_CACHE_SIZE:
                cache.popleft()

    def retry_attempt(self, exception: Exception) -> bool:
        self.retry_count = 0
        if self.retry_count < MAX_RETRIES:
            self.retry_count += 1
            logging.warning(f"Transient failure. Retry attempt {self.retry_count}/{MAX_RETRIES}")
            return True
        return False

    async def run(self):
        try:
            await self.connect()
            while True:
                await asyncio.sleep(1)  # Adjust sleep duration as needed
                if self.ws:
                    await self.receive_message()
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            await self.disconnect()


async def example_usage():
    service = WebSocketService()
    asyncio.create_task(service.run())

    await asyncio.sleep(5)  # Allow time for the server to respond

    message = {"type": "update", "data": {"value": 42}}
    await service.send_message(message)

    await asyncio.sleep(10)

    print("Example finished.")


if __name__ == "__main__":
    asyncio.run(example_usage())