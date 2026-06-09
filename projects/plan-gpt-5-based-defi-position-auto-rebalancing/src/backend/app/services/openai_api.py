import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Define enum for auth types
class AuthType(Enum):
    API_KEY = "api_key"

# Define a dataclass for API configuration
@dataclass
class OpenAIConfig:
    api_key: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: List[str] = ["\n"]

# OpenAI Service Class
class OpenAIAPI:
    def __init__(self, config: OpenAIConfig):
        self.config = config
        openai.api_key = config.api_key
        self.cache = {}  # Simple in-memory cache
        self.retry_config = tenacity.RetryContext(
            retry=tenacity.retry_http_500_exceptions(
                stop=tenacity.stop_after_attempts(3),
                wait=tenacity.wait_exponential(multiplier=1, min=1, max=10)
            )
        )

    def _cache_key(self, prompt: str) -> str:
        return f"{prompt}-{self.config.model}"

    def _get_from_cache(self, prompt: str) -> Optional[str]:
        key = self._cache_key(prompt)
        if key in self.cache:
            logging.debug(f"Returning cached response for prompt: {prompt}")
            return self.cache[key]
        return None

    def _cache_response(self, prompt: str, response: str) -> None:
        key = self._cache_key(prompt)
        self.cache[key] = response
        logging.debug(f"Caching response for prompt: {prompt}")

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generates text using the OpenAI API.
        """
        try:
            with tenacity.retry(self.retry_config) as retries:
                response = openai.ChatCompletion.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
                text = response.choices[0].message.content
                self._cache_response(prompt, text)
                return text
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def analyze_text(self, text: str, **kwargs) -> Dict:
        """
        Analyzes text using the OpenAI API.
        """
        try:
            with tenacity.retry(self.retry_config) as retries:
                response = openai.Completion.create(
                    model=self.config.model,
                    prompt=text,
                    **kwargs
                )
                return response.choices[0].text.strip()
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def clear_cache(self):
        self.cache = {}

if __name__ == '__main__':
    # Example Usage (replace with your actual configuration)
    config = OpenAIConfig(
        api_key="YOUR_OPENAI_API_KEY",
        model="gpt-3.5-turbo",
        max_tokens=100
    )
    api = OpenAIAPI(config)

    # Generate text
    try:
        generated_text = api.generate_text("Write a short story about a cat.")
        print(f"Generated Text: {generated_text}")
    except Exception as e:
        print(f"Error generating text: {e}")

    # Analyze text
    try:
        analysis_result = api.analyze_text("This is a sample text to analyze.")
        print(f"Analysis Result: {analysis_result}")
    except Exception as e:
        print(f"Error analyzing text: {e}")