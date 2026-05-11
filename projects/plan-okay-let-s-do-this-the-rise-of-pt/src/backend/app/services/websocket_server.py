import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import rate_limiter
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, ws_url: str, rate_limit_calls: int = 10, retry_count: int = 3, retry_delay: float = 1.0):
        """
        Initializes the WebSocketService.

        Args:
            ws_url: The URL of the WebSocket server.
            rate_limit_calls: The maximum number of calls allowed within a time window.
            retry_count: The number of times to retry a failed connection attempt.
            retry_delay: The delay in seconds between retry attempts.
        """
        self.ws_url = ws_url
        self.rate_limiter = rate_limiter.RateLimiter(rate_limit_calls, period=1.0)  # 1 second window
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.connected_clients = {}  # Store connected clients (client_id: websocket)
        self.client_id_counter = 0
        self.cache = {} # Simple in-memory cache for demonstration

    def _connect(self) -> Optional[asyncio.Client]:
        """
        Attempts to connect to the WebSocket server with retry logic.

        Returns:
            The WebSocket client if successful, None otherwise.
        """
        for attempt in range(self.retry_count):
            try:
                ws = asyncio.ClientProtocol(
                    protocol=self._protocol)
                asyncio.get_event_loop().add_callback(ws.callback)
                await ws.connect()
                return ws
            except Exception as e:
                logging.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_count - 1:
                    return None
                await asyncio.sleep(self.retry_delay)
        return None

    def _protocol(self, msg):
        """
        WebSocket protocol handler.
        """
        try:
            data = json.loads(msg)
            action = data.get('action')

            if action == 'send':
                message = data.get('message')
                self._handle_send(message)
            elif action == 'receive':
                message = data.get('message')
                self._handle_receive(message)
            else:
                logging.warning(f"Unknown action: {action}")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")

    async def _handle_send(self, message: str):
        """
        Handles the 'send' action from the WebSocket server.
        """
        if message in self.cache:
            logging.debug(f"Message '{message}' retrieved from cache.")
            return

        # Simulate some processing
        await asyncio.sleep(0.1)
        logging.info(f"Received message: {message}")

        # Simulate sending a response
        response = f"Processed: {message}"
        try:
            await self._send_message(response)
        except Exception as e:
            logging.error(f"Error sending response: {e}")

    async def _handle_receive(self, message: str):
        """
        Handles the 'receive' action from the WebSocket server.
        """
        logging.info(f"Received receive event: {message}")

    async def _send_message(self, message: str):
        """
        Sends a message to the WebSocket server.
        """
        if not self.rate_limiter.allow():
            logging.warning("Rate limit exceeded. Skipping message.")
            return

        try:
            await self.ws.send(json.dumps({"action": "send", "message": message}))
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    async def connect(self):
        """
        Connects to the WebSocket server.
        """
        ws = self._connect()
        if ws:
            logging.info(f"Connected to WebSocket server at {self.ws_url}")
            self.connected_clients[ws.client_id] = ws
            return ws
        else:
            logging.error(f"Failed to connect to WebSocket server at {self.ws_url}")
            return None

    async def disconnect(self, client_id: str):
        """
        Disconnects a client from the WebSocket server.
        """
        if client_id in self.connected_clients:
            ws = self.connected_clients.pop(client_id)
            try:
                await ws.disconnect()
                logging.info(f"Disconnected client: {client_id}")
            except Exception as e:
                logging.error(f"Error disconnecting client {client_id}: {e}")

    def get_connected_clients(self) -> Dict[str, asyncio.ClientProtocol]:
        """
        Returns a dictionary of all connected clients.
        """
        return self.connected_clients

    def register_callback(self, callback: Callable):
        """
        Registers a callback function to be executed when a message is received.
        """
        # Placeholder for more sophisticated callback registration
        pass

    def close(self):
        """
        Closes the connection to the WebSocket server.
        """
        try:
            asyncio.get_event_loop().call_soon_threadsafe(asyncio.sleep, 0.1) # Allow loop to finish
            asyncio.get_event_loop().stop()
        except Exception as e:
            logging.error(f"Error closing WebSocket connection: {e}")