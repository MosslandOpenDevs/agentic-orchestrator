import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional
from collections import deque
import rate_limiter
from websockets import connect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
WS_URL = os.environ.get("WS_URL", "ws://localhost:8765")
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 10))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 60))
MAX_MESSAGE_BUFFER_SIZE = int(os.environ.get("MAX_MESSAGE_BUFFER_SIZE", 100))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", 0.5))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))

# Rate limiter
rate_limiter_instance = rate_limiter.RateLimiter(max_rate=RATE_LIMIT_MAX, period=RATE_LIMIT_WINDOW)

# Message buffer
message_buffer = deque(maxlen=MAX_MESSAGE_BUFFER_SIZE)


class WebSocketService:
    def __init__(self):
        self.ws: Optional[websockets.Connection] = None
        self.connect = None
        self.disconnect = None
        self.send_message = None
        self.receive_message = None
        self.retry_count = 0

    async def connect_to_websocket(self):
        try:
            self.ws = await connect(WS_URL)
            logging.info(f"Connected to WebSocket server at {WS_URL}")
            return True
        except Exception as e:
            logging.error(f"Error connecting to WebSocket: {e}")
            return False

    async def disconnect_from_websocket(self):
        if self.ws:
            try:
                await self.ws.close()
                logging.info("Disconnected from WebSocket server.")
            except Exception as e:
                logging.error(f"Error disconnecting from WebSocket: {e}")
            finally:
                self.ws = None

    async def send_message(self, message: str) -> bool:
        if not self.ws:
            logging.warning("WebSocket is not connected. Cannot send message.")
            return False

        try:
            if rate_limiter_instance.wait(0.1):
                await self.ws.send(message)
                logging.debug(f"Sent message: {message}")
                return True
            else:
                logging.debug("Rate limit exceeded.")
                return False
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False

    async def receive_message(self) -> Optional[str]:
        try:
            if not self.ws:
                logging.warning("WebSocket is not connected. Cannot receive message.")
                return None

            async def _receive():
                while True:
                    try:
                        message = await self.ws.recv()
                        logging.debug(f"Received message: {message}")
                        return message
                    except websockets.exceptions.ConnectionClosedError as e:
                        logging.error(f"Connection closed unexpectedly: {e}")
                        return None
                    except Exception as e:
                        logging.error(f"Error receiving message: {e}")
                        return None

            return await _receive()
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    async def handle_message(self, callback: Callable[[], Any]) -> None:
        try:
            message = await self.receive_message()
            if message:
                result = await callback()
                if result is not None:
                    await self.send_message(str(result))
        except Exception as e:
            logging.error(f"Error in message handler: {e}")

    async def run_forever(self):
        try:
            while True:
                await self.handle_message(self.handle_callback)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logging.info("WebSocket service stopped.")
        finally:
            await self.disconnect_from_websocket()

    def start(self):
        asyncio.create_task(self.run_forever())

    def stop(self):
        asyncio.get_event_loop().call_soon_threadsafe(self.stop_running)

    def stop_running(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logging.error(f"Error closing websocket: {e}")
        self.ws = None
        logging.info("WebSocket service stopped.")


if __name__ == "__main__":
    service = WebSocketService()
    service.start()

    try:
        # Example usage
        async def my_callback():
            await time.sleep(1)
            return "Hello from callback!"

        service.handle_message(my_callback)
        while True:
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        service.stop()