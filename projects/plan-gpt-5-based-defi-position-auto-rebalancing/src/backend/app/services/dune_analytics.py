import os
import time
import logging
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variable names
API_KEY_ENV = "DUNE_API_KEY"
API_URL = "https://api.dune.com/events"  # Replace with actual API URL if different
RATE_LIMIT_DELAY = 0.5  # Seconds - Adjust based on Dune's rate limits
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor

# Retry decorator
@retry(stop=stop_after_attempt(MAX_RETRIES),
       delay=BACKOFF_FACTOR * RATE_LIMIT_DELAY,
       retry=retry_if_exception_type((requests.exceptions.RequestException,
                                      Timeout,
                                      ConnectionError)))
def make_dune_request(url: str, method: str, data: Dict = None) -> Dict:
    """
    Makes a request to the Dune API with retry logic.
    """
    headers = {
        "Accept": "application/json",
        "Dune-Api-Key": os.environ.get(API_KEY_ENV)
    }
    try:
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Dune API request failed: {e}")
        raise


class DuneAnalyticsService:
    def __init__(self):
        self.api_key = os.environ.get(API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"Dune API key not found in environment variable {API_KEY_ENV}")
        self.cache = {}  # Simple in-memory cache

    def _cache_key(self, query: str) -> str:
        """Generates a cache key based on the query."""
        return f"dune_query_{query}"

    def query_events(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Queries the Dune Analytics API for events matching the given query.

        Args:
            query: The Dune query string.
            limit: The maximum number of events to return.

        Returns:
            A list of dictionaries, where each dictionary represents an event.
        """
        cache_key = self._cache_key(query)
        if cache_key in self.cache:
            logger.debug(f"Returning cached results for query: {query}")
            return self.cache[cache_key]

        try:
            response = make_dune_request(f"{API_URL}/{query}?limit={limit}")
            data = response.get("data", [])
            self.cache[cache_key] = data
            logger.info(f"Query results for query: {query} - {len(data)} events")
            return data
        except Exception as e:
            logger.error(f"Error querying Dune for query: {query} - {e}")
            return []

    def get_event(self, query: str, event_id: str) -> Optional[Dict]:
        """
        Retrieves a single event by its ID.

        Args:
            query: The Dune query string.
            event_id: The ID of the event to retrieve.

        Returns:
            A dictionary representing the event, or None if the event is not found.
        """
        try:
            response = make_dune_request(f"{API_URL}/events/{event_id}", "GET")
            data = response.get("data", [])
            if data:
                return data[0]
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting event {event_id} - {e}")
            return None

    def get_event_stream(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Retrieves an event stream.
        """
        try:
            response = make_dune_request(f"{API_URL}/{query}?limit={limit}")
            data = response.get("data", [])
            return data
        except Exception as e:
            logger.error(f"Error getting event stream - {e}")
            return []


if __name__ == '__main__':
    # Example Usage (replace with your actual Dune query)
    try:
        dune_service = DuneAnalyticsService()
        events = dune_service.query_events("eth_tx.created")
        print(f"First 5 events: {events[:5]}")

        event = dune_service.get_event("eth_tx.created", "0x1234567890abcdef1234567890abcdef12345678")
        print(f"Event: {event}")

    except ValueError as e:
        print(f"Error: {e}")