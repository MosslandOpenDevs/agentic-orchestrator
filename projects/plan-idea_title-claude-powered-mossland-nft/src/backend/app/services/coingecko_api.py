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
            rate_limit_delay: Delay in seconds between API calls to respect rate limits.
            max_retries: Maximum number of retries for a failed request.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_backoff = 2  # Exponential backoff
        self.retry_exceptions = (RequestException, Exception)

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.
        Handles retries for transient errors.

        Args:
            endpoint: The API endpoint to call.
            params: Query parameters to include in the request.

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
                if not self.retry_exceptions.__contains__(type(e)):
                    raise
                time.sleep(self.retry_backoff * (2 ** retries))
        raise Exception(f"Failed to retrieve data after {self.max_retries} retries.")

    def get_ticker(self, symbol: str) -> Dict:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker data as a dictionary.
        """
        endpoint = f"/coins/{symbol}/ticker"
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
        return ticker["price"]

    def get_latest_prices(self, symbols: List[str]) -> Dict:
        """
        Gets the latest prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where keys are symbols and values are their latest prices.
        """
        data = {}
        with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
            results = list(executor.map(self.get_price, symbols))
        for i, symbol in enumerate(symbols):
            data[symbol] = results[i]
        return data

    def get_gemini_exchange_rate(self, symbol: str) -> float:
        """
        Gets the exchange rate for a cryptocurrency on Gemini.
        """
        endpoint = f"/coins/{symbol}/last_exchange_rate"
        return self._make_request(endpoint)


if __name__ == '__main__':
    # Example Usage (replace with your actual API key)
    api_key = os.environ.get("COINGEKO_API_KEY", "YOUR_API_KEY")  # Use environment variable or default
    service = CoingeckoService(api_key=api_key)

    try:
        bitcoin_price = service.get_price("bitcoin")
        print(f"Bitcoin price: {bitcoin_price}")

        latest_prices = service.get_latest_prices(["bitcoin", "ethereum", "cardano"])
        print("Latest prices:", latest_prices)

        gemini_rate = service.get_gemini_exchange_rate("bitcoin")
        print(f"Gemini Bitcoin Rate: {gemini_rate}")

    except Exception as e:
        print(f"An error occurred: {e}")