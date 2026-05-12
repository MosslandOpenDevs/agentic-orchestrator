import os
import time
import logging
import requests
from typing import Dict, Optional, List
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CoingeckoService:
    """
    Service for integrating with the Coingecko API.
    """

    def __init__(self, api_key: str, rate_limit_interval: int = 60, max_retries: int = 3):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: The Coingecko API key.
            rate_limit_interval: The interval (in seconds) for rate limiting.
            max_retries: The maximum number of retries for transient failures.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.retry_delay = 2  # Seconds
        self.executor = ThreadPoolExecutor(max_workers=5) # Thread pool for concurrent requests

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint.
            params: The request parameters.

        Returns:
            The JSON response from the API.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        headers = {"X-CG-Token": self.api_key}
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logging.error(f"Request failed for {endpoint}: {e}")
            return None

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker information as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/exchange/{symbol}/tickers"
        data = self._make_request(endpoint)
        return data

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price as a float, or None if an error occurred.
        """
        ticker = self.get_ticker(symbol)
        if ticker and ticker.get("last"):
            return ticker["last"]
        else:
            return None

    def get_market_caps(self, symbol: str) -> Optional[float]:
        """
        Gets the market cap of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The market cap as a float, or None if an error occurred.
        """
        ticker = self.get_ticker(symbol)
        if ticker and ticker.get("market_caps"):
            return ticker["market_caps"]
        else:
            return None

    def get_all_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Gets the current prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where the keys are the symbols and the values are the prices.
        """
        prices = {}
        for symbol in symbols:
            prices[symbol] = self.get_price(symbol)
        return prices

    def get_coin_info(self, symbol: str) -> Optional[Dict]:
        """
        Gets the coin information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The coin information as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/coins/{symbol}"
        data = self._make_request(endpoint)
        return data

    def _retry_request(self, func, args=None, kwargs=None):
        """
        Retries a request with exponential backoff.
        """
        for attempt in range(self.max_retries):
            result = func(*args, **kwargs)
            if result is not None:
                return result
            time.sleep(self.retry_delay * (attempt + 1))
        return None

    def get_ticker_with_retry(self, symbol: str) -> Optional[Dict]:
        """
        Gets the ticker information for a cryptocurrency with retry logic.
        """
        return self._retry_request(self.get_ticker, args=(symbol,))