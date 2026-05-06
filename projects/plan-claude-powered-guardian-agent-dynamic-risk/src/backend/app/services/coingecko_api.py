import os
import time
import logging
import requests
from typing import Dict, Optional, List
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            max_retries: Maximum number of retries for transient errors.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_backoff_multiplier = 2  # Exponential backoff
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
                response = requests.get(endpoint, params=params, headers={"X-CG-Token": self.api_key})
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed: {e}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_backoff_multiplier * (2 ** retries))
                else:
                    raise Exception(f"Request failed after {self.max_retries} retries: {e}")
        return None  # Should not reach here

    def get_ticker(self, coin_id: str) -> Optional[Dict]:
        """
        Gets the ticker information for a cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.

        Returns:
            The ticker information as a dictionary, or None if an error occurred.
        """
        endpoint = f"/coins/{coin_id}/tickers"
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
        endpoint = f"/coins/{coin_id}/last_price"
        params = {"vs": vs_currency}
        return self._make_request(endpoint, params)

    def get_current_prices(self, coin_ids: List[str], vs_currency: str = "usd") -> Dict[str, float]:
        """
        Gets the current prices for a list of cryptocurrencies.

        Args:
            coin_ids: A list of cryptocurrency IDs.
            vs_currency: The currency to convert to (default: USD).

        Returns:
            A dictionary of cryptocurrency prices, or an empty dictionary if an error occurred.
        """
        endpoint = f"/coins/listings/{','.join(coin_ids)}/last_price"
        params = {"vs": vs_currency}
        response = self._make_request(endpoint, params)
        if response:
            return {coin_id: response[0].get("last_price") for coin_id in coin_ids}
        else:
            return {}

    def get_market_caps(self, coin_ids: List[str]) -> Dict[str, float]:
        """
        Gets the market caps for a list of cryptocurrencies.

        Args:
            coin_ids: A list of cryptocurrency IDs.

        Returns:
            A dictionary of cryptocurrency market caps, or an empty dictionary if an error occurred.
        """
        endpoint = f"/coins/listings/{','.join(coin_ids)}/market_caps"
        response = self._make_request(endpoint)
        if response:
            return {coin_id: response[0].get("market_caps") for coin_id in coin_ids}
        else:
            return {}

    def get_all_coins(self, ticker_symbol: str = None) -> List[Dict]:
        """
        Gets a list of all coins.

        Args:
            ticker_symbol: The ticker symbol to filter by.

        Returns:
            A list of coin dictionaries.
        """
        endpoint = "/coins/listings"
        params = {}
        if ticker_symbol:
            params["vs_currency"] = ticker_symbol
        response = self._make_request(endpoint, params)
        if response:
            return response
        else:
            return []

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("COINGEKO_API_KEY")
    if not api_key:
        api_key = "YOUR_COINGEKO_API_KEY"  # Replace with your actual API key
    service = CoingeckoService(api_key=api_key)

    try:
        btc_ticker = service.get_ticker("bitcoin")
        print(f"Bitcoin Ticker: {btc_ticker}")

        btc_price = service.get_price("bitcoin")
        print(f"Bitcoin Price (USD): {btc_price}")

        coin_ids = ["bitcoin", "ethereum"]
        prices = service.get_current_prices(coin_ids)
        print(f"Prices for {coin_ids}: {prices}")

        market_caps = service.get_market_caps(coin_ids)
        print(f"Market Caps for {coin_ids}: {market_caps}")

        all_coins = service.get_all_coins("btc")
        print(f"All coins with btc ticker: {all_coins}")

    except Exception as e:
        print(f"An error occurred: {e}")