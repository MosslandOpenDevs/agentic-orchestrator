import os
import time
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AlchemyAPI:
    def __init__(self, api_key: str, base_url: str = "https://ethervm.alchemyapi.io/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.retry_config = retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(1, 2),
            retry=retry_on_exception(
                None,  # No specific exception to retry on
                # Add more specific exceptions to retry on here if needed
            )
        )

    def _make_request(self, endpoint: str, params: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}"
        headers = {"X-API-KEY": self.api_key}
        try:
            response = requests.post(url, headers=headers, json=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Alchemy API request failed: {e}")
            return None

    def get_node_info(self) -> Optional[Dict[str, Any]]:
        return self._make_request("node_info")

    def get_block(self, block_number: int) -> Optional[Dict[str, Any]]:
        return self._make_request(f"blocks/{block_number}")

    def get_transaction(self, transaction_hash: str) -> Optional[Dict[str, Any]]:
        return self._make_request(f"transactions/{transaction_hash}")

    def get_account(self, address: str) -> Optional[Dict[str, Any]]:
        return self._make_request(f"accounts/{address}")

    def get_log(self, event_type: str, block_number: int) -> Optional[Dict[str, Any]]:
        return self._make_request(f"logs", params={"event_type": event_type, "blockNumber": block_number})

    def get_token_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self._make_request(f"tokens/{symbol}")

    def get_nft_info(self, contract_address: str, token_id: int) -> Optional[Dict[str, Any]]:
        return self._make_request(f"nfts/{contract_address}/{token_id}")
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(1, 2), retry=retry_on_exception)
    def execute_request(self, endpoint: str, params: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
        return self._make_request(endpoint, params)