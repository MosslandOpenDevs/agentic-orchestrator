import asyncio
import logging
import time
from typing import Callable, Dict, Optional

from websockets import connect
import rate_limiter
import json
from cachetools import TTLCache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
WS_URL = "ws://localhost:8765"  # Replace with your WebSocket server URL
RATE_LIMIT_MAX = 10  # Maximum requests per window
RATE_LIMIT_WINDOW = 5  # Time window in seconds
CACHE_TTL = 60  # Cache TTL in seconds
CACHE_MAX_SIZE = 100  # Maximum cache size


class WebSocketService:
    def __init__(self):
        self.connection: Optional[websockets.connect] = None
        self.rate_limiter = rate_limiter.RateLimiter(max_calls=RATE_LIMIT_MAX, period=RATE_LIMIT_WINDOW)
        self.cache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL)
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    async def connect(self):
        try:
            self.connection = await connect(WS_URL)
            logging.info("Connected to WebSocket server.")
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            raise

    async def disconnect(self):
        if self.connection:
            try:
                await self.connection.close()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Failed to disconnect from WebSocket server: {e}")

    async def send_message(self, message: str) -> Optional[str]:
        if not self.connection:
            logging.warning("Not connected to WebSocket server. Cannot send message.")
            return None

        try:
            await self.rate_limiter.wait()  # Rate limiting
            await self.connection.send(message)
            logging.debug(f"Sent message: {message}")
            return await self.connection.recv()
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            self.retry_count = 0
            await self.retry_and_reconnect()
            return None

    async def receive_message(self) -> Optional[str]:
        if not self.connection:
            logging.warning("Not connected to WebSocket server. Cannot receive message.")
            return None

        try:
            response = await self.connection.recv()
            logging.debug(f"Received message: {response}")
            return response
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            self.retry_count = 0
            await self.retry_and_reconnect()
            return None

    async def retry_and_reconnect(self):
        if self.retry_count < self.max_retries:
            logging.warning(f"Transient failure. Retrying in {self.retry_delay} seconds...")
            await asyncio.sleep(self.retry_delay)
            self.retry_count += 1
            await self.connect()
        else:
            logging.error("Max retries reached. Connection failed.")
            raise Exception("WebSocket connection failed after multiple retries.")

    async def process_data(self, callback: Callable, *args, **kwargs):
        try:
            response = await self.send_message(json.dumps({"type": "data_request", "args": args, "kwargs": kwargs}))
            if response:
                data = json.loads(response)
                return await callback(*data["args"], **data["kwargs"])
            else:
                return None
        except Exception as e:
            logging.error(f"Error processing data: {e}")
            return None


if __name__ == "__main__":
    async def main():
        ws_service = WebSocketService()
        try:
            await ws_service.connect()
            # Example usage
            # await ws_service.send_message("Hello, WebSocket Server!")
            # response = await ws_service.receive_message()
            # print(f"Received: {response}")

            # Simulate data processing
            # result = await ws_service.process_data(lambda x, y: x + y, 5, 3)
            # print(f"Result: {result}")

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            await ws_service.disconnect()

    asyncio.run(main())