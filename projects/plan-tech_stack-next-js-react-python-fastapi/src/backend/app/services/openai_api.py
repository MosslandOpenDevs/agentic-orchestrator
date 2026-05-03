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
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

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
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise


class OpenAIAPIService:
    """
    Service for integrating with the OpenAI API.
    """

    def __init__(self):
        self.cache_key_prefix = "openai_cache_"
        self.cache_expiration_time = CACHE_EXPIRATION_TIME

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Generates text using the OpenAI API.
        """
        cache_key = f"{self.cache_key_prefix}{prompt}_{model}"
        if cache_key in CACHE and datetime.now() < CACHE[cache_key]["expiration"]:
            logging.debug(f"Cache hit for prompt: {cache_key}")
            return CACHE[cache_key]["value"]

        try:
            text = call_openai_api(prompt, model)
            CACHE[cache_key] = {
                "value": text,
                "expiration": datetime.now() + self.cache_expiration_time
            }
            logging.debug(f"Cache miss for prompt: {cache_key}, generated text.")
            return text
        except Exception as e:
            logging.error(f"Error generating text: {e}")
            raise

    def analyze_text(self, text: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Analyzes text using the OpenAI API.
        """
        prompt = f"Analyze the following text: {text}. Provide a summary and key insights."
        return self.generate_text(prompt, model)

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.error.OpenAIError as e:
            logging.error(f"Error listing models: {e}")
            raise