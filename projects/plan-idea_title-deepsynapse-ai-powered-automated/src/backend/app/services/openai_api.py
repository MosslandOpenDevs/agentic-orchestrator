import os
import time
import logging
import openai
import tenacity
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

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

# Caching configuration
CACHE_EXPIRATION = timedelta(minutes=5)

# Global cache (replace with a more robust caching solution for production)
cache = {}

# Retry decorator with exponential backoff
@tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.error.OpenAIError),
    stop_after_all(MAX_RETRIES),
    wait=tenacity.wait_exponential(BASE=RATE_LIMIT_DELAY, MAX=RATE_LIMIT_DELAY * BACKOFF_FACTOR),
    backoff=tenacity.backoff.ExponentialBackoff,
    retry_kwargs={"timeout": 10}  # Timeout in seconds
)
def call_openai_api(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Calls the OpenAI API for text generation.
    """
    cache_key = f"openai_prompt_{prompt}_{model}"
    if cache_key in cache and datetime.now() - cache['timestamp'] < CACHE_EXPIRATION:
        logging.debug(f"Cache hit for prompt: {prompt}")
        return cache[cache_key]

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        cache[cache_key] = {
            "content": response.choices[0].message.content,
            "timestamp": datetime.now()
        }
        logging.debug(f"Cache miss for prompt: {prompt}")
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise

class OpenAIAPIService:
    """
    Service for integrating with the OpenAI API.
    """

    def __init__(self):
        pass

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Generates text using the OpenAI API.
        """
        return call_openai_api(prompt, model)

    def analyze_text(self, text: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Analyzes text using the OpenAI API.  (Placeholder - Implement your analysis logic here)
        """
        return call_openai_api(f"Analyze the following text: {text}", model)

    def get_current_time(self) -> str:
        """
        Returns the current time in ISO format.
        """
        return datetime.now().isoformat()