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
        self.retry_backoff_factor = 2  # Exponential backoff
        self.lock = threading.Lock() # Thread safety

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.
        Handles retries for transient errors.

        Args:
            endpoint: The API endpoint to call.
            params: Query parameters.

        Returns:
            The JSON response from the API.

        Raises:
            Exception: If the request fails after multiple retries.
        """
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(endpoint, params=params, headers={'X-CG-TOKEN': self.api_key})
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logger.error(f"Request failed: {e}")
                retries += 1
                if retries < self.max_retries:
                    logger.info(f"Retrying in {self.retry_backoff_factor} seconds...")
                    time.sleep(self.retry_backoff_factor * (2 ** retries))
                else:
                    logger.error("Max retries reached. Request failed.")
                    raise

    def get_ticker(self, symbol: str) -> Dict:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., 'bitcoin').

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
        if ticker and ticker['last']:
            return float(ticker['last'])
        else:
            logger.warning(f"Could not retrieve price for {symbol}")
            return None

    def get_latest_prices(self, symbols: List[str]) -> Dict:
        """
        Gets the latest prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where keys are symbols and values are their latest prices.
        """
        prices = {}
        with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
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

    def get_gemini_exchange_rate(self, symbol: str) -> float:
        """
        Gets the exchange rate from Gemini for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The exchange rate as a float.
        """
        endpoint = f"/exchanges/{symbol.lower()}/tickers"
        data = self._make_request(endpoint)
        if data and 'last' in data:
            return float(data['last'])
        else:
            logger.warning(f"Could not retrieve exchange rate for {symbol}")
            return None

import threading
if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("COINGEKO_API_KEY")
    if not api_key:
        print("COINGEKO_API_KEY environment variable not set.")
        exit()

    service = CoingeckoService(api_key=api_key)

    bitcoin_price = service.get_price("bitcoin")
    if bitcoin_price:
        print(f"Bitcoin price: {bitcoin_price}")

    latest_prices = service.get_latest_prices(["bitcoin", "ethereum", "cardano"])
    print("Latest prices:", latest_prices)

    gemini_btc_rate = service.get_gemini_exchange_rate("bitcoin")
    if gemini_btc_rate:
        print(f"Gemini BTC rate: {gemini_btc_rate}")