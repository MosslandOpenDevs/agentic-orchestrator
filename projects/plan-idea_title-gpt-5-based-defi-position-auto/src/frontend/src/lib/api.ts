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
      this.handleErrorInterceptors
    );
  }

  private async handleRequestInterceptors(config: AxiosRequestConfig): Promise<AxiosRequestConfig> {
    // Add authentication headers
    if (this.authHeaders) {
      for (const key in this.authHeaders) {
        if (this.authHeaders.hasOwnProperty(key)) {
          config.headers[key] = this.authHeaders[key];
        }
      }
    }
    return config;
  }

  private async handleErrorInterceptors(error: CanceledError | AxiosError): Promise<AxiosError> {
    // Handle errors here (e.g., logging, retries)
    console.error("Axios Error:", error);
    return Promise.reject(error as AxiosError);
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
      console.error("Error fetching data:", error);
      return {
        data: null,
        success: false,
        error: error instanceof Error ? error.message : String(error),
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
    } catch (error) {
      console.error("Error posting data:", error);
      return {
        data: null,
        success: false,
        error: error instanceof Error ? error.message : String(error),
      } as BaseResponse<T>;
    }
  }

  // Placeholder for rebalance endpoint - implement as needed
  async rebalance(): Promise<BaseResponse<any>> {
    return this.post('/api/rebalance', {});
  }

  // Placeholder for gpt5/analyze endpoint - implement as needed
  async analyze(data: any): Promise<BaseResponse<any>> {
    return this.post('/api/gpt5/analyze', data);
  }
}

export default ApiClient;