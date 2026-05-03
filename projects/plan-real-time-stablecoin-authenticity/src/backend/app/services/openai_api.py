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
            api_key: The OpenAI API key.
            model: The OpenAI model to use.
            max_tokens: The maximum number of tokens in the generated text.
            temperature: The temperature for controlling randomness.
            rate_limit: The maximum number of requests per window.
        """
        self.api_key = api_key
        openai.api_key = self.api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_request_time = datetime.now()
        self.cache = {}  # Simple in-memory cache

    def _check_rate_limit(self) -> bool:
        """
        Checks if the rate limit has been exceeded.
        """
        current_time = datetime.now()
        time_window = current_time - datetime.timedelta(seconds=60)  # 1-minute window
        
        requests_in_window = 0
        for key in self.cache:
            if self.cache[key]["timestamp"] >= time_window:
                requests_in_window += 1
        
        if requests_in_window >= self.rate_limit:
            return True
        else:
            return False

    def _cache_response(self, key: str, response: Dict) -> None:
        """
        Caches the response for a given key.
        """
        self.cache[key] = {"response": response, "timestamp": datetime.now()}

    def _get_cached_response(self, key: str) -> Optional[Dict]:
        """
        Retrieves the response from the cache.
        """
        current_time = datetime.now()
        for key_ in self.cache:
            if self.cache[key_]["timestamp"] >= current_time - datetime.timedelta(seconds=60):
                return self.cache[key_]
        return None

    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to use for generating text.

        Returns:
            The generated text.
        """
        key = f"{prompt}_{self.model}"
        cached_response = self._get_cached_response(key)

        if cached_response:
            logging.info(f"Returning cached response for key: {key}")
            return cached_response["response"]

        while True:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                text = response.choices[0].message.content
                self._cache_response(key, response.to_dict())
                self.request_count += 1
                self.last_request_time = datetime.now()
                logging.info(f"Generated text for prompt: {prompt}")
                return text
            except openai.error.RateLimitError as e:
                logging.error(f"Rate limit exceeded: {e}")
                time.sleep(2)  # Wait before retrying
            except openai.error.OpenAIError as e:
                logging.error(f"OpenAI API error: {e}")
                raise  # Re-raise the exception for handling elsewhere
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                raise

    @tenacity.retry(stop=stop_after_retries, retry=retry_delay_factor, backoff=tenacity.retry.ExponentialBackoff())
    def generate_text_with_retry(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API with retry logic.
        """
        return self.generate_text(prompt)

    def stop_after_retries(self, exception, attempts, key, raised, metadata):
        """
        Stop the retry operation after a certain number of attempts.
        """
        return attempts >= 5  # Example: Stop after 5 attempts

    def retry_delay_factor(self, attempts, key, raised, metadata):
        """
        Determine the delay between retry attempts.
        """
        return 2 ** attempts  # Example: Exponential backoff

if __name__ == '__main__':
    # Replace with your actual API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        exit(1)

    openai_service = OpenAIAPI(api_key=api_key, model="gpt-3.5-turbo", max_tokens=50)
    prompt = "Write a short poem about a cat."
    try:
        generated_text = openai_service.generate_text_with_retry(prompt)
        print(f"Generated text: {generated_text}")
    except Exception as e:
        print(f"Error: {e}")