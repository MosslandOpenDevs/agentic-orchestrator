import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OpenAIAPI:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", max_tokens: int = 100, temperature: float = 0.7, rate_limit: int = 10):
        """
        Initializes the OpenAI API service.

        Args:
            api_key: OpenAI API key.
            model: The OpenAI model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: Controls randomness (0.0 - 1.0).
            rate_limit:  Maximum number of requests per window (seconds).
        """
        openai.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.request_count = 0

    def _check_rate_limit(self) -> bool:
        """
        Checks if the rate limit has been exceeded.
        """
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit:
            return True
        else:
            self.last_request_time = current_time
            self.request_count = 0  # Reset count on rate limit reset
            return False

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(openai.error.RateLimitError),
                    wait=tenacity.wait_exponential(multiplier=1, min=1, max=10))
    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            The generated text.
        """
        if self._check_rate_limit():
            logging.warning("Rate limit exceeded.  Retrying...")
            raise openai.error.RateLimitError("Rate limit exceeded")

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the sentiment analysis results.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": f"Analyze the sentiment of the following text: {text}"}
                ],
                max_tokens=100,
                temperature=0.2
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding for the given text.

        Args:
            text: The text to generate an embedding for.

        Returns:
            A list of floats representing the embedding.
        """
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=[text]
            )
            return response['data'][0]['embedding']
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise