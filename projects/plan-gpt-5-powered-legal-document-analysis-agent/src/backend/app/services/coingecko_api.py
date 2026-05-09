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
    def __init__(self, api_key: str, rate_limit_interval: int = 60, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_interval = rate_limit_interval  # Seconds
        self.max_retries = max_retries
        self.executor = ThreadPoolExecutor(max_workers=5)  # Adjust based on needs
        self.cache = {}  # Simple in-memory cache

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Makes a request to the Coingecko API with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(endpoint, params=params, headers={'X-CG-Token': self.api_key})
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise  # Re-raise if all retries failed
                time.sleep(2 ** attempt)  # Exponential backoff

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Retrieves the ticker for a given cryptocurrency symbol.
        """
        cache_key = f"ticker_{symbol}"
        if cache_key in self.cache:
            logging.debug(f"Fetching ticker from cache for {symbol}")
            return self.cache[cache_key]

        endpoint = f"{self.base_url}/exchange/v3/ticker/{symbol}"
        data = self._make_request(endpoint)
        self.cache[cache_key] = data
        logging.debug(f"Fetched ticker for {symbol} from Coingecko")
        return data

    def get_price(self, symbol: str) -> Optional[float]:
        """
        Retrieves the current price for a given cryptocurrency symbol.
        """
        ticker = self.get_ticker(symbol)
        if ticker:
            return ticker["last"]
        else:
            return None

    def get_market_caps(self, symbol: str) -> Optional[float]:
        """
        Retrieves the market cap for a given cryptocurrency symbol.
        """
        ticker = self.get_ticker(symbol)
        if ticker:
            return ticker["market_cap"]
        else:
            return None

    def get_all_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Retrieves the current price for a list of cryptocurrency symbols.
        """
        prices = {}
        with self.executor:
            futures = [self.get_price(symbol) for symbol in symbols]
            prices = dict(futures)
        return prices

    def get_coins_by_symbol(self, symbols: List[str]) -> List[Dict]:
        """
        Retrieves a list of coins by their symbols.
        """
        endpoint = f"{self.base_url}/coins/list"
        params = {"ids": ",".join(symbols)}
        try:
            response = self._make_request(endpoint, params)
            return response
        except RequestException as e:
            logging.error(f"Error fetching coins by symbol: {e}")
            return []

    def clear_cache(self):
        """Clears the in-memory cache."""
        self.cache = {}