import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# Rate limiting configuration (adjust as needed)
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor

# Caching configuration (simple in-memory cache)
CACHE_EXPIRATION = datetime.timedelta(minutes=5)
CACHE = {}

# Retry decorator with exponential backoff
@tenacity.retry(
    tries=MAX_RETRIES,
    backoff=tenacity.retry.ExponentialBackoff(factor=BACKOFF_FACTOR, max_attempts=MAX_RETRIES),
    retry_on_exception=(openai.exceptions.APIError, openai.exceptions.RateLimitError),
    add_sleep=RATE_LIMIT_DELAY
)
def call_openai_api(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
    """
    Calls the OpenAI API for text generation.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=100,  # Adjust as needed
            n=1,
            stop=None,
        )
        return response.choices[0].message.content
    except openai.exceptions.APIError as e:
        logging.error(f"OpenAI API Error: {e}")
        raise
    except openai.exceptions.RateLimitError as e:
        logging.warning(f"OpenAI Rate Limit Error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


class OpenAIAPIService:
    def __init__(self):
        pass

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
        """
        Generates text using the OpenAI API.
        """
        cached_result = self._get_from_cache(prompt)
        if cached_result:
            logging.debug(f"Text generated from cache for prompt: {prompt}")
            return cached_result

        try:
            text = call_openai_api(prompt, model, temperature)
            self._set_to_cache(prompt, text)
            return text
        except Exception as e:
            logging.error(f"Failed to generate text for prompt: {prompt}. Error: {e}")
            return None

    def analyze_text(self, text: str, model: str = "text-davinci-003") -> str:
        """
        Analyzes text using the OpenAI API (placeholder - replace with actual analysis).
        """
        try:
            response = openai.Completion.create(
                model=model,
                prompt=text,
                max_tokens=50,
                temperature=0.5
            )
            return response.choices[0].text.strip()
        except openai.exceptions.APIError as e:
            logging.error(f"OpenAI API Error during analysis: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during analysis: {e}")
            return None

    def _get_from_cache(self, key: str) -> Optional[str]:
        """
        Retrieves data from the cache.
        """
        if key in CACHE:
            if CACHE[key].expire_at is None or datetime.now() < CACHE[key].expire_at:
                return CACHE[key].value
            else:
                del CACHE[key]
        return None

    def _set_to_cache(self, key: str, value: str):
        """
        Stores data in the cache.
        """
        CACHE[key] = CacheEntry(value, datetime.now() + CACHE_EXPIRATION)

class CacheEntry:
    def __init__(self, value, expire_at):
        self.value = value
        self.expire_at = expire_at