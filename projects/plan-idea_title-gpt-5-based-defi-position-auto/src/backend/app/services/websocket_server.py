import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional
from collections import deque
import json
import rate_limiter
from websockets import connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
WS_URL = os.environ.get("WS_URL", "ws://localhost:8765")
RATE_LIMIT_RATE = int(os.environ.get("RATE_LIMIT_RATE", 10))  # Requests per second
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 100)) # Maximum requests
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", 100))
CACHE_TTL = int(os.environ.get("CACHE_TTL", 60)) # Cache TTL in seconds

# Rate limiter
rate_limiter_instance = rate_limiter.RateLimiter(rate=RATE_LIMIT_RATE, max=RATE_LIMIT_MAX)

# Caching mechanism (using a deque for simplicity)
cache = deque(maxlen=CACHE_MAX_SIZE)
cache_lock = asyncio.Lock()

# Retry logic configuration
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", 0.5))  # Delay in seconds


class WebSocketService:
    def __init__(self):
        self.connected = False
        self.ws = None
        self.message_callback: Optional[Callable[[str], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None

    async def connect(self):
        try:
            self.ws = await connect(WS_URL)
            self.connected = True
            logging.info(f"Connected to WebSocket server at {WS_URL}")
            await self.ws.ping(None, 60)  # Keep-alive ping
        except Exception as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        if self.ws:
            try:
                await self.ws.close()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting from WebSocket server: {e}")
            finally:
                self.ws = None
                self.connected = False

    async def send_message(self, message: str):
        if not self.connected:
            logging.warning("Not connected to WebSocket server. Cannot send message.")
            return

        if not rate_limiter_instance.allow(message):
            logging.warning(f"Rate limit exceeded for message: {message}")
            return

        try:
            await self.ws.send(message)
            logging.debug(f"Sent message: {message}")
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            if self.error_callback:
                self.error_callback(e)

    async def receive_messages(self):
        if not self.connected:
            logging.warning("Not connected to WebSocket server. Cannot receive messages.")
            return

        try:
            async for message in self.ws:
                logging.debug(f"Received message: {message}")
                if self.message_callback:
                    self.message_callback(message)
        except Exception as e:
            logging.error(f"Error receiving messages: {e}")
            if self.error_callback:
                self.error_callback(e)
        finally:
            self.connected = False

    async def set_message_callback(self, callback: Callable[[str], None]):
        self.message_callback = callback

    async def set_error_callback(self, callback: Callable[[Exception], None]):
        self.error_callback = callback

    async def run(self):
        try:
            await self.connect()
            asyncio.create_task(self.receive_messages())
        except Exception as e:
            logging.error(f"Error in WebSocketService: {e}")
        finally:
            await self.disconnect()


async def example_usage():
    service = WebSocketService()
    service.set_message_callback(lambda msg: print(f"Message received: {msg}"))
    service.set_error_callback(lambda e: print(f"Error: {e}"))

    try:
        await service.run()
    except Exception as e:
        print(f"Example usage failed: {e}")


if __name__ == "__main__":
    asyncio.run(example_usage())