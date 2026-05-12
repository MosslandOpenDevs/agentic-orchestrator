import fetch, { Response } from 'node-fetch';

interface Config {
  baseUrl: string;
  headers: {
    [key: string]: string;
  };
}

interface CustomError {
  statusCode: number;
  message: string;
  data?: any;
}

class ApiClient {
  private baseUrl: string;
  private headers: { [key: string]: string };

  constructor(config: Config) {
    this.baseUrl = config.baseUrl;
    this.headers = config.headers;
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    body?: any
  ): Promise<T> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const options = {
        method,
        headers: {
          ...this.headers,
          'Content-Type': 'application/json',
        },
      };
      if (body) {
        options.body = JSON.stringify(body);
      }

      const response: Response = await fetch(url, options);

      if (!response.ok) {
        const errorData = await response.json();
        throw new CustomError(response.status, errorData.message, errorData);
      }

      return await response.json() as T;
    } catch (error) {
      console.error('API Request Error:', error);
      throw new CustomError(500, 'Internal Server Error', error);
    }
  }

  // Contract Analysis
  async analyzeContract(contractCode: string): Promise<any> {
    return this.request('POST', '/api/contracts/analyze', { contractCode });
  }

  // Contract Reports
  async getContractReports(contractId: string): Promise<any> {
    return this.request('GET', `/api/contracts/${contractId}/reports`);
  }

  // User Registration
  async registerUser(userData: any): Promise<any> {
    return this.request('POST', '/api/users/register', userData);
  }
}

export default ApiClient;