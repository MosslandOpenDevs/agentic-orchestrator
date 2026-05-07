import fetch from 'node-fetch';

interface BaseResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request<T>(
    method: 'get' | 'post',
    endpoint: string,
    body?: any
  ): Promise<BaseResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `${response.status} - ${response.statusText} - ${errorData.error || response.statusText}`
        );
      }

      const data = await response.json() as T;
      return { success: true, data };
    } catch (error) {
      console.error('API Request Error:', error);
      throw new Error(`API Request Error: ${error}`);
    }
  }

  // /api/billions/price
  async getBillionsPrice(): Promise<BaseResponse<number>> {
    return await this.request('get', '/api/billions/price');
  }

  // /api/nft/portfolio/{portfolioId}
  async getNftPortfolio(portfolioId: string): Promise<BaseResponse<any>> {
    return await this.request('get', `/api/nft/portfolio/${portfolioId}`);
  }

  // /api/gpt/prompt
  async postGptPrompt(body: any): Promise<BaseResponse<any>> {
    return await this.request('post', '/api/gpt/prompt', body);
  }

  // /api/coinmarketcap/price/{symbol}
  async getCoinMarketcapPrice(symbol: string): Promise<BaseResponse<number>> {
    return await this.request('get', `/api/coinmarketcap/price/${symbol}`);
  }
}

export default ApiClient;