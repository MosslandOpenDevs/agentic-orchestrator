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

# Rate limiting configuration (adjust as needed)
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor

# Caching configuration (simple in-memory cache)
CACHE_EXPIRATION_TIME = datetime.timedelta(minutes=5)
CACHE = {}

# Retry configuration
retry_client = tenacity.RetryContext(retries=MAX_RETRIES, backoff=tenacity.exponential_backoff(factor=BACKOFF_FACTOR))

class OpenAIAPI:
    def __init__(self):
        self.model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.cache_key_prefix = "openai_api_"

    def _cache_key(self, prompt: str) -> str:
        return f"{self.cache_key_prefix}{prompt}"

    def _get_from_cache(self, prompt: str) -> Optional[str]:
        key = self._cache_key(prompt)
        if key in CACHE and CACHE[key].expire_at > datetime.now():
            logging.debug(f"Cache hit for prompt: {prompt}")
            return CACHE[key]["value"]
        else:
            logging.debug(f"Cache miss for prompt: {prompt}")
            return None

    def _set_to_cache(self, prompt: str, value: str) -> None:
        key = self._cache_key(prompt)
        CACHE[key] = {"value": value, "expire_at": datetime.now() + CACHE_EXPIRATION_TIME}

    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generates text using the OpenAI API.
        """
        try:
            with retry_client:
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
                self._set_to_cache(prompt, text)
                return text
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit exceeded: {e}")
            time.sleep(RATE_LIMIT_DELAY)
            raise
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text.
        """
        try:
            with retry_client:
                response = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=f"Analyze the sentiment of the following text: {text}.  Output a JSON object with 'sentiment' (positive, negative, or neutral) and 'score' (a value between -1 and 1).",
                    max_tokens=50,
                    n=1,
                    stop=None,
                    temperature=0.5,
                )
                result = response.choices[0].text.strip()
                try:
                    sentiment_data = eval(result)
                    if not isinstance(sentiment_data, dict) or "sentiment" not in sentiment_data or "score" not in sentiment_data:
                        raise ValueError(f"Invalid sentiment analysis response: {result}")
                    return sentiment_data
                except (SyntaxError, ValueError) as e:
                    logging.error(f"Error parsing sentiment analysis response: {e}")
                    raise
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            with retry_client:
                response = openai.models.list()
                return [model['id'] for model in response.data]
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise