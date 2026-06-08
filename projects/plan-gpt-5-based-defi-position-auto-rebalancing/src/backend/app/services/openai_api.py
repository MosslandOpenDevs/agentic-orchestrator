import os
import time
import logging
import openai
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenAIAPI:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", max_tokens: int = 200, temperature: float = 0.7, rate_limit: int = 10):
        """
        Initializes the OpenAI API service.

        Args:
            api_key: The OpenAI API key.
            model: The OpenAI model to use.
            max_tokens: The maximum number of tokens in the generated text.
            temperature: The temperature for controlling randomness.
            rate_limit: The maximum number of requests allowed per period.
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.request_count = 0
        openai.api_key = self.api_key

        # Configure retry logic
        self.retry_config = {
            'retry': retry,
            'stop': stop_after_attempt(rate_limit),
            'wait': wait_exponential(multiplier=1, min=3, max=10)
        }

    def _generate_text(self, prompt: str) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            The generated text.

        Raises:
            Exception: If the API request fails.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False  # Disable streaming for simplicity
            )
            return response['choices'][0]['message']['content']
        except openai.error.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            raise

    def generate(self, prompt: str) -> str:
        """
        Generates text based on the given prompt.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            The generated text.
        """
        self.request_count += 1
        if self.request_count % self.rate_limit == 0:
            time.sleep(2)  # Simple rate limiting
        try:
            return self._generate_text(prompt)
        except Exception:
            logger.exception("Failed to generate text.")
            raise

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
                model="text-davinci-003",
                prompt=f"Analyze the sentiment of the following text: {text}\nSentiment:",
                max_tokens=50,
                temperature=0.2,
                n=1,
                stop=["\n"]
            )
            return {"sentiment": response.choices[0].text.strip()}
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            return {"sentiment": "Error"}
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            return {"sentiment": "Error"}

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            return []
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            return []