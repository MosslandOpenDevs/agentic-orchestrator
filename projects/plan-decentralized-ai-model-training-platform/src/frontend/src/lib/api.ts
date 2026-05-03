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

  async request<T>(method: string, endpoint: string, options?: RequestInit): Promise<BaseResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = {
        'Content-Type': 'application/json',
        ...(this.accessToken ? { 'Authorization': `Bearer ${this.accessToken}` } : {}),
      };

      const response = await fetch(url, { method, headers, ...options });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `${response.status} - ${response.statusText} - ${JSON.stringify(errorData)}`
        );
      }

      const data = await response.json() as BaseResponse<T>;
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw new Error(`API Request Error: ${error}`);
    }
  }

  // Generic methods for easier usage
  get<T>(endpoint: string): Promise<BaseResponse<T>> {
    return this.request('GET', endpoint);
  }

  post<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    return this.request('POST', endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    return this.request('PUT', endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string): Promise<BaseResponse<T>> {
    return this.request('DELETE', endpoint);
  }

  // Specific Endpoints

  async getModels(): Promise<BaseResponse<any[]>> {
    return this.get('/api/models');
  }

  async getModel(modelId: string): Promise<BaseResponse<any>> {
    return this.get(`/api/models/${modelId}`);
  }

  async registerUser(userData: any): Promise<BaseResponse<any>> {
    return this.post('/api/users/register', userData);
  }

  async createTransaction(transactionData: any): Promise<BaseResponse<any>> {
    return this.post('/api/transactions', transactionData);
  }
}

export default ApiClient;