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
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", rate_limit: int = 10, retry_attempts: int = 3, retry_delay: float = 1):
        """
        Initializes the OpenAI API service.

        Args:
            api_key: The OpenAI API key.
            model: The OpenAI model to use (default: "gpt-3.5-turbo").
            rate_limit: The maximum number of requests allowed per period (default: 10).
            retry_attempts: The number of times to retry a failed request (default: 3).
            retry_delay: The delay in seconds between retry attempts (default: 1).
        """
        openai.api_key = api_key
        self.model = model
        self.rate_limit = rate_limit
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.request_count = 0
        self.last_request_time = datetime.now()

    def _is_rate_limited(self) -> bool:
        """
        Checks if the rate limit has been exceeded.
        """
        current_time = datetime.now()
        time_since_last_request = (current_time - self.last_request_time).total_seconds()
        if time_since_last_request < self.retry_delay:
            return False
        
        self.last_request_time = current_time
        self.request_count = 0  # Reset count after rate limit
        return True

    @tenacity.retry(stop=stop_after_attempts, retry=retry_on_exception, delay=retry_delay)
    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to use for text generation.
            max_tokens: The maximum number of tokens to generate (default: 100).

        Returns:
            The generated text.

        Raises:
            Exception: If the API request fails after multiple retries.
        """
        if self._is_rate_limited():
            raise Exception("Rate limit exceeded")

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except openai.error.RateLimitError as e:
            raise Exception(f"OpenAI Rate Limit Error: {e}")
        except openai.error.APIError as e:
            raise Exception(f"OpenAI API Error: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

    def analyze_text(self, text: str) -> Dict:
        """
        Analyzes text using the OpenAI API.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the analysis results.
        """
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=text,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.5,
            )
            return response.choices[0].text.strip()
        except openai.error.RateLimitError as e:
            raise Exception(f"OpenAI Rate Limit Error: {e}")
        except openai.error.APIError as e:
            raise Exception(f"OpenAI API Error: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

    def get_all_completions(self, prompt: str, max_tokens: int = 100, n: int = 5) -> List[str]:
        """
        Generates multiple completions using the OpenAI API.

        Args:
            prompt: The prompt to use for text generation.
            max_tokens: The maximum number of tokens to generate (default: 100).
            n: The number of completions to generate (default: 5).

        Returns:
            A list of generated texts.
        """
        completions = []
        for _ in range(n):
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=max_tokens,
                    n=1,
                    stop=None,
                    temperature=0.7,
                )
                completions.append(response.choices[0].text.strip())
            except openai.error.RateLimitError as e:
                raise Exception(f"OpenAI Rate Limit Error: {e}")
            except openai.error.APIError as e:
                raise Exception(f"OpenAI API Error: {e}")
            except Exception as e:
                raise Exception(f"An unexpected error occurred: {e}")
        return completions


# Retry decorators
stop_after_attempts = tenacity.stop_after_attempts(self.retry_attempts)
retry_on_exception = tenacity.retry_wait(retry_delay)