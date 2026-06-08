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
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", max_tokens: int = 100, temperature: float = 0.7, rate_limit_delay: int = 2):
        """
        Initializes the OpenAI API service.

        Args:
            api_key: Your OpenAI API key.
            model: The OpenAI model to use (default: "gpt-3.5-turbo").
            max_tokens: The maximum number of tokens in the generated response (default: 100).
            temperature: Controls randomness (default: 0.7).
            rate_limit_delay: Delay in seconds to apply when rate limit is hit (default: 2).
        """
        openai.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit_delay = rate_limit_delay
        self.cache = {}  # Simple in-memory cache
        self.retry_strategy = tenacity.retry_wait(retry_exponential=True, multiplier=1, min=1, max=5)

    def _cache_key(self, prompt: str) -> str:
        """Generates a cache key based on the prompt."""
        return f"{prompt}-{self.model}"

    def _get_from_cache(self, prompt: str) -> Optional[str]:
        """Retrieves a response from the cache."""
        key = self._cache_key(prompt)
        if key in self.cache:
            now = datetime.now()
            if now - self.cache[key]['timestamp'] < datetime.timedelta(minutes=60): # Cache for 1 hour
                logging.debug(f"Cache hit for prompt: {prompt}")
                return self.cache[key]['response']
        return None

    def _cache_response(self, prompt: str, response: str):
        """Stores a response in the cache."""
        key = self._cache_key(prompt)
        self.cache[key] = {'response': response, 'timestamp': datetime.now()}

    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            The generated text.
        """
        if self._get_from_cache(prompt):
            logging.debug(f"Returning cached response for prompt: {prompt}")
            return self._get_from_cache(prompt)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False  # Disable streaming for simplicity
            )
            text = response['choices'][0]['message']['content']
            self._cache_response(prompt, text)
            logging.info(f"Generated text for prompt: {prompt}")
            return text
        except openai.error.RateLimitError as e:
            logging.warning(f"Rate limit exceeded: {e}. Retrying in {self.rate_limit_delay} seconds...")
            time.sleep(self.rate_limit_delay)
            return self.generate_text(prompt)  # Retry
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise  # Re-raise the exception for handling at a higher level
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

    def analyze_text(self, text: str) -> Dict:
        """
        Analyzes the given text using the OpenAI API.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the analysis results.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": f"Analyze the following text: {text}"}
                ],
                max_tokens=200,
                temperature=0.5
            )
            analysis = response['choices'][0]['message']['content']
            return {"analysis": analysis}
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error during analysis: {e}")
            return {"error": str(e)}
        except Exception as e:
            logging.exception(f"An unexpected error occurred during analysis: {e}")
            return {"error": str(e)}