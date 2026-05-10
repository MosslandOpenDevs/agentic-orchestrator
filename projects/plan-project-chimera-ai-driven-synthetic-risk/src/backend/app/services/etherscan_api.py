import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class EtherscanAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.etherscan.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.cache = {}  # Simple in-memory cache
        self.retry_config = {
            'retry': retry(
                stop=stop_after_attempt(5),
                wait=wait_exponential(1, 5),
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
            logging.error(f"Request failed: {e}")
            return None

    def get_transaction_by_hash(self, transaction_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves transaction details by transaction hash.
        """
        endpoint = f"transaction/v1/etherscan/transaction/{transaction_hash}"
        cached_result = self.cache.get(transaction_hash)
        if cached_result:
            logging.debug(f"Transaction hash {transaction_hash} found in cache.")
            return cached_result

        result = self._make_request(endpoint)
        if result:
            self.cache[transaction_hash] = result
        return result

    def get_block_by_number(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves block details by block number.
        """
        endpoint = f"block/v1/etherscan/block/{block_number}"
        cached_result = self.cache.get(block_number)
        if cached_result:
            logging.debug(f"Block number {block_number} found in cache.")
            return cached_result

        result = self._make_request(endpoint)
        if result:
            self.cache[block_number] = result
        return result

    def get_contract_code(self, contract_address: str, abi_encoded_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the contract code by contract address and abi_encoded_id.
        """
        endpoint = f"contract/v1/etherscan/contract/{contract_address}"
        params = {"code": abi_encoded_id}
        cached_result = self.cache.get((contract_address, abi_encoded_id))
        if cached_result:
            logging.debug(f"Contract address {contract_address} and abi_encoded_id {abi_encoded_id} found in cache.")
            return cached_result

        result = self._make_request(endpoint, params=params)
        if result:
            self.cache[(contract_address, abi_encoded_id)] = result
        return result

    def get_token_balance(self, contract_address: str, account_address: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the token balance for a given account.
        """
        endpoint = f"token/v1/etherscan/token/{contract_address}"
        params = {"account": account_address}
        cached_result = self.cache.get((contract_address, account_address))
        if cached_result:
            logging.debug(f"Contract address {contract_address} and account {account_address} found in cache.")
            return cached_result

        result = self._make_request(endpoint, params=params)
        if result:
            self.cache[(contract_address, account_address)] = result
        return result


if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("ETHERSCAN_API_KEY", "YOUR_API_KEY")
    etherscan = EtherscanAPI(api_key)

    # Example Usage
    transaction_hash = "0x..."  # Replace with a valid transaction hash
    transaction_details = etherscan.get_transaction_by_hash(transaction_hash)
    if transaction_details:
        print(f"Transaction details: {transaction_details}")
    else:
        print(f"Could not retrieve transaction details for hash: {transaction_hash}")

    block_number = 123456789  # Replace with a valid block number
    block_details = etherscan.get_block_by_number(block_number)
    if block_details:
        print(f"Block details: {block_details}")
    else:
        print(f"Could not retrieve block details for number: {block_number}")