import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { logger } from './logger'; // Assuming a logger is defined elsewhere
import { RateLimiter } from './rate-limiter'; // Assuming a rate limiter is defined elsewhere
import { Cache } from './cache'; // Assuming a cache is defined elsewhere

interface EtherscanOptions {
  apiKey: string;
  cache?: Cache;
  rateLimiter?: RateLimiter;
}

export class EtherscanAPI {
  private readonly axiosInstance: AxiosInstance;
  private readonly baseUrl: string = 'https://api.etherscan.io/api';
  private readonly options: EtherscanOptions;

  constructor(options: EtherscanOptions) {
    this.options = {
      apiKey: options.apiKey,
      cache: options.cache || new Cache(),
      rateLimiter: options.rateLimiter || new RateLimiter(60000), // Default rate limit: 60 seconds
    };

    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': this.options.apiKey,
      },
    });

    logger.info('EtherscanAPI service initialized');
  }

  /**
   * Searches for transactions by address and keyword.
   * @param address The Ethereum address to search for.
   * @param keyword The keyword to search for in the transaction details.
   * @param page Number of the page to retrieve (default: 1).
   * @param limit Number of results per page (default: 20).
   * @returns A promise that resolves to an array of transaction objects or an error.
   */
  async searchTransactions(
    address: string,
    keyword: string,
    page: number = 1,
    limit: number = 20
  ): Promise<
    AxiosResponse<any> | { success: false; error: string }
  > {
    try {
      const cacheKey = `searchTransactions-${address}-${keyword}-${page}-${limit}`;
      const cachedData = this.options.cache.get(cacheKey);

      if (cachedData) {
        logger.debug(`Cache hit for searchTransactions: ${cacheKey}`);
        return { data: cachedData };
      }

      const retryCount = 3;
      for (let i = 0; i < retryCount; i++) {
        const response = await this.axiosInstance.get(
          `/txs?module=account&action=search&sort=asc&order=byDate&startblock=0&endblock=99999&fromBlock=0&toBlock=99999&from=0&to=0&keyword=${keyword}&page=${page}&limit=${limit}&apikey=${this.options.apiKey}`
        );

        if (response.status === 200) {
          this.options.cache.set(cacheKey, response.data);
          logger.debug(`Cache miss for searchTransactions: ${cacheKey}`);
          return response;
        } else {
          logger.error(
            `Search transactions failed (attempt ${i + 1}/${retryCount}): ${response.status} - ${response.data}`
          );
          await this.rateLimiter.wait(); // Wait before retrying
          if (i === retryCount - 1) {
            throw new Error(
              `Failed to search transactions after ${retryCount} attempts.`
            );
          }
        }
      }
    } catch (error) {
      logger.error(`Error searching transactions: ${error}`);
      return { data: null, status: 500, error: 'Internal Server Error' };
    }
  }

  /**
   * Retrieves a transaction by its transaction hash.
   * @param transactionHash The transaction hash to retrieve.
   * @returns A promise that resolves to the transaction object or an error.
   */
  async getTransaction(transactionHash: string): Promise<
    AxiosResponse<any> | { success: false; error: string }
  > {
    try {
      const cacheKey = `getTransaction-${transactionHash}`;
      const cachedData = this.options.cache.get(cacheKey);

      if (cachedData) {
        logger.debug(`Cache hit for getTransaction: ${cacheKey}`);
        return { data: cachedData };
      }

      const retryCount = 3;
      for (let i = 0; i < retryCount; i++) {
        const response = await this.axiosInstance.get(
          `/txs/${transactionHash}?module=account&sort=asc&apikey=${this.options.apiKey}`
        );

        if (response.status === 200) {
          this.options.cache.set(cacheKey, response.data);
          logger.debug(`Cache miss for getTransaction: ${cacheKey}`);
          return response;
        } else {
          logger.error(
            `Get transaction failed (attempt ${i + 1}/${retryCount}): ${response.status} - ${response.data}`
          );
          await this.rateLimiter.wait(); // Wait before retrying
          if (i === retryCount - 1) {
            throw new Error(
              `Failed to get transaction after ${retryCount} attempts.`
            );
          }
        }
      }
    } catch (error) {
      logger.error(`Error getting transaction: ${error}`);
      return { data: null, status: 500, error: 'Internal Server Error' };
    }
  }
}