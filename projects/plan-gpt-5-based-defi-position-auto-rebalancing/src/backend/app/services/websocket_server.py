import asyncio
import logging
import time
import os
from typing import Callable, Dict, Optional, Any

from websockets import connect

# Configuration
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 5
CACHE_EXPIRY_SECONDS = 60
LOG_LEVEL = logging.INFO

# Logging setup
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, url: str, connect_timeout: int = 10, retry_attempts: int = 3):
        self.url = url
        self.connect_timeout = connect_timeout
        self.retry_attempts = retry_attempts
        self.last_request_time = 0
        self.request_count = 0
        self.cache = {}  # Simple in-memory cache
        self.lock = asyncio.Lock()

    async def _connect(self) -> websockets.Connection:
        try:
            async with connect(self.url, timeout=self.connect_timeout) as websocket:
                logging.info(f"Connected to WebSocket server at {self.url}")
                return websocket
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedStatus,
                websockets.exceptions.ConnectionClosedError) as e:
            logging.error(f"WebSocket connection error: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected WebSocket connection error: {e}")
            raise

    async def _send_message(self, websocket: websockets.Connection, message: Any) -> bool:
        with self.lock:
            now = time.time()
            if now - self.last_request_time < self.RATE_LIMIT_WINDOW_SECONDS:
                self.request_count += 1
                if self.request_count > RATE_LIMIT_MAX_REQUESTS:
                    await asyncio.sleep(self.RATE_LIMIT_WINDOW_SECONDS)
            else:
                self.last_request_time = now
                self.request_count = 1

            try:
                await websocket.send(str(message))
                logging.debug(f"Sent message: {message}")
                return True
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                return False

    async def _receive_message(self, websocket: websockets.Connection) -> Optional[Any]:
        try:
            message = await websocket.recv()
            logging.debug(f"Received message: {message}")
            return message
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    async def send_and_receive(self, callback: Callable[[Any], None]) -> None:
        try:
            websocket = await self._connect()
            message = await self._send_message(websocket, "Hello from client")
            if message:
                received_message = await self._receive_message(websocket)
                if received_message is not None:
                    callback(received_message)
                else:
                    logging.warning("Received message was None.")
            else:
                logging.error("Failed to send initial message.")
        except Exception as e:
            logging.error(f"Error during send and receive: {e}")
        finally:
            try:
                await websocket.close()
            except Exception as e:
                logging.error(f"Error closing websocket: {e}")

    async def run_forever(self):
        while True:
            try:
                await self.send_and_receive(lambda x: print(f"Callback received: {x}"))
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                logging.info("WebSocket service cancelled.")
                break
            except Exception as e:
                logging.error(f"Unexpected error in run_forever: {e}")

    def start(self):
        asyncio.create_task(self.run_forever())

    def stop(self):
        # No explicit stop mechanism implemented for simplicity.
        # In a real application, you'd need to gracefully close the websocket.
        pass


if __name__ == '__main__':
    # Example Usage (replace with your WebSocket server URL)
    ws_url = os.environ.get("WS_URL", "ws://localhost:8765")
    service = WebSocketService(ws_url)
    service.start()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Stopping WebSocket service...")
        service.stop()