import os
import time
import logging
import requests
from typing import List, Dict, Optional
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Nansen:
    def __init__(self, api_key: str, base_url: str = "https://api.nansen.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.rate_limit_delay = 0.5  # Initial delay in seconds
        self.retry_count = 3
        self.retry_delay = 2  # Seconds between retries

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Makes a request to the Nansen API with retry logic."""
        for attempt in range(self.retry_count):
            try:
                response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.retry_count}): {e}")
                if attempt == self.retry_count - 1:
                    raise  # Re-raise if all retries failed
                time.sleep(self.retry_delay)
        return {}  # Should not reach here, but return empty dict for safety

    def get_wallet_info(self, wallet_address: str) -> Dict:
        """
        Retrieves information about a specific wallet address.
        """
        endpoint = f"wallets/{wallet_address}"
        return self._make_request(endpoint)

    def get_whale_list(self, min_balance: float = 100000000) -> List[Dict]:
        """
        Retrieves a list of whale wallets based on a minimum balance.
        """
        endpoint = "wallets/whale_list"
        params = {"min_balance": min_balance}
        return self._make_request(endpoint, params)

    def get_asset_details(self, asset_address: str) -> Dict:
        """
        Retrieves details about a specific asset.
        """
        endpoint = f"assets/{asset_address}"
        return self._make_request(endpoint)

    def get_transaction_history(self, wallet_address: str, asset_address: str, limit: int = 100) -> List[Dict]:
        """
        Retrieves the transaction history for a specific wallet and asset.
        """
        endpoint = f"wallets/{wallet_address}/transactions"
        params = {
            "asset": asset_address,
            "limit": limit
        }
        return self._make_request(endpoint, params)

    def get_dbs(self) -> List[Dict]:
        """
        Retrieves a list of DBS.
        """
        endpoint = "dbs"
        return self._make_request(endpoint)

    def get_dbs_by_asset(self, asset_address: str) -> List[Dict]:
        """
        Retrieves a list of DBS that contain a specific asset.
        """
        endpoint = f"dbs?asset={asset_address}"
        return self._make_request(endpoint)

    def get_asset_transfers(self, asset_address: str, limit: int = 100) -> List[Dict]:
        """
        Retrieves the transfer history for a specific asset.
        """
        endpoint = f"assets/{asset_address}/transfers"
        params = {"limit": limit}
        return self._make_request(endpoint, params)

    def get_top_dbs_by_asset(self, asset_address: str, limit: int = 100) -> List[Dict]:
        """
        Retrieves the top DBS that contain a specific asset.
        """
        endpoint = f"dbs?asset={asset_address}&sort=volume&order=desc&limit={limit}"
        return self._make_request(endpoint)


if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("Nansen_API_KEY", "YOUR_API_KEY")
    nansen_service = Nansen(api_key=api_key)

    # Example usage:
    try:
        wallet_address = "0x74e5d6363851573800359883d918881866497191"
        wallet_info = nansen_service.get_wallet_info(wallet_address)
        print(f"Wallet Info for {wallet_address}: {wallet_info}")

        whale_list = nansen_service.get_whale_list()
        print(f"Whale List: {whale_list}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")