import fetch, { Response } from 'node-fetch';

interface BaseResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    body?: any
  ): Promise<BaseResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}`,
    };

    try {
      const response: Response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `${response.status} - ${response.statusText} - ${JSON.stringify(
            errorData
          )}`
        );
      }

      const data = await response.json() as T;
      return { success: true, data };
    } catch (error) {
      console.error('API Request Error:', error);
      throw new Error(`API Request Failed: ${error}`);
    }
  }

  // Ethereum Market Data
  async getEthereumMarketData(): Promise<BaseResponse<any>> {
    return this.request('get', '/api/marketdata/ethereum');
  }

  // Dune Analytics Portfolio Data
  async getDunePortfolioData(): Promise<BaseResponse<any>> {
    return this.request('get', '/api/marketdata/dune');
  }

  // Portfolio Rebalancing
  async rebalancePortfolio(body: any): Promise<BaseResponse<any>> {
    return this.request('post', '/api/portfolio/rebalance', body);
  }
}

export default ApiClient;