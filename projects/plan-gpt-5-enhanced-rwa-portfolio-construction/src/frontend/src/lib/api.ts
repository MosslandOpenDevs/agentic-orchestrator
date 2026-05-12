import axios, { AxiosInstance, AxiosInterceptorManager, AxiosResponse, AxiosError } from 'axios';

interface RwaAsset {
  id: string;
  name: string;
  quantity: number;
  // Add other asset properties as needed
}

interface Price {
  asset: string;
  price: number;
}

interface RebalanceRequest {
  riskTolerance: 'low' | 'medium' | 'high';
  // Add other rebalance parameters as needed
}

interface Gpt5AnalysisRequest {
  rwaData: {
    assets: RwaAsset[];
    prices: Price[];
  };
}

interface Gpt5AnalysisResponse {
  analysis: string;
}

interface CustomError {
  statusCode: number;
  message: string;
  error?: any;
}

export class RwaApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private interceptors: AxiosInterceptorManager<AxiosInstance>;

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

  // Request Interceptors
  use(fn: (id: number, config: any) => void): this {
    this.interceptors.request.use(fn);
    return this;
  }

  // Response Interceptors
  onResponseErrorHandler(fn: (err: AxiosError) => void): this {
    this.interceptors.response.use(null, fn);
    return this;
  }

  // Helper function to handle errors
  async handleResponse<T>(response: Response): Promise<T> {
    return await response.json() as Promise<T>;
  }

  async getRwaAssets(): Promise<RwaAsset[]> {
    try {
      const response = await this.axiosInstance.get<RwaAsset[]>('/api/rwa/assets');
      return response.data;
    } catch (error) {
      console.error('Error fetching RWA assets:', error);
      throw new CustomError(500, 'Failed to fetch RWA assets');
    }
  }

  async getRwaPrices(): Promise<Price[]> {
    try {
      const response = await this.axiosInstance.get<Price[]>('/api/rwa/prices');
      return response.data;
    } catch (error) {
      console.error('Error fetching RWA prices:', error);
      throw new CustomError(500, 'Failed to fetch RWA prices');
    }
  }

  async rebalance(request: RebalanceRequest): Promise<any> {
    try {
      const response = await this.axiosInstance.post<any>('/api/rwa/rebalance', request);
      return response.data;
    } catch (error) {
      console.error('Error rebalancing:', error);
      throw new CustomError(500, 'Failed to rebalance');
    }
  }

  async analyzeRwaData(data: Gpt5AnalysisRequest): Promise<Gpt5AnalysisResponse> {
    try {
      const response = await this.axiosInstance.post<Gpt5AnalysisResponse>('/api/gpt5/analyze', data);
      return response.data;
    } catch (error) {
      console.error('Error analyzing RWA data:', error);
      throw new CustomError(500, 'Failed to analyze RWA data');
    }
  }
}