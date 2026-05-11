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
        openai.api_key = api_key
        self.model = model
        self.cache = {}  # Simple in-memory cache
        self.retry_count = 3  # Number of retries for transient errors
        self.retry_delay = 5  # Delay between retries in seconds
        self.max_retries = 5 # Maximum retries
        self.rate_limit_delay = 1 # Delay in seconds to respect rate limits
    
    def _cache_key(self, prompt: str) -> str:
        """Generates a cache key based on the prompt."""
        return f"{prompt}_{datetime.now().timestamp()}"

    def _get_from_cache(self, prompt: str) -> Optional[str]:
        """Retrieves data from the cache."""
        key = self._cache_key(prompt)
        if key in self.cache:
            logging.debug(f"Cache hit for prompt: {prompt}")
            return self.cache[key]
        return None

    def _cache_result(self, prompt: str, result: str) -> None:
        """Stores the result in the cache."""
        key = self._cache_key(prompt)
        self.cache[key] = result
        logging.debug(f"Cached result for prompt: {prompt}")

    def generate_text(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to use for text generation.
            max_tokens: The maximum number of tokens to generate.
            temperature: The temperature to use for text generation (0.0 - 1.0).

        Returns:
            The generated text.
        """
        prompt = prompt.strip()
        if prompt in self._get_from_cache(prompt):
            return self._get_from_cache(prompt)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            result = response.choices[0].message.content
            self._cache_result(prompt, result)
            return result
        except openai.error.RateLimitError as e:
            logging.warning(f"Rate limit exceeded: {e}. Retrying in {self.rate_limit_delay} seconds...")
            time.sleep(self.rate_limit_delay)
            return self.generate_text(prompt, max_tokens, temperature) # Retry
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise  # Re-raise the exception for handling at a higher level
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise # Re-raise for handling

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
                prompt=f"Analyze the sentiment of the following text: '{text}'. Return a JSON object with 'positive' and 'negative' scores between 0 and 1.",
                max_tokens=50,
                n=1,
                stop=None,
                temperature=0.3,
            )
            result = response.choices[0].text.strip()
            try:
                import json
                sentiment = json.loads(result)
                return sentiment
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}. Response: {result}")
                raise
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise
    
    def list_models(self) -> List[str]:
        """Lists available OpenAI models."""
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise