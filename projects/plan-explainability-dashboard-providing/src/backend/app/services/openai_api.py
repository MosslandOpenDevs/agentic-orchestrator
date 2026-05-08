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
        self.cache_key_prefix = "openai:"
        self.cache_expiration = CACHE_EXPIRATION_TIME

    def _cache_key(self, prompt: str) -> str:
        return f"{self.cache_key_prefix}{prompt}{datetime.now().timestamp()}"

    def _get_from_cache(self, prompt: str) -> Optional[str]:
        key = self._cache_key(prompt)
        if key in CACHE and CACHE[key]["expiration"] > datetime.now():
            logging.debug(f"Cache hit for prompt: {prompt}")
            return CACHE[key]["value"]
        return None

    def _set_to_cache(self, prompt: str, response: str) -> None:
        key = self._cache_key(prompt)
        CACHE[key] = {"value": response, "expiration": datetime.now() + self.cache_expiration}

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generates text using the OpenAI API.
        """
        cached_response = self._get_from_cache(prompt)
        if cached_response:
            logging.debug(f"Returning cached response for prompt: {prompt}")
            return cached_response

        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )
            text = response.choices[0].message.content
            self._set_to_cache(prompt, text)
            logging.info(f"Generated text for prompt: {prompt}")
            return text
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def analyze_sentiment(self, text: str, **kwargs) -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text.
        """
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f"Analyze the sentiment of the following text: {text}.  Output as a JSON object with 'sentiment' and 'score'.",
                max_tokens=50,
                **kwargs
            )
            result = response.choices[0].text.strip()
            try:
                import json
                sentiment_data = json.loads(result)
                return sentiment_data
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON response: {e}, Response: {result}")
                raise
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise