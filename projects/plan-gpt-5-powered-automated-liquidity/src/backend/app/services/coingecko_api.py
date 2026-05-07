import os
import time
import logging
import tenacity
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from coingecko import CoinGeckoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoingeckoService:
    """
    Service for integrating with the Coingecko API.
    """

    def __init__(self, api_key: str):
        """
        Initializes the CoingeckoService with the provided API key.
        """
        self.api_key = api_key
        self.client = CoinGeckoClient(key=self.api_key)
        self.cache = {}  # Simple in-memory cache
        self.cache_expiry = timedelta(hours=1)  # Cache expiry time

    def _cache_key(self, symbol: str, timeframe: str) -> str:
        """
        Generates a cache key based on symbol and timeframe.
        """
        return f"{symbol}_{timeframe}"

    def _get_data_from_cache(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        Retrieves data from the cache.
        """
        key = self._cache_key(symbol, timeframe)
        if key in self.cache and datetime.now() - datetime.fromtimestamp(self.cache[key]['timestamp']) < self.cache_expiry:
            logger.debug(f"Data retrieved from cache for {symbol}, {timeframe}")
            return self.cache[key]
        return None

    def _cache_data(self, symbol: str, timeframe: str, data: Dict) -> None:
        """
        Caches the data.
        """
        self.cache[self._cache_key(symbol, timeframe)] = {
            'data': data,
            'timestamp': time.time()
        }

    def get_ticker_price(self, symbol: str, timeframe: str = "1h") -> float:
        """
        Retrieves the ticker price for a given cryptocurrency and timeframe.
        """
        data = self._get_data_from_cache(symbol, timeframe)
        if data:
            logger.debug(f"Returning cached ticker price for {symbol}, {timeframe}")
            return data['price']

        try:
            ticker = self.client.get_ticker(id=symbol, params={'timeframe': timeframe})
            price = ticker[0]['last']
            logger.info(f"Fetched ticker price for {symbol}, {timeframe}: {price}")
            self._cache_data(symbol, timeframe, {'price': price})
            return price
        except Exception as e:
            logger.error(f"Error fetching ticker price for {symbol}, {timeframe}: {e}")
            raise

    def get_coin_info(self, symbol: str) -> Dict:
        """
        Retrieves information about a given cryptocurrency.
        """
        data = self._get_data_from_cache(symbol, "24h")
        if data:
            logger.debug(f"Returning cached coin info for {symbol}")
            return data

        try:
            coin = self.client.get_coin_info(id=symbol)
            info = coin[0]
            logger.info(f"Fetched coin info for {symbol}: {info}")
            self._cache_data(symbol, "24h", info)
            return info
        except Exception as e:
            logger.error(f"Error fetching coin info for {symbol}: {e}")
            raise

    def get_coins_listings(self, timeframe: str = "1h") -> List[Dict]:
        """
        Retrieves a list of all listed cryptocurrencies.
        """
        try:
            coins = self.client.get_coins_listings(timeframe=timeframe)
            logger.info(f"Fetched coins listings for {timeframe}")
            return coins
        except Exception as e:
            logger.error(f"Error fetching coins listings for {timeframe}: {e}")
            raise