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
        self.retry_backoff_factor = 2  # Exponential backoff
        self.executor = ThreadPoolExecutor(max_workers=5)  # Thread pool for concurrent requests

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
        headers = {"X-CG-VERSION": "v3", "Authorization": f"Bearer {self.api_key}"}
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
        endpoint = f"{self.base_url}/exchange/{symbol}/tickers"
        data = self._make_request(endpoint)
        if data:
            return data[0]  # Return the first ticker
        else:
            return None

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Gets the current price of a cryptocurrency.

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
        Gets the market cap of a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The market cap as a float, or None if an error occurred.
        """
        ticker = self.get_ticker(symbol)
        if ticker:
            return ticker["market_caps"]
        else:
            return None

    def get_all_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Gets the current prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where keys are symbols and values are their prices.
        """
        prices = {}
        for symbol in symbols:
            prices[symbol] = self.get_price(symbol)
        return prices

    def get_coin_info(self, symbol: str) -> Optional[Dict]:
        """
        Gets the basic information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The coin information as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/coins/{symbol}"
        data = self._make_request(endpoint)
        if data:
            return data
        else:
            return None

    def fetch_data(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Helper function to handle retries and rate limiting.
        """
        for attempt in range(self.max_retries):
            data = self._make_request(endpoint, params)
            if data:
                return data
            else:
                logger.info(f"Attempt {attempt + 1} failed for {endpoint}.  Retrying in {self.retry_backoff_factor} seconds...")
                time.sleep(self.retry_backoff_factor)
        logger.error(f"Failed to fetch data after {self.max_retries} attempts for {endpoint}")
        return None

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("COINGEKO_API_KEY")
    if not api_key:
        api_key = "YOUR_COINGEKO_API_KEY"  # Replace with your actual API key

    service = CoingeckoService(api_key=api_key)

    bitcoin_price = service.get_price("bitcoin")
    if bitcoin_price:
        print(f"Bitcoin price: {bitcoin_price}")
    else:
        print("Could not retrieve Bitcoin price.")

    all_prices = service.get_all_prices(["bitcoin", "ethereum", "cardano"])
    print("All prices:", all_prices)