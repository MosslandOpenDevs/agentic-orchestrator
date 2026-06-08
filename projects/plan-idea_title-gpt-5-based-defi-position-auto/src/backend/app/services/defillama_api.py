import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configuration
API_URL = os.environ.get("DEFIL_API_URL", "https://api.defillama.com")
RATE_LIMIT_DELAY = int(os.environ.get("DEFIL_RATE_LIMIT_DELAY", 0.2))  # Seconds
MAX_RETRIES = int(os.environ.get("DEFIL_MAX_RETRIES", 3))
INITIAL_DELAY = float(os.environ.get("DEFIL_INITIAL_DELAY", 0.1))
EXPONENTIAL_BACKOFF = int(os.environ.get("DEFIL_EXPONENTIAL_BACKOFF", 3))

# Cache (Simple in-memory dictionary)
cache = {}

# Retry decorator
@retry(stop=stop_after_attempt(MAX_RETRIES),
       wait=wait_exponential(INITIAL_DELAY, EXPONENTIAL_BACKOFF),
       retry=retry)
def fetch_data(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Fetches data from DefiLlama API with retry logic.
    """
    url = f"{API_URL}/{endpoint}"
    logging.info(f"Fetching data from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        logging.debug(f"Successfully fetched data: {data}")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None


class DefiLlamaService:
    """
    Service for integrating with the DefiLlama API.
    """

    def __init__(self):
        self.cache_duration = 60  # Cache for 60 seconds
        self.logger = logging.getLogger(__name__)

    def get_tvl(self, chain: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves TVL data for a given chain.
        """
        cache_key = f"tvl_{chain}"
        if cache_key in cache and time.time() - cache_key.split("_")[1] < self.cache_duration:
            logging.debug(f"Returning cached TVL data for {chain}")
            return cache[cache_key]

        data = fetch_data(f"defi_tvl")
        if data:
            # Filter TVL data by chain
            filtered_data = {
                item["name"]: item for item in data if item["chain"] == chain
            }
            if filtered_data:
                cache[cache_key] = filtered_data[list(filtered_data.keys())[0]]
            else:
                logging.warning(f"No TVL data found for chain {chain}")
        else:
            logging.warning(f"Failed to retrieve TVL data for chain {chain}")

        return data

    def get_protocols(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves a list of DeFi protocols.
        """
        data = fetch_data("protocols")
        if data:
            logging.debug(f"Successfully fetched protocols: {data}")
        else:
            logging.warning("Failed to retrieve protocols.")
        return data

    def get_protocol_details(self, protocol_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves details for a specific DeFi protocol.
        """
        data = fetch_data(f"protocol/{protocol_name}")
        if data:
            logging.debug(f"Successfully fetched protocol details for {protocol_name}: {data}")
        else:
            logging.warning(f"Failed to retrieve protocol details for {protocol_name}.")
        return data


if __name__ == '__main__':
    service = DefiLlamaService()

    # Example Usage
    tvl_eth = service.get_tvl("ethereum")
    print(f"TVL for Ethereum: {tvl_eth}")

    protocols = service.get_protocols()
    print(f"All Protocols: {protocols}")

    protocol_details = service.get_protocol_details("Aave")
    print(f"Aave Details: {protocol_details}")