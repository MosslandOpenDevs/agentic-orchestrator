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
        logging.debug(f"Making request to: {url} with params: {params}")
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            response_data = response.json()
            self._cache[url] = response_data  # Cache the response
            logging.debug(f"Request successful: {response_data}")
            return response_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            raise  # Re-raise the exception for handling upstream

    @retry(stop=stop_after_attempt, delay=wait_exponential(multiplier=1, min=3, max=10))
    def get_transaction_details(self, transaction_hash: str) -> Dict[str, Any]:
        return self._make_request(f"transaction/{transaction_hash}", params={"module": "contract", "action": "decrypt"})

    @retry(stop=stop_after_attempt, delay=wait_exponential(multiplier=1, min=3, max=10))
    def get_token_balance(self, address: str, token_address: str) -> Dict[str, Any]:
        return self._make_request(f"token/{token_address}", params={"account": address, "module": "account", "action": "balance"})

    @retry(stop=stop_after_attempt, delay=wait_exponential(multiplier=1, min=3, max=10))
    def get_block_by_number(self, block_number: int) -> Dict[str, Any]:
        return self._make_request(f"block/{block_number}", params={"module": "block", "action": "get"})

    @retry(stop=stop_after_attempt, delay=wait_exponential(multiplier=1, min=3, max=10))
    def get_contract_code(self, contract_address: str, block_number: int = None) -> Dict[str, Any]:
        params = {"address": contract_address}
        if block_number:
            params["blockNumber"] = block_number
        return self._make_request(f"contract/{contract_address}", params=params)

    def clear_cache(self):
        self.cache.clear()

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: ETHERSCAN_API_KEY environment variable not set.")
        exit(1)

    etherscan = EtherscanAPI(api_key)

    try:
        transaction_hash = "0x..."  # Replace with a valid transaction hash
        transaction_details = etherscan.get_transaction_details(transaction_hash)
        print(f"Transaction Details: {transaction_details}")

        address = "0x..."  # Replace with a valid Ethereum address
        token_address = "0x..."  # Replace with a valid token address
        balance = etherscan.get_token_balance(address, token_address)
        print(f"Token Balance: {balance}")

    except Exception as e:
        print(f"An error occurred: {e}")