import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface BaseResponse {
  status: 'success' | 'error';
  message?: string;
  data?: any;
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: Record<string, string>;

  constructor(baseUrl: string, authHeaders: Record<string, string> = {}) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authHeaders = authHeaders;
    this.axiosInstance.interceptors.request.use(
      this.handleRequestInterceptors,
      this.handleResponseInterceptors
    );
  }

  private handleRequestInterceptors = (config: AxiosRequestConfig) => {
    if (this.authHeaders) {
      config.headers = {
        ...config.headers,
        ...this.authHeaders,
      };
    }
    return config;
  };

  private handleResponseInterceptors = (response: AxiosResponse) => {
    return response;
  };

  async get<T>(endpoint: string): Promise<T> {
    try {
      const response = await this.axiosInstance.get(endpoint);
      const data: BaseResponse = { status: 'success', data: response.data };
      return data.data as T;
    } catch (error: any) {
      const errorData: BaseResponse = { status: 'error', message: error.message };
      throw errorData;
    }
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await this.axiosInstance.post(endpoint, data);
      const data: BaseResponse = { status: 'success', data: response.data };
      return data.data as T;
    } catch (error: any) {
      const errorData: BaseResponse = { status: 'error', message: error.message };
      throw errorData;
    }
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await this.axiosInstance.put(endpoint, data);
      const data: BaseResponse = { status: 'success', data: response.data };
      return data.data as T;
    } catch (error: any) {
      const errorData: BaseResponse = { status: 'error', message: error.message };
      throw errorData;
    }
  }

  async delete<T>(endpoint: string): Promise<T> {
    try {
      const response = await this.axiosInstance.delete(endpoint);
      const data: BaseResponse = { status: 'success', data: response.data };
      return data.data as T;
    } catch (error: any) {
      const errorData: BaseResponse = { status: 'error', message: error.message };
      throw errorData;
    }
  }
}

export default ApiClient;