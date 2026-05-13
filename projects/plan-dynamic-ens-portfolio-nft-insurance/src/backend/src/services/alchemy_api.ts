import axios, { AxiosError, AxiosResponse } from 'axios';
import { logger } from './logger'; // Assuming a logger is defined elsewhere
import { EnvironmentVariables } from './environment-variables';

interface AlchemyResponse<T> extends AxiosResponse {
  data: T;
}

class AlchemyApiService {
  private apiKey: string;
  private baseApiUrl: string;
  private rateLimitWindow: number; // in seconds
  private retryCount: number = 3;
  private retryDelay: number = 1000; // 1 second
  private cacheTTL: number = 60; // 60 seconds
  private cache: { [key: string]: any } = {};

  constructor(env: EnvironmentVariables) {
    this.apiKey = env.alchemyApiKey;
    this.baseApiUrl = 'https://eth-mainnet.alchemyapi.io'; // Or other network
    this.rateLimitWindow = 60; // Default rate limit window
  }

  private async checkRateLimit(): Promise<boolean> {
    // Placeholder for actual rate limit check.  Alchemy API provides headers
    // indicating rate limit status.  This is a simplified example.
    try {
      const response = await axios.get(`${this.baseApiUrl}/networks/eth/stats`, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });

      if (response.status === 200 && response.data.currentRequests <= this.rateLimitWindow) {
        return true;
      }
      return false;
    } catch (error) {
      logger.error('Error checking rate limit:', error);
      return true; // Assume rate limited on error to avoid blocking
    }
  }

  private async fetchData<T>(endpoint: string): Promise<T> {
    let cachedData = this.cache[endpoint];
    if (cachedData && cachedData.expiry > Date.now() - this.cacheTTL) {
      logger.debug(`Fetching from cache: ${endpoint}`);
      return cachedData as T;
    }

    let data: T;
    let attempt = 0;

    while (attempt < this.retryCount) {
      try {
        const url = `${this.baseApiUrl}${endpoint}`;
        const response = await axios.get<T>(url, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-KEY': this.apiKey,
          },
        });
        data = response.data;

        // Cache the data
        this.cache[endpoint] = {
          data,
          expiry: Date.now() + this.cacheTTL,
        };
        logger.debug(`Fetched from Alchemy: ${endpoint}`, { data });
        return data;
      } catch (error: any) {
        attempt++;
        if (attempt === this.retryCount) {
          logger.error(`Failed after ${this.retryCount} retries: ${endpoint}`, error);
          throw error;
        }
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      }
    }

    throw new Error(`Failed to fetch data from Alchemy after ${this.retryCount} retries: ${endpoint}`);
  }

  /**
   * Example: Get block number
   */
  getBlockNumber(): Promise<number> {
    return this.fetchData<number>('/blocks/latest');
  }

  /**
   * Example: Get transaction details
   */
  getTransaction(id: string): Promise<any> {
    return this.fetchData<any>(`/transactions/${id}`);
  }

  /**
   * Example: Get network stats
   */
  getNetworkStats(): Promise<any> {
    return this.fetchData<any>('/networks/eth/stats');
  }
}

export { AlchemyApiService };