import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional
from collections import deque
from ratelimit import RateLimitException, RateLimitList

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DEFAULT_RATE_LIMIT = 10  # Requests per second
MAX_CACHE_SIZE = 100
CACHE_TTL = 60  # Seconds

# Environment variable names
WS_SERVER_URL = "ws://localhost:8765"  # Default WebSocket server URL
RATE_LIMIT_MAX = os.environ.get("RATE_LIMIT_MAX", DEFAULT_RATE_LIMIT)
RATE_LIMIT_PERIOD = os.environ.get("RATE_LIMIT_PERIOD", 1)  # Seconds
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class WebSocketService:
    def __init__(self):
        self.ws: Optional[asyncio.BaseClient] = None
        self.cache: Dict[str, Any] = {}
        self.cache_lock = asyncio.Lock()
        self.rate_limit = RateLimitList(max_requests=RATE_LIMIT_MAX, period=RATE_LIMIT_PERIOD)
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 2  # Seconds

    async def connect(self):
        try:
            self.ws = await asyncio.open_connection(
                WS_SERVER_URL, None, ssl=False
            )
            logging.info(f"Connected to WebSocket server at {WS_SERVER_URL}")
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
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

    async def send_message(self, message: str) -> bool:
        try:
            await self.ws.send(message)
            logging.debug(f"Sent message: {message}")
            return True
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False

    async def receive_message(self) -> Optional[str]:
        try:
            return await self.ws.recv()
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    def _get_from_cache(self, key: str) -> Any:
        with self.cache_lock:
            if key in self.cache and time.time() - self.cache[key]["timestamp"] < CACHE_TTL:
                logging.debug(f"Cache hit for key: {key}")
                return self.cache[key]["value"]
            else:
                logging.debug(f"Cache miss for key: {key}")
                return None

    def _set_to_cache(self, key: str, value: Any) -> None:
        with self.cache_lock:
            self.cache[key] = {"value": value, "timestamp": time.time()}

    async def call_ws_handler(self, handler_func: Callable, *args, **kwargs) -> Any:
        try:
            await self.rate_limit.acquire(timeout=1)  # Allow rate limiting
            message = await handler_func(*args, **kwargs)
            await self.send_message(message)
            return message
        except RateLimitException:
            logging.warning("Rate limit exceeded.")
            await asyncio.sleep(0.1)  # Small delay
            return None
        except Exception as e:
            logging.error(f"Error in WebSocket handler: {e}")
            return None
        finally:
            await self.rate_limit.release()

    async def handle_messages(self):
        while True:
            try:
                message = await self.receive_message()
                if message:
                    logging.debug(f"Received message: {message}")
                    # Process the message here (e.g., cache it)
                    self._set_to_cache(message, message)
            except Exception as e:
                logging.error(f"Error in handle_messages: {e}")
                break

    async def run(self):
        try:
            await self.connect()
            asyncio.create_task(self.handle_messages())
        except Exception as e:
            logging.error(f"Exception in WebSocketService: {e}")
        finally:
            await self.disconnect()


if __name__ == '__main__':
    # Example Usage (for testing)
    service = WebSocketService()
    asyncio.run(service.run())