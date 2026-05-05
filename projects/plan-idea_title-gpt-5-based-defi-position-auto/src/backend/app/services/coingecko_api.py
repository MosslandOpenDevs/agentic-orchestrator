import os
import time
import logging
import requests
from typing import Dict, Optional, List
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, Future

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
            max_retries: The maximum number of retries for transient failures.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.retry_backoff_factor = 2  # Exponential backoff
        self.lock = threading.Lock()  # For thread-safe rate limiting

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint.
            params: The request parameters.

        Returns:
            The API response as a dictionary.

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
            raise

    def get_ticker(self, symbol: str) -> Dict:
        """
        Gets the ticker data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker data as a dictionary.
        """
        endpoint = f"/coins/{symbol}/tickers"
        return self._make_request(endpoint)

    def get_price(self, symbol: str) -> float:
        """
        Gets the current price of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The current price as a float.
        """
        ticker = self.get_ticker(symbol)
        if ticker and ticker.get("last"):
            return float(ticker["last"])
        else:
            logger.warning(f"Could not retrieve price for {symbol}")
            return None

    def get_market_caps(self, symbol: str) -> Dict:
        """
        Gets the market cap data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The market cap data as a dictionary.
        """
        endpoint = f"/coins/{symbol}/market_caps"
        return self._make_request(endpoint)

    def get_all_prices(self, symbols: List[str]) -> Dict:
        """
        Gets the current prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where the keys are the symbols and the values are the prices.
        """
        prices = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.get_price, symbol): symbol for symbol in symbols}
            for future in futures:
                try:
                    symbol = futures[future]
                    price = future.result()
                    if price is not None:
                        prices[symbol] = price
                except Future.cancelError:
                    logger.info(f"Task for {symbol} cancelled")
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {e}")
        return prices

    def get_latest_trades(self, symbol: str) -> List[Dict]:
        """
        Gets the latest trades for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            A list of trade dictionaries.
        """
        endpoint = f"/coins/{symbol}/trades"
        return self._make_request(endpoint)

import threading

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("COINGEKO_API_KEY")
    if not api_key:
        print("Please set the COINGEKO_API_KEY environment variable.")
    else:
        service = CoingeckoService(api_key=api_key)
        btc_price = service.get_price("bitcoin")
        if btc_price:
            print(f"Bitcoin price: {btc_price}")
        else:
            print("Could not retrieve Bitcoin price.")

        all_prices = service.get_all_prices(["bitcoin", "ethereum", "cardano"])
        print("\nAll Prices:", all_prices)