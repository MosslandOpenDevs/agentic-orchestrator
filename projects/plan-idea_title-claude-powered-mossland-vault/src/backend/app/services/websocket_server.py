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
WS_URI = os.environ.get("WS_URI", "ws://localhost:8765")
RATE_LIMIT_RATE = int(os.environ.get("RATE_LIMIT_RATE", 10))  # Requests per second
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", 100)) # Max requests
CACHE_TTL = int(os.environ.get("CACHE_TTL", 60)) # Cache TTL in seconds
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))

# Rate limiter
rate_limiter_instance = rate_limiter.RateLimiter(rate=RATE_LIMIT_RATE, max=RATE_LIMIT_MAX)

# Caching mechanism (using a deque for simplicity - replace with a proper cache for production)
message_cache = deque(maxlen=CACHE_TTL)

# Retry logic
retry_count = 0
retry_delay = 0.5

# WebSocket connection
websocket = None
async def connect_websocket():
    global websocket
    try:
        async with connect(WS_URI) as ws:
            websocket = ws
            logging.info(f"Connected to WebSocket server at {WS_URI}")
    except ConnectionError as e:
        logging.error(f"WebSocket connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected WebSocket error: {e}")
        raise

# Message handler
async def handle_message(callback: Callable[[str], None], message_id: str):
    try:
        if message_id in message_cache:
            logging.debug(f"Message {message_id} retrieved from cache.")
            callback(message_cache[message_id])
            return
        
        with rate_limiter_instance:
            try:
                await websocket.send(message_id)
                logging.debug(f"Sent message {message_id} to WebSocket server.")
            except Exception as e:
                logging.error(f"Error sending message {message_id}: {e}")
                
            # Retry logic
            for i in range(MAX_RETRIES):
                try:
                    await websocket.recv()
                    break
                except ConnectionError as e:
                    logging.error(f"WebSocket connection error during receive: {e}")
                    if i == MAX_RETRIES - 1:
                        logging.error(f"Max retries reached for message {message_id}")
                        raise
                    await asyncio.sleep(retry_delay * (i + 1))
                except Exception as e:
                    logging.error(f"Unexpected WebSocket error during receive: {e}")
                    if i == MAX_RETRIES - 1:
                        logging.error(f"Max retries reached for message {message_id}")
                        raise
                    await asyncio.sleep(retry_delay * (i + 1))
            else:
                logging.error(f"Failed to receive response for message {message_id} after multiple retries.")
                raise
        
        # Cache the message
        message_cache[message_id] = message_id
        logging.debug(f"Message {message_id} added to cache.")
    except Exception as e:
        logging.error(f"Error handling message {message_id}: {e}")
        raise

# Example usage (replace with your actual callback)
async def my_callback(message: str):
    logging.info(f"Received message: {message}")

async def main():
    try:
        await connect_websocket()
        # Example message handling
        await handle_message(my_callback, "message_1")
        await handle_message(my_callback, "message_2")
        await handle_message(my_callback, "message_1") # Retrieve from cache
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if websocket:
            try:
                await websocket.close()
                logging.info("WebSocket connection closed.")
            except Exception as e:
                logging.error(f"Error closing WebSocket connection: {e}")

if __name__ == "__main__":
    asyncio.run(main())