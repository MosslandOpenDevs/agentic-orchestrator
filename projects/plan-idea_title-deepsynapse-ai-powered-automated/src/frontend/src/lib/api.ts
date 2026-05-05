import fetch, { AbortController, Response } from 'node-fetch';

interface BaseResponse {
  success: boolean;
  timestamp: number;
  data?: any;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private abortController: AbortController | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setAccessToken(token: string) {
    this.accessToken = token;
  }

  async request<T>(method: string, endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.accessToken ? { 'Authorization': `Bearer ${this.accessToken}` } : {}),
    };

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
        signal: this.abortController?.signal,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new ApiError(response.status, errorData.message || `Request failed: ${response.status}`);
      }

      const data: BaseResponse = await response.json();
      if (data.success) {
        return data.data as T;
      }
      throw new ApiError(response.status, data.error || 'Request successful but data is empty');
    } catch (error) {
      if (this.abortController) {
        this.abortController.abort();
      }
      throw new ApiError(0, error instanceof Error ? error.message : 'An unexpected error occurred');
    }
  }

  // Generic CRUD operations
  get<T>(endpoint: string): Promise<T> {
    return this.request('GET', endpoint);
  }

  post<T>(endpoint: string, body: any): Promise<T> {
    return this.request('POST', endpoint, body);
  }

  put<T>(endpoint: string, body: any): Promise<T> {
    return this.request('PUT', endpoint, body);
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request('DELETE', endpoint);
  }

  // Specific Endpoints

  async getSecurityPrices(): Promise<any> {
    return this.get('/api/security-prices');
  }

  async rebalance(body: any): Promise<any> {
    return this.post('/api/rebalance', body);
  }

  async executeTrade(body: any): Promise<any> {
    return this.post('/api/execute-trade', body);
  }
}

class ApiError extends Error {
  public status: number;
  public data?: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

export default ApiClient;