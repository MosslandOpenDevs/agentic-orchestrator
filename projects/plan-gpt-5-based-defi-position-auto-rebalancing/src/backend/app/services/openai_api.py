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
        self.retry_delay = 2  # Seconds
        self.max_retries = 3
        self.rate_limit_delay = 1  # Seconds (for rate limiting)

    def _cache_key(self, prompt: str) -> str:
        """Generates a cache key based on the prompt."""
        return f"{prompt}_{datetime.now().timestamp()}"

    def _get_from_cache(self, prompt: str) -> Optional[str]:
        """Retrieves a response from the cache."""
        key = self._cache_key(prompt)
        if key in self.cache:
            logging.debug(f"Cache hit for prompt: {prompt}")
            return self.cache[key]
        return None

    def _cache_response(self, prompt: str, response: str) -> None:
        """Stores a response in the cache."""
        key = self._cache_key(prompt)
        self.cache[key] = response
        logging.debug(f"Cached response for prompt: {prompt}")

    @tenacity.retry(stop=tenacity.stop_after_attempt(self.max_retries),
                    wait=tenacity.wait_exponential(multiplier=self.retry_delay),
                    retry=lambda error: self._handle_retry_error(error))
    def generate_text(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to use for text generation.
            max_tokens: The maximum number of tokens to generate.
            temperature: The temperature to use for text generation.

        Returns:
            The generated text.
        """
        logging.info(f"Generating text for prompt: {prompt}")
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        text = response['choices'][0]['message']['content']
        self._cache_response(prompt, text)
        return text

    def _handle_retry_error(self, error):
        """Handles retry errors."""
        if isinstance(error, openai.error.RateLimitError):
            logging.warning("Rate limit exceeded. Retrying...")
            time.sleep(self.rate_limit_delay)
            return None
        elif isinstance(error, openai.error.APIError):
            logging.error(f"OpenAI API error: {error}")
            return None
        else:
            logging.error(f"Unexpected error: {error}")
            return None

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the sentiment analysis results.
        """
        logging.info(f"Analyzing sentiment for text: {text}")
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Analyze the sentiment of the following text: {text}\nSentiment:",
                max_tokens=50,
                n=1,
                stop=None,
                temperature=0.5,
            )
            sentiment = response['choices'][0]['text'].strip()
            self._cache_response(text, sentiment)
            return {"sentiment": sentiment}
        except openai.error.APIError as e:
            logging.error(f"Sentiment analysis API error: {e}")
            return {"sentiment": "Error"}