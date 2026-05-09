import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
openai.api_key = OPENAI_API_KEY

# Rate limiting configuration (adjust as needed)
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor

# Caching configuration
CACHE_EXPIRATION = timedelta(minutes=5)

# Retry configuration
retry_client = tenacity.RetryContext(
    retries=MAX_RETRIES,
    backoff=tenacity.exponential_backoff(factor=BACKOFF_FACTOR),
    retry=tenacity.retry_if_exception_type(
        (openai.error.Timeout, openai.error.APIConnectionError, openai.error.RateLimitError)
    )
)


class OpenAIAPI:
    def __init__(self):
        self.cache = {}
        self.cache_lock = threading.Lock()

    def _call_openai(self, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
        """
        Calls the OpenAI API with the given prompt, model, and temperature.
        Handles rate limiting, retries, and caching.
        """
        key = (prompt, model, temperature)

        if key in self.cache:
            if datetime.now() < self.cache[key]["expiry"]:
                logging.debug(f"Cache hit for prompt: {prompt}, model: {model}, temperature: {temperature}")
                return self.cache[key]["value"]
            else:
                logging.debug(f"Cache expired for prompt: {prompt}, model: {model}, temperature: {temperature}")
                del self.cache[key]

        try:
            with retry_client:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature
                )
                result = response.choices[0].message.content
                logging.debug(f"API call successful for prompt: {prompt}, model: {model}, temperature: {temperature}")
                self._cache_result(key, result)
                return result
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit error: {e}")
            time.sleep(RATE_LIMIT_DELAY)
            raise
        except openai.error.APIConnectionError as e:
            logging.error(f"API connection error: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
        """
        Generates text using the OpenAI API.
        """
        return self._call_openai(prompt, model, temperature)

    def analyze_sentiment(self, text: str, model: str = "gpt-3.5-turbo") -> Dict:
        """
        Analyzes the sentiment of the given text using the OpenAI API.
        """
        prompt = f"Analyze the sentiment of the following text: '{text}'. Return the sentiment as a JSON object with 'sentiment' and 'score' keys."
        return self._call_openai(prompt, model)

    def _cache_result(self, key: tuple, value: str):
        """
        Caches the result for a given key.
        """
        with self.cache_lock:
            self.cache[key] = {"value": value, "expiry": datetime.now() + CACHE_EXPIRATION}

import threading