import os
import time
import logging
import requests
from typing import Optional, Dict, List
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EtherscanAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.etherscan.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.cache = {}  # Simple in-memory cache
        self.retry_count = 3
        self.retry_delay = 5  # seconds

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Makes a request to the Etherscan API with retry logic.
        """
        for attempt in range(self.retry_count):
            try:
                url = f"{self.base_url}/{endpoint}"
                if params:
                    url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
                response = requests.get(url, headers={"APIKEY": self.api_key})
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed (attempt {attempt + 1}/{self.retry_count}): {e}")
                if attempt == self.retry_count - 1:
                    logging.error("Max retries reached.  Consider the request invalid.")
                    return None
                time.sleep(self.retry_delay)
        return None

    def get_transaction_by_hash(self, transaction_hash: str) -> Optional[Dict]:
        """
        Retrieves transaction details by transaction hash.
        """
        cache_key = f"transaction_hash_{transaction_hash}"
        if cache_key in self.cache:
            logging.debug(f"Returning cached data for transaction hash: {transaction_hash}")
            return self.cache[cache_key]

        result = self._make_request(endpoint="transaction/{}".format(transaction_hash))
        if result:
            self.cache[cache_key] = result
        return result

    def get_logs(self, transaction_hash: str, address: str, start_block: int = 0, end_block: int = None) -> Optional[List[Dict]]:
        """
        Retrieves logs for a specific transaction.
        """
        params = {
            "transactionhash": transaction_hash,
            "fromBlock": start_block,
            "toBlock": end_block,
            "module": "logs",
            "apikey": self.api_key
        }
        result = self._make_request(endpoint="log", params=params)
        if result:
            return result
        return None

    def get_token_balance(self, address: str, symbol: str = None) -> Optional[float]:
        """
        Retrieves the token balance for a given address.
        """
        params = {
            "address": address,
            "decimals": "18",
            "apikey": self.api_key
        }
        if symbol:
            params["symbol"] = symbol
        result = self._make_request(endpoint="tokenBalance", params=params)
        if result:
            return result.get("balance", 0.0)
        return None

    def get_contract_code(self, contract_address: str, abi_json: str) -> Optional[str]:
        """
        Retrieves the contract code from Etherscan.
        """
        params = {
            "address": contract_address,
            "abi": abi_json,
            "apikey": self.api_key
        }
        result = self._make_request(endpoint="contract", params=params)
        if result:
            return result.get("result", "")
        return None
    
    def get_block_number(self) -> Optional[int]:
        """
        Retrieves the latest block number.
        """
        result = self._make_request(endpoint="blockNumber")
        if result:
            return result.get("result", 0)
        return None


if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("Please set the ETHERSCAN_API_KEY environment variable.")
    else:
        etherscan = EtherscanAPI(api_key=api_key)
        
        # Example: Get transaction details
        transaction_hash = "0x1234567890abcdef1234567890abcdef12345678"
        transaction = etherscan.get_transaction_by_hash(transaction_hash)
        if transaction:
            print(f"Transaction Details: {transaction}")
        else:
            print(f"Could not retrieve transaction details for hash: {transaction_hash}")

        # Example: Get logs
        logs = etherscan.get_logs(transaction_hash, "0xYourAddress")
        if logs:
            print(f"Logs: {logs}")
        else:
            print("Could not retrieve logs.")