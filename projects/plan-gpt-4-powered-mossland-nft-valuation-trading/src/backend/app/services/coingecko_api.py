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

    def __init__(self, api_key: str, rate_limit_interval: int = 60, max_retries: int = 3):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: The Coingecko API key.
            rate_limit_interval: The interval in seconds for rate limiting.
            max_retries: The maximum number of retries for a request.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.retry_delay = 2  # seconds
        self.lock = threading.Lock()  # For rate limiting

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
            The ticker information as a dictionary, or None if the request fails.
        """
        endpoint = f"/coins/{symbol}/ticker"
        return self._make_request(endpoint)

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price as a float, or None if the request fails.
        """
        ticker = self.get_ticker(symbol)
        if ticker and ticker["last"]:
            return float(ticker["last"])
        return None

    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Gets the latest prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where the keys are the symbols and the values are the latest prices.
        """
        prices = {}
        with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
            results = list(executor.map(self.get_price, symbols))
        for i, symbol in enumerate(symbols):
            prices[symbol] = results[i]
        return prices

    def get_gemini_exchange_rate(self, symbol: str) -> Optional[float]:
        """
        Gets the exchange rate for a cryptocurrency on Gemini.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The exchange rate as a float, or None if the request fails.
        """
        endpoint = f"/exchanges/{symbol.lower()}"
        data = self._make_request(endpoint)
        if data and "price" in data["rates"]:
            return float(data["rates"][symbol.lower()])
        return None

    def get_all_coins(self) -> List[str]:
        """
        Gets a list of all available coins on Coingecko.
        """
        try:
            response = requests.get(f"{self.base_url}/coins/list")
            response.raise_for_status()
            return response.json()["coins"]
        except RequestException as e:
            logging.error(f"Failed to get coin list: {e}")
            return []

import threading
if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("COINGEKO_API_KEY")
    if not api_key:
        print("Please set the COINGEKO_API_KEY environment variable.")
    else:
        service = CoingeckoService(api_key=api_key)
        btc_price = service.get_price("bitcoin")
        print(f"Bitcoin price: {btc_price}")

        prices = service.get_latest_prices(["bitcoin", "ethereum", "cardano"])
        print(f"Latest prices: {prices}")

        gemini_eth_rate = service.get_gemini_exchange_rate("ethereum")
        print(f"Ethereum exchange rate on Gemini: {gemini_eth_rate}")