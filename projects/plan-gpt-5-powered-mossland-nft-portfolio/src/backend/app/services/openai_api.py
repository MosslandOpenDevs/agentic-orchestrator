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
        self.retry_count = 3  # Max retry attempts
        self.retry_delay = 5  # Seconds between retries
        self.max_retries = 5 # Max total retries

    def _cache_key(self, prompt: str, **kwargs) -> str:
        """Generates a cache key based on the prompt and arguments."""
        return f"{prompt}-{kwargs}"

    def _get_from_cache(self, prompt: str, **kwargs) -> Optional[str]:
        """Retrieves data from the cache."""
        key = self._cache_key(prompt, **kwargs)
        if key in self.cache:
            logging.debug(f"Cache hit for prompt: {key}")
            return self.cache[key]
        return None

    def _cache_result(self, prompt: str, response: str, **kwargs) -> None:
        """Stores the result in the cache."""
        key = self._cache_key(prompt, **kwargs)
        self.cache[key] = response
        logging.debug(f"Cached result for prompt: {key}")

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.
            **kwargs: Additional parameters to pass to the OpenAI API (e.g., max_tokens, temperature).

        Returns:
            The generated text.

        Raises:
            Exception: If the API request fails after multiple retries.
        """
        retries = tenacity.retry(
            stop=tenacity.stop_after_attempts(self.retry_count),
            reraise=tenacity.retry_if_exception_type(Exception),
            retry=tenacity.retry_wait(tenacity.exponential_backoff(base=self.retry_delay)),
            before_attempt=lambda attempt: logging.info(f"Attempt {attempt+1} of {self.retry_count} for prompt: {prompt}"),
            after_attempt=lambda attempt: logging.debug(f"Attempt {attempt+1} of {self.retry_count} for prompt: {prompt} completed."),
            update_delay=self.retry_delay
        )
        
        result = retries.execute(lambda: openai.ChatCompletion.create,
                                 model=self.model,
                                 prompt=prompt,
                                 **kwargs)
        
        if result:
            response = result.choices[0].message.content
            self._cache_result(prompt, response, **kwargs)
            return response
        else:
            raise Exception("Failed to generate text from OpenAI API.")

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
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
                prompt=f"Analyze the sentiment of the following text: '{text}'.  Output as a JSON object with 'sentiment' (positive, negative, or neutral) and 'score' (a value between -1 and 1).",
                max_tokens=50,
                n=1,
                stop=None,
                temperature=0.5,
            )
            
            json_response = response.choices[0].text.strip()
            
            import json
            result = json.loads(json_response)
            
            return result
        except Exception as e:
            logging.error(f"Error during sentiment analysis: {e}")
            raise