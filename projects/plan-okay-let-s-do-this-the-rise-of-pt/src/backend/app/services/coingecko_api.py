import os
import time
import logging
import requests
from typing import Dict, Optional, Union
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, Future

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
            rate_limit_delay: Delay in seconds between API calls to respect rate limits.
            max_retries: Maximum number of retries for transient errors.
        """
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/v3"
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_backoff = 2  # Exponential backoff

    def _make_request(self, endpoint: str, params: Dict = None) -> Union[Dict, None]:
        """
        Makes a request to the Coingecko API.
        Handles retries for transient errors.

        Args:
            endpoint: The API endpoint to request.
            params: Query parameters to include in the request.

        Returns:
            The JSON response from the API if successful, or None if an error occurred.
        """
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(endpoint, params=params, headers={'X-CG-KEY': self.api_key})
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed: {e}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_backoff * (2 ** retries))  # Exponential backoff
                else:
                    logging.error("Max retries reached.  Request failed.")
                    return None
        return None

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Gets the ticker information for a cryptocurrency.

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
        if ticker:
            return ticker["last"]
        else:
            return None

    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Gets the market data for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The market data as a dictionary, or None if an error occurred.
        """
        endpoint = f"/coins/{symbol}"
        return self._make_request(endpoint)

    def get_all_prices(self, symbols: list) -> Dict[str, float]:
        """
        Gets the current price for a list of cryptocurrencies.

        Args:
            symbols: A list of cryptocurrency symbols.

        Returns:
            A dictionary where keys are symbols and values are their prices.
        """
        prices = {}
        with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
            futures = [executor.submit(self.get_price, symbol) for symbol in symbols]
            for future in futures:
                try:
                    price = future.result()
                    if price is not None:
                        prices[future.future.id] = price
                except Exception as e:
                    logging.error(f"Error getting price for {future.future.id}: {e}")
        return prices
    
    def get_coin_info(self, symbol: str) -> Optional[Dict]:
        """
        Gets the coin information for a cryptocurrency.

        Args:
            symbol: The cryptocurrency symbol.

        Returns:
            The coin information as a dictionary, or None if an error occurred.
        """
        endpoint = f"/coins/{symbol}"
        return self._make_request(endpoint)


if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("COINGEKO_API_KEY")
    if not api_key:
        print("COINGEKO_API_KEY environment variable not set.")
        exit(1)

    service = CoingeckoService(api_key=api_key)

    bitcoin_price = service.get_price("bitcoin")
    if bitcoin_price:
        print(f"Bitcoin price: {bitcoin_price}")
    else:
        print("Could not retrieve Bitcoin price.")

    all_prices = service.get_all_prices(["bitcoin", "ethereum", "cardano"])
    print("All prices:", all_prices)