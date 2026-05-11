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
            api_key: The OpenAI API key.
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
        log_message = f"Response: {method} - Prompt: '{prompt}' - Params: {params} - Status Code: {response.get('headers', {}).get('status_code', 'N/A')}"
        logging.info(log_message)

    def _handle_exception(self, exception: Exception) -> Optional[Dict]:
        """Handles exceptions and implements retry logic."""
        self.retry_count += 1
        logging.error(f"Exception: {exception}")
        if self.retry_count <= self.max_retries:
            logging.info(f"Retrying in {self.retry_delay} seconds...")
            time.sleep(self.retry_delay)
            return None  # Retry
        else:
            logging.error(f"Max retries reached for {self.model}.  Giving up.")
            return {"error": f"Max retries reached for {self.model}", "details": str(exception)}

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 100) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to use for text generation.
            temperature: The temperature for controlling randomness (default: 0.7).
            max_tokens: The maximum number of tokens to generate (default: 100).

        Returns:
            The generated text.
        """
        cache_key = f"{prompt}-{temperature}-{max_tokens}"
        if cache_key in self.cache:
            logging.debug(f"Returning cached response for prompt: {cache_key}")
            return self.cache[cache_key]

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                n=1,
                stop=None,
            )
            generated_text = response['choices'][0]['message']['content']
            self.cache[cache_key] = generated_text
            logging.debug(f"Generated text for prompt: {cache_key}")
            return generated_text
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit error: {e}")
            return self._handle_exception(e)
        except openai.error.APIError as e:
            logging.error(f"API error: {e}")
            return self._handle_exception(e)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return self._handle_exception(e)

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyzes the sentiment of the given text.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the sentiment analysis results.
        """
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Analyze the sentiment of the following text: '{text}'.  Output only the sentiment (positive, negative, or neutral).",
                max_tokens=10,
                n=1,
                stop=None,
            )
            sentiment = response['choices'][0]['text'].strip()
            return {"sentiment": sentiment}
        except openai.error.RateLimitError as e:
            logging.error(f"Rate limit error: {e}")
            return {"error": f"Rate limit error: {e}"}
        except openai.error.APIError as e:
            logging.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {e}"}