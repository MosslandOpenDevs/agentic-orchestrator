import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any
from collections import deque
import rate_limiter
from websockets import connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
WS_URL = os.environ.get("WS_URL", "ws://localhost:8765")
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 10))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 5))
MAX_MESSAGE_QUEUE_SIZE = int(os.environ.get("MAX_MESSAGE_QUEUE_SIZE", 100))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", 0.5))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))


class WebSocketService:
    def __init__(self):
        self.ws: Optional[websockets.connect._Connection] = None
        self.message_queue: deque = deque()
        self.rate_limiter = rate_limiter.RateLimiter(max_rate=RATE_LIMIT_MAX, period=RATE_LIMIT_WINDOW)
        self.retry_count = 0
        self.is_running = False

    def connect(self):
        try:
            self.ws = connect(WS_URL)
            self.is_running = True
            logging.info(f"Connected to WebSocket server at {WS_URL}")
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket server: {e}")
            self.ws = None

    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.is_running = False
            logging.info("Disconnected from WebSocket server.")

    def send_message(self, message: str) -> bool:
        if not self.ws:
            logging.warning("WebSocket is not connected. Cannot send message.")
            return False

        try:
            with self.rate_limiter:
                self.ws.send(message)
                logging.debug(f"Sent message: {message}")
                return True
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False

    def receive_messages(self, callback: Callable[[str], None]) -> None:
        if not self.ws:
            logging.warning("WebSocket is not connected. Cannot receive messages.")
            return

        async def run():
            try:
                async for message in self.ws:
                    self.message_queue.append(message)
                    callback(message)
            except Exception as e:
                logging.error(f"Error receiving messages: {e}")
            finally:
                logging.info("Receive messages task completed.")

        asyncio.create_task(run())

    def process_messages(self, callback: Callable[[str], None]) -> None:
        while self.is_running:
            if self.message_queue:
                message = self.message_queue.popleft()
                callback(message)
            else:
                asyncio.sleep(0.1)  # Avoid busy-waiting

    def start(self):
        self.connect()
        if self.ws:
            receive_task = asyncio.create_task(self.receive_messages(self.process_messages))
            logging.info("Message processing started.")

    def stop(self):
        self.disconnect()
        logging.info("Service stopped.")

    def run_in_background(self):
        asyncio.run(self.process_messages(self.process_messages))

if __name__ == '__main__':
    service = WebSocketService()
    service.start()
    try:
        # Example usage
        for i in range(20):
            service.send_message(f"Message {i}")
            time.sleep(0.2)
    except KeyboardInterrupt:
        service.stop()