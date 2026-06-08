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
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_backoff_factor = 2  # Exponential backoff
        self.retry_exceptions = (RequestException, Exception)

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint.
            params: Query parameters.

        Returns:
            The JSON response from the API.

        Raises:
            Exception: If the request fails after multiple retries.
        """
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(endpoint, params=params, headers={'X-CG-Token': self.api_key})
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed: {e}")
                retries += 1
                if not self.retry_exceptions.__cause__ in [e.__cause__ for e in self.retry_exceptions]:
                    raise
                time.sleep(self.retry_backoff_factor * (2 ** retries))
        raise Exception(f"Failed to fetch data after {self.max_retries} retries.")

    def get_ticker(self, coin_id: str) -> Dict:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.

        Returns:
            The ticker information.
        """
        endpoint = f"/coins/{coin_id}/ticker"
        return self._make_request(endpoint)

    def get_price(self, coin_id: str) -> float:
        """
        Gets the current price of a cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.

        Returns:
            The current price.
        """
        ticker = self.get_ticker(coin_id)
        return ticker[0]['price']

    def get_latest_prices(self, coin_ids: List[str]) -> Dict:
        """
        Gets the latest prices for a list of cryptocurrencies.

        Args:
            coin_ids: A list of cryptocurrency IDs.

        Returns:
            A dictionary of latest prices.
        """
        data = {}
        with ThreadPoolExecutor(max_workers=len(coin_ids)) as executor:
            results = list(executor.map(self.get_price, coin_ids))
        for i, coin_id in enumerate(coin_ids):
            data[coin_id] = results[i]
        return data

    def get_gemini_exchange_rate(self, coin_id: str) -> float:
        """
        Gets the exchange rate for a cryptocurrency on Gemini.
        """
        endpoint = f"/coins/{coin_id}/last_exchange_rate"
        return self._make_request(endpoint)['result']