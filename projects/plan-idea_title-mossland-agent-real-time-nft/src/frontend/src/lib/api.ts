import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface BaseResponse<T> extends AxiosResponse {
  data: T;
}

interface CustomError extends Error {
  code?: number;
  message?: string;
  data?: any;
}

interface Portfolio {
  id: string;
  name: string;
}

interface NftCollection {
  id: string;
  name: string;
  description: string;
  imageUrl: string;
}

interface Transaction {
  id: string;
  nftId: string;
  quantity: number;
  price: number;
  timestamp: string;
}

interface RiskAssessmentResponse {
  riskLevel: string;
  recommendations: string;
}

interface PriceData {
  symbol: string;
  price: number;
  lastUpdated: string;
}

interface ApiClient {
  /**
   * Retrieves a list of NFT collections.
   * @returns A Promise resolving to an array of NftCollection objects.
   */
  getNftCollections(): Promise<NftCollection[]>;

  /**
   * Retrieves NFT transactions for a specific portfolio.
   * @param portfolioId The ID of the portfolio.
   * @returns A Promise resolving to an array of Transaction objects.
   */
  getNftTransactions(portfolioId: string): Promise<Transaction[]>;

  /**
   * Generates a risk assessment for a portfolio using GPT-5.
   * @param portfolioId The ID of the portfolio.
   * @returns A Promise resolving to a RiskAssessmentResponse object.
   */
  generateRiskAssessment(portfolioId: string): Promise<RiskAssessmentResponse>;

  /**
   * Retrieves price data for a given cryptocurrency symbol.
   * @param symbol The cryptocurrency symbol.
   * @returns A Promise resolving to a PriceData object.
   */
  getPriceData(symbol: string): Promise<PriceData>;
}

class ApiClientImpl implements ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;

  constructor(axios: AxiosInstance, baseUrl: string) {
    this.axiosInstance = axios;
    this.baseUrl = baseUrl;
  }

  async getNftCollections(): Promise<NftCollection[]> {
    const response = await this.axiosInstance.get<NftCollection[]>('/api/nftCollections');
    return response.data;
  }

  async getNftTransactions(portfolioId: string): Promise<Transaction[]> {
    const response = await this.axiosInstance.get<Transaction[]>(`/api/nftTransactions/${portfolioId}`);
    return response.data;
  }

  async generateRiskAssessment(portfolioId: string): Promise<RiskAssessmentResponse> {
    const response = await this.axiosInstance.get<RiskAssessmentResponse>(`/api/riskAssessment/${portfolioId}`);
    return response.data;
  }

  async getPriceData(symbol: string): Promise<PriceData> {
    const response = await this.axiosInstance.get<PriceData>(`/api/priceData/${symbol}`);
    return response.data;
  }
}

export default ApiClient;