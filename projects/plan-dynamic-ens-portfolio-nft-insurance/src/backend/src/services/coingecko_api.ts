import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { logger } from './logger'; // Assuming you have a logger service
import { RateLimiter } from './rate-limiter'; // Assuming you have a rate limiter service
import { Cache } from './cache'; // Assuming you have a cache service
import { CoingeckoData } from '../types/coingecko-data';

export class CoingeckoAPI {
  private apiKey: string;
  private axiosInstance: AxiosInstance;
  private rateLimiter: RateLimiter;
  private cache: Cache;
  private baseUrl: string = 'https://api.coingecko.com/api/v3';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'X-CG-PRO-API-KEY': this.apiKey,
      },
    });
    this.rateLimiter = new RateLimiter(100, 60000); // 100 requests per 60 seconds
    this.cache = new Cache();
    logger.info('CoingeckoAPI service initialized');
  }

  async getCoinData(coinId: string): Promise<CoingeckoData | null> {
    const cacheKey = `coin:${coinId}`;
    const cachedData = this.cache.get(cacheKey);

    if (cachedData) {
      logger.debug(`Coin data retrieved from cache for ${coinId}`);
      return cachedData;
    }

    try {
      const url = `${this.baseUrl}/coins/${coinId}`;
      const response = await this.axiosInstance.get<CoingeckoData>(url);
      const data = response.data;

      this.cache.set(cacheKey, data);
      logger.debug(`Coin data retrieved from API for ${coinId}`);
      return data;
    } catch (error) {
      logger.error(`Error fetching coin data for ${coinId}: ${error}`);
      if (axios.isAxiosError(error)) {
        if (error.response && error.response.status === 429) {
          logger.warn(`Rate limit exceeded for ${coinId}.  Retrying...`);
          await this.rateLimiter.sleep();
          return this.getCoinData(coinId); // Retry
        }
      }
      return null;
    }
  }

  async getPrice(coinId: string, vsCurrency: string): Promise<number | null> {
    const cacheKey = `price:${coinId}:${vsCurrency}`;
    const cachedData = this.cache.get(cacheKey);

    if (cachedData) {
      logger.debug(`Price retrieved from cache for ${coinId} in ${vsCurrency}`);
      return cachedData;
    }

    try {
      const url = `${this.baseUrl}/simple/price?ids=${coinId}&vs=${vsCurrency}`;
      const response: AxiosResponse<any> = await this.axiosInstance.get(url);
      const data = response.data[coinId];

      this.cache.set(cacheKey, data);
      logger.debug(`Price retrieved from API for ${coinId} in ${vsCurrency}`);
      return data;
    } catch (error) {
      logger.error(`Error fetching price for ${coinId} in ${vsCurrency}: ${error}`);
      if (axios.isAxiosError(error)) {
        if (error.response && error.response.status === 429) {
          logger.warn(`Rate limit exceeded. Retrying...`);
          await this.rateLimiter.sleep();
          return this.getPrice(coinId, vsCurrency); // Retry
        }
      }
      return null;
    }
  }

  async getExchangeInfo(): Promise<any | null> {
    try {
      const url = `${this.baseUrl}/exchange/info`;
      const response = await this.axiosInstance.get<any>(url);
      logger.debug('Exchange info retrieved successfully');
      return response.data;
    } catch (error) {
      logger.error(`Error fetching exchange info: ${error}`);
      return null;
    }
  }
}