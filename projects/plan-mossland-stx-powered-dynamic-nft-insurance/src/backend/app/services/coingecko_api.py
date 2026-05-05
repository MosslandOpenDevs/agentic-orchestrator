import os
import time
import logging
import requests
from typing import Dict, Optional, List
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CoingeckoService:
    """
    Service for integrating with the Coingecko API.
    """

    def __init__(self, api_key: str, cache_duration: timedelta = timedelta(hours=12)):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: The Coingecko API key.
            cache_duration: The duration for which cached data should be considered valid.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_duration = cache_duration
        self.retry_count = 3  # Max retry attempts
        self.retry_delay = 2  # Seconds between retries

    def _cache_key(self, endpoint: str, params: Dict) -> str:
        """Generates a cache key based on the endpoint and parameters."""
        return f"{endpoint}-{str(params)}"

    def _get_from_cache(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Retrieves data from the cache."""
        key = self._cache_key(endpoint, params)
        if key in self.cache and self.cache[key]["expiry"] > datetime.now():
            logging.debug(f"Cache hit for {key}")
            return self.cache[key]["data"]
        return None

    def _cache_result(self, endpoint: str, params: Dict, data: Dict) -> None:
        """Caches the result for a specified duration."""
        key = self._cache_key(endpoint, params)
        expiry = datetime.now() + self.cache_duration
        self.cache[key] = {"data": data, "expiry": expiry}

    @retry(stop=retry_if_exception_type((RequestException, TimeoutError)),
           max=self.retry_count,
           wait=self.retry_delay,
           reraise=True)
    def fetch_ticker(self, symbol: str) -> Dict:
        """
        Fetches the ticker data for a given cryptocurrency symbol.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            A dictionary containing the ticker data.

        Raises:
            Exception: If the API request fails after multiple retries.
        """
        url = f"{self.base_url}/exchange/v3/ticker/{symbol}"
        params = {"vs_currency": "usd"}
        data = self._get_from_cache(url, params)
        if data is None:
            logging.info(f"Fetching ticker for {symbol}...")
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                data = response.json()
                self._cache_result(url, params, data)
            except RequestException as e:
                logging.error(f"Error fetching ticker for {symbol}: {e}")
                raise
        return data

    def fetch_price(self, symbol: str) -> float:
        """
        Fetches the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price.
        """
        try:
            ticker = self.fetch_ticker(symbol)
            return float(ticker["last"])
        except Exception as e:
            logging.error(f"Error fetching price for {symbol}: {e}")
            raise

    def fetch_all_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetches the current prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary containing the current prices for each cryptocurrency.
        """
        prices = {}
        for symbol in symbols:
            try:
                prices[symbol] = self.fetch_price(symbol)
            except Exception:
                prices[symbol] = None  # Handle errors gracefully
        return prices