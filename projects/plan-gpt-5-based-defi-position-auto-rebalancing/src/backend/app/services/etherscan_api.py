import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class EtherscanAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.etherscan.io/v1"):
        """
        Initializes the EtherscanAPI service.

        Args:
            api_key: Your Etherscan API key.
            base_url: The base URL for the Etherscan API.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.cache = {}  # Simple in-memory cache
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _make_request(self, endpoint: str, params: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
        """
        Makes a request to the Etherscan API. Handles retries and rate limiting.

        Args:
            endpoint: The API endpoint to call.
            params: The query parameters to include in the request.

        Returns:
            The JSON response from the API, or None if an error occurred after retries.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {"APIKEY": self.api_key}
        retries = self.retry_count
        while retries < self.max_retries:
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed: {e}")
                self.retry_count += 1
                if self.retry_count > self.max_retries:
                    logging.error("Max retries reached.  Request failed.")
                    return None
                time.sleep(self.retry_delay)
        return None

    def get_transaction_by_hash(self, transaction_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves transaction details by transaction hash.

        Args:
            transaction_hash: The transaction hash to search for.

        Returns:
            The transaction details as a dictionary, or None if not found.
        """
        cache_key = f"transaction_hash_{transaction_hash}"
        if cache_key in self.cache:
            logging.debug(f"Returning cached data for transaction hash: {transaction_hash}")
            return self.cache[cache_key]

        endpoint = "transaction/v1/etherscan/transaction"
        params = {"transactionHash": transaction_hash}
        data = self._make_request(endpoint, params)

        if data:
            self.cache[cache_key] = data
        else:
            logging.warning(f"Transaction hash {transaction_hash} not found.")

        return data

    def get_block_by_number(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves block details by block number.

        Args:
            block_number: The block number to search for.

        Returns:
            The block details as a dictionary, or None if not found.
        """
        cache_key = f"block_number_{block_number}"
        if cache_key in self.cache:
            logging.debug(f"Returning cached data for block number: {block_number}")
            return self.cache[cache_key]

        endpoint = "block/v1/etherscan/block"
        params = {"blockNumber": block_number}
        data = self._make_request(endpoint, params)

        if data:
            self.cache[cache_key] = data
        else:
            logging.warning(f"Block number {block_number} not found.")

        return data

    def get_token_balance(self, address: str, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the token balance for a given address.

        Args:
            address: The Ethereum address to query.
            token_address: The contract address of the token.

        Returns:
            The token balance as a dictionary, or None if not found.
        """
        cache_key = f"token_balance_{address}_{token_address}"
        if cache_key in self.cache:
            logging.debug(f"Returning cached data for token balance: {address} - {token_address}")
            return self.cache[cache_key]

        endpoint = "token/v1/etherscan/token"
        params = {
            "contractAddress": token_address,
            "address": address
        }
        data = self._make_request(endpoint, params)

        if data:
            self.cache[cache_key] = data
        else:
            logging.warning(f"Token balance for {address} - {token_address} not found.")

        return data


if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("ETHERSCAN_API_KEY", "YOUR_API_KEY")
    etherscan = EtherscanAPI(api_key=api_key)

    # Example usage:
    transaction_hash = "0x..."  # Replace with a valid transaction hash
    transaction_details = etherscan.get_transaction_by_hash(transaction_hash)
    if transaction_details:
        print(f"Transaction details: {transaction_details}")

    block_number = 123456789  # Replace with a valid block number
    block_details = etherscan.get_block_by_number(block_number)
    if block_details:
        print(f"Block details: {block_details}")

    address = "0x..." # Replace with a valid Ethereum address
    token_address = "0x..." # Replace with a valid token contract address
    token_balance = etherscan.get_token_balance(address, token_address)
    if token_balance:
        print(f"Token balance: {token_balance}")