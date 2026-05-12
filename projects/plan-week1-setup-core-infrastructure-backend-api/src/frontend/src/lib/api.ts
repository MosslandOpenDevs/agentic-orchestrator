import fetch, { Response } from 'node-fetch';

interface ApiConfig {
  baseUrl: string;
  authHeaderKey: string;
  authHeaderValue: string;
}

class ApiClient {
  private baseUrl: string;
  private authHeaderKey: string;
  private authHeaderValue: string;

  constructor(config: ApiConfig) {
    this.baseUrl = config.baseUrl;
    this.authHeaderKey = config.authHeaderKey;
    this.authHeaderValue = config.authHeaderValue;
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    body?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      [this.authHeaderKey]: this.authHeaderValue,
    };

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new ApiError(response.status, response.statusText, errorData);
      }

      const data = await response.json() as T;
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  }

  // Contract Analysis
  async analyzeContract(contractCode: string): Promise<any> {
    return this.request('POST', '/api/contracts/analyze', { contractCode });
  }

  // Contract CRUD
  async getContract(contractId: string): Promise<any> {
    return this.request('GET', `/api/contracts/${contractId}`);
  }

  async createContract(contractData: any): Promise<any> {
    return this.request('POST', '/api/contracts', contractData);
  }

  async updateContract(contractId: string, contractData: any): Promise<any> {
    return this.request('PUT', `/api/contracts/${contractId}`, contractData);
  }

  async deleteContract(contractId: string): Promise<any> {
    return this.request('DELETE', `/api/contracts/${contractId}`);
  }

  // Report Creation
  async createReport(reportData: any): Promise<any> {
    return this.request('POST', '/api/reports/create', reportData);
  }
}

class ApiError extends Error {
  public status: number;
  public statusText: string;
  public data: any;

  constructor(status: number, statusText: string, data: any) {
    super(`${status} - ${statusText}`);
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

export default ApiClient;