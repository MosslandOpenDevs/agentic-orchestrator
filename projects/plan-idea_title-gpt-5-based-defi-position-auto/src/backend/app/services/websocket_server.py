import asyncio
import logging
import time
import os
import json
from collections import deque
from typing import Dict, Any, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, reconnect_interval: int = 5, max_retries: int = 3, retry_delay: float = 1.0):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connected = False
        self.websocket = None
        self.message_queue = deque()
        self.lock = asyncio.Lock()
        self.rate_limit_enabled = os.environ.get("RATE_LIMIT_ENABLED", "False").lower() == "true"
        self.rate_limit_interval = int(os.environ.get("RATE_LIMIT_INTERVAL", "10"))
        self.rate_limit_max_messages = int(os.environ.get("RATE_LIMIT_MAX_MESSAGES", "100"))

    async def connect(self):
        try:
            self.websocket = await asyncio.wrap_future(
                asyncio.connect(self.url)
            )
            self.connected = True
            logging.info(f"Connected to WebSocket server at {self.url}")
        except Exception as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            self.connected = False

    async def disconnect(self):
        if self.websocket:
            try:
                await self.websocket.close()
                self.connected = False
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting from WebSocket server: {e}")

    async def send_message(self, message: Dict[str, Any]):
        if not self.connected:
            logging.warning("Not connected to WebSocket server, message not sent.")
            return

        if self.rate_limit_enabled:
            timestamp = time.time()
            messages_since_last_reset = timestamp - (self.rate_limit_interval / 60.0)
            if len(self.message_queue) >= self.rate_limit_max_messages:
                logging.warning("Rate limit exceeded, message not sent.")
                return

        try:
            await self.websocket.send(json.dumps(message))
            logging.debug(f"Sent message: {message}")
            self.message_queue.append(message)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    async def receive_message(self):
        try:
            message = await self.websocket.recv()
            logging.debug(f"Received message: {message}")
            self.message_queue.append(json.loads(message))
        except Exception as e:
            logging.error(f"Error receiving message: {e}")

    async def run(self):
        try:
            await self.connect()
            while self.connected:
                if self.rate_limit_enabled:
                    await asyncio.sleep(self.rate_limit_interval / 60.0)
                await asyncio.sleep(self.reconnect_interval)
                if not self.connected:
                    break

                await asyncio.Task.sleep(0)
                try:
                    await self.receive_message()
                except asyncio.CancelledError:
                    break

        finally:
            await self.disconnect()

    async def get_message(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            if self.message_queue:
                message = self.message_queue.popleft()
                return message
            else:
                return None

    def get_messages(self, limit: int = 10) -> list[Dict[str, Any]]:
        messages = []
        with self.lock:
            messages.extend(list(self.message_queue)[:limit])
        return messages