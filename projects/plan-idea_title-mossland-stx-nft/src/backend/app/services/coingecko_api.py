import os
import time
import logging
import requests
from typing import Dict, Optional, Union
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class CoingeckoService:
    """
    Service for integrating with the Coingecko API.
    """

    def __init__(self, api_key: str, rate_limit_delay: int = 1, max_retries: int = 3):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: The Coingecko API key.
            rate_limit_delay: Delay in seconds between API requests to respect rate limits.
            max_retries: Maximum number of retries for a failed request.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.executor = ThreadPoolExecutor(max_workers=5)  # Use thread pool for concurrency
        self.cache = {}  # Simple in-memory cache

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint.
            params: Query parameters.

        Returns:
            The JSON response as a dictionary, or None if an error occurred.
        """
        headers = {"X-CG-VERSION": "v3", "Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logging.error(f"Request failed for {endpoint}: {e}")
            return None
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return None

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Gets the ticker for a given cryptocurrency symbol.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker data as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/exchange/{symbol}/ticker"
        cached_data = self.cache.get(symbol)
        if cached_data:
            logging.debug(f"Fetching ticker for {symbol} from cache.")
            return cached_data

        data = self._make_request(endpoint)
        if data:
            self.cache[symbol] = data
        return data

    def get_coin_info(self, symbol: str) -> Optional[Dict]:
        """
        Gets the basic information for a given cryptocurrency symbol.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The coin information as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/coins/{symbol}"
        cached_data = self.cache.get(symbol)
        if cached_data:
            logging.debug(f"Fetching coin info for {symbol} from cache.")
            return cached_data

        data = self._make_request(endpoint)
        if data:
            self.cache[symbol] = data
        return data

    def get_price(self, symbol: str, vs_currency: str = "usd") -> Optional[float]:
        """
        Gets the price of a cryptocurrency in a specified currency.

        Args:
            symbol: The cryptocurrency symbol.
            vs_currency: The currency to convert to (default: "usd").

        Returns:
            The price as a float, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/simple/price?ids={symbol}&vs_currency={vs_currency}"
        cached_data = self.cache.get((symbol, vs_currency))
        if cached_data:
            logging.debug(f"Fetching price for {symbol} in {vs_currency} from cache.")
            return cached_data

        data = self._make_request(endpoint)
        if data and symbol in data:
            self.cache[(symbol, vs_currency)] = data[symbol]
        return data.get(symbol)

    def get_market_data(self, symbol: str, timeframe: str = "1h") -> Optional[Dict]:
        """
        Gets the market data for a given cryptocurrency symbol and timeframe.

        Args:
            symbol: The cryptocurrency symbol.
            timeframe: The timeframe to fetch data for (e.g., "1h", "1m", "7d").

        Returns:
            The market data as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/exchange/{symbol}/chart"
        params = {"period": timeframe}
        cached_data = self.cache.get((symbol, timeframe))
        if cached_data:
            logging.debug(f"Fetching market data for {symbol} in {timeframe} from cache.")
            return cached_data

        data = self._make_request(endpoint, params)
        if data:
            self.cache[(symbol, timeframe)] = data
        return data

    def clear_cache(self):
        """
        Clears the in-memory cache.
        """
        self.cache.clear()
        logging.info("Cache cleared.")