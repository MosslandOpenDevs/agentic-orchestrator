import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import rate_limiter
from websockets import connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
WS_URL = os.environ.get("WS_URL", "ws://localhost:8765")
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 10))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 60))
RETRY_COUNT = int(os.environ.get("RETRY_COUNT", 3))
CACHE_TTL = int(os.environ.get("CACHE_TTL", 60))

# Rate limiter
rate_limit = rate_limiter.RateLimiter(max_calls=RATE_LIMIT_MAX, period=RATE_LIMIT_WINDOW)

# Cache (using a deque for FIFO)
cache = deque(maxlen=CACHE_TTL)

# Retry logic
def retry_with_delay(func, args, delay=1):
    """Retries a function with exponential backoff."""
    for i in range(RETRY_COUNT):
        try:
            return func(*args)
        except Exception as e:
            logging.error(f"Attempt {i+1} failed: {e}")
            if i < RETRY_COUNT - 1:
                time.sleep(delay * (2 ** i))
            else:
                raise  # Re-raise the last exception

# WebSocket Service Class
class WebSocketService:
    def __init__(self, url: str):
        self.url = url
        self.ws = None
        self.connected = False

    async def connect(self):
        """Connects to the WebSocket server."""
        try:
            self.ws = connect(self.url)
            self.connected = True
            logging.info(f"Connected to WebSocket server at {self.url}")
            await self.ws.ping(None)  # Keep-alive
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            self.connected = False

    async def disconnect(self):
        """Disconnects from the WebSocket server."""
        if self.ws:
            try:
                await self.ws.close()
                logging.info("Disconnected from WebSocket server.")
                self.connected = False
            except Exception as e:
                logging.error(f"Failed to disconnect from WebSocket server: {e}")
            finally:
                self.ws = None

    async def send_message(self, message: str) -> Optional[str]:
        """Sends a message to the WebSocket server and returns the response."""
        if not self.connected:
            logging.warning("Not connected to WebSocket server. Cannot send message.")
            return None

        try:
            await rate_limit.acquire()
            response = await self.ws.send(message)
            logging.debug(f"Sent message: {message}, Received: {response}")
            return response
        except Exception as e:
            logging.error(f"Failed to send message: {e}")
            return None
        finally:
            rate_limit.release()

    async def receive_messages(self, callback: Callable[[str], None]) -> None:
        """Receives messages from the WebSocket server and calls the callback."""
        try:
            async for message in self.ws:
                await callback(message)
        except Exception as e:
            logging.error(f"Failed to receive messages: {e}")
        finally:
            await self.disconnect()

    async def execute_command(self, command: str) -> Optional[str]:
        """Executes a command on the WebSocket server and returns the response."""
        response = await retry_with_delay(self.send_message, (command,))
        return response

    async def subscribe(self, topic: str, callback: Callable[[str], None]) -> None:
        """Subscribes to a topic and receives messages."""
        await self.receive_messages(callback)

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribes from a topic."""
        pass # Placeholder for unsubscribe functionality

# Example Usage (Illustrative - Not part of the core service class)
if __name__ == "__main__":
    service = WebSocketService(WS_URL)
    async def my_callback(message):
        print(f"Received: {message}")

    await service.connect()
    await service.subscribe("topic1", my_callback)
    #await service.send_message("Hello, WebSocket Server!")
    #await time.sleep(5)
    #await service.disconnect()