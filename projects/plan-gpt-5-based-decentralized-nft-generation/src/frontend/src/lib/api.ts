import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  success: boolean;
  data: T | null;
  error?: string;
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: { [key: string]: string };

  constructor(baseUrl: string, authHeaders: { [key: string]: string }) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authHeaders = authHeaders;
    this.axiosInstance.interceptors.request.use(
      this.setupInterceptors,
      (error) => {
        console.error('Request Error:', error);
        return Promise.reject(error);
      }
    );
  }

  private async setupInterceptors(): Promise<void> {
    return Promise.resolve();
  }

  async get<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.get(endpoint, {
        headers: {
          ...this.authHeaders,
        },
      });
      return {
        success: true,
        data: response.data,
        error: null,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error('API Error:', error.message, error.response?.data, error.response?.status);
        return {
          success: false,
          data: null,
          error: error.message || 'Unknown error',
        } as BaseResponse<T>;
      } else {
        console.error('Unexpected Error:', error);
        return {
          success: false,
          data: null,
          error: 'Unexpected error',
        } as BaseResponse<T>;
      }
    }
  }

  async post<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.post(endpoint, data, {
        headers: {
          ...this.authHeaders,
        },
      });
      return {
        success: true,
        data: response.data,
        error: null,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error('API Error:', error.message, error.response?.data, error.response?.status);
        return {
          success: false,
          data: null,
          error: error.message || 'Unknown error',
        } as BaseResponse<T>;
      } else {
        console.error('Unexpected Error:', error);
        return {
          success: false,
          data: null,
          error: 'Unexpected error',
        } as BaseResponse<T>;
      }
    }
  }

  async put<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.put(endpoint, data, {
        headers: {
          ...this.authHeaders,
        },
      });
      return {
        success: true,
        data: response.data,
        error: null,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error('API Error:', error.message, error.response?.data, error.response?.status);
        return {
          success: false,
          data: null,
          error: error.message || 'Unknown error',
        } as BaseResponse<T>;
      } else {
        console.error('Unexpected Error:', error);
        return {
          success: false,
          data: null,
          error: 'Unexpected error',
        } as BaseResponse<T>;
      }
    }
  }

  async delete<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.delete(endpoint, {
        headers: {
          ...this.authHeaders,
        },
      });
      return {
        success: true,
        data: response.data,
        error: null,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error('API Error:', error.message, error.response?.data, error.response?.status);
        return {
          success: false,
          data: null,
          error: error.message || 'Unknown error',
        } as BaseResponse<T>;
      } else {
        console.error('Unexpected Error:', error);
        return {
          success: false,
          data: null,
          error: 'Unexpected error',
        } as BaseResponse<T>;
      }
    }
  }
}

export default ApiClient;