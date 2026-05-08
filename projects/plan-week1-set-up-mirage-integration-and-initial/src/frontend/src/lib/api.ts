import fetch, { Response } from 'node-fetch';

interface BaseResponse {
  status: number;
  data?: any;
  error?: string;
}

class DaoApi {
  private baseUrl: string;
  private authToken: string | undefined;

  constructor(baseUrl: string, authToken?: string) {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
  }

  private async request<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    body?: any
  ): Promise<BaseResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          `${response.status} - ${response.statusText} - ${JSON.stringify(
            errorData
          )}`
        );
      }

      const data = await response.json() as T;
      return { status: response.status, data, error: undefined };
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  }

  async getStrategies(): Promise<BaseResponse<any[]>> {
    return await this.request('get', '/api/strategies');
  }

  async getStrategy(strategyId: string): Promise<BaseResponse<any>> {
    return await this.request('get', `/api/strategies/${strategyId}`);
  }

  async createSimulation(strategyId: string, simulationData: any): Promise<BaseResponse<any>> {
    return await this.request('post', '/api/simulations', simulationData);
  }

  async getSimulationResults(): Promise<BaseResponse<any[]>> {
    return await this.request('get', '/api/simulation-results');
  }
}

export default DaoApi;