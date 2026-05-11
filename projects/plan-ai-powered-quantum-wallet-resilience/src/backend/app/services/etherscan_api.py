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
            The JSON response from the API if successful, None otherwise.
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
            logger.debug(f"Retrieving transaction details from cache for {transaction_hash}")
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
        if data:
            return data
        else:
            logger.warning(f"Block with number {block_number} not found.")
            return None

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
        if data:
            return data
        else:
            logger.warning(f"Token balance for address {address} and token {token_address} not found.")
            return None

    def get_contract_code(self, contract_address: str, abi_json: str) -> Optional[str]:
        """
        Retrieves the contract code for a given contract address.

        Args:
            contract_address: The Ethereum contract address.
            abi_json: The ABI JSON string.

        Returns:
            The contract code as a string, or None if not found.
        """
        data = self._make_request(f"contract/{contract_address}", params={'abi': abi_json})
        if data and 'code' in data:
            return data['code']
        else:
            logger.warning(f"Contract code for address {contract_address} not found.")
            return None

# Example Usage (for testing - not part of the class itself)
if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("ETHERSCAN_API_KEY", "YOUR_API_KEY")
    etherscan = EtherscanAPI(api_key=api_key)

    # Example: Get transaction details
    transaction_hash = "0x..."  # Replace with a valid transaction hash
    transaction_details = etherscan.get_transaction_by_hash(transaction_hash)
    if transaction_details:
        print(f"Transaction details: {transaction_details}")

    # Example: Get block details
    block_number = 123456789
    block_details = etherscan.get_block_by_number(block_number)
    if block_details:
        print(f"Block details: {block_details}")

    # Example: Get token balance
    address = "0x..."  # Replace with a valid Ethereum address
    token_address = "0x..."  # Replace with a valid token contract address
    token_balance = etherscan.get_token_balance(address, token_address)
    if token_balance:
        print(f"Token balance: {token_balance}")

    # Example: Get contract code
    contract_address = "0x..."
    abi_json = '{"name":"MyContract","abi":[{"constant":true,"inputs":[],"name":"name","outputs":[{"type":"string"}],"payable":false},{"constant":true,"inputs":[{"name":"id","type":"uint256"}],"name":"get_id","outputs":[{"type":"uint256"}],"payable":false}]}'
    contract_code = etherscan.get_contract_code(contract_address, abi_json)
    if contract_code:
        print(f"Contract code: {contract_code}")