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
            The JSON response from the API if the request is successful, otherwise None.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {"APIKEY": self.api_key}
        params.update({"apikey": self.api_key})  # Ensure API key is always present

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

        endpoint = "transaction/verify"
        result = self._make_request(endpoint, params={"transactionhash": transaction_hash})
        if result:
            self.cache[cache_key] = result
        else:
            logging.warning(f"Transaction hash {transaction_hash} not found.")
        return result

    def get_block_by_number(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves block details by block number.

        Args:
            block_number: The block number to search for.

        Returns:
            The block details as a dictionary, or None if not found.
        """
        endpoint = "block/header"
        result = self._make_request(endpoint, params={"blockNumber": block_number})
        if result:
            return result
        else:
            logging.warning(f"Block number {block_number} not found.")
            return None

    def get_token_balance(self, address: str, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the token balance for a given address.

        Args:
            address: The Ethereum address to query.
            token_address: The contract address of the token.

        Returns:
            The token balance as a dictionary, or None if not found.
        """
        endpoint = "contract/balances"
        result = self._make_request(endpoint, params={"contractAddress": token_address, "address": address})
        if result and result.get("result"):
            return result["result"]
        else:
            logging.warning(f"Token balance for address {address} and contract {token_address} not found.")
            return None
    
    def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves token information by contract address.

        Args:
            token_address: The contract address of the token.

        Returns:
            The token information as a dictionary, or None if not found.
        """
        endpoint = "contract/info"
        result = self._make_request(endpoint, params={"address": token_address})
        if result:
            return result
        else:
            logging.warning(f"Token information for contract {token_address} not found.")
            return None