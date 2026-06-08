import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
from collections import deque
from aiohttp import web_socket_response, ws_connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Rate limiting configuration (example)
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 5

# Caching configuration (example)
CACHE_EXPIRATION_SECONDS = 60

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Environment variable names
WS_SERVER_URL = os.environ.get("WS_SERVER_URL", "ws://localhost:8000")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "WebSocketService")


class WebSocketService:
    def __init__(self):
        self.connected_clients: Dict[asyncio.StreamWriter, asyncio.StreamRunner] = {}
        self.message_queue: deque = deque()
        self.lock = asyncio.Lock()

    async def connect(self, writer: asyncio.StreamWriter):
        """Connects a client to the WebSocket server."""
        try:
            await writer.send(b"Connected")
            async for msg in writer:
                try:
                    message = msg.decode()
                    logging.info(f"Received message from {writer.name}: {message}")
                    await self.handle_message(writer, message)
                except Exception as e:
                    logging.error(f"Error handling message from {writer.name}: {e}")
        except Exception as e:
            logging.error(f"Error during connection: {e}")
        finally:
            with self.lock:
                if writer in self.connected_clients:
                    del self.connected_clients[writer]
                    logging.info(f"Client {writer.name} disconnected.")

    async def handle_message(self, writer: asyncio.StreamWriter, message: str):
        """Handles incoming messages from the WebSocket server."""
        # Simulate processing the message
        await self.process_message(writer, message)

    async def process_message(self, writer: asyncio.StreamWriter, message: str):
        """Simulates processing the message.  Replace with actual logic."""
        await asyncio.sleep(0.1)  # Simulate processing time
        response = f"Server received: {message}"
        try:
            await writer.send(response.encode())
        except Exception as e:
            logging.error(f"Error sending response to {writer.name}: {e}")

    async def send_to_all(self, message: str):
        """Sends a message to all connected clients."""
        with self.lock:
            for writer in self.connected_clients.values():
                try:
                    await writer.send(message.encode())
                except Exception as e:
                    logging.error(f"Error sending message to {writer.name}: {e}")

    async def clear_queue(self):
        """Clears the message queue."""
        with self.lock:
            self.message_queue.clear()

    async def run(self):
        """Main function to run the WebSocket service."""
        try:
            logging.info(f"WebSocket Service started for {SERVICE_NAME} at {WS_SERVER_URL}")
            async with web_socket_response(self.send_to_all) as resp:
                async for msg in resp:
                    try:
                        message = msg.decode()
                        logging.info(f"Received initial message: {message}")
                        await self.handle_message(resp, message)
                    except Exception as e:
                        logging.error(f"Error processing initial message: {e}")

        except Exception as e:
            logging.error(f"WebSocket Service encountered an error: {e}")
        finally:
            logging.info(f"WebSocket Service stopped for {SERVICE_NAME}")


if __name__ == "__main__":
    service = WebSocketService()
    asyncio.run(service.run())