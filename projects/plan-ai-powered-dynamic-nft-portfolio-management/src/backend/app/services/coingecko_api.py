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
        """
        Initializes the CoingeckoService.

        Args:
            api_key: Your Coingecko API key.
            rate_limit_interval: Interval in seconds for rate limiting.
            max_retries: Maximum number of retries for a request.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.retry_delay = 2  # Seconds to wait before retrying
        self.executor = ThreadPoolExecutor(max_workers=5) # Thread pool for concurrent requests
        self.cache = {} # Simple in-memory cache

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API with retry logic.

        Args:
            endpoint: The API endpoint.
            params: Query parameters.

        Returns:
            The JSON response from the API.

        Raises:
            requests.exceptions.RequestException: If the request fails after multiple retries.
        """
        for attempt in range(self.max_retries):
            try:
                url = f"{self.base_url}{endpoint}"
                headers = {"X-CG-Token": self.api_key}
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    logging.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise  # Re-raise the exception if all retries failed

    def get_ticker(self, symbol: str) -> Dict:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker data as a dictionary.
        """
        cache_key = f"ticker:{symbol}"
        if cache_key in self.cache:
            logging.debug(f"Fetching ticker from cache for {symbol}")
            return self.cache[cache_key]

        ticker = self._make_request(f"/coins/{symbol}/tickers")
        self.cache[cache_key] = ticker
        return ticker

    def get_price(self, symbol: str) -> float:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price as a float.
        """
        ticker = self.get_ticker(symbol)
        return ticker["last"]

    def get_market_caps(self, symbol: str) -> Dict:
        """
        Gets the market cap information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The market cap data as a dictionary.
        """
        cache_key = f"market_caps:{symbol}"
        if cache_key in self.cache:
            logging.debug(f"Fetching market caps from cache for {symbol}")
            return self.cache[cache_key]

        market_caps = self._make_request(f"/coins/{symbol}/market_caps")
        self.cache[cache_key] = market_caps
        return market_caps

    def get_all_coins(self) -> List[Dict]:
        """
        Gets a list of all available coins.

        Returns:
            A list of coin dictionaries.
        """
        coins = self._make_request("/coins/list")
        return coins

    def get_coin_info(self, symbol: str) -> Dict:
        """
        Gets the information for a specific coin.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The coin information as a dictionary.
        """
        coin_info = self._make_request(f"/coins/{symbol}")
        return coin_info

    def clear_cache(self):
        """
        Clears the in-memory cache.
        """
        self.cache = {}
        logging.info("Cache cleared.")