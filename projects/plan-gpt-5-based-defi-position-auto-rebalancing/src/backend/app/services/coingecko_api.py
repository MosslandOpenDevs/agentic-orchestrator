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

    def __init__(self, api_key: str, cache_duration: timedelta = timedelta(hours=12)):
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
        self.retry_wait = timedelta(seconds=5)

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint.
            params: The query parameters.

        Returns:
            The JSON response from the API.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"X-CG-KEY": self.api_key}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logging.error(f"Request failed: {e}")
            raise

    @retry(stop=retry_call, delay=retry_wait, retry=retry_count,
           before=lambda: logging.warning("Retrying request..."),
           after=lambda req, result, err: logging.info(f"Request {req.url} retried. Error: {err}"))
    def get_coin_info(self, coin_id: str) -> Dict:
        """
        Gets information about a specific cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.

        Returns:
            The cryptocurrency information.
        """
        cache_key = f"coin_info_{coin_id}"
        if cache_key in self.cache and datetime.now() - datetime.fromtimestamp(self.cache[cache_key]['timestamp']) < self.cache_duration:
            logging.debug(f"Cache hit for coin_info_{coin_id}")
            return self.cache[cache_key]

        data = self._make_request(f"coins/{coin_id}")
        self.cache[cache_key] = {"data": data, "timestamp": time.time()}
        logging.debug(f"Cache miss for coin_info_{coin_id}")
        return data

    def get_current_price(self, coin_id: str) -> float:
        """
        Gets the current price of a cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.

        Returns:
            The current price.
        """
        coin_info = self.get_coin_info(coin_id)
        if "market_data" in coin_info and "current_price" in coin_info["market_data"]:
            return coin_info["market_data"]["current_price"]
        else:
            logging.warning(f"Current price not found for coin_id: {coin_id}")
            return None

    def get_latest_prices(self, coin_ids: List[str]) -> Dict:
        """
        Gets the latest prices for a list of cryptocurrencies.

        Args:
            coin_ids: A list of cryptocurrency IDs.

        Returns:
            A dictionary of latest prices.
        """
        data = {}
        for coin_id in coin_ids:
            price = self.get_current_price(coin_id)
            if price is not None:
                data[coin_id] = price
        return data

    def get_24h_performance(self, coin_id: str) -> Dict:
        """
        Gets the 24h performance data for a cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.

        Returns:
            The 24h performance data.
        """
        return self._make_request(f"coins/{coin_id}/24h_performance")

    def get_all_coins(self) -> List[Dict]:
        """
        Gets a list of all available coins.
        """
        return self._make_request("coins/listings")