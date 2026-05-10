import axios, { AxiosResponse, AxiosError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class NFTClient {
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
          // Handle HTTP errors (4xx, 5xx)
          const errorMessage = error.response.data?.message || error.response.statusText;
          return Promise.reject({
            ...error,
            data: { message: errorMessage },
          });
        } else {
          // Handle non-HTTP errors (e.g., network errors)
          return Promise.reject(error);
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
    } catch (error) {
      console.error('Error fetching portfolio:', error);
      throw error;
    }
  }

  async getMarketData(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/nft/marketdata/${tokenId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      console.error('Error fetching market data:', error);
      throw error;
    }
  }

  async predict(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/gpt5/predict', { tokenId });
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      console.error('Error predicting:', error);
      throw error;
    }
  }

  async getMetadata(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/nft/metadata/${tokenId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      console.error('Error fetching metadata:', error);
      throw error;
    }
  }
}

export default NFTClient;