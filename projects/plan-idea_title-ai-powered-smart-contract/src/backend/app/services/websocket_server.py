import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional

from websockets import connect

# Configuration
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 5
CACHE_EXPIRY_SECONDS = 60

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, on_message_callback: Callable[[str], None], on_error_callback: Optional[Callable[[str], None]] = None, retry_attempts: int = 3):
        self.url = url
        self.on_message_callback = on_message_callback
        self.on_error_callback = on_error_callback
        self.retry_attempts = retry_attempts
        self.connection = None
        self.last_request_time = 0
        self.request_count = 0
        self.lock = asyncio.Lock()

    async def connect(self):
        try:
            async with self.lock:
                self.connection = await connect(self.url)
                logging.info(f"Connected to WebSocket server at {self.url}")
        except asyncio.ConnectError as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
            raise

    async def disconnect(self):
        if self.connection:
            try:
                await self.connection.close()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting: {e}")

    async def send_message(self, message: str):
        await self.lock
        now = time.time()
        if now - self.last_request_time < RATE_LIMIT_WINDOW_SECONDS:
            logging.debug(f"Rate limit exceeded for message: {message}")
            return

        self.last_request_time = now
        self.request_count += 1

        if self.request_count > RATE_LIMIT_MAX_REQUESTS:
            await asyncio.sleep(RATE_LIMIT_WINDOW_SECONDS)
            self.request_count = 1

        try:
            await self.connection.send(message)
            logging.debug(f"Sent message: {message}")
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
            raise

    async def receive_messages(self):
        try:
            while True:
                try:
                    message = await self.connection.recv()
                    await self.lock
                    logging.debug(f"Received message: {message}")
                    if self.on_message_callback:
                        self.on_message_callback(message)
                except Exception as e:
                    logging.error(f"Error receiving message: {e}")
                    if self.on_error_callback:
                        self.on_error_callback(str(e))
                    break
                await asyncio.sleep(0.01)  # Avoid busy-waiting
        except Exception as e:
            logging.error(f"Unexpected error in receive_messages: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
        finally:
            await self.disconnect()

    async def run(self):
        try:
            await self.connect()
            await self.receive_messages()
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))


if __name__ == '__main__':
    # Example Usage (replace with your actual URL and callbacks)
    ws_url = os.environ.get("WS_URL", "ws://localhost:8765")  # Default URL
    on_message = lambda message: print(f"Message received: {message}")
    on_error = lambda error: print(f"Error: {error}")

    service = WebSocketService(ws_url=ws_url, on_message_callback=on_message, on_error_callback=on_error, retry_attempts=3)
    asyncio.run(service.run())