import os
import time
import logging
import requests
from typing import Dict, Optional, Union
from tenacity import retry, retry_if_exception_type
from tenacity.stop_after_attempt import StopAfterAttempt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DuneAnalyticsService:
    """
    Service for integrating with Dune Analytics.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.dune.honeycomb.io/v1"):
        """
        Initializes the DuneAnalyticsService.

        Args:
            api_key: Your Dune Analytics API key.
            base_url: The base URL for the Dune Analytics API.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def _make_request(self, endpoint: str, params: Dict = None) -> Union[Dict, None]:
        """
        Makes a request to the Dune Analytics API.
        Handles rate limiting, retries, and error handling.

        Args:
            endpoint: The API endpoint to query.
            params: Query parameters to include in the request.

        Returns:
            The JSON response from the API if successful, otherwise None.
        """
        retry_obj = retry(
            stop=StopAfterAttempt(retries=3, backoff=retry_if_exception_type(Exception))
        )

        with retry_obj:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                return None

    @staticmethod
    def get_events(
        query: str,
        limit: int = 100,
        since: Optional[int] = None,
        until: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[Dict, None]:
        """
        Retrieves events from Dune Analytics.

        Args:
            query: The query string to filter events.
            limit: The maximum number of events to return.
            since: The Unix timestamp (seconds since epoch) to start from.
            until: The Unix timestamp (seconds since epoch) to end at.
            offset: The offset for pagination.

        Returns:
            The JSON response containing the events.
        """
        params = {
            "query": query,
            "limit": limit,
            "since": since,
            "until": until,
            "offset": offset,
        }
        return DuneAnalyticsService._make_request("/events", params)

    @staticmethod
    def get_contracts(
        query: str,
        limit: int = 100,
        since: Optional[int] = None,
        until: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[Dict, None]:
        """
        Retrieves contracts from Dune Analytics.

        Args:
            query: The query string to filter contracts.
            limit: The maximum number of contracts to return.
            since: The Unix timestamp (seconds since epoch) to start from.
            until: The Unix timestamp (seconds since epoch) to end at.
            offset: The offset for pagination.

        Returns:
            The JSON response containing the contracts.
        """
        params = {
            "query": query,
            "limit": limit,
            "since": since,
            "until": until,
            "offset": offset,
        }
        return DuneAnalyticsService._make_request("/contracts", params)

    @staticmethod
    def get_users(
        query: str,
        limit: int = 100,
        since: Optional[int] = None,
        until: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[Dict, None]:
        """
        Retrieves users from Dune Analytics.

        Args:
            query: The query string to filter users.
            limit: The maximum number of users to return.
            since: The Unix timestamp (seconds since epoch) to start from.
            until: The Unix timestamp (seconds since epoch) to end at.
            offset: The offset for pagination.

        Returns:
            The JSON response containing the users.
        """
        params = {
            "query": query,
            "limit": limit,
            "since": since,
            "until": until,
            "offset": offset,
        }
        return DuneAnalyticsService._make_request("/users", params)