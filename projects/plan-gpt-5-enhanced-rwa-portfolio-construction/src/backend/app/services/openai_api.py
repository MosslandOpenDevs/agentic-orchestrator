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
            api_key: Your OpenAI API key.
            model: The OpenAI model to use (default: "gpt-3.5-turbo").
            max_tokens: The maximum number of tokens to generate (default: 100).
            temperature: Controls randomness (default: 0.7).
            rate_limit:  Maximum number of requests per window (default: 10).
        """
        openai.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_window = 60  # seconds
        self.rate_limit_counter = 0

    def _log_request(self, prompt: str) -> None:
        """Logs the request details."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Request - Timestamp: {timestamp}, Prompt: {prompt}, Model: {self.model}, Max Tokens: {self.max_tokens}, Temperature: {self.temperature}")

    def _is_rate_limited(self) -> bool:
        """Checks if the rate limit has been exceeded."""
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit_window:
            self.rate_limit_counter += 1
            if self.rate_limit_counter > self.rate_limit:
                self.rate_limit_counter = 1
                return True
        self.last_request_time = current_time
        self.rate_limit_counter = 0
        return False

    def _retry_request(self, error):
        """Retries the request with exponential backoff."""
        if isinstance(error, openai.error.RateLimitError):
            logging.warning("Rate limit exceeded. Retrying...")
            time.sleep(2)  # Exponential backoff
            return
        elif isinstance(error, openai.error.OpenAIError):
            logging.error(f"OpenAI API error: {error}")
            return
        else:
            logging.error(f"Unexpected error: {error}")
            return

    @tenacity.retry(stop=stop_after_retries, retry=retry_delay_seconds, exceptions=(openai.error.RateLimitError, openai.error.OpenAIError))
    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            The generated text.

        Raises:
            Exception: If any error occurs during the API call.
        """
        self._log_request(prompt)
        if self._is_rate_limited():
            raise openai.error.RateLimitError("Rate limit exceeded.")

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            self._retry_request(e)
            raise

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the sentiment scores.
        """
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Analyze the sentiment of the following text: {text}\nSentiment Score:",
                max_tokens=50,
                n=1,
                stop=None,
                temperature=0.3,
            )
            result = response.choices[0].text.strip()
            return {"sentiment": float(result)}
        except openai.error.OpenAIError as e:
            self._retry_request(e)
            raise

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.

        Returns:
            A list of model names.
        """
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.error.OpenAIError as e:
            self._retry_request(e)
            raise