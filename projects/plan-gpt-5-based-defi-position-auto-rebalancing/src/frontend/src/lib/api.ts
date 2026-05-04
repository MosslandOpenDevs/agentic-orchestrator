import fetch, { Response } from 'node-fetch';

interface ApiConfig {
  baseUrl: string;
  authHeaderKey: string;
  authHeaderValue: string;
}

class ApiClient {
  private baseUrl: string;
  private authHeaderKey: string;
  private authHeaderValue: string;

  constructor(config: ApiConfig) {
    this.baseUrl = config.baseUrl;
    this.authHeaderKey = config.authHeaderKey;
    this.authHeaderValue = config.authHeaderValue;
  }

  private async request<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    body?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      [this.authHeaderKey]: this.authHeaderValue,
    };

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new ApiError(response.status, response.statusText, errorData);
      }

      const data = await response.json() as T;
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  }

  // NFT Portfolio
  async getPortfolio(): Promise<any> {
    return this.request('get', '/api/nft/portfolio');
  }

  // Rain Market Data
  async getRainMarketData(): Promise<any> {
    return this.request('get', '/api/marketdata/rain');
  }

  // Rebalance
  async rebalance(strategy: any): Promise<any> {
    return this.request('post', '/api/rebalance', strategy);
  }
}

class ApiError extends Error {
  public status: number;
  public statusText: string;
  public data: any;

  constructor(status: number, statusText: string, data: any) {
    super(`${status} - ${statusText}`);
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

export default ApiClient;