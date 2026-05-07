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
        // Example: config.headers['Authorization'] = 'Bearer ' + token;
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
          return Promise.reject(
            new CustomError('API Error', 400, error.response.data)
          );
        } else {
          return Promise.reject(new CustomError('Network Error', 500, null));
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
      } as BaseResponse<T>;
    } catch (error) {
      throw new CustomError('Generic Error', 500, error.message);
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
    } catch (error) {
      throw new CustomError('Generic Error', 500, error.message);
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
    } catch (error) {
      throw new CustomError('Generic Error', 500, error.message);
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
    } catch (error) {
      throw new CustomError('Generic Error', 500, error.message);
    }
  }
}

class CustomError extends Error {
  constructor(message: string, statusCode: number, data?: any) {
    super(message);
    this.statusCode = statusCode;
    this.data = data;
    Object.setPrototypeOf(this, CustomError.prototype);
  }
}

export default ApiClient;