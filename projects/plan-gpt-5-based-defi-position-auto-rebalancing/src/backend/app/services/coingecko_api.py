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

    def __init__(self, api_key: str, rate_limit_delay: int = 1, max_retries: int = 3):
        """
        Initializes the CoingeckoService.

        Args:
            api_key: Your Coingecko API key.
            rate_limit_delay: Delay in seconds between API requests to respect rate limits.
            max_retries: Maximum number of retries for transient errors.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Makes a request to the Coingecko API.

        Args:
            endpoint: The API endpoint to request.
            params: Query parameters to include in the request.

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
        Gets the ticker information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol (e.g., "bitcoin").

        Returns:
            The ticker information as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/exchange/{symbol}/tickers"
        ticker = self._make_request(endpoint)
        if ticker:
            return ticker
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
        if ticker and "last" in ticker:
            return ticker["last"]
        else:
            return None

    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Gets the latest prices for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where keys are symbols and values are their latest prices.
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
                except Future.CancelledError:
                    logger.warning(f"Task for {symbol} was cancelled.")
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {e}")
        return prices

    def get_gemini_exchange_rate(self, symbol: str) -> Optional[float]:
        """
        Gets the exchange rate for a cryptocurrency on Gemini.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The exchange rate as a float, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/exchanges/gemini/tickers/{symbol}"
        ticker = self._make_request(endpoint)
        if ticker and "last" in ticker:
            return ticker["last"]
        else:
            return None

    def get_coin_market_cap(self) -> Optional[Dict]:
        """
        Gets the total market cap of all cryptocurrencies.

        Returns:
            The market cap data as a dictionary, or None if an error occurred.
        """
        endpoint = f"{self.base_url}/market_chart"
        params = {"vs_currencies": "usd"}
        market_cap = self._make_request(endpoint, params)
        if market_cap and "total" in market_cap:
            return market_cap
        else:
            return None