import axios, { AxiosResponse, AxiosError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class NftApi {
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
          return Promise.reject(new ApiError(500, 'Network Error'));
        }
      }
    );
  }

  async getPortfolio(): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get('/api/nft/portfolio');
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      throw new ApiError(error.response?.status || 500, error.response?.data?.message || 'Error fetching portfolio');
    }
  }

  async rebalancePortfolio(data: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/portfolio/rebalance', data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      throw new ApiError(error.response?.status || 500, error.response?.data?.message || 'Error rebalancing portfolio');
    }
  }

  async getPrediction(nftId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/nft/prediction/${nftId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      throw new ApiError(error.response?.status || 500, error.response?.data?.message || 'Error fetching prediction');
    }
  }

  async getMarketData(): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get('/api/marketdata');
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      throw new ApiError(error.response?.status || 500, error.response?.data?.message || 'Error fetching market data');
    }
  }
}

class ApiError extends Error {
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export default NftApi;