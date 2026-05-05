import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface ApiError {
  statusCode: number;
  message: string;
  error?: any;
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
      this.addToHeaders,
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );
  }

  private addToHeaders = (config: AxiosRequestConfig) => {
    if (this.authHeaders) {
      for (const key in this.authHeaders) {
        if (this.authHeaders.hasOwnProperty(key)) {
          config.headers[key] = this.authHeaders[key];
        }
      }
    }
    return config;
  };

  async getPortfolioFractions(portfolioId: string): Promise<any> {
    try {
      const response = await this.axiosInstance.get(`/api/nftfraction/portfolio/${portfolioId}`);
      return response.data;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error("Axios Error:", error);
        throw new ApiError(error.response?.status, error.response?.data?.message || error.message, error.response);
      } else {
        throw new ApiError(500, 'Internal Server Error', error);
      }
    }
  }

  async createPortfolio(name: string): Promise<any> {
    try {
      const response = await this.axiosInstance.post('/api/portfolio/create', { name });
      return response.data;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error("Axios Error:", error);
        throw new ApiError(error.response?.status, error.response?.data?.message || error.message, error.response);
      } else {
        throw new ApiError(500, 'Internal Server Error', error);
      }
    }
  }

  async getAssetPrice(asset: string): Promise<any> {
    try {
      const response = await this.axiosInstance.get(`/api/nftfraction/price/${asset}`);
      return response.data;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error("Axios Error:", error);
        throw new ApiError(error.response?.status, error.response?.data?.message || error.message, error.response);
      } else {
        throw new ApiError(500, 'Internal Server Error', error);
      }
    }
  }

  async triggerAiValuation(portfolioId: string): Promise<any> {
    try {
      const response = await this.axiosInstance.post('/api/ai/valuation', { portfolioId });
      return response.data;
    } catch (error: any) {
      if (error instanceof axios.AxiosError) {
        console.error("Axios Error:", error);
        throw new ApiError(error.response?.status, error.response?.data?.message || error.message, error.response);
      } else {
        throw new ApiError(500, 'Internal Server Error', error);
      }
    }
  }
}

export default ApiClient;