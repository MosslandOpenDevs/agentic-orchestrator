import os
import time
import logging
import openai
import tenacity
from typing import List, Dict, Optional
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
    tries=MAX_RETRIES,
    backoff=tenacity.wait_exponential(multiplier=BACKOFF_FACTOR),
    retry_on_exception=(openai.exceptions.APIError, openai.exceptions.RateLimitError),
    auto_reraise=True
)
def retry_openai_call(func, *args, **kwargs):
    return func(*args, **kwargs)

class OpenAIAPI:
    def __init__(self):
        self.model_cache = {}  # Cache for model names
        self.messages_cache = {} # Cache for conversation messages

    def get_model_name(self, model_id: str) -> str:
        if model_id in self.model_cache:
            return self.model_cache[model_id]
        else:
            self.model_cache[model_id] = model_id
            return model_id

    def get_completion(self, prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 100, temperature: float = 0.7, n: int = 1) -> str:
        """
        Generates text completion using the OpenAI API.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.get_model_name(model),
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                n=n
            )
            return response.choices[0].message.content
        except openai.exceptions.APIError as e:
            logging.error(f"OpenAI API Error: {e}")
            raise
        except openai.exceptions.RateLimitError as e:
            logging.warning(f"OpenAI Rate Limit Error: {e}")
            time.sleep(RATE_LIMIT_DELAY)
            return retry_openai_call(self.get_completion, prompt, model, max_tokens, temperature, n)
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            raise

    def analyze_sentiment(self, text: str, model: str = "gpt-3.5-turbo") -> Dict[str, float]:
        """
        Analyzes the sentiment of the given text using the OpenAI API.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.get_model_name(model),
                messages=[
                    {"role": "user", "content": f"Analyze the sentiment of the following text: {text}. Return a dictionary with 'positive' and 'negative' scores between 0 and 1."},
                ],
                max_tokens=150,
                temperature=0.2,
                n=1
            )
            result = response.choices[0].message.content
            try:
                return eval(result)  # Evaluate the string result
            except (SyntaxError, ValueError) as e:
                logging.error(f"Error evaluating sentiment result: {e}")
                raise
        except openai.exceptions.APIError as e:
            logging.error(f"OpenAI API Error: {e}")
            raise
        except openai.exceptions.RateLimitError as e:
            logging.warning(f"OpenAI Rate Limit Error: {e}")
            time.sleep(RATE_LIMIT_DELAY)
            return retry_openai_call(self.analyze_sentiment, text, model)
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            raise

    def generate_prompt(self, prompt_text: str) -> str:
        """
        Generates a prompt for the OpenAI API.
        """
        return prompt_text

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Retrieves the conversation history from the cache.
        """
        if conversation_id in self.messages_cache:
            return self.messages_cache[conversation_id]
        else:
            self.messages_cache[conversation_id] = []
            return self.messages_cache[conversation_id]