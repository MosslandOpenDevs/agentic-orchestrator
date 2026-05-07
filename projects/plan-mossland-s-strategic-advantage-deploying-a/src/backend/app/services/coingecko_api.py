import time
import logging
import os
import tenacity
from typing import Dict, Optional, List
from coingecko import CoinGeckoClient
from dataclasses import dataclass
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Environment variable configuration
COINGEKO_API_KEY = os.environ.get("COINGEKO_API_KEY")
CACHE_EXPIRY = timedelta(hours=1)  # Cache expiry time
RATE_LIMIT_DELAY = 0.5  # Delay in seconds for rate limiting

# Retry configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor


@dataclass
class CoinGeckoService:
    client: CoinGeckoClient

    def get_price(self, coin_id: str, currency: str = "usd") -> Optional[float]:
        """
        Retrieves the price of a cryptocurrency.
        """
        try:
            if COINGEKO_API_KEY:
                client.set_api_key(COINGEKO_API_KEY)
            price = client.get_coin_ticker_price(id=coin_id, currency=currency)
            logging.info(f"Price for {coin_id} in {currency}: {price}")
            return price
        except tenacity.RetryError as e:
            logging.error(f"CoinGecko API error for {coin_id} in {currency}: {e}")
            return None
        except Exception as e:
            logging.exception(f"Unexpected error fetching price for {coin_id} in {currency}: {e}")
            return None

    def get_price_history(self, coin_id: str, currency: str = "usd", timeframe: str = "1d", limit: int = 100) -> List[Dict]:
        """
        Retrieves price history for a cryptocurrency.
        """
        try:
            if COINGEKO_API_KEY:
                client.set_api_key(COINGEKO_API_KEY)
            history = client.get_coin_history(id=coin_id, currency=currency, timeframe=timeframe, limit=limit)
            logging.info(f"Price history for {coin_id} in {currency}: {history}")
            return history
        except tenacity.RetryError as e:
            logging.error(f"CoinGecko API error for {coin_id} in {currency}: {e}")
            return []
        except Exception as e:
            logging.exception(f"Unexpected error fetching price history for {coin_id} in {currency}: {e}")
            return []

    def get_market_data(self, coin_id: str) -> Dict:
        """
        Retrieves market data for a cryptocurrency.
        """
        try:
            if COINGEKO_API_KEY:
                client.set_api_key(COINGEKO_API_KEY)
            market_data = client.get_coin_market_data(id=coin_id)
            logging.info(f"Market data for {coin_id}: {market_data}")
            return market_data
        except tenacity.RetryError as e:
            logging.error(f"CoinGecko API error for {coin_id}: {e}")
            return {}
        except Exception as e:
            logging.exception(f"Unexpected error fetching market data for {coin_id}: {e}")
            return {}


# Service class
class CoingeckoAPI:
    def __init__(self):
        self.client = CoinGeckoClient()

    def execute(self, method_name: str, *args, **kwargs) -> Optional[Dict]:
        """
        Executes a method on the CoinGecko client with retry logic.
        """
        with tenacity.retry(stop=tenacity.stop_after_attempt(MAX_RETRIES),
                            wait=tenacity.wait_exponential(BASE=RATE_LIMIT_DELAY, FACTOR=BACKOFF_FACTOR),
                            retry=tenacity.retry_if_exception_type(Exception)) as retries:
            result = getattr(self.client, method_name)(*args, **kwargs)
            return result

    def get_coin_price(self, coin_id: str, currency: str = "usd") -> Optional[float]:
        return self.execute("get_coin_ticker_price", coin_id, currency)

    def get_coin_price_history(self, coin_id: str, currency: str = "usd", timeframe: str = "1d", limit: int = 100) -> List[Dict]:
        return self.execute("get_coin_history", coin_id, currency, timeframe, limit)

    def get_coin_market_data(self, coin_id: str) -> Dict:
        return self.execute("get_coin_market_data", coin_id)


if __name__ == '__main__':
    service = CoingeckoAPI()

    # Example usage
    btc_price = service.get_coin_price("bitcoin")
    print(f"Bitcoin price: {btc_price}")

    eth_history = service.get_coin_price_history("ethereum")
    print(f"Ethereum price history: {eth_history}")

    bnb_market_data = service.get_coin_market_data("binancecoin")
    print(f"BinanceCoin market data: {bnb_market_data}")