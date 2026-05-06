import fetch, { Response } from 'node-fetch';

interface BaseResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setAccessToken(token: string) {
    this.accessToken = token;
  }

  async request<T>(method: string, endpoint: string, body?: any, headers?: any): Promise<BaseResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headerOptions = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (this.accessToken) {
      headerOptions['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      const data = await response.json();

      if (response.ok) {
        return { success: true, data };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error || response.statusText };
      }
    } catch (error) {
      console.error('API Request Error:', error);
      return { success: false, error: 'An unexpected error occurred' };
    }
  }

  // Portfolio Endpoints
  async getPortfolio(): Promise<BaseResponse<any>> {
    return this.request('GET', '/api/portfolio');
  }

  async createPortfolio(body: any): Promise<BaseResponse<any>> {
    return this.request('POST', '/api/portfolio', body);
  }

  async getRiskProfile(): Promise<BaseResponse<any>> {
    return this.request('GET', '/api/riskProfile');
  }

  async getStrategy(): Promise<BaseResponse<any>> {
    return this.request('GET', '/api/strategy');
  }
}

export default ApiClient;