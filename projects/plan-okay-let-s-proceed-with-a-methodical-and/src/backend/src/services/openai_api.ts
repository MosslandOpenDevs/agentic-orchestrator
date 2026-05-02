import axios, { AxiosError, AxiosResponse } from 'axios';
import { logger } from './logger'; // Assuming a logger is defined elsewhere
import { OpenAIConfig } from './openai-config';

export class OpenAIAPIService {
  private apiKey: string;
  private config: OpenAIConfig;
  private rateLimitCounter: { [key: string]: number } = {};
  private cache: { [key: string]: string } = {};
  private readonly baseApiUrl = 'https://api.openai.com/v1/';

  constructor(config: OpenAIConfig) {
    this.apiKey = process.env.OPENAI_API_KEY || 'YOUR_API_KEY'; // Fallback for testing
    this.config = config;
    logger.info('OpenAI API Service initialized');
  }

  private async makeRequest(endpoint: string, data: any): Promise<AxiosResponse> {
    try {
      logger.debug(`Making request to: ${endpoint} with data: ${JSON.stringify(data)}`);
      const response = await axios.post(endpoint, data, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
      });
      logger.debug(`Request to ${endpoint} successful. Status: ${response.status}`);
      return response;
    } catch (error: any) {
      logger.error(`Error making request to ${endpoint}: ${error.message}`);
      throw error;
    }
  }

  async generateText(prompt: string, model: string = this.config.defaultModel): Promise<string> {
    const cacheKey = `generateText-${prompt}-${model}`;
    if (this.cache[cacheKey]) {
      logger.debug(`Returning cached response for prompt: ${prompt}`);
      return this.cache[cacheKey];
    }

    try {
      const data = {
        model: model,
        prompt: prompt,
        max_tokens: this.config.maxTokens,
        temperature: this.config.temperature,
      };

      const response = await this.makeRequest('/completions', data);
      const text = response.data.choices[0].text;
      this.cache[cacheKey] = text;
      return text;
    } catch (error: any) {
      logger.error(`Error generating text for prompt: ${prompt}`);
      throw error;
    }
  }

  async analyzeSentiment(text: string, model: string = this.config.defaultModel): Promise<string> {
    const cacheKey = `analyzeSentiment-${text}-${model}`;
    if (this.cache[cacheKey]) {
      logger.debug(`Returning cached response for text: ${text}`);
      return this.cache[cacheKey];
    }

    try {
      const data = {
        model: model,
        prompt: `Analyze the sentiment of the following text: ${text}`,
        max_tokens: this.config.maxTokens,
        temperature: this.config.temperature,
      };

      const response = await this.makeRequest('/completions', data);
      const sentiment = response.data.choices[0].text;
      this.cache[cacheKey] = sentiment;
      return sentiment;
    } catch (error: any) {
      logger.error(`Error analyzing sentiment for text: ${text}`);
      throw error;
    }
  }

  // Example of rate limiting (simplified) - can be expanded
  private async rateLimitCheck(endpoint: string): Promise<boolean> {
    // In a real implementation, you'd check against a rate limiting service
    // or use a token bucket algorithm.  This is a placeholder.
    await new Promise(resolve => setTimeout(resolve, 50)); // Simulate delay
    return Math.random() < 0.1; // Simulate rate limiting
  }

  // Example of retry logic
  async executeWithRetry(fn: () => Promise<any>, maxRetries: number = 3): Promise<any> {
    let retries = 0;
    while (retries < maxRetries) {
      try {
        return await fn();
      } catch (error) {
        retries++;
        if (retries === maxRetries) {
          logger.error(`Max retries reached for ${fn.name}`);
          throw error;
        }
        await new Promise(resolve => setTimeout(resolve, 1000 * retries)); // Exponential backoff
      }
    }
  }
}