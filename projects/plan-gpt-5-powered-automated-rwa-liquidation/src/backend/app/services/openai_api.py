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
            model: The OpenAI model to use (default: "gpt-3.5-turbo").
            max_tokens: The maximum number of tokens to generate (default: 100).
            temperature: The temperature for controlling randomness (default: 0.7).
            rate_limit: The maximum number of requests per window (default: 10).
        """
        openai.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_request_time = None
        self.rate_limit_window = None

    def _log_request(self, prompt: str) -> None:
        """Logs the request details."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Request - Timestamp: {timestamp}, Prompt: {prompt}, Model: {self.model}, Max Tokens: {self.max_tokens}, Temperature: {self.temperature}")

    def _check_rate_limit(self) -> bool:
        """Checks if the rate limit has been exceeded."""
        if self.last_request_time is None:
            return False

        current_time = time.time()
        time_window = current_time - (self.rate_limit_window / 60)  # Window in minutes
        
        if self.request_count >= self.rate_limit:
            return True
        
        return False

    @tenacity.retry(stop=stop_after_retries, retry=retry_on_exception, timeout=10)
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
        self._log_request(prompt)
        if self._check_rate_limit():
            raise Exception("Rate limit exceeded")

        self.request_count += 1
        self.last_request_time = time.time()

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

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Analyzes text using the OpenAI API.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the analysis results.
        """
        self._log_request(text)
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": f"Analyze the following text: {text}"}
                ],
                max_tokens=200,
                temperature=0.5
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            return {"error": str(e)}

def stop_after_retries(exception):
    return exception.response.status_code == 429

def retry_on_exception(exception):
    if stop_after_retries(exception):
        return False
    return True