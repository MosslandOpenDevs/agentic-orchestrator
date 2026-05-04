import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class AaveApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: { [key: string]: string };

  constructor(
    baseUrl: string,
    authHeaders: { [key: string]: string } = {}
  ) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
    });

    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Add authentication headers here if not already present
        if (config.headers && this.authHeaders) {
          for (const key in this.authHeaders) {
            if (!config.headers[key]) {
              config.headers[key] = this.authHeaders[key];
            }
          }
        }
        return config;
      },
      (error) => {
        console.error('Axios Request Error:', error);
        return Promise.reject(error);
      }
    );
  }

  async get<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.get(endpoint);
      const data = response.data;

      if (response.status !== 200) {
        throw new Error(`HTTP error ${response.status}`);
      }

      return {
        data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      if (axios.isCancel(error)) {
        throw error;
      }
      if (error instanceof Error && error.response) {
        // Handle HTTP errors
        const responseData = error.response.data;
        throw new Error(`HTTP error ${error.response.status}: ${JSON.stringify(responseData)}`);
      }
      throw error;
    }
  }

  async post<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.post(endpoint, data);
      const dataResult = response.data;

      if (response.status !== 201 && response.status !== 200) {
        throw new Error(`HTTP error ${response.status}`);
      }

      return {
        data: dataResult,
        success: true,
        error: undefined,
      };
    } catch (error) {
      if (axios.isCancel(error)) {
        throw error;
      }
      if (error instanceof Error && error.response) {
        const responseData = error.response.data;
        throw new Error(`HTTP error ${error.response.status}: ${JSON.stringify(responseData)}`);
      }
      throw error;
    }
  }

  // Placeholder for future endpoints
  async aavePositions(portfolio: string): Promise<BaseResponse<any>> {
    return this.get(`/api/aave/positions?portfolio=${portfolio}`);
  }

  async compoundPositions(portfolio: string): Promise<BaseResponse<any>> {
    return this.get(`/api/compound/positions?portfolio=${portfolio}`);
  }

  async agentReceipts(): Promise<BaseResponse<any>> {
    return this.get(`/api/agentReceipts`);
  }

  async createAgentReceipt(data: any): Promise<BaseResponse<any>> {
    return this.post(`/api/agentReceipts`, data);
  }
}

export default AaveApiClient;