import OpenAI from 'openai';
import { logger } from './logger';
import { RateLimiter } from './rate-limiter';
import { Cache } from './cache';
import { Config } from './config';

export class OpenAIService {
  private openai: OpenAI;
  private rateLimiter: RateLimiter;
  private cache: Cache;
  private config: Config;

  constructor(config: Config) {
    this.config = config;
    this.rateLimiter = new RateLimiter(config.rateLimit);
    this.cache = new Cache(config.cache);
    this.openai = new OpenAI({ apiKey: this.config.apiKey });
  }

  async generateCompletion(prompt: string, options?: OpenAI.Completion.Options): Promise<OpenAI.Completion.Response> {
    logger.info(`Generating completion for prompt: ${prompt}`);

    if (this.cache.has(`completion:${prompt}`)) {
      logger.debug(`Retrieving completion from cache for prompt: ${prompt}`);
      return this.cache.get(`completion:${prompt}`) as OpenAI.Completion.Response;
    }

    if (await this.rateLimiter.shouldAllow()) {
      try {
        const response = await this.openai.completions.create({
          model: this.config.model,
          prompt,
          ...options,
        });
        this.cache.set(`completion:${prompt}`, response);
        logger.debug(`Completion generated successfully for prompt: ${prompt}`);
        return response;
      } catch (error) {
        logger.error(`Error generating completion for prompt: ${prompt}`, error);
        throw error;
      }
    } else {
      logger.warn(`Rate limit exceeded for prompt: ${prompt}`);
      throw new Error('Rate limit exceeded');
    }
  }

  async analyzeSentiment(text: string): Promise<any> {
    logger.info(`Analyzing sentiment for text: ${text}`);

    if (this.cache.has(`sentiment:${text}`)) {
      logger.debug(`Retrieving sentiment from cache for text: ${text}`);
      return this.cache.get(`sentiment:${text}`) as any;
    }

    if (await this.rateLimiter.shouldAllow()) {
      try {
        const response = await this.openai.completions.create({
          model: this.config.model,
          prompt: `Analyze the sentiment of the following text: ${text}. Return a JSON object with 'sentiment' and 'score' keys.`,
          max_tokens: 50,
          temperature: 0.1,
        });
        const result = response.choices[0].text;
        this.cache.set(`sentiment:${text}`, result);
        logger.debug(`Sentiment analysis completed successfully for text: ${text}`);
        return JSON.parse(result);
      } catch (error) {
        logger.error(`Error analyzing sentiment for text: ${text}`, error);
        throw error;
      }
    } else {
      logger.warn(`Rate limit exceeded for text: ${text}`);
      throw new Error('Rate limit exceeded');
    }
  }

  async getEmbedding(text: string): Promise<OpenAI.Embedding.Response> {
    logger.info(`Getting embedding for text: ${text}`);

    if (this.cache.has(`embedding:${text}`)) {
      logger.debug(`Retrieving embedding from cache for text: ${text}`);
      return this.cache.get(`embedding:${text}`) as OpenAI.Embedding.Response;
    }

    if (await this.rateLimiter.shouldAllow()) {
      try {
        const response = await this.openai.embeddings.create({
          model: this.config.model,
          input: text,
        });
        this.cache.set(`embedding:${text}`, response);
        logger.debug(`Embedding generated successfully for text: ${text}`);
        return response;
      } catch (error) {
        logger.error(`Error generating embedding for text: ${text}`, error);
        throw error;
      }
    } else {
      logger.warn(`Rate limit exceeded for text: ${text}`);
      throw new Error('Rate limit exceeded');
    }
  }
}