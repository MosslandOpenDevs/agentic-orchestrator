import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  data: T;
  status: number;
  error?: string;
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: { [key: string]: string };

  constructor(baseUrl: string, authHeaders: { [key: string]: string } = {}) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
      interceptors: {
        request: [
          (config) => {
            if (this.authHeaders) {
              for (const key in this.authHeaders) {
                if (this.authHeaders.hasOwnProperty(key)) {
                  config.headers[key] = this.authHeaders[key];
                }
              }
            }
            return config;
          },
        ],
        response: [
          (response) => {
            if (response.status >= 400) {
              throw new ApiError(response.status, response.data?.error || 'Request failed');
            }
            return response;
          },
        ],
      },
    });
  }

  async get<T>(endpoint: string): Promise<BaseResponse<T>> {
    const response = await this.axiosInstance.get(endpoint);
    return response.data as BaseResponse<T>;
  }

  async post<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    const response = await this.axiosInstance.post(endpoint, data);
    return response.data as BaseResponse<T>;
  }

  async put<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    const response = await this.axiosInstance.put(endpoint, data);
    return response.data as BaseResponse<T>;
  }

  async delete<T>(endpoint: string): Promise<BaseResponse<T>> {
    const response = await this.axiosInstance.delete(endpoint);
    return response.data as BaseResponse<T>;
  }

  async patch<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    const response = await this.axiosInstance.patch(endpoint, data);
    return response.data as BaseResponse<T>;
  }

  // Example endpoint: /api/riskScore
  async getRiskScore(walletAddress: string): Promise<BaseResponse<any>> {
    return this.get(`/api/riskScore?walletAddress=${walletAddress}`);
  }

  // Example endpoint: /api/marketData
  async getMarketData(assetAddress: string): Promise<BaseResponse<any>> {
    return this.get(`/api/marketData?assetAddress=${assetAddress}`);
  }

  // Example endpoint: /api/agentPrompt
  async createAgentPrompt(prompt: any): Promise<BaseResponse<any>> {
    return this.post(`/api/agentPrompt`, prompt);
  }
}

interface ApiError extends Error {
  statusCode: number;
  message: string;
}

export default ApiClient;