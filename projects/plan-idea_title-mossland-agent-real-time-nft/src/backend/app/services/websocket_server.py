import asyncio
import logging
import time
import os
from typing import Callable, Dict, Any, Optional
from collections import deque
import aioredis  # Use aioredis for asynchronous Redis
from aioredis.exceptions import RedisError

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WebSocketService:
    def __init__(self, redis_host: str = os.environ.get("REDIS_HOST", "localhost"),
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 cache_ttl: int = 60,
                 rate_limit_interval: int = 10,
                 max_rate_limit: int = 100,
                 ):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.cache_ttl = cache_ttl
        self.rate_limit_interval = rate_limit_interval
        self.max_rate_limit = max_rate_limit
        self.rate_limits = {}  # Rate limit per user
        self.cache = {}
        self.connection_pool = None
        self.logger = logging.getLogger(__name__)

        try:
            self.connection_pool = aioredis.ConnectionPool(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                max_connections=10
            )
        except RedisError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def _get_rate_limit(self, user_id: str) -> int:
        """Retrieves the rate limit for a user from Redis."""
        key = f"rate_limit:{user_id}"
        current_time = int(time.time())
        if key not in self.rate_limits:
            self.rate_limits[key] = deque()
        
        # Remove old entries
        while self.rate_limits[key] and self.rate_limits[key][0] <= current_time - self.rate_limit_interval:
            self.rate_limits[key].popleft()

        count = len(self.rate_limits[key])
        if count >= self.max_rate_limit:
            await asyncio.sleep(self.rate_limit_interval)  # Wait before next request
            return 0
        
        self.rate_limits[key].append(current_time)
        return self.max_rate_limit - count

    async def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves data from the cache."""
        if key in self.cache:
            if self.cache[key]['expiration'] > time.time():
                self.logger.debug(f"Cache hit for key: {key}")
                return self.cache[key]['data']
            else:
                self.logger.debug(f"Cache expired for key: {key}, removing")
                del self.cache[key]
        return None

    async def _set_cached_data(self, key: str, data: Dict[str, Any], expiration: int):
        """Sets data in the cache."""
        self.cache[key] = {'data': data, 'expiration': time.time() + expiration}
        self.logger.debug(f"Cache set for key: {key}")

    async def handle_websocket(self, websocket: asyncio.WebSocketServerProtocol, callback: Callable):
        """Handles a single WebSocket connection."""
        user_id = "user_" + str(hash(websocket.remote_address))  # Simple user ID
        self.logger.info(f"New WebSocket connection from {websocket.remote_address}")

        try:
            rate_limit = await self._get_rate_limit(user_id)
            if rate_limit <= 0:
                self.logger.warning(f"Rate limit exceeded for user: {user_id}")
                await asyncio.sleep(1) # Avoid spamming
                continue

            # Cache the result
            cached_data = self._get_cached_data(f"data:{user_id}")
            if cached_data:
                self.logger.info(f"Serving cached data for user: {user_id}")
                await callback(cached_data)
                continue

            # Simulate some processing
            await asyncio.sleep(2)  # Simulate work

            data = {"message": "Hello from server!"}
            await callback(data)

            # Cache the result
            self._set_cached_data(f"data:{user_id}", data, self.cache_ttl)

        except Exception as e:
            self.logger.exception(f"Error handling WebSocket connection: {e}")
        finally:
            self.logger.info(f"WebSocket connection closed from {websocket.remote_address}")
            await websocket.close()

    async def start(self):
        """Starts the WebSocket server."""
        self.logger.info("Starting WebSocket server...")
        try:
            # Example WebSocket server setup (replace with your actual server)
            async with asyncio.ServerProtocol("websocket_server", self.handle_websocket) as server:
                self.logger.info("WebSocket server started.")
                await server.serve_forever()
        except Exception as e:
            self.logger.exception(f"Error starting WebSocket server: {e}")
        finally:
            self.logger.info("WebSocket server stopped.")

    async def stop(self):
        """Stops the WebSocket server."""
        self.logger.info("Stopping WebSocket server...")
        if self.connection_pool:
            try:
                await self.connection_pool.close()
            except Exception as e:
                self.logger.error(f"Error closing Redis connection pool: {e}")
        self.logger.info("WebSocket server stopped.")

if __name__ == '__main__':
    # Example usage (replace with your actual callback)
    async def my_callback(data: Dict[str, Any]):
        print(f"Received data: {data}")

    service = WebSocketService()
    service.start()