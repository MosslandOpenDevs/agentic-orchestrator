import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any

from websockets import connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, retry_interval: float = 1.0, max_retries: int = 3, rate_limit: int = 10):
        self.url = url
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.connection = None
        self.session = None
        self.callbacks = {}

    def connect(self):
        try:
            self.connection = connect(self.url)
            self.session = self.connection
            asyncio.create_task(self._rate_limit())
            logging.info(f"Connected to WebSocket server at {self.url}")
        except ConnectionError as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            raise

    def disconnect(self):
        if self.connection:
            self.connection.close()
            asyncio.get_event_loop().remove_callback(self._rate_limit)
            logging.info("Disconnected from WebSocket server.")

    def register_callback(self, event_name: str, callback: Callable):
        self.callbacks[event_name] = callback

    def send_message(self, message: str):
        if not self.connection:
            logging.warning("WebSocket connection not established. Cannot send message.")
            return

        now = time.time()
        if now - self.last_request_time < 1 / self.rate_limit:
            logging.debug(f"Rate limit exceeded for message: {message}")
            return

        self.last_request_time = now
        try:
            async with self.session.send(message) as response:
                if response:
                    logging.debug(f"Message sent and received: {message}")
        except ConnectionError as e:
            logging.error(f"Error sending message: {e}")
            self._retry_send(message)
        except Exception as e:
            logging.exception(f"Unexpected error sending message: {e}")

    def _retry_send(self, message: str):
        for attempt in range(self.max_retries):
            try:
                async with self.session.send(message) as response:
                    if response:
                        logging.debug(f"Message sent after retry: {message}")
                        return
            except ConnectionError as e:
                logging.error(f"Retry attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logging.error(f"Max retries reached for message: {message}")
            time.sleep(self.retry_interval)

    def _rate_limit(self):
        while True:
            time.sleep(1 / self.rate_limit)
            # This is a placeholder for more sophisticated rate limiting
            # Consider using a dedicated rate limiting library for production
            pass

    async def receive_messages(self):
        try:
            async for message in self.connection:
                for event_name, callback in self.callbacks.items():
                    try:
                        callback(message)
                    except Exception as e:
                        logging.exception(f"Error in callback for event {event_name}: {e}")
        except ConnectionError as e:
            logging.error(f"Connection error during message reception: {e}")
        finally:
            self.disconnect()

if __name__ == '__main__':
    # Example Usage (Replace with your actual WebSocket URL)
    ws_url = os.environ.get("WS_URL", "ws://localhost:8765")
    service = WebSocketService(ws_url=ws_url, retry_interval=0.5, max_retries=2, rate_limit=5)

    try:
        service.connect()
        asyncio.create_task(service.receive_messages())

        # Simulate sending messages
        service.send_message("Hello, WebSocket Server!")
        time.sleep(1)
        service.send_message("This is another message.")
        time.sleep(1)

    except Exception as e:
        logging.exception(f"An error occurred: {e}")
    finally:
        if service.connection:
            service.disconnect()