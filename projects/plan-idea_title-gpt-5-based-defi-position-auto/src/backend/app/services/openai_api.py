import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
from dataclasses import dataclass
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
CACHE_EXPIRATION_TIME = datetime.timedelta(minutes=5)
CACHE = {}

# Retry decorator with exponential backoff
@tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.error.OpenAIError),
    stop_after_all(MAX_RETRIES),
    wait=tenacity.wait_exponential(BASE=RATE_LIMIT_DELAY, MAX=RATE_LIMIT_DELAY * BACKOFF_FACTOR),
    backoff=tenacity.backoff.ExponentialBackoff,
    retry_kwargs={"timeout": 10}  # Timeout in seconds
)
def retry_openai_call(func, *args, **kwargs):
    return func(*args, **kwargs)


class OpenAIAPI:
    def __init__(self):
        self.model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.cache_key_prefix = "openai_api_"

    def _get_from_cache(self, key: str) -> Optional[str]:
        if key in CACHE and CACHE[key].expire_at > datetime.now():
            logging.debug(f"Cache hit for key: {key}")
            return CACHE[key].value
        return None

    def _set_to_cache(self, key: str, value: str, expiration_time: datetime.timedelta) -> None:
        CACHE[key] = CACHE.CacheEntry(value, expiration_time)

    class CacheEntry:
        def __init__(self, value: str, expiration_time: datetime.timedelta):
            self.value = value
            self.expire_at = datetime.now() + expiration_time

        def expire(self):
            self.expire_at = datetime.now()

    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        key = f"{self.cache_key_prefix}{prompt}_{max_tokens}"
        response = self._get_from_cache(key)
        if response:
            logging.info(f"Returning cached response for prompt: {prompt}")
            return response

        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=0.7,
            )
            text = response.choices[0].message.content
            self._set_to_cache(key, text, CACHE_EXPIRATION_TIME)
            logging.info(f"Generated text for prompt: {prompt}")
            return text
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"Analyze the sentiment of the following text: '{text}'.  Output as a JSON object with 'sentiment' (positive, negative, or neutral) and 'score' (a value between -1 and 1).",
                max_tokens=50,
                n=1,
                stop=None,
                temperature=0.5,
            )
            result = response.choices[0].text.strip()
            import json
            try:
                data = json.loads(result)
                return data
            except json.JSONDecodeError as e:
                logging.error(f"JSON decoding error: {e}, raw response: {result}")
                raise
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def list_models(self) -> List[str]:
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise