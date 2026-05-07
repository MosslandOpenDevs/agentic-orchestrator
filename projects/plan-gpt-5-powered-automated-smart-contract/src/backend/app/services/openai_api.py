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
cache = {}

# Retry decorator with exponential backoff
@tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.OpenAIError),
    stop_after_all(MAX_RETRIES),
    wait=tenacity.wait_exponential(BACKOFF_FACTOR),
    backoff=tenacity.backoff.ExponentialBackoff,
    retry_kwargs={"timeout": 10}  # Timeout in seconds
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
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise

# Service class
class OpenAIAPIService:
    def __init__(self):
        self.cache_key = "openai_cache"
        self.cache_lock = threading.Lock()  # Use a lock for thread safety

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Generates text using the OpenAI API.
        """
        cache_key = f"generate_text_{prompt}_{model}"

        with self.cache_lock:
            if cache_key in cache:
                logging.debug(f"Cache hit for prompt: {prompt}, model: {model}")
                return cache[cache_key]

        try:
            response = call_openai_api(prompt, model)
            self.cache[cache_key] = response
            logging.info(f"Generated text for prompt: {prompt}, model: {model}")
            return response
        except Exception as e:
            logging.error(f"Error generating text for prompt: {prompt}, model: {model}: {e}")
            raise

    def analyze_text(self, text: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Analyzes text using the OpenAI API.
        """
        cache_key = f"analyze_text_{text}_{model}"

        with self.cache_lock:
            if cache_key in cache:
                logging.debug(f"Cache hit for prompt: {text}, model: {model}")
                return cache[cache_key]

        try:
            response = call_openai_api(text, model)
            self.cache[cache_key] = response
            logging.info(f"Analyzed text for prompt: {text}, model: {model}")
            return response
        except Exception as e:
            logging.error(f"Error analyzing text for prompt: {text}, model: {model}: {e}")
            raise

    def clear_cache(self):
        """
        Clears the cache.
        """
        self.cache.clear()

import threading
if __name__ == '__main__':
    service = OpenAIAPIService()
    try:
        response = service.generate_text("Write a short story about a cat.")
        print(f"Generated text: {response}")

        response = service.analyze_text("The quick brown fox jumps over the lazy dog.")
        print(f"Analyzed text: {response}")

    except Exception as e:
        print(f"An error occurred: {e}")