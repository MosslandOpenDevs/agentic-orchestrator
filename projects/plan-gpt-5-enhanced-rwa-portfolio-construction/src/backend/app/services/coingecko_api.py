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
            api_key: Your Coingecko API key.
            rate_limit_delay: Delay in seconds between API requests to respect rate limits.
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
                if retries < self.max_retries:
                    time.sleep(self.retry_backoff * (2 ** retries))  # Exponential backoff
                else:
                    raise Exception(f"Request failed after {self.max_retries} retries")
        return None  # Should not reach here

    def get_ticker(self, coin_id: str) -> Optional[Dict]:
        """
        Gets the ticker information for a specific cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency (e.g., 'bitcoin').

        Returns:
            The ticker data as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/exchange/tickers/{coin_id}"
        return self._make_request(endpoint)

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Optional[float]:
        """
        Gets the price of a cryptocurrency in a specific currency.

        Args:
            coin_id: The ID of the cryptocurrency.
            vs_currency: The currency to convert to (default: USD).

        Returns:
            The price as a float, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/simple/price?ids={coin_id}&vs_currency={vs_currency}"
        response = self._make_request(endpoint)
        if response and coin_id in response:
            return response[coin_id]['price']
        return None

    def get_latest_prices(self, coin_ids: List[str], vs_currency: str = "usd") -> Dict[str, float]:
        """
        Gets the latest prices for a list of cryptocurrencies.

        Args:
            coin_ids: A list of cryptocurrency IDs.
            vs_currency: The currency to convert to (default: USD).

        Returns:
            A dictionary of latest prices, or an empty dictionary if an error occurred.
        """
        endpoint = f"{self.base_url}/simple/price?ids={','.join(coin_ids)}&vs_currency={vs_currency}"
        response = self._make_request(endpoint)
        if response:
            return {coin_id: response[coin_id]['price'] for coin_id in coin_ids}
        return {}

    def get_market_caps(self, coin_ids: List[str]) -> Dict[str, float]:
        """
        Gets the market caps for a list of cryptocurrencies.

        Args:
            coin_ids: A list of cryptocurrency IDs.

        Returns:
            A dictionary of market caps, or an empty dictionary if an error occurred.
        """
        endpoint = f"{self.base_url}/coins/markets?ids={','.join(coin_ids)}"
        response = self._make_request(endpoint)
        if response:
            return {coin_id: data['market_cap'] for coin_id, data in response.items()}
        return {}

    def get_all_coins(self, category: str = "cryptocurrency") -> List[Dict]:
        """
        Gets a list of all coins in a specific category.

        Args:
            category: The category to filter by (default: "cryptocurrency").

        Returns:
            A list of coin dictionaries.
        """
        endpoint = f"{self.base_url}/coins/{category}"
        response = self._make_request(endpoint)
        if response:
            return response
        return []


if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("COINGEKO_API_KEY")
    if not api_key:
        print("Please set the COINGEKO_API_KEY environment variable.")
    else:
        service = CoingeckoService(api_key=api_key)

        bitcoin_ticker = service.get_ticker("bitcoin")
        print("Bitcoin Ticker:", bitcoin_ticker)

        bitcoin_price = service.get_price("bitcoin")
        print("Bitcoin Price (USD):", bitcoin_price)

        latest_prices = service.get_latest_prices(["bitcoin", "ethereum"], "usd")
        print("Latest Prices:", latest_prices)

        market_caps = service.get_market_caps(["bitcoin", "ethereum"])
        print("Market Caps:", market_caps)

        all_coins = service.get_all_coins()
        print("All Coins:", all_coins)