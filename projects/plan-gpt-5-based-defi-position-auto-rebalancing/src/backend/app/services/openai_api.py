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
        """Logs the details of an API request."""
        log_message = f"Request: {method} - Prompt: '{prompt}' - Params: {params}"
        logging.info(log_message)

    def _log_response(self, response: Dict, method: str, prompt: str, params: Dict) -> None:
        """Logs the details of an API response."""
        log_message = f"Response: {method} - Prompt: '{prompt}' - Params: {params} - Status Code: {response.get('headers', {}).get('status_code', None)}"
        logging.info(log_message)

    def _get_cached_response(self, prompt: str, params: Dict) -> Optional[Dict]:
        """Retrieves a response from the cache."""
        timestamp = datetime.now().timestamp()
        key = (prompt, tuple(params.items()))
        if key in self.cache:
            cached_response = self.cache[key]
            if cached_response['timestamp'] > timestamp:
                logging.debug("Cache entry expired.  Fetching new response.")
                return None
            logging.debug("Response retrieved from cache.")
            return cached_response
        return None

    def _cache_response(self, prompt: str, params: Dict, response: Dict) -> None:
        """Caches a response for future use."""
        timestamp = datetime.now().timestamp()
        key = (prompt, tuple(params.items()))
        self.cache[key] = {'timestamp': timestamp, 'response': response}

    def generate_text(self, prompt: str, **params: Dict) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.
            **params: Additional parameters for the API call (e.g., max_tokens, temperature).

        Returns:
            The generated text.
        """
        self._log_request(prompt, "generate_text", params)

        cached_response = self._get_cached_response(prompt, params)
        if cached_response:
            logging.debug("Returning cached response.")
            return cached_response['response']

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **params
            )
            text = response['choices'][0]['message']['content']
            self._cache_response(prompt, params, response)
            self._log_response(response, "generate_text", prompt, params)
            return text
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit error: {e}")
            self.retry_count += 1
            if self.retry_count <= self.max_retries:
                logging.info(f"Retrying (attempt {self.retry_count}/{self.max_retries}) in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                return self.generate_text(prompt, **params)  # Recursive retry
            else:
                logging.error(f"Max retries reached for rate limit error.")
                raise
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def analyze_text(self, text: str, **params: Dict) -> str:
        """
        Analyzes text using the OpenAI API. (Placeholder - Implement your analysis logic here)

        Args:
            text: The text to analyze.
            **params: Additional parameters for the API call.

        Returns:
            The analysis result.
        """
        self._log_request(text, "analyze_text", params)
        # Placeholder implementation - Replace with your actual analysis logic
        return f"Analysis result for: {text} -  Params: {params}"