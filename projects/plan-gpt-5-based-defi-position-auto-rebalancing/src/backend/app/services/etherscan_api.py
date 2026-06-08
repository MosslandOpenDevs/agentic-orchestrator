import os
import time
import logging
import requests
from typing import Optional, Dict, List
from tenacity import retry, retry_if_exception_type
from tenacity.stop_after_attempt import StopAfterAttempt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EtherscanAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.etherscan.io/data"):
        self.api_key = api_key
        self.base_url = base_url
        self.cache = {}  # Simple in-memory cache
        self.retry_config = {
            'retry': retry_if_exception_type(Exception),
            'stop_after_attempt': 3,
            'wait': 2  # seconds
        }

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Makes a request to the Etherscan API with retry logic."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"APIKEY": self.api_key}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise  # Re-raise the exception for retry logic

    @retry(stop=StopAfterAttempt(retries=3), delay=2, backoff=2)
    def get_transaction_details(self, transaction_hash: str) -> Dict:
        """
        Retrieves transaction details from Etherscan.
        """
        endpoint = f"transaction/{transaction_hash}"
        try:
            data = self._make_request(endpoint)
            if data:
                logger.info(f"Successfully retrieved transaction details for hash: {transaction_hash}")
                return data
            else:
                logger.warning(f"No data returned for transaction hash: {transaction_hash}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get transaction details for hash {transaction_hash}: {e}")
            raise

    def get_token_info(self, contract_address: str, symbol: str) -> Dict:
        """
        Retrieves token information from Etherscan.
        """
        endpoint = f"token/{symbol}/{contract_address}"
        try:
            data = self._make_request(endpoint)
            if data:
                logger.info(f"Successfully retrieved token info for contract: {contract_address}, symbol: {symbol}")
                return data
            else:
                logger.warning(f"No token info found for contract: {contract_address}, symbol: {symbol}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get token info for contract {contract_address}, symbol {symbol}: {e}")
            raise

    def get_block_by_number(self, block_number: int) -> Dict:
        """
        Retrieves block details from Etherscan.
        """
        endpoint = f"block/{block_number}"
        try:
            data = self._make_request(endpoint)
            if data:
                logger.info(f"Successfully retrieved block details for number: {block_number}")
                return data
            else:
                logger.warning(f"No block data found for number: {block_number}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get block details for number {block_number}: {e}")
            raise

    def get_contract_code(self, contract_address: str, code_hash: str) -> Dict:
        """
        Retrieves contract code from Etherscan.
        """
        endpoint = f"contract/{code_hash}/{contract_address}"
        try:
            data = self._make_request(endpoint)
            if data:
                logger.info(f"Successfully retrieved contract code for contract: {contract_address}, code_hash: {code_hash}")
                return data
            else:
                logger.warning(f"No contract code found for contract: {contract_address}, code_hash: {code_hash}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get contract code for contract {contract_address}, code_hash {code_hash}: {e}")
            raise