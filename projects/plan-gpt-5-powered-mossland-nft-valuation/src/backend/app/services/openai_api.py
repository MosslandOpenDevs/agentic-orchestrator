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
            model: The OpenAI model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: The temperature for controlling randomness.
            rate_limit: The maximum number of requests per window (seconds).
        """
        self.api_key = api_key
        openai.api_key = self.api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_request_time = 0
        self.cache = {}  # Simple in-memory cache

    def _is_rate_limited(self) -> bool:
        """
        Checks if the rate limit has been exceeded.
        """
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit:
            return True
        self.last_request_time = current_time
        return False

    def _retry(self, error):
        """
        Retry logic for transient errors.
        """
        if isinstance(error, openai.error.RateLimitError):
            logging.warning("Rate limit exceeded. Retrying...")
            time.sleep(2)  # Exponential backoff could be added
            return None
        elif isinstance(error, openai.error.OpenAIError):
            logging.error(f"OpenAI API error: {error}")
            return None
        else:
            logging.error(f"Unexpected error: {error}")
            return None

    @tenacity.retry(stop=stop_after_retries, retry=retry, exceptions=(openai.error.RateLimitError, openai.error.OpenAIError))
    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to generate text from.

        Returns:
            The generated text.
        """
        if prompt in self.cache:
            logging.debug(f"Returning cached response for prompt: {prompt}")
            return self.cache[prompt]

        if self._is_rate_limited():
            logging.warning("Rate limit exceeded. Skipping request.")
            return None

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            generated_text = response['choices'][0]['message']['content']
            self.cache[prompt] = generated_text
            logging.info(f"Generated text for prompt: {prompt}")
            return generated_text
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            return None

    def analyze_text(self, text: str) -> Dict:
        """
        Placeholder for text analysis functionality.
        """
        # Replace with actual analysis logic
        logging.warning("Text analysis functionality not implemented.")
        return {}

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            models = openai.models.list()
            return [model['id'] for model in models['data']]
        except openai.error.OpenAIError as e:
            logging.error(f"Error listing models: {e}")
            return []


if __name__ == '__main__':
    # Example Usage (replace with your actual API key)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
    else:
        openai_service = OpenAIAPI(api_key=api_key, model="gpt-3.5-turbo", max_tokens=50)
        prompt = "Write a short story about a cat."
        generated_story = openai_service.generate_text(prompt)
        if generated_story:
            print(f"Generated Story: {generated_story}")
        else:
            print("Failed to generate story.")