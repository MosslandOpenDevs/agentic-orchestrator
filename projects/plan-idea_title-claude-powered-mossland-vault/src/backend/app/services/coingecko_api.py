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

    def __init__(self, api_key: str, rate_limit_interval: int = 60, max_retries: int = 3):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: The Coingecko API key.
            rate_limit_interval: The interval in seconds for rate limiting.
            max_retries: The maximum number of retries for transient errors.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.retry_backoff_factor = 2  # Exponential backoff
        self.lock = threading.Lock()  # For thread safety

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
        headers = {"X-CG-KEY": self.api_key}
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return None

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Gets the ticker data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker data as a dictionary, or None if an error occurred.
        """
        endpoint = f"/coins/{symbol}/tickers"
        return self._make_request(endpoint)

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price as a float, or None if an error occurred.
        """
        ticker = self.get_ticker(symbol)
        if ticker and ticker["last"]:
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
        if ticker and ticker["market_cap"]:
            return ticker["market_cap"]
        else:
            return None

    def get_all_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Gets the current price for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where the keys are the symbols and the values are the prices.
        """
        prices = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.get_price, symbol): symbol for symbol in symbols}
            for future in futures:
                symbol = futures[future]
                try:
                    price = future.result()
                    if price is not None:
                        prices[symbol] = price
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {e}")
        return prices

import threading

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("COINGEKO_API_KEY", "YOUR_API_KEY")
    service = CoingeckoService(api_key=api_key)

    bitcoin_price = service.get_price("bitcoin")
    if bitcoin_price:
        print(f"Bitcoin price: {bitcoin_price}")
    else:
        print("Could not retrieve Bitcoin price.")

    all_prices = service.get_all_prices(["bitcoin", "ethereum", "cardano"])
    print("All prices:", all_prices)