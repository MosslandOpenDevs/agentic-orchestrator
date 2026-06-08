import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional
from collections import deque
import json
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
MAX_RATE_LIMIT = 10  # Requests per second
CACHE_TTL = 60  # Cache expiration time in seconds
RETRY_COUNT = 3
RETRY_DELAY = 2  # Seconds

# Environment variable names
WS_SERVER_URL = "ws://localhost:8765"  # Replace with your WebSocket server URL
RATE_LIMIT_KEY = "websocket_rate_limit"


class WebSocketService:
    def __init__(self):
        self.ws: Optional[aiohttp.ClientSession] = None
        self.connected = False
        self.rate_limit_lock = asyncio.Lock()
        self.rate_limit_count = 0
        self.message_queue = deque()
        self.cache = {}
        self.retry_count = 0

    async def connect(self):
        """Connects to the WebSocket server."""
        try:
            self.ws = aiohttp.ClientSession()
            ws = await self.ws.ws_connect(WS_SERVER_URL)
            self.connected = True
            logging.info("Connected to WebSocket server.")
            await self.send_message(ws, {"type": "connect"})
        except aiohttp.ClientError as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            self.connected = False

    async def disconnect(self):
        """Disconnects from the WebSocket server."""
        if self.ws and self.connected:
            try:
                await self.ws.close()
                logging.info("Disconnected from WebSocket server.")
                self.connected = False
            except aiohttp.ClientError as e:
                logging.error(f"Error disconnecting from WebSocket server: {e}")
            finally:
                self.ws = None

    async def send_message(self, ws: aiohttp.WSOcket, message: Dict[str, Any]):
        """Sends a message to the WebSocket server."""
        await ws.send(json.dumps(message))
        logging.debug(f"Sent message: {message}")

    async def receive_message(self, ws: aiohttp.WSOcket) -> Optional[Dict[str, Any]]:
        """Receives a message from the WebSocket server."""
        try:
            response = await ws.recv()
            logging.debug(f"Received message: {response}")
            return json.loads(response)
        except aiohttp.ClientError as e:
            logging.error(f"Error receiving message: {e}")
            return None

    async def process_messages(self):
        """Processes incoming messages from the WebSocket server."""
        while self.connected:
            message = await self.receive_message(self.ws)
            if message:
                self.handle_message(message)

    def handle_message(self, message: Dict[str, Any]):
        """Handles incoming messages based on their type."""
        message_type = message.get("type")
        if message_type == "data":
            # Simulate processing data
            logging.info(f"Received data: {message.get('data')}")
        elif message_type == "connect":
            logging.info("Received connect message.")
        elif message_type == "disconnect":
            logging.info("Received disconnect message.")
        else:
            logging.warning(f"Received unknown message type: {message_type}")

    async def send_data(self, data: Any):
        """Sends data to the WebSocket server, handling rate limiting and retries."""
        async with self.rate_limit_lock:
            if self.rate_limit_count >= MAX_RATE_LIMIT:
                logging.warning("Rate limit exceeded. Dropping message.")
                return

            self.rate_limit_count += 1
            try:
                await self.send_message(self.ws, {"type": "data", "data": data})
            except aiohttp.ClientError as e:
                logging.error(f"Error sending data: {e}")
                self.retry_message(data)

    def retry_message(self, data: Any):
        """Retries sending a message with exponential backoff."""
        self.retry_count = 0
        while self.retry_count < RETRY_COUNT:
            asyncio.create_task(self.send_data(data))
            await asyncio.sleep(RETRY_DELAY)
            self.retry_count += 1

    async def run(self):
        """Runs the WebSocket service."""
        await self.connect()
        if not self.connected:
            return

        asyncio.create_task(self.process_messages())
        await asyncio.sleep(10)  # Keep the service running for a while
        await self.disconnect()


if __name__ == "__main__":
    service = WebSocketService()
    asyncio.run(service.run())