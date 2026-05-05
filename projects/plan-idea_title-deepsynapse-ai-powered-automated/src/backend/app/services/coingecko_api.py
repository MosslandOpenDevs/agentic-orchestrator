import os
import time
import logging
import requests
from typing import Dict, Optional, List
from requests.exceptions import RequestException
from tenacity import retry, retry_call, retry_wait
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CoingeckoService:
    """
    Service for integrating with the Coingecko API.
    """

    def __init__(self, api_key: str, cache_duration: timedelta = timedelta(minutes=5)):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: The Coingecko API key.
            cache_duration: The duration for which cached data is considered valid.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_duration = cache_duration
        self.retry_count = 3
        self.retry_wait = timedelta(seconds=2)

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Makes a request to the Coingecko API.
        Handles rate limiting, retries, and errors.

        Args:
            endpoint: The API endpoint to request.

        Returns:
            The JSON response from the API if successful, None otherwise.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {"X-CG-VERSION": "v3", "Accept": "application/json"}

        with retry(
            retry=retry_call(stop=self._should_retry, retry=self.retry_count,
                             wait=self.retry_wait,
                             reraise=True)
        ) as ret:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed for {url}: {e}")
                return None

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Gets the ticker data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker data if successful, None otherwise.
        """
        cache_key = f"ticker_{symbol}"
        if cache_key in self.cache and datetime.now() - datetime.fromtimestamp(self.cache[cache_key]['timestamp']) < self.cache_duration:
            logging.debug(f"Fetching ticker from cache for {symbol}")
            return self.cache[cache_key]

        data = self._make_request(f"exchange/{symbol}/tickers")
        if data:
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": data
            }
            logging.debug(f"Fetched ticker for {symbol} and cached.")
        return data

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The current price if successful, None otherwise.
        """
        ticker = self.get_ticker(symbol)
        if ticker and ticker["last"]:
            return float(ticker["last"])
        return None

    def get_market_caps(self, symbol: str) -> Optional[float]:
        """
        Gets the market cap of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The market cap if successful, None otherwise.
        """
        ticker = self.get_ticker(symbol)
        if ticker and ticker["market_caps"]:
            return float(ticker["market_caps"])
        return None

    def get_all_coins(self) -> List[str]:
        """
        Gets a list of all available cryptocurrency symbols.
        """
        response = self._make_request("coins/list")
        if response:
            return [coin["id"] for coin in response]
        return []