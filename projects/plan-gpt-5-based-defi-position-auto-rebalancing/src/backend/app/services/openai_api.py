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
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# Rate limiting configuration (example - adjust as needed)
RATE_LIMIT_DELAY = 0.5  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # Exponential backoff factor

# Caching configuration (example - adjust as needed)
CACHE_EXPIRATION_TIME = datetime.timedelta(minutes=5)

# Retry configuration
retry_client = tenacity.RetryClient(retry=tenacity.allow_retry(stop=after_retry, multiplier=BACKOFF_FACTOR))


@dataclass
class OpenAIResponse:
    """Data class to represent the OpenAI API response."""
    choices: List[Dict]
    usage: Dict
    object: str


@tenacity.retry(retry=retry_client, backend=openai.RateLimitError,
                retry_kwargs={"wait": RATE_LIMIT_DELAY})
async def generate_text(prompt: str, model: str = "gpt-3.5-turbo") -> OpenAIResponse:
    """
    Generates text using the OpenAI API.

    Args:
        prompt: The text prompt to send to the API.
        model: The OpenAI model to use.

    Returns:
        An OpenAIResponse object containing the generated text.
    """
    try:
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
            n=1,
            stop=None,
        )
        return OpenAIResponse(choices=response.choices, usage=response.usage, object=response.object)
    except openai.error.RateLimitError as e:
        logging.error(f"Rate limit exceeded: {e}")
        raise
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        raise


async def analyze_text(text: str, model: str = "gpt-3.5-turbo") -> OpenAIResponse:
    """
    Analyzes text using the OpenAI API.

    Args:
        text: The text to analyze.
        model: The OpenAI model to use.

    Returns:
        An OpenAIResponse object containing the analysis results.
    """
    try:
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=[
                {"role": "user", "content": f"Analyze the following text: {text}"}
            ],
            temperature=0.5,
            max_tokens=200,
            n=1,
            stop=None,
        )
        return OpenAIResponse(choices=response.choices, usage=response.usage, object=response.object)
    except openai.error.RateLimitError as e:
        logging.error(f"Rate limit exceeded: {e}")
        raise
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        raise


class OpenAIAPIService:
    """
    Service class for integrating with the OpenAI API.
    """

    def __init__(self):
        pass

    async def generate(self, prompt: str, model: str = "gpt-3.5-turbo") -> OpenAIResponse:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The text prompt to send to the API.
            model: The OpenAI model to use.

        Returns:
            An OpenAIResponse object containing the generated text.
        """
        return await generate_text(prompt, model)

    async def analyze(self, text: str, model: str = "gpt-3.5-turbo") -> OpenAIResponse:
        """
        Analyzes text using the OpenAI API.

        Args:
            text: The text to analyze.
            model: The OpenAI model to use.

        Returns:
            An OpenAIResponse object containing the analysis results.
        """
        return await analyze_text(text, model)


if __name__ == '__main__':
    async def main():
        service = OpenAIAPIService()
        prompt = "Write a short story about a cat."
        try:
            response = await service.generate(prompt)
            print(f"Generated text: {response.choices[0]['content']}")
        except Exception as e:
            print(f"Error: {e}")

        text_to_analyze = "The quick brown fox jumps over the lazy dog."
        try:
            analysis_response = await service.analyze(text_to_analyze)
            print(f"Analysis: {analysis_response.choices[0]['content']}")
        except Exception as e:
            print(f"Error: {e}")

    import asyncio
    asyncio.run(main())