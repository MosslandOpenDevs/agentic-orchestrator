import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import aioredis
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedStatus, ConnectionClosedException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 5
CACHE_TTL = 60  # Cache expiry in seconds

# Environment variable names
WEBSOCKET_SERVER_URL = "WEBSOCKET_SERVER_URL"
REDIS_HOST = "REDIS_HOST"
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
RATE_LIMIT_REDIS_KEY = "rate_limit"


class WebSocketService:
    def __init__(self):
        self.rate_limit_client = aioredis.Redis(host=os.environ.get(REDIS_HOST), port=REDIS_PORT)
        self.cache = {}
        self.connected_clients = set()
        self.message_queue = deque()
        self.message_processing_task = None

    async def _rate_limit(self):
        """
        Rate limiting using Redis.
        """
        key = RATE_LIMIT_REDIS_KEY
        with self.rate_limit_client.lock(key, timeout=RATE_LIMIT_WINDOW_SECONDS):
            pass  # Lock acquired successfully

    async def _publish_message(self, message):
        """
        Publishes a message to the message queue.
        """
        self.message_queue.append(message)
        logging.debug(f"Message added to queue: {message}")

    async def _consume_message(self):
        """
        Consumes messages from the message queue and processes them.
        """
        while True:
            if not self.message_queue:
                await asyncio.sleep(1)
                continue

            message = self.message_queue.popleft()
            logging.debug(f"Processing message: {message}")
            try:
                await self.process_message(message)
            except Exception as e:
                logging.error(f"Error processing message: {e}")

    async def process_message(self, message):
        """
        Placeholder for message processing logic.  Replace with your actual processing.
        """
        # Simulate some processing time
        await asyncio.sleep(0.1)
        logging.info(f"Message processed: {message}")

    async def connect_websocket(self, websocket: websockets.WebSocketClient):
        """
        Handles a new WebSocket connection.
        """
        self.connected_clients.add(websocket)
        logging.info(f"Client connected: {websocket.remote_address}")

        try:
            # Example: Send a welcome message
            await websocket.send("Welcome to the WebSocket server!")

            # Start message consumption task
            self.message_processing_task = asyncio.create_task(self._consume_message())

            # Receive messages from the client
            while True:
                try:
                    message = await websocket.recv()
                    logging.info(f"Received message from {websocket.remote_address}: {message}")
                    await self._publish_message(message)
                except ConnectionClosedOK:
                    logging.info(f"Client disconnected gracefully: {websocket.remote_address}")
                    break
                except ConnectionClosedStatus as e:
                    logging.error(f"Client disconnected with status {e}: {websocket.remote_address}")
                    break
                except ConnectionClosedException as e:
                    logging.error(f"Client disconnected unexpectedly: {e}: {websocket.remote_address}")
                    break
                except Exception as e:
                    logging.error(f"Error receiving message from {websocket.remote_address}: {e}")
                    break

        finally:
            self.connected_clients.remove(websocket)
            logging.info(f"Client disconnected: {websocket.remote_address}")
            if self.message_processing_task:
                self.message_processing_task.cancel()


    async def close_websocket(self, websocket):
        """
        Handles a WebSocket disconnection.
        """
        self.connected_clients.remove(websocket)
        logging.info(f"Client disconnected: {websocket.remote_address}")

    async def start(self):
        """
        Starts the WebSocket service.
        """
        # Start the message consumption task
        asyncio.create_task(self._consume_message())

    async def stop(self):
        """
        Stops the WebSocket service.
        """
        logging.info("Stopping WebSocket service...")
        if self.message_processing_task:
            self.message_processing_task.cancel()
        self.rate_limit_client.close()
        self.connected_clients.clear()
        self.message_queue.clear()
        logging.info("WebSocket service stopped.")


if __name__ == "__main__":
    async def main():
        service = WebSocketService()
        await service.start()

        # Example usage (replace with your actual WebSocket server setup)
        # This is just a placeholder to demonstrate the integration.
        try:
            # Simulate a WebSocket server
            async with websockets.serve(service.connect_websocket, "localhost", 8765):
                await asyncio.Future()  # Run forever
        except Exception as e:
            logging.error(f"Error running WebSocket server: {e}")
        finally:
            await service.stop()

    asyncio.run(main())