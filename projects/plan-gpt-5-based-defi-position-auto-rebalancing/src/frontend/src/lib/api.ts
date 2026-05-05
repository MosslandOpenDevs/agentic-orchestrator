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

  async request<T>(method: string, endpoint: string, body?: any, headers?: any): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headerOptions = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (this.accessToken) {
      headerOptions['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response: Response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new ApiError(response.status, errorData.message || `HTTP error ${response.status}`);
      }

      const data = await response.json() as T;
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw new ApiError(500, 'Internal Server Error');
    }
  }
}

class SecurityPricesClient extends ApiClient {
  constructor() {
    super('/api/security-prices');
  }

  getSecurityPrices(): Promise<any> {
    return this.request('GET', '');
  }
}

class RebalanceClient extends ApiClient {
  constructor() {
    super('/api/rebalance');
  }

  generateRebalance(body: any): Promise<any> {
    return this.request('POST', '', body);
  }
}

class PortfolioClient extends ApiClient {
  constructor() {
    super('/api/portfolio');
  }

  getPortfolio(userId: string): Promise<any> {
    return this.request('GET', `/${userId}`);
  }
}

class ApiError extends Error {
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export { SecurityPricesClient, RebalanceClient, PortfolioClient, ApiClient, ApiError };