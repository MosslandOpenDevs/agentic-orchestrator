import os
import time
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from alchemyapi import AlchemyAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlchemyAPIService:
    def __init__(self, api_key: str, rate_limit_delay: float = 0.5):
        """
        Initializes the AlchemyAPIService.

        Args:
            api_key: Your Alchemy API key.
            rate_limit_delay: Delay in seconds between API calls to respect rate limits.
        """
        self.api_key = api_key
        self.alchemy_api = AlchemyAPI(api_key=self.api_key)
        self.rate_limit_delay = rate_limit_delay
        self.retry_strategy = retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=5, max=30),
            retry=retry_with_propagation
        )
        self.cache = {}  # Simple in-memory cache

    def _call_alchemy_api(self, method_name: str, **kwargs) -> Dict[str, Any]:
        """
        Calls the Alchemy API with the specified method and arguments.
        Handles retries for transient errors.
        """
        key = (method_name, kwargs)
        if key in self.cache:
            logger.debug(f"Cache hit for {method_name} with params {kwargs}")
            return self.cache[key]

        try:
            response = self.retry_strategy(lambda: self.alchemy_api.request(method_name, **kwargs))
            self.cache[key] = response
            logger.debug(f"Successfully called {method_name} with params {kwargs}")
            return response
        except Exception as e:
            logger.error(f"Error calling {method_name} with params {kwargs}: {e}")
            raise

    def detect_address(self, address: str) -> Dict[str, Any]:
        """
        Detects the type of an address.
        """
        try:
            return self._call_alchemy_api("detect_address", address=address)
        except Exception as e:
            logger.error(f"Error detecting address {address}: {e}")
            raise

    def verify_address(self, address: str) -> Dict[str, Any]:
        """
        Verifies the validity of an address.
        """
        try:
            return self._call_alchemy_api("verify_address", address=address)
        except Exception as e:
            logger.error(f"Error verifying address {address}: {e}")
            raise

    def tokenize_address(self, address: str) -> Dict[str, Any]:
        """
        Tokenizes an address.
        """
        try:
            return self._call_alchemy_api("tokenize_address", address=address)
        except Exception as e:
            logger.error(f"Error tokenizing address {address}: {e}")
            raise

    def get_address_info(self, address: str) -> Dict[str, Any]:
        """
        Gets information about an address.
        """
        try:
            return self._call_alchemy_api("get_address_info", address=address)
        except Exception as e:
            logger.error(f"Error getting address info for {address}: {e}")
            raise

    def get_address_history(self, address: str, limit: int = 10) -> Dict[str, Any]:
        """
        Gets the transaction history for an address.
        """
        try:
            return self._call_alchemy_api("get_address_history", address=address, limit=limit)
        except Exception as e:
            logger.error(f"Error getting address history for {address}: {e}")
            raise

    def get_transaction_details(self, transaction_id: str) -> Dict[str, Any]:
        """
        Gets details about a specific transaction.
        """
        try:
            return self._call_alchemy_api("get_transaction_details", transaction_id=transaction_id)
        except Exception as e:
            logger.error(f"Error getting transaction details for {transaction_id}: {e}")
            raise