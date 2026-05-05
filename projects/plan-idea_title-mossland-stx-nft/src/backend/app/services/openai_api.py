import os
import time
import logging
import openai
import tenacity
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OpenAIAPI:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", rate_limit: int = 10, retry_attempts: int = 3, retry_delay: float = 1):
        """
        Initializes the OpenAI API service.

        Args:
            api_key: The OpenAI API key.
            model: The OpenAI model to use (default: "gpt-3.5-turbo").
            rate_limit: The maximum number of requests per window (default: 10).
            retry_attempts: The number of retry attempts (default: 3).
            retry_delay: The delay between retry attempts in seconds (default: 1).
        """
        self.api_key = api_key
        openai.api_key = self.api_key
        self.model = model
        self.rate_limit = rate_limit
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.request_count = 0
        self.last_reset_time = time.time()

    def _check_rate_limit(self) -> bool:
        """
        Checks if the rate limit has been exceeded.
        """
        current_time = time.time()
        if current_time - self.last_reset_time >= 60:
            self.request_count = 0
            self.last_reset_time = current_time
        
        return self.request_count >= self.rate_limit

    @tenacity.retry(stop=tenacity.stop_after_attempt(self.retry_attempts),
                    wait=tenacity.wait_exponential(multiplier=1, min=self.retry_delay, max=self.retry_delay * 2),
                    retry=self._handle_retry)
    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The prompt to use.
            max_tokens: The maximum number of tokens to generate.

        Returns:
            The generated text.

        Raises:
            Exception: If the API call fails after multiple retry attempts.
        """
        if self._check_rate_limit():
            raise Exception("Rate limit exceeded.")

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=0.7,
            )
            self.request_count += 1
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text using the OpenAI API.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary containing the analysis results.
        """
        try:
            response = openai.Completion.create(
                engine=self.model,
                prompt=text,
                max_tokens=100,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].text.strip()
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

    def _handle_retry(self, exception, attempts):
        """
        Handles a retry attempt.
        """
        logging.warning(f"Attempt {attempts} failed. Retrying...")
        time.sleep(self.retry_delay)


if __name__ == '__main__':
    # Example Usage (replace with your actual API key)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
    else:
        try:
            openai_service = OpenAIAPI(api_key=api_key)
            prompt = "Write a short story about a cat."
            generated_text = openai_service.generate_text(prompt)
            print(f"Generated text: {generated_text}")

            text_to_analyze = "This is a sample text for analysis."
            analysis_result = openai_service.analyze_text(text_to_analyze)
            print(f"Analysis result: {analysis_result}")

        except Exception as e:
            print(f"An error occurred: {e}")