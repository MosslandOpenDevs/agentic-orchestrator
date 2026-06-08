import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DefiLlamaService:
    """
    Service for integrating with the DefiLlama API.
    """

    def __init__(self, api_url: str = "https://api.defillama.com/"):
        """
        Initializes the DefiLlamaService.

        Args:
            api_url: The base URL for the DefiLlama API.
        """
        self.api_url = api_url
        self.cache = {}  # Simple in-memory cache
        self.retry_count = 3
        self.retry_delay = 5  # seconds
        self.max_retries = 5

    def _fetch_data(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches data from the DefiLlama API with retry logic.

        Args:
            endpoint: The API endpoint to fetch data from.
            params: Optional query parameters.

        Returns:
            The parsed JSON response as a dictionary, or None if an error occurred.
        """
        for attempt in range(self.retry_count + 1):
            try:
                response = requests.get(f"{self.api_url}{endpoint}", params=params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except RequestException as e:
                logging.error(f"Request failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}")
                if attempt == self.retry_count:
                    logging.error("Max retries reached.")
                    return None
                time.sleep(self.retry_delay)

    def get_tvl_by_protocol(self, protocol_name: str, timeframe: str = "all") -> Optional[Dict[str, Any]]:
        """
        Gets TVL data for a specific protocol.

        Args:
            protocol_name: The name of the DeFi protocol.
            timeframe: The timeframe for the TVL data (e.g., "all", "7d", "30d").

        Returns:
            The TVL data as a dictionary, or None if not found.
        """
        cache_key = f"tvl_{protocol_name}_{timeframe}"
        if cache_key in self.cache:
            logging.debug(f"Returning cached TVL data for {protocol_name} and {timeframe}")
            return self.cache[cache_key]

        endpoint = f"/tvl/protocol"
        params = {"protocol": protocol_name, "timeframe": timeframe}
        data = self._fetch_data(endpoint, params)

        if data:
            self.cache[cache_key] = data
            logging.debug(f"Stored TVL data for {protocol_name} and {timeframe} in cache.")
        else:
            logging.warning(f"Failed to retrieve TVL data for {protocol_name} and {timeframe}")

        return data

    def get_protocols(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of all DeFi protocols.

        Returns:
            The list of protocols as a dictionary, or None if an error occurred.
        """
        endpoint = "/protocols"
        data = self._fetch_data(endpoint)
        return data

    def get_protocol_details(self, protocol_name: str) -> Optional[Dict[str, Any]]:
        """
        Gets detailed information about a specific protocol.

        Args:
            protocol_name: The name of the DeFi protocol.

        Returns:
            The protocol details as a dictionary, or None if not found.
        """
        endpoint = f"/protocols/{protocol_name}"
        data = self._fetch_data(endpoint)
        return data

    def get_defi_lending_pools(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi lending pools.
        """
        endpoint = "/lending/pools"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_stablecoins(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi stablecoins.
        """
        endpoint = "/stablecoins"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_yield_farms(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi yield farms.
        """
        endpoint = "/yieldfarms"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_token_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi token metrics.
        """
        endpoint = "/tokenmetrics"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_markets(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi defi markets.
        """
        endpoint = "/defimarkets"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_options(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi options.
        """
        endpoint = "/options"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_perps(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi perpetuals.
        """
        endpoint = "/perps"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_synthetic(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi synthetics.
        """
        endpoint = "/synthetic"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_money(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi money.
        """
        endpoint = "/money"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_index(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi index.
        """
        endpoint = "/index"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_treasury(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi treasury.
        """
        endpoint = "/treasury"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_nft(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi nft.
        """
        endpoint = "/nft"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_launchpad(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi launchpad.
        """
        endpoint = "/launchpad"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_staking(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi staking.
        """
        endpoint = "/staking"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_insurance(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi insurance.
        """
        endpoint = "/insurance"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_social(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi social.
        """
        endpoint = "/social"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_governance(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi governance.
        """
        endpoint = "/governance"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_credit(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi credit.
        """
        endpoint = "/credit"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_assets(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi assets.
        """
        endpoint = "/assets"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_derivatives(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi derivatives.
        """
        endpoint = "/derivatives"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_lending(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi lending.
        """
        endpoint = "/lending"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_trading(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi trading.
        """
        endpoint = "/trading"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_payment(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi payment.
        """
        endpoint = "/payment"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_portfolio(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of DeFi portfolio.
        """
        endpoint = "/portfolio"
        data = self._fetch_data(endpoint)
        return data
    
    def get_defi_defi_yield(self) -> Optional[Dict[str, Any]]:
        """
        Gets a list of