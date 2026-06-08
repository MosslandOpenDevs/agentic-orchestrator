import axios from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class PortfolioClient {
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
  }

  async getPortfolio(portfolioId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/portfolio/${portfolioId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error('Error fetching portfolio:', error);
      return {
        data: null,
        success: false,
        error: error.message || 'Failed to fetch portfolio',
      };
    }
  }

  async createPortfolio(portfolioData: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/portfolio/create', portfolioData);
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

  async getAssetPrice(assetId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/asset/price/${assetId}`);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error('Error fetching asset price:', error);
      return {
        data: null,
        success: false,
        error: error.message || 'Failed to fetch asset price',
      };
    }
  }
}

class UserAuthClient {
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
  }

  async authenticate(userData: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/user/auth', userData);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error: any) {
      console.error('Error authenticating user:', error);
      return {
        data: null,
        success: false,
        error: error.message || 'Failed to authenticate user',
      };
    }
  }
}

export { PortfolioClient, UserAuthClient };