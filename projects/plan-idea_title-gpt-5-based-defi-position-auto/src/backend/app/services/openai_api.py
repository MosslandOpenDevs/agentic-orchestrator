import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class OpenAIAPI:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", rate_limit: int = 10, retry_attempts: int = 3, retry_delay: float = 1):
        """
        Initializes the OpenAI API service.

        Args:
            api_key: OpenAI API key.
            model: The OpenAI model to use (default: "gpt-3.5-turbo").
            rate_limit: Maximum number of requests per period (default: 10).
            retry_attempts: Number of retry attempts (default: 3).
            retry_delay: Delay between retry attempts in seconds (default: 1).
        """
        self.api_key = api_key
        openai.api_key = self.api_key
        self.model = model
        self.rate_limit = rate_limit
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.request_count = 0
        self.last_request_time = datetime.now()

    def _check_rate_limit(self) -> bool:
        """
        Checks if the rate limit has been exceeded.
        """
        now = datetime.now()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request.total_seconds() < 60:  # Check every 60 seconds
            return True
        self.last_request_time = now
        return False

    @tenacity.retry(stop=tenacity.stop_after_attempt(self.retry_attempts),
                    wait=tenacity.wait_exponential(multiplier=1, min=self.retry_delay, max=self.retry_delay * 2),
                    retry=self._retry_openai_request)
    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to use for text generation.
            max_tokens: The maximum number of tokens to generate (default: 100).

        Returns:
            The generated text.

        Raises:
            Exception: If the API request fails after multiple retries.
        """
        if self._check_rate_limit():
            logging.warning("Rate limit exceeded. Pausing.")
            time.sleep(60)  # Pause for 60 seconds

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def _retry_openai_request(self, exception):
        """
        Retry function for OpenAI API requests.
        """
        logging.error(f"OpenAI API request failed. Retrying... {exception}")
        time.sleep(self.retry_delay)

    def analyze_text(self, text: str) -> Dict:
        """
        Analyzes text using the OpenAI API.  Placeholder for future implementation.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the analysis results.
        """
        # Placeholder - Replace with actual analysis logic
        logging.warning("Text analysis not yet implemented. Returning empty dictionary.")
        return {}

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            response = openai.models.list()
            return [model['id'] for model in response['data']]
        except openai.error.OpenAIError as e:
            logging.error(f"Error listing models: {e}")
            return []