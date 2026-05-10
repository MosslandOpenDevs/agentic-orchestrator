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
        self.log_prefix = f"OpenAIAPI - "

    def generate_text(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> str:
        """
        Generates text using the OpenAI API.
        """
        cache_key = f"{prompt}-{max_tokens}-{temperature}"
        if cache_key in cache and datetime.now() - cache["timestamp"] < CACHE_EXPIRATION_TIME:
            logging.debug(self.log_prefix + f"Returning cached response for prompt: {prompt}")
            return cache["response"]

        try:
            response = retry_openai_call(
                openai.ChatCompletion.create,
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            cache[cache_key] = {"response": response, "timestamp": datetime.now()}
            logging.debug(self.log_prefix + f"Generated text for prompt: {prompt}")
            return response["choices"][0]["message"]["content"]
        except openai.error.OpenAIError as e:
            logging.error(self.log_prefix + f"OpenAI API error: {e}")
            raise

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text.
        """
        try:
            response = retry_openai_call(
                openai.Completion.create,
                model=self.model_name,
                prompt=f"Analyze the sentiment of the following text: {text}\nSentiment:",
                max_tokens=50,
                temperature=0.2,
                n=1,
                stop=["\n"]
            )
            return {"sentiment": float(response.choices[0].text.strip())}
        except openai.error.OpenAIError as e:
            logging.error(self.log_prefix + f"OpenAI API error: {e}")
            raise

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            response = retry_openai_call(
                openai.models.list,
            )
            return [model["id"] for model in response]
        except openai.error.OpenAIError as e:
            logging.error(self.log_prefix + f"OpenAI API error: {e}")
            raise