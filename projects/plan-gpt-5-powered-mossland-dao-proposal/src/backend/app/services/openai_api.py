import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variable configuration
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

# Rate limiting configuration (example - adjust as needed)
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor

# Caching configuration (simple in-memory cache - replace with a persistent cache for production)
CACHE = {}

# Retry decorator with exponential backoff
@tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.OpenAIError),
    stop_after_all(MAX_RETRIES),
    wait=tenacity.wait_exponential(BACKOFF_FACTOR),
    backoff=tenacity.backoff.ExponentialBackoff,
    retry_kwargs={"timeout": 10}  # Timeout in seconds
)
def call_openai_api(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
    """
    Calls the OpenAI API with the given prompt and model.
    """
    if prompt in CACHE:
        logging.debug(f"Cache hit for prompt: {prompt}")
        return CACHE[prompt]

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        CACHE[prompt] = response.choices[0].message.content
        logging.info(f"Successfully called OpenAI API for prompt: {prompt}")
        return CACHE[prompt]
    except openai.OpenAIError as e:
        logging.error(f"OpenAI API error for prompt: {prompt} - {e}")
        raise  # Re-raise the exception for retry


@dataclass
class OpenAIResponse:
    """
    Represents the response from the OpenAI API.
    """
    text: str
    model: str
    timestamp: datetime


class OpenAIAPIService:
    """
    Service for integrating with the OpenAI API.
    """

    def __init__(self):
        self.max_retries = MAX_RETRIES
        self.rate_limit_delay = RATE_LIMIT_DELAY

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> OpenAIResponse:
        """
        Generates text using the OpenAI API.
        """
        return call_openai_api(prompt, model, temperature)

    def analyze_text(self, text: str, model: str = "text-davinci-003") -> str:
        """
        Analyzes text using the OpenAI API (placeholder - implement specific analysis tasks).
        """
        prompt = f"Analyze the following text: {text}"
        return call_openai_api(prompt, model)

    def list_models(self) -> List[str]:
        """
        Lists available OpenAI models.
        """
        try:
            response = openai.models.list()
            return [model['id'] for model in response.data]
        except openai.OpenAIError as e:
            logging.error(f"Error listing models: {e}")
            return []