import fetch, { Response } from 'node-fetch';

interface BaseResponse {
  status: 'success' | 'error';
  message?: string;
  data?: any;
}

class ApiClient {
  private baseUrl: string;
  private authHeaders: { [key: string]: string };

  constructor(baseUrl: string, authHeaders: { [key: string]: string }) {
    this.baseUrl = baseUrl;
    this.authHeaders = authHeaders;
  }

  private async request<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    body?: any
  ): Promise<BaseResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...this.authHeaders,
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response: Response = await fetch(url, options);

      if (!response.ok) {
        const errorData = await response.json();
        throw new ApiError(response.status, errorData.message || `Request failed: ${response.status}`);
      }

      const data: BaseResponse<T> = await response.json();
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw new ApiError(500, 'Internal Server Error');
    }
  }

  // Withdrawal Data Endpoint
  async getWithdrawalData(): Promise<BaseResponse<any>> {
    return await this.request('get', '/api/withdrawal_data');
  }

  async postClaudeAnalysis(data: any): Promise<BaseResponse<any>> {
    return await this.request('post', '/api/claude_analysis', data);
  }

  // Generic CRUD Operations (Example - Adapt as needed)
  async get<T>(endpoint: string): Promise<BaseResponse<T>> {
    return await this.request('get', endpoint);
  }

  async post<T>(endpoint: string, body: any): Promise<BaseResponse<T>> {
    return await this.request('post', endpoint, body);
  }

  async put<T>(endpoint: string, body: any): Promise<BaseResponse<T>> {
    return await this.request('put', endpoint, body);
  }

  async delete<T>(endpoint: string): Promise<BaseResponse<T>> {
    return await this.request('delete', endpoint);
  }
}

class ApiError extends Error {
  public status: number;
  public message: string;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.message = message;
  }
}

export default ApiClient;