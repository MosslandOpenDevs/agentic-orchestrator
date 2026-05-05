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
            max_retries: The maximum number of retries for transient failures.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_interval = rate_limit_interval
        self.max_retries = max_retries
        self.retry_backoff_factor = 2  # Exponential backoff
        self.lock = threading.Lock() # Thread safety for rate limiting

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint.
            params: The request parameters.

        Returns:
            The JSON response from the API.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        headers = {"X-CG-VERSION": "v3", "Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logging.error(f"Request failed for {endpoint}: {e}")
            return None

    def get_ticker(self, coin_id: str) -> Optional[Dict]:
        """
        Gets the ticker data for a cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.

        Returns:
            The ticker data as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/exchange/tickers/{coin_id}"
        return self._make_request(endpoint)

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Optional[float]:
        """
        Gets the price of a cryptocurrency in a specified currency.

        Args:
            coin_id: The ID of the cryptocurrency.
            vs_currency: The currency to convert to (default: USD).

        Returns:
            The price as a float, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/simple/price?ids={coin_id}&vs_currency={vs_currency}"
        data = self._make_request(endpoint)
        if data and coin_id in data:
            return data[coin_id]["price"]
        return None

    def get_coins(self, vs_currency: str = "usd", skip: int = 0, limit: int = 20) -> List[Dict]:
        """
        Gets a list of cryptocurrencies.

        Args:
            vs_currency: The currency to convert to (default: USD).
            skip: The number of items to skip (for pagination).
            limit: The maximum number of items to return.

        Returns:
            A list of cryptocurrency dictionaries.
        """
        endpoint = f"{self.base_url}/coins/{vs_currency}?skip={skip}&limit={limit}"
        return self._make_request(endpoint)

    def get_gemini_prices(self) -> List[Dict]:
        """
        Gets the current prices of cryptocurrencies on Gemini.
        """
        endpoint = f"{self.base_url}/exchanges/gemini/tickers"
        return self._make_request(endpoint)

    def get_historical_price(self, coin_id: str, vs_currency: str = "usd", timeframe: str = "1h", granularity: str = "1m", skip: int = 0, limit: int = 200) -> List[Dict]:
        """
        Gets historical price data for a cryptocurrency.

        Args:
            coin_id: The ID of the cryptocurrency.
            vs_currency: The currency to convert to (default: USD).
            timeframe: The timeframe for the historical data (e.g., "1h", "1d").
            granularity: The granularity of the historical data (e.g., "1m", "1h").
            skip: The number of items to skip (for pagination).
            limit: The maximum number of items to return.

        Returns:
            A list of historical price dictionaries.
        """
        endpoint = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "timeframe": timeframe,
            "granularity": granularity,
            "skip": skip,
            "limit": limit
        }
        return self._make_request(endpoint, params)


import threading

class RateLimiter:
    def __init__(self, rate_limit_interval: int, max_requests: int):
        self.rate_limit_interval = rate_limit_interval
        self.max_requests = max_requests
        self.request_counts = {}
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()
            if "coingecko_requests" not in self.request_counts:
                self.request_counts["coingecko_requests"] = []
            self.request_counts["coingecko_requests"].append(now)
            self.request_counts["coingecko_requests"] = sorted(list(set(self.request_counts["coingecko_requests"])))

            while len(self.request_counts["coingecko_requests"]) >= self.max_requests:
                oldest_request = self.request_counts["coingecko_requests"][0]
                self.request_counts["coingecko_requests"].pop(0)
                wait_time = self.rate_limit_interval - (time.time() - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)

    def check(self):
        with self.lock:
            now = time.time()
            self.request_counts["coingecko_requests"].append(now)
            self.request_counts["coingecko_requests"] = sorted(list(set(self.request_counts["coingecko_requests"])))
            return len(self.request_counts["coingecko_requests"]) <= self.max_requests

# Example usage (replace with your API key)
if __name__ == '__main__':
    os.environ['COINGEKO_API_KEY'] = 'YOUR_COINGEKO_API_KEY'
    service = CoingeckoService(api_key=os.environ['COINGEKO_API_KEY'])

    # Example: Get the price of Bitcoin in USD
    btc_price = service.get_price("bitcoin")
    print(f"Bitcoin price: {btc_price}")

    # Example: Get a list of coins
    coins = service.get_coins()
    print(f"Coins: {coins}")

    # Example: Get historical price data
    historical_data = service.get_historical_price("bitcoin", timeframe="1d")
    print(f"Historical data: {historical_data}")