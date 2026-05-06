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
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initializes the OpenAI API service.

        Args:
            api_key: Your OpenAI API key.
            model: The OpenAI model to use (default: "gpt-3.5-turbo").
        """
        self.api_key = api_key
        openai.api_key = self.api_key
        self.model = model
        self.cache = {}  # Simple in-memory cache
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _log_request(self, prompt: str, method: str, params: Dict) -> None:
        """Logs the request details."""
        log_message = f"Request: {method} - Prompt: '{prompt}' - Params: {params}"
        logging.info(log_message)

    def _log_response(self, response: Dict, method: str, prompt: str, params: Dict) -> None:
        """Logs the response details."""
        log_message = f"Response: {method} - Prompt: '{prompt}' - Params: {params} - Status Code: {response.get('headers', {}).get('status_code', None)}"
        logging.info(log_message)

    def _get_from_cache(self, prompt: str) -> Optional[str]:
        """Retrieves data from the cache."""
        if prompt in self.cache:
            now = datetime.now()
            cached_expiry = 60  # Cache expiry in seconds
            if now - self.cache[prompt]['timestamp'].timestamp() < cached_expiry:
                logging.debug(f"Cache hit for prompt: {prompt}")
                return self.cache[prompt]['data']
            else:
                logging.debug(f"Cache expired for prompt: {prompt}, removing...")
                del self.cache[prompt]
        return None

    def _cache_response(self, prompt: str, data: str) -> None:
        """Caches the response for a specified duration."""
        self.cache[prompt] = {'data': data, 'timestamp': datetime.now()}

    def generate_text(self, prompt: str, **kwargs: Dict) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.
            **kwargs: Additional parameters to pass to the OpenAI API (e.g., max_tokens, temperature).

        Returns:
            The generated text.
        """
        if prompt in self.cache:
            logging.debug(f"Returning cached response for prompt: {prompt}")
            return self.cache[prompt]['data']

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            text = response['choices'][0]['message']['content']
            self._cache_response(prompt, text)
            return text
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit error: {e}")
            self._handle_rate_limit_error()
            raise
        except openai.error.APIError as e:
            logging.error(f"OpenAI API error: {e}")
            self._handle_api_error(e)
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def _handle_rate_limit_error(self):
        """Handles rate limit errors with retry logic."""
        if self.retry_count < self.max_retries:
            logging.warning(f"Rate limit exceeded. Retrying in {self.retry_delay} seconds...")
            time.sleep(self.retry_delay)
            self.retry_count += 1
        else:
            logging.error("Max retries reached for rate limit error.")
            raise

    def _handle_api_error(self, e):
        """Handles other OpenAI API errors with retry logic."""
        if self.retry_count < self.max_retries:
            logging.warning(f"OpenAI API error. Retrying in {self.retry_delay} seconds...")
            time.sleep(self.retry_delay)
            self.retry_count += 1
        else:
            logging.error(f"Max retries reached for API error: {e}")
            raise

    def analyze_text(self, text: str, **kwargs: Dict) -> Dict:
        """
        Analyzes text using the OpenAI API.

        Args:
            text: The text to analyze.
            **kwargs: Additional parameters to pass to the OpenAI API (e.g., model).

        Returns:
            The analysis results.
        """
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",  # Or another suitable engine
                prompt=text,
                **kwargs
            )
            return response
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit error: {e}")
            self._handle_rate_limit_error()
            raise
        except openai.error.APIError as e:
            logging.error(f"OpenAI API error: {e}")
            self._handle_api_error(e)
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise