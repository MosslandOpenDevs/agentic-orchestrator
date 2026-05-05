import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
from collections import deque
from urllib.parse import urlparse
import websockets
import aiohttp
import rate_limiter
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    "websocket_service.log",
    level="INFO",
    rotation="rotatelogs",
    retention="3 days",
    encoding="utf-8",
)

# Environment variable configuration
WS_URL = os.environ.get("WS_URL", "ws://localhost:8765")
RATE_LIMIT_RATE = int(os.environ.get("RATE_LIMIT_RATE", 10))  # Requests per second
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 100)) # Max requests
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", 100))
CACHE_TTL = int(os.environ.get("CACHE_TTL", 60)) # Cache TTL in seconds

# Rate limiter
rate_limiter_instance = rate_limiter.RateLimiter(rate=RATE_LIMIT_RATE, max=RATE_LIMIT_MAX)

# Caching mechanism (using a deque for simplicity - replace with a more robust cache if needed)
cache = deque(maxlen=CACHE_MAX_SIZE)
cache_lock = asyncio.Lock()

# Retry logic
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds

class WebSocketService:
    def __init__(self):
        self.websocket: Optional[websockets.Connection] = None
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self):
        """Connects to the WebSocket server."""
        try:
            url = urlparse(WS_URL)
            self.websocket = await websockets.connect(url.netloc, timeout=10)
            logger.info(f"Connected to WebSocket server at {WS_URL}")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred during connection: {e}")
            raise

    async def disconnect(self):
        """Disconnects from the WebSocket server."""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Disconnected from WebSocket server.")
            except websockets.exceptions.ConnectionClosedError:
                pass
            finally:
                self.websocket = None

    async def send_message(self, message: str) -> bool:
        """Sends a message to the WebSocket server."""
        try:
            await self.websocket.send(message)
            logger.info(f"Sent message: {message}")
            return True
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed while sending message: {e}")
            return False
        except Exception as e:
            logger.exception(f"An unexpected error occurred while sending message: {e}")
            return False

    async def receive_message(self) -> Optional[str]:
        """Receives a message from the WebSocket server."""
        try:
            message = await self.websocket.recv()
            logger.info(f"Received message: {message}")
            return message
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed while receiving message: {e}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred while receiving message: {e}")
            return None

    async def process_message(self, message: str) -> None:
        """Processes the received message (example)."""
        # Simulate some processing
        await asyncio.sleep(0.1)
        # Example: Cache the message
        with cache_lock:
            cache.append(message)
            if len(cache) > CACHE_MAX_SIZE:
                cache.popleft()

    async def run(self):
        """Runs the WebSocket service."""
        try:
            await self.connect()
            while True:
                try:
                    message = await self.receive_message()
                    if message:
                        await self.process_message(message)
                except asyncio.CancelledError:
                    break
        except Exception as e:
            logger.exception(f"An error occurred in the main loop: {e}")
        finally:
            await self.disconnect()

async def main():
    service = WebSocketService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())