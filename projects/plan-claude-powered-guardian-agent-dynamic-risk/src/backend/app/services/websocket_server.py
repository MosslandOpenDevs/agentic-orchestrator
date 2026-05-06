import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
from collections import deque
import rate_limiter
from websockets import connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
WS_URL = os.environ.get("WS_URL", "ws://localhost:8765")  # Default URL
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 10))  # Default rate limit
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 60))  # Default window
MAX_MESSAGE_BUFFER_SIZE = int(os.environ.get("MAX_MESSAGE_BUFFER_SIZE", 100))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", 0.5))  # Default retry delay in seconds

# Rate limiter
rate_limiter_instance = rate_limiter.RateLimiter(max_calls=RATE_LIMIT_MAX, period=RATE_LIMIT_WINDOW)

# Message buffer (deque for efficient adding/removing from both ends)
message_buffer = deque()

# Caching (simple dictionary for demonstration)
message_cache = {}


class WebSocketService:
    def __init__(self):
        self.ws: Optional[websockets.Connection] = None
        self.is_connected = False

    async def connect(self) -> None:
        """Connects to the WebSocket server."""
        try:
            self.ws = await connect(WS_URL)
            self.is_connected = True
            logging.info(f"Connected to WebSocket server at {WS_URL}")
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            self.is_connected = False

    async def disconnect(self) -> None:
        """Disconnects from the WebSocket server."""
        if self.ws and self.is_connected:
            try:
                await self.ws.close()
                logging.info("Disconnected from WebSocket server.")
                self.is_connected = False
            except Exception as e:
                logging.error(f"Error during disconnection: {e}")
        else:
            logging.warning("WebSocket was not connected, cannot disconnect.")

    async def send_message(self, message: str) -> bool:
        """Sends a message to the WebSocket server with rate limiting and retry logic."""
        if not self.is_connected:
            logging.warning("Not connected to WebSocket server, cannot send message.")
            return False

        if len(message_buffer) >= MAX_MESSAGE_BUFFER_SIZE:
            logging.warning("Message buffer is full, dropping message.")
            return False

        if not rate_limiter_instance.allow():
            logging.warning("Rate limit exceeded, skipping message.")
            await asyncio.sleep(RETRY_DELAY)  # Wait before retrying
            return False

        try:
            await self.ws.send(message)
            logging.debug(f"Sent message: {message}")
            message_buffer.append(message)
            return True
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            self.retry_message(message)
            return False

    def retry_message(self, message: str):
        """Retries sending a message after a delay."""
        if not self.is_connected:
            return

        asyncio.create_task(self._retry_send_message(message))

    async def _retry_send_message(self, message: str):
        """Asynchronous retry function."""
        await asyncio.sleep(RETRY_DELAY)
        if self.ws and self.is_connected:
            await self.send_message(message)
        else:
            logging.warning("WebSocket connection lost during retry, attempting to reconnect.")
            await self.connect()  # Attempt to reconnect
            await asyncio.sleep(RETRY_DELAY)
            if self.ws and self.is_connected:
                await self.send_message(message)
            else:
                logging.error("Failed to reconnect and send message after retry.")

    async def receive_messages(self) -> None:
        """Receives messages from the WebSocket server."""
        try:
            while self.is_connected:
                try:
                    message = await self.ws.recv()
                    logging.debug(f"Received message: {message}")
                    self.process_message(message)
                except websockets.exceptions.ConnectionClosedError as e:
                    logging.error(f"Connection closed unexpectedly: {e}")
                    break
                except Exception as e:
                    logging.error(f"Error receiving message: {e}")
                    break
        finally:
            if self.ws and self.is_connected:
                await self.disconnect()

    def process_message(self, message: str) -> None:
        """Processes received messages (example: caching)."""
        if message not in message_cache:
            logging.info(f"Received message (cached): {message}")
            message_cache[message] = time.time()  # Store timestamp for potential expiry
        else:
            logging.info(f"Received message (cached): {message}")

    async def run(self) -> None:
        """Runs the WebSocket service."""
        try:
            await self.connect()
            asyncio.create_task(self.receive_messages())
            # Simulate sending messages
            for i in range(5):
                await self.send_message(f"Message {i}")
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            await self.disconnect()


if __name__ == "__main__":
    service = WebSocketService()
    asyncio.run(service.run())