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
        self.cache = {}  # Simple in-memory cache
        self.retry_config = {
            'retry': retry(
                stop=stop_after_attempt(5),
                wait=wait_exponential(1, 2),
                reraise=True
            )
        }

    def _make_request(self, endpoint: str, params: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
        """Makes a request to the Etherscan API with retry logic."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"APIKEY": self.api_key}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request to Etherscan failed: {e}")
            return None

    def get_transaction_count(self, contract_address: str, from_block: str = "0", to_block: str = "latest") -> int:
        """
        Gets the transaction count for a given contract address.
        """
        cache_key = f"transaction_count_{contract_address}_{from_block}_{to_block}"
        if cache_key in self.cache:
            logging.debug(f"Returning cached transaction count for {contract_address}")
            return self.cache[cache_key]

        endpoint = "contract/count"
        params = {"contractAddress": contract_address, "fromBlock": from_block, "toBlock": to_block}
        data = self._make_request(endpoint, params)

        if data and data.get("message") == "OK":
            count = data["result"]
            self.cache[cache_key] = count
            logging.debug(f"Updated cached transaction count for {contract_address}")
            return count
        else:
            logging.warning(f"Failed to get transaction count for {contract_address}: {data.get('message')}")
            return 0

    def get_transaction_details(self, transaction_hash: str) -> Optional[Dict[str, Any]]:
        """
        Gets the details of a transaction by its hash.
        """
        endpoint = "transaction/details"
        params = {"transactionHash": transaction_hash}
        data = self._make_request(endpoint, params)

        if data and data.get("message") == "OK":
            return data["result"]
        else:
            logging.warning(f"Failed to get transaction details for {transaction_hash}: {data.get('message')}")
            return None

    def get_token_balance(self, contract_address: str, address: str) -> float:
        """
        Gets the token balance for a given address.
        """
        endpoint = "token/balance"
        params = {"contractAddress": contract_address, "address": address}
        data = self._make_request(endpoint, params)

        if data and data.get("message") == "OK":
            return data["result"]
        else:
            logging.warning(f"Failed to get token balance for {contract_address}/{address}: {data.get('message')}")
            return 0.0

    def get_block_number(self) -> int:
        """
        Gets the current block number.
        """
        endpoint = "blockNumber"
        data = self._make_request(endpoint)
        if data and data.get("message") == "OK":
            return data["result"]
        else:
            logging.warning(f"Failed to get block number: {data.get('message')}")
            return 0

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("Error: Etherscan API key not found. Set the ETHERSCAN_API_KEY environment variable.")
    else:
        etherscan = EtherscanAPI(api_key)
        # Example: Get transaction count for a contract
        count = etherscan.get_transaction_count("0xdAC17F958D2ee523a2206206994597C13D831ec7")
        print(f"Transaction count: {count}")

        # Example: Get transaction details
        details = etherscan.get_transaction_details("0x787352039a3394768729442975943609799895138a695997935472529671885")
        if details:
            print("Transaction details:", details)