import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional
from collections import deque
from aiowebsocket import *
from aiowebsocket.exceptions import ConnectionClosedError
import rate_limiter
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1  # seconds
RATE_LIMIT_MAX = 100  # Requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

# Environment variable names
WS_SERVER_URL = "WS_SERVER_URL"
LOG_LEVEL = "LOG_LEVEL"

# Rate Limiter
rate_limiter_instance = rate_limiter.RateLimiter(max_rate=RATE_LIMIT_MAX, period=RATE_LIMIT_WINDOW)


class WebSocketService:
    def __init__(self):
        self.connected_clients: Dict[str, asyncio.WebSocketClient] = {}
        self.message_queue: deque[Dict[str, Any]] = deque()
        self.retry_count = 0
        self.logger = logging.getLogger(__name__)

    def _get_config(self) -> Dict[str, Any]:
        """Retrieves configuration from environment variables."""
        config = {
            WS_SERVER_URL: os.environ.get(WS_SERVER_URL, ""),
            LOG_LEVEL: os.environ.get(LOG_LEVEL, "INFO").upper()
        }
        logging.basicConfig(level=config[LOG_LEVEL])
        return config

    def _connect(self, client_id: str) -> Optional[asyncio.WebSocketClient]:
        """Connects to the WebSocket server."""
        try:
            ws = AsyncioWSocket(self.WS_SERVER_URL)
            await ws.connect()
            self.logger.info(f"Client {client_id} connected.")
            return ws
        except ConnectionRefusedError as e:
            self.logger.error(f"Failed to connect to WebSocket server: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            return None

    def _send_message(self, client: asyncio.WebSocketClient, message: Dict[str, Any]) -> None:
        """Sends a message to a client."""
        try:
            await client.send_text(json.dumps(message))
            self.logger.debug(f"Sent message to client {client.id}: {message}")
        except Exception as e:
            self.logger.error(f"Error sending message to client {client.id}: {e}")

    def _receive_message(self, client: asyncio.WebSocketClient) -> None:
        """Receives a message from a client."""
        try:
            message = await client.receive_text()
            self.logger.debug(f"Received message from client {client.id}: {message}")
            self.message_queue.append({"client_id": client.id, "message": message})
        except ConnectionClosedError:
            self.logger.warning(f"Client {client.id} disconnected.")
            self.disconnect_client(client)
        except Exception as e:
            self.logger.error(f"Error receiving message from client {client.id}: {e}")

    def _process_message_queue(self) -> None:
        """Processes messages from the message queue."""
        while self.message_queue:
            message = self.message_queue.popleft()
            for client in self.connected_clients.values():
                if client.id == message["client_id"]:
                    self._send_message(client, message)
                    break

    def connect_client(self, client_id: str, callback: Callable[[asyncio.WebSocketClient], None] = None) -> asyncio.WebSocketClient:
        """Connects a client to the WebSocket server."""
        ws = self._connect(client_id)
        if ws:
            self.connected_clients[client_id] = ws
            self.logger.info(f"Client {client_id} connected.")
            if callback:
                asyncio.create_task(callback(ws))
            asyncio.create_task(self._receive_message(ws))
            return ws
        else:
            return None

    def disconnect_client(self, client: asyncio.WebSocketClient) -> None:
        """Disconnects a client from the WebSocket server."""
        if client.id in self.connected_clients:
            del self.connected_clients[client.id]
            self.logger.info(f"Client {client.id} disconnected.")
            asyncio.current_task().cancel()

    def send_message_to_client(self, client_id: str, message: Dict[str, Any]) -> None:
        """Sends a message to a specific client."""
        client = self.connected_clients.get(client_id)
        if client:
            self._send_message(client, message)
        else:
            self.logger.warning(f"Client {client_id} not connected.")

    def process_messages(self) -> None:
        """Processes messages from the message queue."""
        self._process_message_queue()

    def run(self) -> None:
        """Runs the WebSocket service."""
        asyncio.run(self._process_messages())