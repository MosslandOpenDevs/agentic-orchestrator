import axios, { AxiosError, AxiosResponse } from 'axios';
import { logger } from './logger'; // Assuming you have a logger service
import { OpenAIConfig } from './openai-config'; // Assuming you have a config class

export class OpenAIAPI {
  private apiKey: string;
  private baseApiUrl: string;
  private config: OpenAIConfig;
  private rateLimitCounter: { [key: string]: number } = {};
  private retryCount: { [key: string]: number } = {};

  constructor(config: OpenAIConfig) {
    this.apiKey = process.env.OPENAI_API_KEY || 'YOUR_DEFAULT_API_KEY'; // Use env or default
    this.baseApiUrl = 'https://api.openai.com/v1/';
    this.config = config;
  }

  private async makeRequest(endpoint: string, data: any): Promise<AxiosResponse> {
    try {
      logger.info(`Making request to: ${this.baseApiUrl}${endpoint}`, { data });
      const response = await axios.post(this.baseApiUrl + endpoint, data, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
      });
      logger.info(`Request successful: ${endpoint}`, { response });
      return response;
    } catch (error: any) {
      logger.error(`Request failed: ${endpoint}`, { error });
      throw error;
    }
  }

  async generateCompletion(prompt: string, model: string = this.config.defaultModel): Promise<string> {
    const endpoint = `completions?model=${model}&prompt=${prompt}`;
    try {
      await this.rateLimitCheck(endpoint);
      const response = await this.makeRequest(endpoint, {
        'temperature': this.config.temperature,
        'max_tokens': this.config.maxTokens,
      });
      return response.data.choices[0].text;
    } catch (error: any) {
      if (error.response) {
        throw new Error(`OpenAI Completion Error: ${error.response.status} - ${error.response.data.error.message}`);
      }
      throw error;
    }
  }

  async analyzeSentiment(text: string, model: string = this.config.defaultModel): Promise<string> {
    const endpoint = `completions?model=${model}&prompt=Analyze the sentiment of the following text: ${text}`;
    try {
      await this.rateLimitCheck(endpoint);
      const response = await this.makeRequest(endpoint, {
        'temperature': this.config.temperature,
        'max_tokens': this.config.maxTokens,
      });
      return response.data.choices[0].text;
    } catch (error: any) {
      if (error.response) {
        throw new Error(`OpenAI Sentiment Analysis Error: ${error.response.status} - ${error.response.data.error.message}`);
      }
      throw error;
    }
  }

  private async rateLimitCheck(endpoint: string): Promise<void> {
    // Placeholder for rate limiting logic.  Implement actual rate limiting
    // based on OpenAI's API limits.  This is a simplified example.
    // Consider using a library like 'ratelimit' for more robust rate limiting.
    if (endpoint.includes('completions') && this.rateLimitCounter[endpoint] >= 5) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }
  }

  private async handleTransientError(error: any): Promise<void> {
    if (error.response && error.response.status === 429) {
      // Handle 429 Too Many Requests (Rate Limit Exceeded)
      logger.warn('Transient error - Rate limit exceeded. Retrying...', { error });
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
    } else {
      // Handle other transient errors
      logger.error('Transient error', { error });
    }
  }

  private async retryRequest(endpoint: string, data: any): Promise<AxiosResponse> {
    let retries = 0;
    const maxRetries = 3;

    while (retries <= maxRetries) {
      try {
        return await this.makeRequest(endpoint, data);
      } catch (error: any) {
        await this.handleTransientError(error);
        retries++;
        if (retries > maxRetries) {
          throw error;
        }
      }
    }
    throw new Error(`Failed to make request after ${maxRetries} retries`);
  }
}