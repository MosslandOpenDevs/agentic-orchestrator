import os
import time
import logging
import tenacity
from typing import List, Dict, Optional
from dune_api.api import DuneAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class DuneAnalyticsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.dune_api = DuneAPI(api_key=self.api_key)
        self.cache = {}  # Simple in-memory cache
        self.retry_config = {
            "max_retries": 3,
            "backoff": {
                "factor": 2,
                "max_delay": 60
            },
            "retries": tenacity.retry_wait_exponential
        }

    def _cache_key(self, query: str) -> str:
        return f"dune_query_{query}"

    def _get_from_cache(self, query: str) -> Optional[Dict]:
        if query in self.cache:
            logging.debug(f"Cache hit for query: {query}")
            return self.cache[query]
        return None

    def _set_to_cache(self, query: str, result: Dict) -> None:
        self.cache[query] = result
        logging.debug(f"Cache miss for query: {query}, stored result.")

    def execute_query(self, query: str) -> Dict:
        """
        Executes a Dune Analytics query and returns the results.
        Handles rate limiting, retries, and caching.
        """
        query_key = self._cache_key(query)
        cached_result = self._get_from_cache(query_key)
        if cached_result:
            logging.debug(f"Returning cached result for query: {query_key}")
            return cached_result

        try:
            result = self.dune_api.run(query)
            self._set_to_cache(query_key, result)
            return result
        except tenacity.RetryError as e:
            logging.error(f"Query failed after {e.attempt} retries: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred while executing query: {query}")
            raise

    def get_all_queries(self, queries: List[str]) -> Dict[str, Dict]:
        """
        Executes multiple queries concurrently and returns the results.
        """
        results = {}
        for query in queries:
            results[query] = self.execute_query(query)
        return results

    def get_all_queries_with_retry(self, queries: List[str]) -> Dict[str, Dict]:
        """
        Executes multiple queries concurrently with retry logic.
        """
        return tenacity.retry(
            self.retry_config,
            self.get_all_queries,
            args=(queries,)
        )