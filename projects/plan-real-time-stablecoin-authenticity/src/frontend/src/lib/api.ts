import axios, { AxiosInstance, AxiosInterceptorManager, AxiosResponse } from 'axios';

interface BaseResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class StablecoinClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private interceptors: AxiosInterceptorManager<AxiosResponse>;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.interceptors = this.axiosInstance.interceptors;
  }

  public addInterceptor(interceptor: (config: any) => void) {
    this.interceptors.request.use(interceptor);
  }

  public removeInterceptor(interceptor: (config: any) => void) {
    this.interceptors.request.remove()(interceptor);
  }

  public async getRiskScore(stablecoinId: string): Promise<BaseResponse> {
    try {
      const response = await this.axiosInstance.get(`/api/stablecoin/risk/${stablecoinId}`);
      return {
        success: true,
        data: response.data,
        error: undefined,
      };
    } catch (error: any) {
      console.error('Error fetching risk score:', error);
      return {
        success: false,
        data: undefined,
        error: error.message || 'Failed to fetch risk score',
      };
    }
  }

  public async analyzeTransaction(transactionData: any): Promise<BaseResponse> {
    try {
      const response = await this.axiosInstance.post('/api/transaction/analyze', transactionData);
      return {
        success: true,
        data: response.data,
        error: undefined,
      };
    } catch (error: any) {
      console.error('Error analyzing transaction:', error);
      return {
        success: false,
        data: undefined,
        error: error.message || 'Failed to analyze transaction',
      };
    }
  }
}

interface CustomError {
  code: number;
  message: string;
}

export { StablecoinClient, CustomError };