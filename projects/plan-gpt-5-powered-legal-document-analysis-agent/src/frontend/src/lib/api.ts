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
          // Handle server errors
          return Promise.reject(
            new CustomError('API Error', 500, { message: error.response.data.message })
          );
        } else {
          // Handle network errors
          return Promise.reject(new CustomError('Network Error', 500, { message: error.message }));
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
      throw new CustomError('GET Error', 400, { message: error.message });
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
      throw new CustomError('POST Error', 400, { message: error.message });
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
      throw new CustomError('PUT Error', 400, { message: error.message });
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
      throw new CustomError('DELETE Error', 400, { message: error.message });
    }
  }
}

interface NFTValuationResponse {
  valuation: number;
}

interface PortfolioHoldingsResponse {
  holdings: any[];
}

interface RiskAssessmentResponse {
  riskScore: number;
  riskCategory: string;
}

class NFTClient extends ApiClient {
  constructor() {
    super('/api/nft');
  }

  async valuation(nftId: string): Promise<NFTValuationResponse> {
    return this.get<NFTValuationResponse>(`valuation/${nftId}`);
  }
}

class PortfolioClient extends ApiClient {
  constructor() {
    super('/api/portfolio');
  }

  async holdings(userId: string): Promise<PortfolioHoldingsResponse> {
    return this.get<PortfolioHoldingsResponse>(`holdings/${userId}`);
  }
}

class RiskClient extends ApiClient {
  constructor() {
    super('/api/nft/risk');
  }

  async risk(nftId: string): Promise<RiskAssessmentResponse> {
    return this.get<RiskAssessmentResponse>(`risk/${nftId}`);
  }
}

export { NFTClient, PortfolioClient, RiskClient, CustomError, BaseResponse };