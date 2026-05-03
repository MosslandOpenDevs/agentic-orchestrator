import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EtherscanAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.etherscan.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"APIKEY": api_key}
        self.cache = {}  # Simple in-memory cache
        self.retry_config = {
            "retry": retry,
            "stop_after_attempt": 5,
            "wait": wait_exponential(multiplier=1, min=3, max=10),
        }

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            raise  # Re-raise the exception for handling upstream

    def get_token_info(self, address: str) -> Optional[Dict[str, Any]]:
        cache_key = f"token_info_{address}"
        if cache_key in self.cache:
            logging.debug(f"Fetching token info from cache for {address}")
            return self.cache[cache_key]

        try:
            response = self._make_request(f"contract/{address}", params={"module": "contract", "action": "getDetails", "address": address})
            data = response.get("result")
            if data:
                self.cache[cache_key] = data
                logging.debug(f"Fetched token info for {address} and cached.")
            else:
                logging.warning(f"No token info found for {address}")
                return None
        except Exception as e:
            logging.error(f"Error getting token info for {address}: {e}")
            return None

        return None

    def get_transaction_history(self, address: str, from_block: str = "0", to_block: str = "latest", limit: int = 100) -> list:
        cache_key = f"transaction_history_{address}_{from_block}_{to_block}_{limit}"
        if cache_key in self.cache:
            logging.debug(f"Fetching transaction history from cache for {address}")
            return self.cache[cache_key]

        try:
            params = {
                "module": "history",
                "sort": "asc",
                "order": "latest",
                "fromBlock": from_block,
                "toBlock": to_block,
                "limit": limit,
                "offset": 0,
            }
            response = self._make_request(f"txlist", params=params)
            data = response.get("result")
            if data:
                self.cache[cache_key] = data
                logging.debug(f"Fetched transaction history for {address} and cached.")
            else:
                logging.warning(f"No transaction history found for {address}")
                return []
        except Exception as e:
            logging.error(f"Error getting transaction history for {address}: {e}")
            return []

        return []

    def get_block_number(self) -> int:
        try:
            response = self._make_request("blockNumber")
            return response.get("result", 0)
        except Exception as e:
            logging.error(f"Error getting block number: {e}")
            return 0