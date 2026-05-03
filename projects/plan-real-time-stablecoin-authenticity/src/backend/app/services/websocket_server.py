import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional
from collections import deque
from ratelimit import RateLimitException, RateLimitContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, reconnect_interval: int = 5, max_retries: int = 3, retry_delay: float = 1.0, rate_limit: int = 100, cache_expiry: int = 60):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit
        self.cache_expiry = cache_expiry
        self.connected = False
        self.ws = None
        self.cache = {}
        self.lock = asyncio.Lock()

    def connect(self):
        try:
            self.ws = asyncio.WebSocketClient.connect(self.url)
            self.connected = True
            logging.info(f"Connected to WebSocket server at {self.url}")
        except Exception as e:
            logging.error(f"Error connecting to WebSocket server: {e}")
            self.connected = False
            self.ws = None

    def disconnect(self):
        if self.ws:
            try:
                self.ws.close()
                self.connected = False
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting from WebSocket server: {e}")
            finally:
                self.ws = None

    def send_message(self, message: str) -> bool:
        if not self.connected:
            logging.warning("Not connected to WebSocket server. Cannot send message.")
            return False

        try:
            with RateLimitContext(self.rate_limit):
                self.ws.send(message)
                logging.debug(f"Sent message: {message}")
                return True
        except RateLimitException as e:
            logging.warning(f"Rate limit exceeded: {e}")
            return False
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False

    def receive_message(self) -> Optional[str]:
        if not self.connected:
            logging.warning("Not connected to WebSocket server. Cannot receive message.")
            return None

        try:
            async def _receive():
                while True:
                    try:
                        message = await self.ws.recv()
                        return message
                    except Exception as e:
                        logging.error(f"Error receiving message: {e}")
                        return None
            return _receive()
        except Exception as e:
            logging.error(f"Error in receive_message: {e}")
            return None

    def run(self, callback: Callable[[str], None], message_callback: Optional[Callable[[str], None]] = None):
        async def main():
            self.connect()
            if not self.connected:
                self.disconnect()
                return

            try:
                while True:
                    message = self.receive_message()
                    if message:
                        if message_callback:
                            message_callback(message)
                        else:
                            logging.debug(f"Received message: {message}")
                    await asyncio.sleep(0.1)  # Avoid busy-waiting
            except asyncio.CancelledError:
                logging.info("WebSocket service cancelled.")
            finally:
                self.disconnect()

        asyncio.create_task(main())

    def get_cached_data(self, key: str) -> Optional[str]:
        try:
            expiry_time = self.cache_expiry
            if key in self.cache and time.time() - self.cache[key]['timestamp'] < expiry_time:
                logging.debug(f"Cache hit for key: {key}")
                return self.cache[key]['value']
            else:
                logging.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logging.error(f"Error accessing cache: {e}")
            return None

    def set_cached_data(self, key: str, value: str):
        try:
            self.cache[key] = {'value': value, 'timestamp': time.time()}
            logging.debug(f"Cached data for key: {key}")
        except Exception as e:
            logging.error(f"Error setting cache: {e}")

    def retry_connect(self):
        while True:
            try:
                self.connect()
                if self.connected:
                    return
            except Exception as e:
                logging.error(f"Retry connect failed: {e}")
            time.sleep(self.reconnect_interval)

if __name__ == '__main__':
    # Example Usage (replace with your actual WebSocket URL)
    ws_service = WebSocketService(url="ws://localhost:8000")  # Replace with your WebSocket URL
    
    def handle_message(message):
        print(f"Received message: {message}")

    ws_service.run(handle_message)