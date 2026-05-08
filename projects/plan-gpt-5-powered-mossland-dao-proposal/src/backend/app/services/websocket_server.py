import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import aioredis
import aiohttp
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, reconnect_interval: int = 5, max_retries: int = 3, retry_delay: float = 1):
        """
        Initializes the WebSocketService.

        Args:
            url: The WebSocket URL.
            reconnect_interval: Time in seconds between reconnection attempts.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay in seconds between retry attempts.
        """
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connected = False
        self.loop = asyncio.get_event_loop()
        self.ws = None
        self.redis_client = None
        self.message_queue = deque()
        self.lock = asyncio.Lock()
        self.callbacks: Dict[str, Callable[[Any], None]] = {}

    async def connect(self):
        """
        Connects to the WebSocket server.
        """
        try:
            self.ws = await aiohttp.WSocketClient(self.url, allow_cancel=True)
            self.connected = True
            await self.ws.connect()
            logging.info(f"Connected to WebSocket server at {self.url}")
        except aiohttp.ClientError as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        """
        Disconnects from the WebSocket server.
        """
        if self.ws:
            try:
                await self.ws.close()
                await self.ws.transport.wait_closed()
                self.connected = False
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting from WebSocket server: {e}")
            finally:
                self.ws = None

    async def send_message(self, message: str):
        """
        Sends a message to the WebSocket server.

        Args:
            message: The message to send.
        """
        if not self.connected:
            logging.warning("Not connected to WebSocket server, message not sent.")
            return

        try:
            await self.ws.send(message)
            logging.debug(f"Sent message: {message}")
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    async def receive_messages(self):
        """
        Receives messages from the WebSocket server.
        """
        try:
            async for message in self.ws:
                if message:
                    logging.debug(f"Received message: {message}")
                    await self.process_message(message)
        except Exception as e:
            logging.error(f"Error receiving messages: {e}")
        finally:
            if self.ws and not self.ws.transport.is_closed():
                self.ws.close()

    async def process_message(self, message: str):
        """
        Processes a received message.

        Args:
            message: The received message.
        """
        try:
            # Implement message processing logic here.
            # Example:
            if "event" in message:
                self.handle_event(message)
        except Exception as e:
            logging.error(f"Error processing message: {e}")

    def handle_event(self, event_message: str):
        """
        Handles specific events received from the WebSocket server.
        """
        # Placeholder for event handling logic.
        pass

    async def register_callback(self, event_name: str, callback: Callable[[Any], None]):
        """
        Registers a callback function for a specific event.
        """
        self.callbacks[event_name] = callback

    async def run(self):
        """
        Runs the WebSocket service.
        """
        try:
            await self.connect()
            asyncio.create_task(self.receive_messages())
            while True:
                await asyncio.sleep(self.reconnect_interval)
        except Exception as e:
            logging.error(f"WebSocket service error: {e}")
        finally:
            await self.disconnect()

    async def close(self):
        """
        Closes the WebSocket connection.
        """
        await self.disconnect()

# Example Usage (Illustrative - Requires Redis setup)
if __name__ == "__main__":
    # Replace with your WebSocket URL
    websocket_url = os.environ.get("WEBSOCKET_URL", "ws://localhost:8000")
    
    service = WebSocketService(websocket_url, reconnect_interval=2, max_retries=5, retry_delay=0.5)

    async def main():
        try:
            await service.run()
        except Exception as e:
            print(f"An error occurred: {e}")

    asyncio.run(main())