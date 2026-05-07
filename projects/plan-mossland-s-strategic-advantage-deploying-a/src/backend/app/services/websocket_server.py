import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional

from websockets import connect

# Configuration
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 5
CACHE_EXPIRY_SECONDS = 60

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.connection: Optional[websockets.Connection] = None
        self.request_timestamps: Dict[str, float] = {}
        self.request_count: Dict[str, int] = {}
        self.lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connects to the WebSocket server."""
        try:
            async with connect(self.server_url) as ws:
                self.connection = ws
                logging.info(f"Connected to WebSocket server: {self.server_url}")
        except ConnectionError as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnects from the WebSocket server."""
        if self.connection:
            try:
                await self.connection.close()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error during disconnection: {e}")
            finally:
                self.connection = None

    async def send_message(self, message: str) -> None:
        """Sends a message to the WebSocket server with rate limiting and retry logic."""
        if not self.connection:
            logging.warning("Not connected to WebSocket server. Cannot send message.")
            return

        async with self.lock:
            now = time.time()
            request_key = message  # Use message as key for rate limiting

            if request_key in self.request_timestamps and now - self.request_timestamps[request_key] < RATE_LIMIT_WINDOW_SECONDS:
                rate_limit_delay = RATE_LIMIT_WINDOW_SECONDS - (now - self.request_timestamps[request_key])
                await asyncio.sleep(rate_limit_delay)
                logging.debug(f"Rate limit applied for message: {request_key}")
                return

            self.request_timestamps[request_key] = now
            self.request_count[request_key] = self.request_count.get(request_key, 0) + 1

            try:
                await self.connection.send(message)
                logging.debug(f"Sent message: {message}")
            except ConnectionError as e:
                logging.error(f"Error sending message: {e}")
                await self.retry_send(message)
            except Exception as e:
                logging.error(f"Unexpected error sending message: {e}")

    def retry_send(self, message: str, max_retries: int = 3) -> None:
        """Retries sending a message with exponential backoff."""
        for attempt in range(max_retries):
            try:
                asyncio.create_task(self.send_message(message))  # Use asyncio.create_task for non-blocking retry
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                break  # Exit the loop if successful
            except Exception as e:
                logging.error(f"Retry failed for message: {message}, attempt {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Max retries reached for message: {message}")
                else:
                    await asyncio.sleep(1)  # Wait before retrying

    async def receive_messages(self) -> None:
        """Receives messages from the WebSocket server."""
        try:
            async for message in self.connection:
                logging.info(f"Received message: {message}")
                # Process the received message here
        except ConnectionError as e:
            logging.error(f"ConnectionError during receive_messages: {e}")
            await self.disconnect()
            raise
        except Exception as e:
            logging.error(f"Unexpected error during receive_messages: {e}")
            await self.disconnect()
            raise

    async def run(self) -> None:
        """Runs the WebSocket service."""
        try:
            await self.connect()
            # Start receiving messages in the background
            receive_task = asyncio.create_task(self.receive_messages())

            # Example: Send a message after a delay
            await asyncio.sleep(2)
            await self.send_message("Hello from the service!")
            await asyncio.sleep(2)
            await self.send_message("Another message!")

            await asyncio.sleep(10) # Keep the connection alive for demonstration
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            await self.disconnect()

if __name__ == '__main__':
    # Get server URL from environment variable
    server_url = os.environ.get("WS_SERVER_URL", "ws://localhost:8765")  # Default URL
    service = WebSocketService(server_url)
    asyncio.run(service.run())