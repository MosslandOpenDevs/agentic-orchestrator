import axios, { AxiosInstance, AxiosInterceptorManager, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private interceptors: AxiosInterceptorManager<AxiosInstance>;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.interceptors = this.axiosInstance.interceptors;
  }

  // Request Interceptors
  use(fn: (id: number, config: any) => void): this {
    this.interceptors.request.use(fn);
    return this;
  }

  // Response Interceptors
  onResponse<T>(fn: (response: Response) => T): this {
    this.interceptors.response.onSuccess(fn);
    return this;
  }

  // Custom Error Type
  class ApiError extends Error {
    public statusCode: number;
    public data?: any;

    constructor(message: string, statusCode: number, data?: any) {
      super(message);
      this.statusCode = statusCode;
      this.data = data;
    }
  }

  // Vault API
  async getVaults(): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get('/api/vaults');
      return { data: response.data, success: true };
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.message, error.response?.status || 500, error.response?.data || null);
      } else {
        throw new ApiError('An unexpected error occurred', 500, null);
      }
    }
  }

  async getVault(vaultId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/vaults/${vaultId}`);
      return { data: response.data, success: true };
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.message, error.response?.status || 500, error.response?.data || null);
      } else {
        throw new ApiError('An unexpected error occurred', 500, null);
      }
    }
  }

  async createVault(vaultData: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/vaults', vaultData);
      return { data: response.data, success: true };
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.message, error.response?.status || 500, error.response?.data || null);
      } else {
        throw new ApiError('An unexpected error occurred', 500, null);
      }
    }
  }

  async updateVault(vaultId: string, vaultData: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.put(`/api/vaults/${vaultId}`, vaultData);
      return { data: response.data, success: true };
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.message, error.response?.status || 500, error.response?.data || null);
      } else {
        throw new ApiError('An unexpected error occurred', 500, null);
      }
    }
  }

  // Asset API
  async getAssets(): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get('/api/assets');
      return { data: response.data, success: true };
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.message, error.response?.status || 500, error.response?.data || null);
      } else {
        throw new ApiError('An unexpected error occurred', 500, null);
      }
    }
  }

  // GPT Analysis API
  async analyzeGPT(data: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/gpt-analysis', data);
      return { data: response.data, success: true };
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        throw new ApiError(error.message, error.response?.status || 500, error.response?.data || null);
      } else {
        throw new ApiError('An unexpected error occurred', 500, null);
      }
    }
  }
}

export default ApiClient;