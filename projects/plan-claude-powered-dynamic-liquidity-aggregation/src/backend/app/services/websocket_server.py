import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import rate_limiter
from websockets import connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, reconnect_interval: int = 5, max_retries: int = 3, retry_delay: float = 1.0, rate_limit_rate: int = 10, rate_limit_window: int = 60):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limiter = rate_limiter.RateLimiter(rate_limit_rate, rate_limit_window)
        self.connection = None
        self.ws = None
        self.message_queue = deque()
        self.lock = asyncio.Lock()
        self.callbacks = {}

    def register_callback(self, event_name: str, callback: Callable):
        """Registers a callback function for a specific event."""
        with self.lock:
            if event_name not in self.callbacks:
                self.callbacks[event_name] = []
            self.callbacks[event_name].append(callback)

    def unregister_callback(self, event_name: str, callback: Callable):
        """Unregisters a callback function for a specific event."""
        with self.lock:
            if event_name in self.callbacks:
                try:
                    self.callbacks[event_name].remove(callback)
                except ValueError:
                    pass  # Callback not found

    def send_message(self, message: str):
        """Sends a message to the WebSocket server."""
        if not self.connection:
            return

        with self.rate_limiter:
            try:
                self.ws.send(message)
                logging.debug(f"Sent message: {message}")
            except Exception as e:
                logging.error(f"Error sending message: {e}")

    def receive_messages(self):
        """Receives messages from the WebSocket server."""
        async def _receive():
            try:
                while True:
                    try:
                        message = await self.ws.recv()
                        logging.debug(f"Received message: {message}")
                        asyncio.create_task(self._process_message(message))
                    except websockets.exceptions.ConnectionClosedOK:
                        logging.info("Connection closed gracefully.")
                        break
                    except websockets.exceptions.ConnectionClosedError as e:
                        logging.error(f"Connection closed with error: {e}")
                        break
                    except Exception as e:
                        logging.error(f"Error receiving message: {e}")
                        break
            finally:
                self.ws = None # Ensure ws is reset after task completion

        asyncio.create_task(_receive())

    def _process_message(self, message: str):
        """Processes received messages and triggers callbacks."""
        with self.lock:
            self.message_queue.append(message)
            for event_name, callbacks in self.callbacks.items():
                for callback in callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        logging.error(f"Error in callback {callback.__name__}: {e}")

    async def connect(self):
        """Connects to the WebSocket server with retry logic."""
        retries = 0
        while retries < self.max_retries:
            try:
                self.connection = connect(self.url)
                self.ws = self.connection.websocket()
                self.ws.ping_timeout = 10  # Adjust as needed
                self.ws.ping(None)
                logging.info(f"Connected to WebSocket server at {self.url}")
                await self.receive_messages()
                return
            except Exception as e:
                logging.error(f"Connection attempt {retries + 1} failed: {e}")
                retries += 1
                await asyncio.sleep(self.retry_delay)
        logging.error(f"Failed to connect to WebSocket server after {self.max_retries} attempts.")

    async def disconnect(self):
        """Disconnects from the WebSocket server."""
        if self.ws:
            try:
                await self.ws.close()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting: {e}")
        if self.connection:
            self.connection.close()

    def run(self):
        """Starts the WebSocket service."""
        asyncio.run(self.connect())


if __name__ == '__main__':
    # Example Usage (replace with your WebSocket server URL)
    ws_service = WebSocketService(url="ws://localhost:8765")

    # Register a callback function
    ws_service.register_callback("new_message", lambda message: print(f"Callback received: {message}"))

    # Start the service
    ws_service.run()