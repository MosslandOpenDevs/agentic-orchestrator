import axios, { AxiosResponse, AxiosError } from 'axios';

interface BaseResponse<T> extends AxiosResponse {
  data: T;
}

interface CustomError extends AxiosError {
  statusCode?: number;
  message?: string;
}

interface PortfolioRebalanceRequest {
  strategy?: string;
  tolerance?: number;
}

interface PortfolioRebalanceResponse {
  status: 'success' | 'error';
  message: string;
  data?: any; // Adjust type based on actual response
}

interface SimulationResult {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  portfolioValue: number;
  metrics: any;
}

interface RwaPrice {
  assetId: string;
  price: number;
}

interface Portfolio {
  id: string;
  assets: any[];
}

interface PortfolioSimulationResults {
  results: SimulationResult[];
}

interface ApiClient {
  /**
   * Retrieves the current price of an RWA asset.
   * @param assetId The ID of the RWA asset.
   * @returns A Promise that resolves to the RWA price.
   * @throws A CustomError if the request fails.
   */
  getRwaPrice(assetId: string): Promise<RwaPrice>;

  /**
   * Initiates the rebalancing of the portfolio based on the GPT-5 agent's recommendations.
   * @param request The rebalancing request.
   * @returns A Promise that resolves to the rebalancing response.
   * @throws A CustomError if the request fails.
   */
  postPortfolioRebalance(request: PortfolioRebalanceRequest): Promise<PortfolioRebalanceResponse>;

  /**
   * Retrieves portfolio simulation results.
   * @returns A Promise that resolves to the simulation results.
   * @throws A CustomError if the request fails.
   */
  getSimulationResults(): Promise<PortfolioSimulationResults>;
}

class ApiClientImpl implements ApiClient {
  private baseUrl: string;
  private axiosInstance: any;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        // Add authentication headers here if needed
        // 'Authorization': 'Bearer <token>'
      },
      interceptors: {
        request: [
          (config) => {
            // Add request interceptors here
            return config;
          }
        ],
        response: [
          (response) => {
            // Add response interceptors here
            return response;
          },
          (error) => {
            // Handle specific error cases here
            if (error.response) {
              // Handle non-successful responses
              console.error('API Error:', error.response.data, error.response.status, error.response.headers);
            }
            return error;
          }
        ]
      }
    });
  }

  async getRwaPrice(assetId: string): Promise<RwaPrice> {
    try {
      const response = await this.axiosInstance.get(`/api/rwa/price?assetId=${assetId}`);
      return response.data as RwaPrice;
    } catch (error: any) {
      throw new CustomError(error);
    }
  }

  async postPortfolioRebalance(request: PortfolioRebalanceRequest): Promise<PortfolioRebalanceResponse> {
    try {
      const response = await this.axiosInstance.post('/api/portfolio/rebalance', request);
      return response.data as PortfolioRebalanceResponse;
    } catch (error: any) {
      throw new CustomError(error);
    }
  }

  async getSimulationResults(): Promise<PortfolioSimulationResults> {
    try {
      const response = await this.axiosInstance.get('/api/simulation/results');
      return response.data as PortfolioSimulationResults;
    } catch (error: any) {
      throw new CustomError(error);
    }
  }
}

export default ApiClient;