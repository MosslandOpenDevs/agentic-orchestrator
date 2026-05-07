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
        self.connection: Optional[websockets.connect] = None
        self.last_request_time = 0
        self.request_count = 0
        self.lock = asyncio.Lock()

    async def connect(self):
        try:
            self.connection = await connect(self.url)
            logging.info(f"Connected to WebSocket server at {self.url}")
        except Exception as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
            raise

    async def disconnect(self):
        if self.connection:
            try:
                await self.connection.close()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting from WebSocket server: {e}")

    async def send_message(self, message: str):
        async with self.lock:
            now = time.time()
            if now - self.last_request_time < RATE_LIMIT_WINDOW_SECONDS:
                logging.debug(f"Rate limit exceeded. Request suppressed.")
                return

            self.last_request_time = now
            self.request_count += 1

            for attempt in range(self.retry_attempts):
                try:
                    await self.connection.send(message)
                    logging.debug(f"Sent message: {message}")
                    return
                except Exception as e:
                    logging.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == self.retry_attempts - 1:
                        logging.error(f"Failed to send message after {self.retry_attempts} attempts: {e}")
                        if self.on_error_callback:
                            self.on_error_callback(str(e))
                        raise
                    await asyncio.sleep(1)  # Exponential backoff

    async def receive_messages(self):
        try:
            async for message in self.connection:
                logging.info(f"Received message: {message}")
                self.on_message_callback(message)
        except Exception as e:
            logging.error(f"Error receiving messages: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
            raise

    async def run(self):
        try:
            await self.connect()
            await asyncio.gather(
                self.receive_messages(),
                asyncio.sleep(0)  # Keep the event loop running
            )
        finally:
            await self.disconnect()

    @classmethod
    def from_config(cls, url: str, on_message_callback: Callable[[str], None], on_error_callback: Optional[Callable[[str], None]] = None, retry_attempts: int = 3) -> 'WebSocketService':
        return cls(url=url, on_message_callback=on_message_callback, on_error_callback=on_error_callback, retry_attempts=retry_attempts)


if __name__ == '__main__':
    # Example Usage (replace with your actual URL and callback)
    ws_url = os.environ.get("WS_URL", "ws://localhost:8765")
    ws_callback = lambda msg: print(f"Callback received: {msg}")
    ws_error_callback = lambda msg: print(f"Error callback: {msg}")

    service = WebSocketService.from_config(ws_url, ws_callback, ws_error_callback)
    asyncio.run(service.run())