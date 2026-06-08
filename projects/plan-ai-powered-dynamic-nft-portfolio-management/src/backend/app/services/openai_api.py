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

# Rate limiting configuration (example - adjust as needed)
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff

# Caching configuration (example - adjust as needed)
CACHE_EXPIRATION_TIME = datetime.timedelta(minutes=5)

# Retry decorator
@tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.OpenAIError),
    stop_after_all(MAX_RETRIES),
    wait=tenacity.wait_exponential(BASE=RATE_LIMIT_DELAY, MAX=RATE_LIMIT_DELAY * BACKOFF_FACTOR),
    retry_kwargs={"metadata": {"attempt": tenacity.retry.current_retry()}}
)
def call_openai_api(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Calls the OpenAI API with the given prompt and model.
    Handles rate limiting, retries, and errors.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise


# Service class
class OpenAIAPIService:
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.cache_lock = threading.Lock()  # Protect cache access

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Generates text using the OpenAI API.
        """
        key = f"generate_text_{prompt}_{model}"
        with self.cache_lock:
            if key in self.cache and self.cache[key]["expiry"] > datetime.now():
                logging.debug(f"Cache hit for prompt: {prompt}")
                return self.cache[key]["value"]

        try:
            result = call_openai_api(prompt, model)
            self.cache[key] = {"value": result, "expiry": datetime.now() + CACHE_EXPIRATION_TIME}
            logging.debug(f"Cache miss for prompt: {prompt}, generated text.")
            return result
        except Exception as e:
            logging.error(f"Error generating text for prompt: {prompt}, error: {e}")
            raise

    def analyze_text(self, text: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Analyzes text using the OpenAI API.
        """
        key = f"analyze_text_{text}_{model}"
        with self.cache_lock:
            if key in self.cache and self.cache[key]["expiry"] > datetime.now():
                logging.debug(f"Cache hit for prompt: {text}")
                return self.cache[key]["value"]

        try:
            result = call_openai_api(text, model)
            self.cache[key] = {"value": result, "expiry": datetime.now() + CACHE_EXPIRATION_TIME}
            logging.debug(f"Cache miss for prompt: {text}, generated text.")
            return result
        except Exception as e:
            logging.error(f"Error analyzing text for prompt: {text}, error: {e}")
            raise

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.OpenAIError as e:
            logging.error(f"Error listing models: {e}")
            raise

import threading
if __name__ == '__main__':
    service = OpenAIAPIService()
    try:
        print(service.generate_text("Write a short story about a cat."))
        print(service.analyze_text("The quick brown fox jumps over the lazy dog."))
        print(service.list_models())
    except Exception as e:
        print(f"An error occurred: {e}")