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

  private async request<T>(method: string, endpoint: string, body?: any): Promise<BaseResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      };

      const options: RequestInit = {
        method,
        headers,
        body: JSON.stringify(body),
      };

      const response: Response = await fetch(url, options);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `${response.status} - ${response.statusText} - ${JSON.stringify(errorData)}`
        );
      }

      const data = await response.json() as T;
      return { success: true, data };
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  }

  // GET /api/assets
  async getAssets(): Promise<BaseResponse<any[]>> {
    return await this.request('GET', '/api/assets');
  }

  // GET /api/portfolios/{portfolioId}
  async getPortfolio(portfolioId: string): Promise<BaseResponse<any>> {
    return await this.request('GET', `/api/portfolios/${portfolioId}`);
  }

  // POST /api/recommedations
  async generateRecommendations(portfolioId: string): Promise<BaseResponse<any>> {
    return await this.request('POST', '/api/recommedations', { portfolioId });
  }
}

export default ApiClient;