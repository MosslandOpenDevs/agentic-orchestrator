import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
from collections import deque
import aioredis
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedStatus, ConnectionClosedException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10  # requests
CACHE_TTL = 300  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds

# Environment Variable Configuration
WEBSOCKET_SERVER_URL = os.environ.get("WEBSOCKET_SERVER_URL", "ws://localhost:8765")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
RATE_LIMIT_REDIS_KEY = "rate_limit"


class WebSocketService:
    def __init__(self):
        self.rate_limit_redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        self.cache = {}
        self.retry_lock = asyncio.Lock()
        self.connection_count = 0
        self.connections = {}  # Store connections for rate limiting

    async def _rate_limit(self) -> bool:
        """
        Rate limiting using Redis.
        """
        with self.retry_lock:
            key = RATE_LIMIT_REDIS_KEY
            count = await self.rate_limit_redis.get(key)
            if count is None:
                await self.rate_limit_redis.set(key, 1)
                return True
            else:
                await self.rate_limit_redis.incr(key)
                if int(count) > RATE_LIMIT_MAX:
                    return False
                return True

    async def _cache_get(self, key: str) -> Optional[Any]:
        """
        Retrieves data from the cache.
        """
        if key in self.cache:
            if time.time() - self.cache[key]["timestamp"] < CACHE_TTL:
                return self.cache[key]["value"]
            else:
                del self.cache[key]
        return None

    async def _cache_set(self, key: str, value: Any) -> None:
        """
        Sets data in the cache.
        """
        self.cache[key] = {"value": value, "timestamp": time.time()}

    async def connect(self, websocket: websockets.WebSocketClient):
        """
        Handles a new WebSocket connection.
        """
        self.connection_count += 1
        self.connections[websocket.id] = True
        logging.info(f"New connection established: {websocket.id}")

        try:
            async for message in websocket:
                logging.info(f"Received message from {websocket.id}: {message}")
                # Process the message here (replace with your logic)
                response = f"Server received: {message}"
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosedOK:
            logging.info(f"Connection {websocket.id} closed normally.")
        except websockets.exceptions.ConnectionClosedStatus as e:
            logging.error(f"Connection {websocket.id} closed with status {e}")
        except ConnectionClosedException as e:
            logging.error(f"Connection {websocket.id} closed unexpectedly: {e}")
        except Exception as e:
            logging.exception(f"An error occurred during communication with {websocket.id}: {e}")
        finally:
            self.connection_count -= 1
            self.connections[websocket.id] = False
            logging.info(f"Connection {websocket.id} closed.")

    async def disconnect(self, websocket_id: str):
        """
        Handles a WebSocket disconnection.
        """
        if websocket_id in self.connections:
            del self.connections[websocket_id]
            logging.info(f"Connection {websocket_id} disconnected.")

    async def run(self):
        """
        Main function to run the WebSocket service.
        """
        async with aioredis.ConnectionPool(aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT)) as pool:
            try:
                async with websockets.serve(self.connect, "localhost", 8765):
                    logging.info("WebSocket server started on ws://localhost:8765")
                    await asyncio.Future()  # Run forever
            except websockets.exceptions.WebSocketException as e:
                logging.error(f"WebSocket server error: {e}")
            finally:
                self.disconnect_all()

    def disconnect_all(self):
        """
        Disconnects all active WebSocket connections.
        """
        for websocket_id in list(self.connections.keys()):
            try:
                self.connections[websocket_id].disconnect()
            except Exception as e:
                logging.exception(f"Error disconnecting connection {websocket_id}: {e}")
            self.disconnect(websocket_id)
        self.connections = {}


if __name__ == "__main__":
    service = WebSocketService()
    asyncio.run(service.run())