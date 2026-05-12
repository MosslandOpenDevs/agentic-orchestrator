import asyncio
import logging
import time
import os
import json
from collections import deque
from typing import Dict, Any, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, ws_url: str, rate_limit: int = 10, retry_count: int = 3, retry_delay: float = 1.0, cache_duration: int = 60):
        self.ws_url = ws_url
        self.rate_limit = rate_limit
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.cache_duration = cache_duration
        self.connected_clients = set()
        self.message_queue = deque()
        self.message_lock = asyncio.Lock()
        self.cache = {}

    def _log(self, message: str):
        logging.info(message)

    def _rate_limit(self, func: Callable):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            while len(self.connected_clients) >= self.rate_limit:
                time.sleep(0.1)
            return func(*args, **kwargs)
        return wrapper

    def _retry(self, func: Callable, max_retries: int = self.retry_count, delay: float = self.retry_delay):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self._log(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
        return wrapper

    def _cache_get(self, key: str, default: Any = None):
        if key in self.cache and time.time() - self.cache_duration < 0:
            self._log(f"Cache hit for key: {key}")
            return self.cache[key]
        else:
            self._log(f"Cache miss for key: {key}")
            return default

    def _cache_set(self, key: str, value: Any):
        self.cache[key] = value
        time.sleep(self.cache_duration)

    def connect(self):
        try:
            self._log(f"Connecting to WebSocket server at {self.ws_url}")
            ws = asyncio.wrap_future(asyncio.open_connection('', int(self.ws_url.split(':')[1]))).result()
            self.connected_clients.add(ws)
            self._log(f"Connected to WebSocket server at {self.ws_url}")
            return ws
        except Exception as e:
            self._log(f"Failed to connect to WebSocket server: {e}")
            return None

    def disconnect(self, ws):
        if ws in self.connected_clients:
            self.connected_clients.remove(ws)
            try:
                ws.close()
                self._log(f"Disconnected WebSocket client.")
            except Exception as e:
                self._log(f"Error closing WebSocket connection: {e}")

    def send_message(self, ws: asyncio.Transport, message: Dict):
        try:
            async def send_async(ws: asyncio.Transport, message: Dict):
                try:
                    await ws.send_json(message)
                    self._log(f"Sent message: {message}")
                except Exception as e:
                    self._log(f"Error sending message: {e}")

            send_async(ws, message)
        except Exception as e:
            self._log(f"Error sending message to specific WebSocket: {e}")

    def receive_message(self, ws: asyncio.Transport):
        try:
            async def receive_async(ws: asyncio.Transport):
                while True:
                    try:
                        message = await ws.recv_json()
                        self.message_queue.append(message)
                        self._log(f"Received message: {message}")
                    except Exception as e:
                        if ws.running:
                            self._log(f"Error receiving message: {e}")
                        else:
                            break
                    await asyncio.sleep(0.01)

            await receive_async(ws)
        except Exception as e:
            self._log(f"Error receiving message from WebSocket: {e}")

    def get_message(self):
        with self.message_lock:
            if self.message_queue:
                message = self.message_queue.popleft()
                return message
            else:
                return None

    @_rate_limit
    @_retry
    def run(self):
        ws = self.connect()
        if ws:
            async def main_task():
                asyncio.create_task(self.receive_message(ws))
                while True:
                    await asyncio.sleep(1)
                    if len(self.connected_clients) == 0:
                        break
            asyncio.create_task(main_task())
            try:
                asyncio.get_event_loop().run_forever()
            except KeyboardInterrupt:
                pass
            finally:
                self.disconnect(ws)
        else:
            self._log("Failed to connect to WebSocket server.")

if __name__ == '__main__':
    # Example Usage (replace with your WebSocket server URL)
    ws_url = os.environ.get("WS_URL", "ws://localhost:8000")
    service = WebSocketService(ws_url=ws_url, rate_limit=5, retry_count=3, retry_delay=0.5, cache_duration=10)
    service.run()