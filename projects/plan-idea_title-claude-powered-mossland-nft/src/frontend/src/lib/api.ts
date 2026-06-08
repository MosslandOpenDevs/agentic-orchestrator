import fetch, { Response } from 'node-fetch';

interface ApiError {
  status: number;
  message: string;
  data?: any;
}

class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request<T>(
    method: 'get' | 'post' | 'put',
    endpoint: string,
    body?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}`,
    };

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        const errorData = await response.json() as ApiError;
        throw new ApiError(response.status, errorData.message, errorData.data);
      }

      const data = await response.json() as T;
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw new ApiError(500, 'Internal Server Error', error);
    }
  }

  // NFT Collections
  async getNFTCollections(): Promise<any[]> {
    return await this.request('get', '/api/nftCollections');
  }

  // Price Feeds
  async getEthereumPrice(): Promise<any> {
    return await this.request('get', '/api/priceFeeds/ethereum');
  }

  // Portfolios
  async createPortfolio(portfolioData: any): Promise<any> {
    return await this.request('post', '/api/portfolios', portfolioData);
  }

  async getPortfolio(portfolioId: string): Promise<any> {
    return await this.request('get', `/api/portfolios/${portfolioId}`);
  }

  async updatePortfolio(portfolioId: string, portfolioData: any): Promise<any> {
    return await this.request('put', `/api/portfolios/${portfolioId}`, portfolioData);
  }
}

export default ApiClient;