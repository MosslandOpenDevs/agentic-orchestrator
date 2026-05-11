import os
import time
import logging
import tenacity
import json
from typing import Dict, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable names
API_KEY_ENV = "COINGEKO_API_KEY"
CACHE_EXPIRY_SECONDS = 600  # 10 minutes

# Rate limiting configuration
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff

# Caching configuration
CACHE_MANAGER = None  # Will be initialized later

class CoingeckoService:
    def __init__(self):
        self.api_key = os.environ.get(API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"COINGEKO_API_KEY environment variable not set.")

        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache_key_prefix = "coingecko_"

        # Initialize tenacity for retry logic
        self.retry_client = tenacity.RetryClient(
            retries=MAX_RETRIES,
            backoff=tenacity.exponential_backoff(multiplier=BACKOFF_FACTOR),
            retry_on_exception=lambda e: isinstance(e, Exception),
        )

        # Initialize logging
        logging.getLogger(__name__).setLevel(logging.INFO)

    def _cache_get(self, key: str) -> Optional[Dict]:
        if not CACHE_MANAGER:
            CACHE_MANAGER = CacheManager()
        return CACHE_MANAGER.get(key)

    def _cache_set(self, key: str, data: Dict, expiry: timedelta = timedelta(minutes=CACHE_EXPIRY_SECONDS)):
        if not CACHE_MANAGER:
            CACHE_MANAGER = CacheManager()
        CACHE_MANAGER.set(key, data, expiry)

    def _cache_delete(self, key: str):
        if not CACHE_MANAGER:
            CACHE_MANAGER = CacheManager()
        CACHE_MANAGER.delete(key)

    def get_coin_info(self, coin_id: str) -> Optional[Dict]:
        """
        Retrieves information for a specific cryptocurrency.
        """
        url = f"{self.base_url}/coins/{coin_id}"
        data = self._retry_get(url)
        if data:
            self._cache_set(f"{self.cache_key_prefix}{coin_id}", data)
            return data
        else:
            logging.warning(f"Failed to retrieve coin info for {coin_id}")
            return None

    def get_ticker(self, coin_id: str) -> Optional[Dict]:
        """
        Retrieves the ticker (price) for a specific cryptocurrency.
        """
        url = f"{self.base_url}/coins/{coin_id}/tickers"
        data = self._retry_get(url)
        if data:
            self._cache_set(f"{self.cache_key_prefix}{coin_id}_ticker", data)
            return data
        else:
            logging.warning(f"Failed to retrieve ticker for {coin_id}")
            return None

    def get_current_price(self, coin_id: str) -> Optional[float]:
        """
        Retrieves the current price of a cryptocurrency.
        """
        ticker = self.get_ticker(coin_id)
        if ticker and ticker["last"]:
            return float(ticker["last"])
        else:
            logging.warning(f"Failed to retrieve current price for {coin_id}")
            return None

    def _retry_get(self, url: str) -> Optional[Dict]:
        try:
            response = tenacity.retry(
                self.retry_client,
                url
            ).get()
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"API request failed with status code {response.status_code}: {response.text}")
                return None
        except tenacity.RetryError as e:
            logging.error(f"Retry failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return None

class CacheManager:
    def __init__(self):
        self.cache = {}

    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            if self.cache[key]["expiry"] is None or datetime.utcnow() <= self.cache[key]["expiry"]:
                return self.cache[key]["data"]
            else:
                self._delete(key)
                return None
        return None

    def set(self, key: str, data: Dict, expiry: timedelta = timedelta(minutes=600)):
        self.cache[key] = {"data": data, "expiry": datetime.utcnow() + expiry}

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]

    def _delete(self, key: str):
        if key in self.cache:
            del self.cache[key]