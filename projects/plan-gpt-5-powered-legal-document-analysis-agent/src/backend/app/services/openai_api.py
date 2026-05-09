import os
import time
import logging
import openai
import tenacity
from typing import Optional, Dict, Any
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
            max_tokens: The maximum number of tokens in the generated response (default: 100).
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

    def _rate_limit_check(self) -> bool:
        """
        Checks if the rate limit has been exceeded.
        """
        if self.rate_limit_window is None:
            self.rate_limit_window = datetime.now()
        if (datetime.now() - self.rate_limit_window).total_seconds() > 60:
            self.rate_limit_window = datetime.now()
            self.request_count = 0
        if self.request_count >= self.rate_limit:
            return True
        return False

    def _retry(fn, args, **kwargs):
        """
        Retry function for tenacity.
        """
        return fn(args, **kwargs)

    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            The generated text.

        Raises:
            Exception: If the API request fails after multiple retries.
        """
        if self._rate_limit_check():
            logging.warning("Rate limit exceeded.  Skipping request.")
            return None

        self.request_count += 1
        self.last_request_time = datetime.now()

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
        except openai.error.RateLimitError as e:
            logging.error(f"OpenAI RateLimitError: {e}")
            time.sleep(5)  # Wait before retrying
            return self.generate_text(prompt)
        except openai.error.APIError as e:
            logging.error(f"OpenAI APIError: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text using the OpenAI API (placeholder - needs implementation).

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the analysis results.
        """
        # Placeholder implementation - replace with actual analysis logic
        logging.warning("Text analysis not yet implemented.")
        return {"status": "analysis_not_implemented"}