import axios, { AxiosInstance, AxiosInterceptorManager, AxiosRequestConfig, CancellationToken } from 'axios';

interface BaseError {
  statusCode: number;
  message: string;
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private interceptors: AxiosInterceptorManager<AxiosInstance>;
  private authenticationHeaders: Record<string, string>;

  constructor(baseUrl: string, interceptors: AxiosInterceptorManager<AxiosInstance>, authenticationHeaders: Record<string, string>) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.interceptors = this.axiosInstance.interceptors;
    this.authenticationHeaders = authenticationHeaders;
  }

  setAuthenticationHeaders(headers: Record<string, string>) {
    this.authenticationHeaders = headers;
    this.interceptors.request.use(this.interceptRequestHandler, null, this);
  }

  private interceptRequestHandler(config: AxiosRequestConfig) {
    if (this.authenticationHeaders) {
      for (const key in this.authenticationHeaders) {
        if (this.authenticationHeaders.hasOwnProperty(key)) {
          config.headers[key] = this.authenticationHeaders[key];
        }
      }
    }
    return config;
  }

  async getPortfolio(portfolioId: string): Promise<any> {
    try {
      const response = await this.axiosInstance.get(`/api/portfolio/${portfolioId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching portfolio:', error);
      throw new ApiError(error.response?.status, error.message);
    }
  }

  async postRebalance(): Promise<any> {
    try {
      const response = await this.axiosInstance.post('/api/rebalance');
      return response.data;
    } catch (error: any) {
      console.error('Error rebalancing portfolio:', error);
      throw new ApiError(error.response?.status, error.message);
    }
  }

  async getAsset(assetId: string): Promise<any> {
    try {
      const response = await this.axiosInstance.get(`/api/asset/${assetId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching asset:', error);
      throw new ApiError(error.response?.status, error.message);
    }
  }
}

class ApiError extends Error {
  statusCode: number;
  message: string;

  constructor(statusCode: number, message: string) {
    super(message);
    this.statusCode = statusCode;
    this.message = message;
  }
}

export { ApiClient, ApiError };