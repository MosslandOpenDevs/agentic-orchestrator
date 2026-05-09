import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Union

from websockets import connect

# Configuration
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 5
CACHE_EXPIRY_SECONDS = 60
LOG_LEVEL = logging.INFO

# Logging setup
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, on_message_callback: Callable[[str], None], on_error_callback: Optional[Callable[[str], None]] = None, rate_limit_max_requests: int = RATE_LIMIT_MAX_REQUESTS, rate_limit_window_seconds: int = RATE_LIMIT_WINDOW_SECONDS, cache_expiry_seconds: int = CACHE_EXPIRY_SECONDS):
        self.url = url
        self.on_message_callback = on_message_callback
        self.on_error_callback = on_error_callback or lambda error: logging.error(f"WebSocket Error: {error}")
        self.ws = None
        self.rate_limit_max_requests = rate_limit_max_requests
        self.rate_limit_window_seconds = rate_limit_window_seconds
        self.cache_expiry_seconds = cache_expiry_seconds
        self.request_timestamps = []
        self.lock = asyncio.Lock()

    async def connect(self):
        try:
            async with connect(self.url) as ws:
                self.ws = ws
                logging.info(f"Connected to WebSocket server at {self.url}")
                await self._run_message_handler(ws)
        except ConnectionError as e:
            self.on_error_callback(e)
            raise
        except Exception as e:
            self.on_error_callback(e)
            raise

    async def _run_message_handler(self, ws: websockets.Connection):
        try:
            while True:
                try:
                    message = await ws.recv()
                    self._handle_message(message)
                except websockets.exceptions.ConnectionClosedError as e:
                    self.on_error_callback(e)
                    break
                except Exception as e:
                    self.on_error_callback(e)
                    break
        finally:
            if self.ws:
                try:
                    await self.ws.close()
                except Exception as e:
                    logging.error(f"Error closing WebSocket connection: {e}")

    def _handle_message(self, message: str):
        self.on_message_callback(message)

    async def send_message(self, message: str):
        await self._rate_limit(message)
        try:
            await self.ws.send(message)
            logging.debug(f"Sent message: {message}")
        except Exception as e:
            self.on_error_callback(e)

    async def _rate_limit(self, message: str):
        with self.lock:
            now = time.time()
            while len(self.request_timestamps) >= self.rate_limit_max_requests:
                oldest_timestamp = self.request_timestamps.pop(0)
                if now - oldest_timestamp > self.rate_limit_window_seconds:
                    pass # Allow to continue
                else:
                    await asyncio.sleep(0.1) # Sleep to avoid busy-waiting
            self.request_timestamps.append(now)

    async def close(self):
        if self.ws:
            try:
                await self.ws.close()
                logging.info("WebSocket connection closed.")
            except Exception as e:
                logging.error(f"Error closing WebSocket connection: {e}")

async def main():
    # Example Usage
    url = os.environ.get("WS_URL", "ws://localhost:8765")
    on_message_callback = lambda msg: print(f"Received: {msg}")
    
    service = WebSocketService(url=url, on_message_callback=on_message_callback)
    
    try:
        await service.connect()
        # Simulate sending messages
        await asyncio.sleep(10)
        await service.send_message("Hello, WebSocket!")
        await asyncio.sleep(1)
        await service.send_message("Another message")
        await asyncio.sleep(1)
        await service.send_message("Yet another message")
        await asyncio.sleep(1)
        await service.send_message("And one more")
        await asyncio.sleep(1)
        await service.send_message("Final message")
        await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(main())