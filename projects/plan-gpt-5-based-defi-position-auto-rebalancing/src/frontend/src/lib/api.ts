import fetch, { Response } from 'node-fetch';

interface BaseResponse {
  statusCode: number;
  data?: any;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private authHeaders: HeadersInit;

  constructor(baseUrl: string, authHeaders?: HeadersInit) {
    this.baseUrl = baseUrl;
    this.authHeaders = authHeaders || {};
  }

  private async request<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    body?: any
  ): Promise<BaseResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...this.authHeaders,
      'Content-Type': 'application/json',
    };

    try {
      const response = await fetch(url, {
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
      return { statusCode: response.status, data, error: undefined };
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  }

  // NFT Collateral
  async getNftCollateral(): Promise<BaseResponse<{}>> {
    return await this.request('get', '/api/nftCollateral');
  }

  // Price Feeds
  async getPriceFeeds(): Promise<BaseResponse<{}>> {
    return await this.request('get', '/api/priceFeeds');
  }

  // Rebalance
  async rebalance(body: any): Promise<BaseResponse<{}>> {
    return await this.request('post', '/api/rebalance', body);
  }
}

export default ApiClient;