import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            params: Query parameters for the request.

        Returns:
            The JSON response from the API, or None if an error occurred.
        """
        url = f"{self.base_url}/{endpoint}"
        params['apikey'] = self.api_key

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                json_data = response.json()
                logger.debug(f"Etherscan API request successful: {json_data}")
                return json_data
            except RequestException as e:
                logger.error(f"Etherscan API request failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached.  Request failed.")
                    return None

    def get_transaction_by_hash(self, transaction_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves transaction details by transaction hash.

        Args:
            transaction_hash: The transaction hash.

        Returns:
            The transaction details as a dictionary, or None if not found.
        """
        cache_key = f"transaction_hash_{transaction_hash}"
        if cache_key in self.cache:
            logger.debug(f"Retrieving transaction from cache: {cache_key}")
            return self.cache[cache_key]

        data = self._make_request(f"transaction/{transaction_hash}")
        if data:
            self.cache[cache_key] = data
        else:
            logger.warning(f"Transaction with hash {transaction_hash} not found.")
        return data

    def get_block_by_number(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves block details by block number.

        Args:
            block_number: The block number.

        Returns:
            The block details as a dictionary, or None if not found.
        """
        data = self._make_request(f"block/{block_number}")
        return data

    def get_token_balance(self, address: str, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the token balance for a given address.

        Args:
            address: The Ethereum address.
            token_address: The token contract address.

        Returns:
            The token balance as a dictionary, or None if not found.
        """
        data = self._make_request(f"tokenBalance?contract={token_address}&owner={address}")
        return data

    def get_contract_code(self, contract_address: str, block_number: int = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves the contract code for a given contract address.

        Args:
            contract_address: The Ethereum contract address.
            block_number: The block number to retrieve the code from. If None, the latest block is used.

        Returns:
            The contract code as a dictionary, or None if not found.
        """
        params = {
            "address": contract_address
        }
        if block_number is None:
            params["blockNumber"] = "latest"
        else:
            params["blockNumber"] = str(block_number)
        data = self._make_request(f"contract/{contract_address}")
        return data