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
            cache_duration: The duration for which data is cached.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_duration = cache_duration
        self.retry_count = 3
        self.retry_wait = timedelta(seconds=2)

    def _make_request(self, endpoint: str) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint to request.

        Returns:
            The JSON response from the API.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {"X-CG-Token": self.api_key}

        with retry(
            stop=retry_call,
            max=self.retry_count,
            wait=retry_wait(retry_count=self.retry_count, multiplier=2),
            retry=retry_call
        ) as retries:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed: {e}")
                raise

    def get_ticker(self, symbol: str) -> Dict:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker information as a dictionary.
        """
        cache_key = f"ticker_{symbol}"
        if cache_key in self.cache and datetime.now() - datetime.fromtimestamp(self.cache[cache_key]['timestamp']) < self.cache_duration:
            logging.debug(f"Fetching ticker from cache for {symbol}")
            return self.cache[cache_key]

        ticker = self._make_request(f"coins/{symbol}/tickers")
        self.cache[cache_key] = {
            "data": ticker,
            "timestamp": datetime.timestamp(datetime.now())
        }
        logging.debug(f"Fetched ticker for {symbol} from Coingecko")
        return ticker

    def get_price(self, symbol: str) -> float:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The current price as a float.
        """
        ticker = self.get_ticker(symbol)
        return ticker["last"]

    def get_latest_trades(self, symbol: str) -> List:
        """
        Gets the latest trades for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The latest trades as a list of dictionaries.
        """
        trades = self._make_request(f"coins/{symbol}/trades")
        return trades[-10:]  # Return the last 10 trades

    def get_market_data(self, symbol: str) -> Dict:
        """
        Gets the market data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The market data as a dictionary.
        """
        market_data = self._make_request(f"coins/{symbol}")
        return market_data