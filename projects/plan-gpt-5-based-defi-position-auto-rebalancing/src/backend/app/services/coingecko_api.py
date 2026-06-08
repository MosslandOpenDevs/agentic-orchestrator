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
            max_retries: Maximum number of retries for transient errors.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.retry_delay = 2  # Seconds to wait before retrying
        self.executor = ThreadPoolExecutor(max_workers=5) # Thread pool for concurrent requests

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint.
            params: Query parameters.

        Returns:
            The JSON response from the API.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        headers = {"X-CG-VERSION": "v3", "Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logging.error(f"Request failed for {endpoint}: {e}")
            raise

    def get_ticker(self, symbol: str) -> Dict:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker information as a dictionary.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        endpoint = f"{self.base_url}/exchange/{symbol}/ticker"
        return self._make_request(endpoint)

    def get_price(self, symbol: str) -> float:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price as a float.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        ticker = self.get_ticker(symbol)
        return ticker["last"]

    def get_latest_trades(self, symbol: str) -> List[Dict]:
        """
        Gets the latest trades for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The latest trades as a list of dictionaries.
        """
        endpoint = f"{self.base_url}/exchange/{symbol}/trades"
        return self._make_request(endpoint)

    def get_market_data(self, symbol: str, timeframe: str) -> List[Dict]:
        """
        Gets market data for a cryptocurrency within a specific timeframe.

        Args:
            symbol: The cryptocurrency symbol.
            timeframe: The timeframe (e.g., "1m", "5m", "1h").

        Returns:
            The market data as a list of dictionaries.
        """
        endpoint = f"{self.base_url}/exchange/{symbol}/chart"
        params = {"vs_currency": "usd", "timeframe": timeframe}
        return self._make_request(endpoint, params)

    def get_all_currencies(self) -> List[str]:
        """
        Gets a list of all available cryptocurrency symbols.
        """
        response = self._make_request(f"{self.base_url}/coins/list")
        return [coin["id"] for coin in response]

    def rate_limit_wait(self) -> None:
        """
        Waits for the rate limit interval to pass.
        """
        time.sleep(self.rate_limit_interval)

    def retry_request(self, func, *args, **kwargs):
        """
        Retries a request with exponential backoff.
        """
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (2 ** attempt))