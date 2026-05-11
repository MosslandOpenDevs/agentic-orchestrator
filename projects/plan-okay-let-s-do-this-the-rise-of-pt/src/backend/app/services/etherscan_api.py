import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from requests.exceptions import RequestException
from tenacity import retry, retry_call, retry_wait
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EtherscanAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.etherscan.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.cache = {}  # Simple in-memory cache
        self.cache_expiry = timedelta(hours=1)  # Cache expiry time

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        headers = {"APIKEY": self.api_key}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    @retry(stop=retry_call, delay=retry_wait.exponential(multiplier=5, min=1, max=30),
           jitter=True,  # Add jitter to avoid overwhelming the API
           before_sleep=lambda x, y: time.sleep(y))
    def get_transaction_count(self, address: str) -> int:
        endpoint = f"transactioncount"
        params = {"address": address, "module": "account", "action": "balance"}
        try:
            data = self._make_request(endpoint, params)
            if data["status"] == "1":
                return int(data["result"])
            else:
                logger.error(f"Failed to get transaction count: {data}")
                raise ValueError(f"Failed to get transaction count: {data}")
        except Exception as e:
            logger.error(f"Error getting transaction count for {address}: {e}")
            raise

    def get_transaction_data(self, transaction_hash: str) -> Dict[str, Any]:
        endpoint = f"transaction/{transaction_hash}"
        try:
            data = self._make_request(endpoint)
            return data
        except Exception as e:
            logger.error(f"Error getting transaction data for {transaction_hash}: {e}")
            raise

    def get_logs(self, address: str, from_block: str = "0", to_block: str = "latest") -> Dict[str, Any]:
        endpoint = f"logs"
        params = {
            "address": address,
            "fromBlock": from_block,
            "toBlock": to_block,
            "module": "logs",
            "apikey": self.api_key
        }
        try:
            data = self._make_request(endpoint, params)
            return data
        except Exception as e:
            logger.error(f"Error getting logs for {address}: {e}")
            raise

    def get_code_contract(self, contract_address: str, block_number: str = "latest") -> Dict[str, Any]:
        endpoint = f"contract/{contract_address}"
        params = {
            "module": "contract",
            "action": "getcode",
            "apikey": self.api_key,
            "contractAddress": contract_address,
            "blockNumber": block_number
        }
        try:
            data = self._make_request(endpoint, params)
            return data
        except Exception as e:
            logger.error(f"Error getting code for {contract_address}: {e}")
            raise

    def get_token_balance(self, address: str, symbol: str = None) -> float:
        endpoint = f"tokenbalance"
        params = {
            "account": address,
            "symbol": symbol,
            "module": "account",
            "action": "tokenbalance",
            "apikey": self.api_key
        }
        try:
            data = self._make_request(endpoint, params)
            return float(data["result"])
        except Exception as e:
            logger.error(f"Error getting token balance for {address}: {e}")
            raise

    def get_block_number(self) -> int:
        endpoint = "blockNumber"
        try:
            data = self._make_request(endpoint)
            return int(data["result"])
        except Exception as e:
            logger.error(f"Error getting block number: {e}")
            raise

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: Etherscan API key not found. Please set the ETHERSCAN_API_KEY environment variable.")
        exit(1)

    etherscan = EtherscanAPI(api_key=api_key)

    try:
        # Get transaction count
        count = etherscan.get_transaction_count("0xdAC17F958D2ee523a2206206994597C13D831ec7")
        print(f"Transaction count for 0xdAC17F958D2ee523a2206206994597C13D831ec7: {count}")

        # Get transaction data
        transaction = etherscan.get_transaction_data("0x7136dc1d894f359d69f3a67f4907e9f0a6a22519")
        print(f"Transaction data: {transaction}")

        # Get logs
        logs = etherscan.get_logs("0xdAC17F958D2ee523a2206206994597C13D831ec7")
        print(f"Logs: {logs}")

    except Exception as e:
        print(f"An error occurred: {e}")