import axios, { AxiosResponse, AxiosError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private axiosInstance: any;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Add authentication headers here if needed
        // Example: config.headers['Authorization'] = 'Bearer ' + this.authToken;
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.axiosInstance.interceptors.response.use(
      (response) => {
        return response as BaseResponse<any>;
      },
      (error) => {
        if (error.response) {
          // Handle HTTP errors
          return Promise.reject(
            new ApiError(error.response.status, error.response.data?.message || 'HTTP Error')
          );
        } else {
          // Handle non-HTTP errors (e.g., network errors)
          return Promise.reject(new ApiError(500, 'Request Error'));
        }
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
      };
    } catch (error: any) {
      throw error;
    }
  }

  async post<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.post(endpoint, data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      throw error;
    }
  }

  async put<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.put(endpoint, data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      throw error;
    }
  }

  async delete<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.delete(endpoint);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      throw error;
    }
  }
}

interface ApiError {
  statusCode: number;
  message: string;
}

export default ApiClient;