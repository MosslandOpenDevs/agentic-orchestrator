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
      this.handleRequestInterceptors,
      this.handleResponseInterceptors
    );
  }

  private async handleRequestInterceptors(config: AxiosRequestConfig): Promise<AxiosRequestConfig> {
    // Add authentication headers
    if (Object.keys(this.authHeaders).length > 0) {
      for (const key in this.authHeaders) {
        if (this.authHeaders.hasOwnProperty(key)) {
          config.headers[key] = this.authHeaders[key];
        }
      }
    }
    return config;
  }

  private async handleResponseInterceptors(response: Response): Promise<Response> {
    if (response.status < 200 || response.status >= 300) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return response;
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
      if (axios.isAxiosError(error)) {
        if (error.response) {
          return {
            data: undefined,
            success: false,
            error: error.response.data?.message || error.response.statusText || 'An error occurred',
          } as BaseResponse<any>;
        } else {
          return {
            data: undefined,
            success: false,
            error: 'An error occurred',
          } as BaseResponse<any>;
        }
      }
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
      } as BaseResponse<T>;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          return {
            data: undefined,
            success: false,
            error: error.response.data?.message || error.response.statusText || 'An error occurred',
          } as BaseResponse<any>;
        } else {
          return {
            data: undefined,
            success: false,
            error: 'An error occurred',
          } as BaseResponse<any>;
        }
      }
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
      } as BaseResponse<T>;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          return {
            data: undefined,
            success: false,
            error: error.response.data?.message || error.response.statusText || 'An error occurred',
          } as BaseResponse<any>;
        } else {
          return {
            data: undefined,
            success: false,
            error: 'An error occurred',
          } as BaseResponse<any>;
        }
      }
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
      } as BaseResponse<T>;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          return {
            data: undefined,
            success: false,
            error: error.response.data?.message || error.response.statusText || 'An error occurred',
          } as BaseResponse<any>;
        } else {
          return {
            data: undefined,
            success: false,
            error: 'An error occurred',
          } as BaseResponse<any>;
        }
      }
      throw error;
    }
  }

  async patch<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.patch(endpoint, data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      } as BaseResponse<T>;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          return {
            data: undefined,
            success: false,
            error: error.response.data?.message || error.response.statusText || 'An error occurred',
          } as BaseResponse<any>;
        } else {
          return {
            data: undefined,
            success: false,
            error: 'An error occurred',
          } as BaseResponse<any>;
        }
      }
      throw error;
    }
  }
}

export default ApiClient;