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
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

# Rate limiting configuration (example - adjust as needed)
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor

# Caching configuration (simple in-memory cache - consider a more robust solution for production)
CACHE_EXPIRATION_TIME = datetime.timedelta(minutes=5)
cache = {}

# Retry decorator with exponential backoff
@tenacity.retry(
    retries=MAX_RETRIES,
    backoff=tenacity.retry.ExponentialBackoff(factor=BACKOFF_FACTOR, max_delay=RATE_LIMIT_DELAY * BACKOFF_FACTOR),
    retry_on_exception=(openai.exceptions.APIError, openai.exceptions.RateLimitError),
)
def retry_openai_call(func, *args, **kwargs):
    return func(*args, **kwargs)

class OpenAIAPI:
    def __init__(self):
        self.model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.cache_key_prefix = "openai_api_"
        self.cache_expiration_time = CACHE_EXPIRATION_TIME

    def _get_from_cache(self, key: str) -> Optional[str]:
        if key in cache:
            if datetime.now() < cache[key]['expiration']:
                return cache[key]['value']
            else:
                del cache[key]
        return None

    def _set_to_cache(self, key: str, value: str) -> None:
        cache[key] = {'value': value, 'expiration': datetime.now() + self.cache_expiration_time}

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100) -> str:
        key = f"{self.cache_key_prefix}{prompt}_{temperature}_{max_tokens}"
        cached_result = self._get_from_cache(key)
        if cached_result:
            logging.info(f"Returning cached result for prompt: {prompt}")
            return cached_result

        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                n=1,
                stop=None,
            )
            result = response.choices[0].message.content
            self._set_to_cache(key, result)
            logging.info(f"Generated text for prompt: {prompt}")
            return result
        except openai.exceptions.APIError as e:
            logging.error(f"OpenAI API Error: {e}")
            return None
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return None

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        key = f"{self.cache_key_prefix}{text}_sentiment"
        cached_result = self._get_from_cache(key)
        if cached_result:
            logging.info(f"Returning cached sentiment analysis for text: {text}")
            return cached_result

        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"Analyze the sentiment of the following text: {text}\nSentiment:",
                max_tokens=50,
                n=1,
                stop=None,
            )
            result = response.choices[0].text.strip()
            self._set_to_cache(key, result)
            logging.info(f"Sentiment analysis completed for text: {text}")
            return {"sentiment": result}
        except openai.exceptions.APIError as e:
            logging.error(f"OpenAI API Error: {e}")
            return {"sentiment": None}
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return {"sentiment": None}