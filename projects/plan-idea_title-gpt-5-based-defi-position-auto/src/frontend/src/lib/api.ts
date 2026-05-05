import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface BaseResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class PortfolioClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: Record<string, string>;

  constructor(
    baseUrl: string,
    authHeaders: Record<string, string> = {}
  ) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.authHeaders = authHeaders;
  }

  async getPortfolio(portfolioId: string): Promise<BaseResponse> {
    try {
      const response = await this.axiosInstance.get(`/api/portfolio/${portfolioId}`);
      return {
        success: true,
        data: response.data,
        error: null,
      };
    } catch (error: any) {
      console.error('Error fetching portfolio:', error);
      return {
        success: false,
        data: null,
        error: error.message || 'Unknown error',
      };
    }
  }

  async postRebalance(portfolioId: string): Promise<BaseResponse> {
    try {
      const response = await this.axiosInstance.post(`/api/rebalance/${portfolioId}`, {
        // Add request body here if needed
      });
      return {
        success: true,
        data: response.data,
        error: null,
      };
    } catch (error: any) {
      console.error('Error rebalancing portfolio:', error);
      return {
        success: false,
        data: null,
        error: error.message || 'Unknown error',
      };
    }
  }

  async getAssetPrice(assetAddress: string): Promise<BaseResponse> {
    try {
      const response = await this.axiosInstance.get(`/api/asset_price/${assetAddress}`);
      return {
        success: true,
        data: response.data,
        error: null,
      };
    } catch (error: any) {
      console.error('Error fetching asset price:', error);
      return {
        success: false,
        data: null,
        error: error.message || 'Unknown error',
      };
    }
  }
}

interface CustomError {
  statusCode: number;
  message: string;
}

export class ApiClient {
  private portfolioClient: PortfolioClient;

  constructor(baseUrl: string, authHeaders: Record<string, string>) {
    this.portfolioClient = new PortfolioClient(baseUrl, authHeaders);
  }

  getPortfolio(portfolioId: string): Promise<BaseResponse> {
    return this.portfolioClient.getPortfolio(portfolioId);
  }

  postRebalance(portfolioId: string): Promise<BaseResponse> {
    return this.portfolioClient.postRebalance(portfolioId);
  }

  getAssetPrice(assetAddress: string): Promise<BaseResponse> {
    return this.portfolioClient.getAssetPrice(assetAddress);
  }
}