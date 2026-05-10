import os
import time
import logging
import requests
from typing import Dict, Optional, List
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoingeckoService:
    """
    Service for integrating with the Coingecko API.
    """

    def __init__(self, api_key: str, rate_limit_delay: int = 1, max_retries: int = 3):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: The Coingecko API key.
            rate_limit_delay: Delay in seconds between API calls to respect rate limits.
            max_retries: Maximum number of retries for transient errors.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries

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
        headers = {"X-CG-Token": self.api_key}
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
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
        data = self._make_request(endpoint)
        if data and "success" in data and data["success"]:
            return data["ticker"]
        else:
            logger.warning(f"Failed to get ticker for {symbol}: {data}")
            return None

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Gets the current price for a given cryptocurrency symbol.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price as a float, or None if an error occurred.
        """
        ticker = self.get_ticker(symbol)
        if ticker:
            return ticker["last"]
        else:
            return None

    def get_market_caps(self, symbol: str) -> Optional[float]:
        """
        Gets the market cap for a given cryptocurrency symbol.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The market cap as a float, or None if an error occurred.
        """
        ticker = self.get_ticker(symbol)
        if ticker:
            return ticker["market_cap"]
        else:
            return None

    def get_all_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Gets the current prices for a list of cryptocurrency symbols.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where the keys are the symbols and the values are the current prices.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
            futures = [executor.submit(self.get_price, symbol) for symbol in symbols]
            for future in futures:
                try:
                    price = future.result()
                    if price is not None:
                        results[future.args[0]] = price
                except Exception as e:
                    logger.error(f"Error getting price for {future.args[0]}: {e}")
        return results

    def get_coin_gecko_coins(self) -> List[str]:
        """
        Gets a list of all coin gecko coins.
        """
        endpoint = f"{self.base_url}/coins/list"
        data = self._make_request(endpoint)
        if data and "coins" in data and data["coins"]:
            return [coin["id"] for coin in data["coins"]]
        else:
            logger.warning(f"Failed to get coin list: {data}")
            return []