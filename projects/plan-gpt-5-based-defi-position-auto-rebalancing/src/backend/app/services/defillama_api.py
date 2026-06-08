import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Environment variable names
API_URL = os.environ.get("DEFIL_API_URL", "https://api.defillama.com")
RATE_LIMIT_DELAY = float(os.environ.get("DEFIL_RATE_LIMIT_DELAY", 0.2))
MAX_RETRIES = int(os.environ.get("DEFIL_MAX_RETRIES", 3))
INITIAL_DELAY = float(os.environ.get("DEFIL_INITIAL_DELAY", 0.1))

# Cache configuration
CACHE_TTL = int(os.environ.get("DEFIL_CACHE_TTL", 600))  # 10 minutes
cache = {}

# Retry configuration
retry_exception = (requests.exceptions.RequestException,
                   requests.exceptions.HTTPError,
                   requests.exceptions.Timeout)

# DefiLlama API Service Class
class DefiLlamaAPI:
    def __init__(self):
        self.api_url = API_URL
        self.retry_config = {
            'retry': retry,
            'stop_after_attempt': MAX_RETRIES,
            'wait': wait_exponential(INITIAL_DELAY, RATE_LIMIT_DELAY),
        }

    def _fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches data from the DefiLlama API with retry logic.
        """
        try:
            response = requests.get(f"{self.api_url}/{endpoint}", params=params, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            logging.debug(f"Successfully fetched data from {endpoint}: {data}")
            return data
        except retry_exception as e:
            logging.error(f"API request failed: {e}. Retrying...")
            # Consider adding more sophisticated error handling here,
            # such as checking for specific error codes and handling them differently.
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return None

    def get_tvl_by_protocol(self, protocol_name: str, chain_id: int = 1) -> Optional[Dict[str, Any]]:
        """
        Fetches TVL data for a specific protocol.
        """
        cache_key = f"tvl_{protocol_name}_{chain_id}"
        if cache_key in cache:
            logging.debug(f"Fetching TVL from cache for {protocol_name}, {chain_id}")
            return cache[cache_key]

        data = self._fetch_data(f"protocols/{protocol_name}", params={"chain_id": chain_id})
        if data:
            tvl = data.get("tvl")
            if tvl is not None:
                cache[cache_key] = tvl
            else:
                logging.warning(f"TVL not found for protocol {protocol_name}, {chain_id}")
        else:
            logging.warning(f"Failed to fetch TVL for protocol {protocol_name}, {chain_id}")

        return data

    def get_protocols(self) -> Optional[Dict[str, Any]]:
        """
        Fetches all protocols.
        """
        return self._fetch_data("protocols")

    def get_chains(self) -> Optional[Dict[str, Any]]:
        """
        Fetches all chains.
        """
        return self._fetch_data("chains")

    def get_defi_assets(self) -> Optional[Dict[str, Any]]:
        """
        Fetches all defi assets.
        """
        return self._fetch_data("assets")