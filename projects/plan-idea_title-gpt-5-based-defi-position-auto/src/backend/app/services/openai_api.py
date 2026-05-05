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
            max_tokens: The maximum number of tokens in the generated text (default: 100).
            temperature: Controls randomness (default: 0.7).
            rate_limit: Maximum number of requests per window (default: 10).
        """
        openai.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_request_time = None
        self.rate_limit_window = None
        self.rate_limit_start_time = None

    def _log_request(self, prompt: str) -> None:
        """Logs the request details."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Request - Timestamp: {timestamp}, Prompt: {prompt}, Model: {self.model}, Max Tokens: {self.max_tokens}, Temperature: {self.temperature}")

    def _check_rate_limit(self) -> bool:
        """Checks if the rate limit has been exceeded."""
        if self.rate_limit_window is None:
            self.rate_limit_window = time.time()
            self.rate_limit_start_time = time.time()
            return False

        elapsed_time = time.time() - self.rate_limit_start_time
        if elapsed_time > self.rate_limit_window:
            self.rate_limit_window = time.time()
            self.rate_limit_start_time = time.time()
            self.request_count = 0
            return False

        return self.request_count >= self.rate_limit

    def _reset_rate_limit(self) -> None:
        """Resets the rate limit counter."""
        self.request_count = 0
        self.last_request_time = None

    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            The generated text.

        Raises:
            Exception: If the API request fails.
        """
        self._log_request(prompt)
        self._check_rate_limit()

        if self._check_rate_limit():
            logging.warning("Rate limit exceeded.  Waiting...")
            time.sleep(2)  # Wait before retrying
            self._check_rate_limit()

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            generated_text = response.choices[0].message.content
            self.request_count += 1
            self._reset_rate_limit()
            return generated_text
        except openai.error.RateLimitError as e:
            logging.error(f"OpenAI RateLimitError: {e}")
            raise
        except openai.error.APIError as e:
            logging.error(f"OpenAI APIError: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def analyze_text(self, text: str) -> Dict:
        """
        Analyzes the given text using OpenAI's API.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the analysis results.
        """
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Analyze the following text: {text}",
                max_tokens=200,
                n=1,
                stop=None,
                temperature=0.5,
            )
            return response.choices[0].text.strip()
        except openai.error.RateLimitError as e:
            logging.error(f"OpenAI RateLimitError: {e}")
            raise
        except openai.error.APIError as e:
            logging.error(f"OpenAI APIError: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise