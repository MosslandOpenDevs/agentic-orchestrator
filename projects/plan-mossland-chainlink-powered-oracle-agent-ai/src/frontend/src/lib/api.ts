import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class PortfolioApiClient {
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
      interceptors: {
        request: [
          (config) => {
            if (this.authHeaders) {
              for (const key in this.authHeaders) {
                if (this.authHeaders.hasOwnProperty(key)) {
                  config.headers[key] = this.authHeaders[key];
                }
              }
            }
            return config;
          },
        ],
        response: [
          (response) => {
            if (response.status >= 400) {
              throw new Error(`Request failed with status ${response.status}`);
            }
            return response;
          },
        ],
      },
    });
  }

  async getPortfolios(): Promise<BaseResponse<Portfolio[]> | Error> {
    try {
      const response = await this.axiosInstance.get('/api/portfolios');
      return { data: response.data as Portfolio[], success: true };
    } catch (error) {
      if (error instanceof Error && error.response) {
        return error;
      }
      return error as Error;
    }
  }

  async createPortfolio(portfolio: Portfolio): Promise<Portfolio | Error> {
    try {
      const response = await this.axiosInstance.post('/api/portfolios', portfolio);
      return response.data as Portfolio;
    } catch (error) {
      if (error instanceof Error && error.response) {
        return error;
      }
      return error as Error;
    }
  }

  async getAssets(portfolioId: string): Promise<Asset[] | Error> {
    try {
      const response = await this.axiosInstance.get(`/api/assets/${portfolioId}`);
      return response.data as Asset[];
    } catch (error) {
      if (error instanceof Error && error.response) {
        return error;
      }
      return error as Error;
    }
  }

  async getChainlinkData(assetType: string): Promise<ChainlinkData | Error> {
    try {
      const response = await this.axiosInstance.get(`/api/chainlinkData/${assetType}`);
      return response.data as ChainlinkData;
    } catch (error) {
      if (error instanceof Error && error.response) {
        return error;
      }
      return error as Error;
    }
  }

  async generateStrategy(strategyRequest: StrategyRequest): Promise<Strategy | Error> {
    try {
      const response = await this.axiosInstance.post('/api/strategies', strategyRequest);
      return response.data as Strategy;
    } catch (error) {
      if (error instanceof Error && error.response) {
        return error;
      }
      return error as Error;
    }
  }
}

interface Portfolio {
  id: string;
  name: string;
  // Add other portfolio properties here
}

interface Asset {
  id: string;
  name: string;
  portfolioId: string;
  // Add other asset properties here
}

interface ChainlinkData {
  assetType: string;
  price: number;
  // Add other chainlink data properties here
}

interface StrategyRequest {
  // Define the structure of the strategy request object
  prompt: string;
}

interface Strategy {
  // Define the structure of the strategy object
  id: string;
  name: string;
  // Add other strategy properties here
}

export default PortfolioApiClient;