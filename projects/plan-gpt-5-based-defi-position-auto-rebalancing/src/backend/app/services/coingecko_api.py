import os
import time
import logging
import requests
from typing import Dict, Optional, List
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class CoingeckoService:
    def __init__(self, api_key: str, rate_limit_interval: int = 60, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.executor = ThreadPoolExecutor(max_workers=5)  # Adjust based on needs
        self.cache = {}  # Simple in-memory cache

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Makes a request to the Coingecko API with retry logic."""
        for attempt in range(self.max_retries):
            try:
                url = f"{self.base_url}{endpoint}"
                if params:
                    url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
                response = requests.get(url, headers={"X-CG-Token": self.api_key})
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logging.error("Max retries reached.  Request failed.")
                    return None
        return None

    def get_coin_info(self, coin_id: str) -> Optional[Dict]:
        """Retrieves information for a specific coin."""
        cache_key = f"coin_info_{coin_id}"
        if coin_id in self.cache and time.time() - self.cache[coin_id].get("timestamp", 0) < self.rate_limit_interval:
            logging.debug(f"Returning cached data for {coin_id}")
            return self.cache[coin_id]

        data = self._make_request(f"coins/{coin_id}")
        if data:
            self.cache[coin_id] = {"timestamp": time.time(), "data": data}
            logging.debug(f"Fetched data for {coin_id} and cached.")
        else:
            logging.warning(f"Failed to fetch data for {coin_id}")
        return data

    def get_trending_coins(self, market_type: str = "default") -> List[Dict]:
        """Retrieves a list of trending coins."""
        try:
            data = self._make_request(f"coins/trending?market_type={market_type}")
            if data:
                return data
            else:
                logging.warning("Failed to fetch trending coins.")
                return []
        except Exception as e:
            logging.error(f"Error fetching trending coins: {e}")
            return []

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Optional[float]:
        """Retrieves the price of a coin in a specific currency."""
        try:
            data = self._make_request(f"coins/{coin_id}/markets?vs_currency={vs_currency}")
            if data:
                return data[0]["price"]
            else:
                logging.warning(f"Failed to fetch price for {coin_id} in {vs_currency}")
                return None
        except Exception as e:
            logging.error(f"Error fetching price for {coin_id}: {e}")
            return None

    def clear_cache(self):
        """Clears the in-memory cache."""
        self.cache = {}