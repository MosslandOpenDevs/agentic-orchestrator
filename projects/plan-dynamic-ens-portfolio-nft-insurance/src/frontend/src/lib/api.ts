import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class NftApi {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaderKey: string;

  constructor(baseUrl: string, authHeaderKey: string) {
    this.baseUrl = baseUrl;
    this.authHeaderKey = authHeaderKey;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(this.authHeaderKey);
        if (token) {
          config.headers[this.authHeaderKey] = token;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
  }

  async getNftholders(): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get('/api/nftholders');
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error('Error fetching NFT holders:', error);
      return {
        data: null,
        success: false,
        error: error.message || 'Failed to fetch NFT holders',
      };
    }
  }

  async getNftholder(userId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/nftholders/${userId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error(`Error fetching NFT holder with ID ${userId}:`, error);
      return {
        data: null,
        success: false,
        error: error.message || `Failed to fetch NFT holder with ID ${userId}`,
      };
    }
  }

  async getNft(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/nft/${tokenId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error(`Error fetching NFT with ID ${tokenId}:`, error);
      return {
        data: null,
        success: false,
        error: error.message || `Failed to fetch NFT with ID ${tokenId}`,
      };
    }
  }

  async getPortfolios(userId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/portfolios/${userId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error(`Error fetching portfolios for user ID ${userId}:`, error);
      return {
        data: null,
        success: false,
        error: error.message || `Failed to fetch portfolios for user ID ${userId}`,
      };
    }
  }

  async createPortfolio(portfolioData: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/portfolios', portfolioData);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error('Error creating portfolio:', error);
      return {
        data: null,
        success: false,
        error: error.message || 'Failed to create portfolio',
      };
    }
  }

  async getValuations(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/valuations/${tokenId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error(`Error fetching valuations for NFT ID ${tokenId}:`, error);
      return {
        data: null,
        success: false,
        error: error.message || `Failed to fetch valuations for NFT ID ${tokenId}`,
      };
    }
  }
}

export default NftApi;