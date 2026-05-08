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
BACKOFF_FACTOR = 2  # Exponential backoff

# Caching configuration (simple in-memory cache)
CACHE_EXPIRATION_TIME = datetime.timedelta(minutes=5)
cache = {}

# Retry decorator with exponential backoff
@tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.OpenAIError),
    stop_after_all(MAX_RETRIES),
    wait=tenacity.wait_exponential(BASE=RATE_LIMIT_DELAY, MAX=RATE_LIMIT_DELAY * BACKOFF_FACTOR),
    backoff=tenacity.backoff.Constant)
def retry_openai_call(func, *args, **kwargs):
    return func(*args, **kwargs)

class OpenAIAPI:
    def __init__(self):
        self.model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.logger = logging.getLogger(__name__)

    def generate_text(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> str:
        """
        Generates text using the OpenAI API.
        """
        cache_key = f"generate_text_{prompt}_{max_tokens}_{temperature}"
        if cache_key in cache and datetime.now() - cache[cache_key]["timestamp"] < CACHE_EXPIRATION_TIME:
            self.logger.debug(f"Returning cached response for prompt: {prompt}")
            return cache[cache_key]["result"]

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
            result = response.choices[0].message.content
            self.logger.info(f"Generated text for prompt: {prompt}")
            cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now()
            }
            return result
        except openai.OpenAIError as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text.
        """
        try:
            response = retry_openai_call(
                openai.Completion.create,
                model=self.model_name,
                prompt=f"Analyze the sentiment of the following text: {text}.  Output as a JSON object with 'sentiment' (positive, negative, or neutral) and 'score' (a value between -1 and 1).",
                max_tokens=150,
                temperature=0.2
            )
            result = response.choices[0].text.strip()
            try:
                sentiment_data = eval(result)
                if not isinstance(sentiment_data, dict) or "sentiment" not in sentiment_data or "score" not in sentiment_data:
                    raise ValueError(f"Invalid sentiment analysis response: {result}")
                return sentiment_data
            except (SyntaxError, ValueError) as e:
                self.logger.error(f"Error parsing sentiment analysis response: {e}")
                raise
        except openai.OpenAIError as e:
            self.logger.error(f"OpenAI API error: {e}")
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
        except openai.OpenAIError as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise