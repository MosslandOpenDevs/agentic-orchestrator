import axios from 'axios';
import { RateLimiter } from 'limiter';
import { createLogger, format, transports } from 'winston';

const logger = createLogger({
  level: 'info',
  format: format.combine(format.timestamp(), format.json()),
  transports: [new transports.Console()],
});

interface DuneResponse {
  result: any;
}

class DuneAnalyticsService {
  private apiKey: string;
  private rateLimiter: RateLimiter;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
    this.rateLimiter = new RateLimiter({ tokensPerInterval: 10, interval: 'second' });
  }

  async executeQuery(queryId: number): Promise<DuneResponse> {
    const url = `https://api.dune.com/api/v1/query/${queryId}/execute`;
    return this.retry(() => this.fetchData(url));
  }

  private async fetchData(url: string): Promise<DuneResponse> {
    await this.rateLimiter.removeTokens(1);
    try {
      const response = await axios.post(url, {}, {
        headers: { 'X-Dune-Api-Key': this.apiKey },
      });
      return response.data as DuneResponse;
    } catch (error) {
      logger.error(`Error fetching data from ${url}:`, error.message);
      throw error;
    }
  }

  private async retry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
    try {
      return await fn();
    } catch (error) {
      if (retries > 0 && this.isTransientError(error)) {
        logger.warn(`Retrying due to transient error: ${error.message}`);
        return this.retry(fn, retries - 1);
      }
      throw error;
    }
  }

  private isTransientError(error: any): boolean {
    const status = error.response?.status;
    return [429, 503].includes(status || 0);
  }
}

export default DuneAnalyticsService;

// Usage
const apiKey = process.env.DUNE_API_KEY;
if (!apiKey) throw new Error('DUNE_API_KEY is required');
const duneService = new DuneAnalyticsService(apiKey);

(async () => {
  try {
    const result = await duneService.executeQuery(12345);
    console.log(result);
  } catch (error) {
    logger.error('Failed to execute query:', error.message);
  }
})();