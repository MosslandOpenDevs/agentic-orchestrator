import os
import time
import logging
import json
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlchemyAPI:
    def __init__(self, api_key: str, rate_limit_delay: float = 0.1):
        """
        Initializes the AlchemyAPI service.

        Args:
            api_key: Your AlchemyAPI API key.
            rate_limit_delay: Delay in seconds to respect rate limits.
        """
        self.api_key = api_key
        self.base_url = "https://eth.alchemyapi.io/vstack"  # Or other network
        self.rate_limit_delay = rate_limit_delay
        self.retry_strategy = retry_if_exception_type(Exception)
        self.retry_counts = 0
        self.max_retry_attempts = 5

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Makes a request to the AlchemyAPI endpoint.

        Args:
            endpoint: The API endpoint to call.
            params: The parameters to send with the request.

        Returns:
            The JSON response from the API.

        Raises:
            Exception: If the request fails after multiple retries.
        """
        headers = {"X-API-KEY": self.api_key}
        try:
            response = requests.post(endpoint, headers=headers, json=params, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    @retry(stop=stop_after_attempt(self.max_retry_attempts), delay=self.rate_limit_delay, retry=self.retry_strategy)
    def get_transaction_info(self, transaction_hash: str) -> Dict[str, Any]:
        """
        Retrieves information about a transaction using its hash.

        Args:
            transaction_hash: The hash of the transaction.

        Returns:
            A dictionary containing the transaction details.
        """
        endpoint = f"{self.base_url}/transaction"
        params = {"transactionHash": transaction_hash}
        return self._make_request(endpoint, params)

    def get_block_number(self) -> Dict[str, Any]:
        """
        Retrieves the current block number.

        Returns:
            A dictionary containing the block number.
        """
        endpoint = f"{self.base_url}/blockNumber"
        params = {}
        return self._make_request(endpoint, params)

    def get_node_info(self) -> Dict[str, Any]:
        """
        Retrieves information about the AlchemyAPI node.

        Returns:
            A dictionary containing the node information.
        """
        endpoint = f"{self.base_url}/nodeInfo"
        params = {}
        return self._make_request(endpoint, params)

import requests  # Import requests here to avoid circular dependency issues

if __name__ == '__main__':
    # Example Usage (replace with your API key)
    api_key = os.environ.get("ALCHEMY_API_KEY")
    if not api_key:
        print("Error: ALCHEMY_API_KEY environment variable not set.")
        exit(1)

    alchemy_api = AlchemyAPI(api_key=api_key)

    try:
        transaction_hash = "0x1234567890abcdef1234567890abcdef12345678"
        transaction_info = alchemy_api.get_transaction_info(transaction_hash)
        print(f"Transaction Info: {transaction_info}")

        block_number = alchemy_api.get_block_number()
        print(f"Block Number: {block_number}")

        node_info = alchemy_api.get_node_info()
        print(f"Node Info: {node_info}")

    except Exception as e:
        print(f"An error occurred: {e}")