import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional

from websockets import connect

# Configuration
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 5
CACHE_EXPIRY_SECONDS = 60

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, on_message: Callable, on_error: Optional[Callable] = None, retry_attempts: int = 3):
        self.url = url
        self.on_message = on_message
        self.on_error = on_error
        self.retry_attempts = retry_attempts
        self.connection = None
        self.last_request_time = 0
        self.request_count = 0
        self.lock = asyncio.Lock()

    async def _connect(self):
        try:
            self.connection = await connect(self.url)
            logging.info(f"Connected to WebSocket server at {self.url}")
        except ConnectionError as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            if self.on_error:
                self.on_error(e)
            raise

    async def _send_message(self, message: str):
        with self.lock:
            now = time.time()
            if now - self.last_request_time < RATE_LIMIT_WINDOW_SECONDS:
                logging.debug(f"Rate limit exceeded. Skipping message: {message}")
                return

            self.last_request_time = now
            self.request_count += 1

            for attempt in range(self.retry_attempts):
                try:
                    await self.connection.send(message)
                    logging.debug(f"Sent message: {message}")
                    return
                except ConnectionError as e:
                    logging.warning(f"WebSocket connection error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                    if attempt < self.retry_attempts - 1 and time.time() - self.last_request_time < RATE_LIMIT_WINDOW_SECONDS:
                        await asyncio.sleep(1)  # Wait before retrying
                    else:
                        break # Stop retrying if max attempts reached

    async def _receive_messages(self):
        try:
            while True:
                try:
                    message = await self.connection.recv()
                    logging.info(f"Received message: {message}")
                    if self.on_message:
                        self.on_message(message)
                except ConnectionError as e:
                    logging.error(f"WebSocket connection error during receive: {e}")
                    if self.on_error:
                        self.on_error(e)
                    break
                except Exception as e:
                    logging.error(f"Unexpected error during receive: {e}")
                    if self.on_error:
                        self.on_error(e)
                    break
                await asyncio.sleep(0.1)  # Avoid busy-waiting
        finally:
            logging.info("Closing WebSocket connection.")
            if self.connection:
                try:
                    await self.connection.close()
                except Exception as e:
                    logging.error(f"Error closing WebSocket connection: {e}")

    async def run(self):
        try:
            await self._connect()
            await self._receive_messages()
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            if self.on_error:
                self.on_error(e)

    def close(self):
        if self.connection:
            try:
                asyncio.create_task(self._close_ws())
            except Exception as e:
                logging.error(f"Error closing WebSocket connection: {e}")

    async def _close_ws(self):
        try:
            await self.connection.close()
            logging.info("WebSocket connection closed.")
        except Exception as e:
            logging.error(f"Error closing WebSocket connection: {e}")

class ConnectionError(Exception):
    pass