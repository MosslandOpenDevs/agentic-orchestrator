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

  constructor(baseUrl: string, authHeaders: { [key: string]: string } = {}) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authHeaders = authHeaders;

    this.axiosInstance.interceptors.request.use(
      (config) => {
        if (config.headers) {
          // Merge auth headers
          config.headers = {
            ...config.headers,
            ...this.authHeaders,
          };
        }
        return config;
      },
      (error) => {
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
        throw new ApiError(error.response?.status, error.message, error.data);
      } else {
        throw new ApiError(500, 'Internal Server Error', null);
      }
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
        throw new ApiError(error.response?.status, error.message, error.data);
      } else {
        throw new ApiError(500, 'Internal Server Error', null);
      }
    }
  }

  async put<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.put(endpoint, data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.response?.status, error.message, error.data);
      } else {
        throw new ApiError(500, 'Internal Server Error', null);
      }
    }
  }

  async delete<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.delete(endpoint);
      return {
        data: response.data,
        success: true,
        error: undefined,
      } as BaseResponse<T>;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.response?.status, error.message, error.data);
      } else {
        throw new ApiError(500, 'Internal Server Error', null);
      }
    }
  }
}

interface ApiError {
  statusCode: number;
  message: string;
  data?: any;
}

export default ApiClient;