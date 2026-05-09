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
            api_key: Your Coingecko API key.
            rate_limit_delay: Delay in seconds between API calls to respect rate limits.
            max_retries: Maximum number of retries for transient errors.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_backoff_factor = 2  # Exponential backoff

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
        Gets the ticker data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker data as a dictionary, or None if an error occurred.
        """
        endpoint = f"/coins/{symbol}/ticker"
        data = self._make_request(endpoint)
        if data:
            logger.info(f"Successfully retrieved ticker for {symbol}")
            return data
        else:
            logger.warning(f"Failed to retrieve ticker for {symbol}")
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
        if ticker and ticker["last"]:
            return float(ticker["last"])
        else:
            return None

    def get_latest_trades(self, symbol: str) -> Optional[List]:
        """
        Gets the latest trades for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The latest trades as a list, or None if an error occurred.
        """
        endpoint = f"/coins/{symbol}/trades/latest"
        data = self._make_request(endpoint)
        if data:
            logger.info(f"Successfully retrieved latest trades for {symbol}")
            return data
        else:
            logger.warning(f"Failed to retrieve latest trades for {symbol}")
            return None

    def get_market_data(self, symbol: str, timeframe: str = "1h") -> Optional[List]:
        """
        Gets market data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.
            timeframe: The timeframe for the data (e.g., "1h", "15m", "1h").

        Returns:
            The market data as a list, or None if an error occurred.
        """
        endpoint = f"/coins/{symbol}/market_data"
        params = {"timeframe": timeframe}
        data = self._make_request(endpoint, params)
        if data:
            logger.info(f"Successfully retrieved market data for {symbol} with timeframe {timeframe}")
            return data
        else:
            logger.warning(f"Failed to retrieve market data for {symbol} with timeframe {timeframe}")
            return None

    def get_all_coins(self) -> List:
        """
        Gets a list of all available coins on Coingecko.
        """
        endpoint = "/coins/list"
        data = self._make_request(endpoint)
        if data:
            logger.info(f"Successfully retrieved list of all coins.")
            return data
        else:
            logger.warning(f"Failed to retrieve list of all coins.")
            return []


if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("COINGEKO_API_KEY", "YOUR_API_KEY")
    service = CoingeckoService(api_key=api_key)

    # Example usage
    bitcoin_price = service.get_price("bitcoin")
    if bitcoin_price:
        print(f"Bitcoin price: {bitcoin_price}")

    eth_latest_trades = service.get_latest_trades("ethereum")
    if eth_latest_trades:
        print(f"Ethereum latest trades: {eth_latest_trades}")

    all_coins = service.get_all_coins()
    print(f"All coins: {all_coins}")