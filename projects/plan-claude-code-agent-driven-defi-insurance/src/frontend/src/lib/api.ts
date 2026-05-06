import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class ApiClient {
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
        // Add authentication headers here if needed
        if (config.headers) {
          for (const key in authHeaders) {
            if (authHeaders.hasOwnProperty(key)) {
              config.headers[key] = authHeaders[key];
            }
          }
        }
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );
  }

  async get<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.get(endpoint);
      return {
        data: response.data,
        success: true,
        error: undefined,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error('API Error:', error.response?.data || error.message);
        return {
          data: null,
          success: false,
          error: error.response?.data?.message || error.message,
        } as BaseResponse<T>;
      }
      return {
        data: null,
        success: false,
        error: 'An unexpected error occurred.',
      } as BaseResponse<T>;
    }
  }

  async post<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.post(endpoint, data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error('API Error:', error.response?.data || error.message);
        return {
          data: null,
          success: false,
          error: error.response?.data?.message || error.message,
        } as BaseResponse<T>;
      }
      return {
        data: null,
        success: false,
        error: 'An unexpected error occurred.',
      } as BaseResponse<T>;
    }
  }

  async rebalance(nftHolderId: string): Promise<BaseResponse<any>> {
    return this.post(`/api/rebalance/${nftHolderId}`, {});
  }

  async portfolio(nftHolderId: string): Promise<BaseResponse<any>> {
    return this.get(`/api/portfolio/${nftHolderId}`);
  }

  async riskAssessment(contractAddress: string): Promise<BaseResponse<any>> {
    return this.get(`/api/riskAssessment/${contractAddress}`);
  }
}

export default ApiClient;