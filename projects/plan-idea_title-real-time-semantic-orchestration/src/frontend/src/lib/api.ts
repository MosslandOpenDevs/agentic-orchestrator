import fetch, { Response } from 'node-fetch';

interface ApiError {
  statusCode: number;
  message: string;
  error?: any;
}

class ApiClient {
  private baseUrl: string;
  private authToken: string | undefined;

  constructor(baseUrl: string, authToken?: string) {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
  }

  private async request<T>(method: string, endpoint: string, body?: any): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    try {
      const response = await fetch(url, { method, headers, body: JSON.stringify(body) });

      if (!response.ok) {
        const errorData = await response.json() as ApiError;
        throw new ApiError(response.status, errorData.message, errorData);
      }

      const data = await response.json() as T;
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw new ApiError(500, 'Internal Server Error', error);
    }
  }

  async createAgent(agentData: any): Promise<any> {
    return await this.request('POST', '/api/agents', agentData);
  }

  async getAgent(agentId: string): Promise<any> {
    return await this.request('GET', `/api/agents/${agentId}`);
  }

  async sendMessage(messageData: any): Promise<any> {
    return await this.request('POST', '/api/messages', messageData);
  }

  async getTransactions(): Promise<any> {
    return await this.request('GET', '/api/transactions');
  }
}

export default ApiClient;