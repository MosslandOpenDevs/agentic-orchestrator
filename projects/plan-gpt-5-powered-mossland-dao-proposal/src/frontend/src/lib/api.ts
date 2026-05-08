import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface BaseResponse<T> extends AxiosResponse {
  data: T;
}

interface CustomError extends Error {
  code?: number;
  message?: string;
  details?: any;
}

interface NftPriceResponse {
  price: number;
}

interface NftDataResponse {
  id: string;
  name: string;
  description: string;
  image: string;
  attributes: any[];
}

interface RiskAssessmentRequest {
  portfolio: {
    assets: string[];
    amounts: number[];
  };
}

interface RiskAssessmentResponse {
  riskScore: number;
  recommendations: string[];
}

interface GPTGenerateRequest {
  prompt: string;
  maxTokens?: number;
}

interface GPTGenerateResponse {
  text: string;
}

interface ApiClient {
  /**
   * Retrieves the current price of an NFT.
   * @param tokenId The ID of the NFT.
   * @returns A promise that resolves to the NFT price.
   * @throws {CustomError} If the request fails.
   */
  getNftPrice(tokenId: string): Promise<NftPriceResponse>;

  /**
   * Retrieves NFT metadata.
   * @returns A promise that resolves to the NFT metadata.
   * @throws {CustomError} If the request fails.
   */
  getNftData(): Promise<NftDataResponse>;

  /**
   * Generates a risk assessment for a portfolio.
   * @param request The portfolio data.
   * @returns A promise that resolves to the risk assessment response.
   * @throws {CustomError} If the request fails.
   */
  postRiskAssessment(request: RiskAssessmentRequest): Promise<RiskAssessmentResponse>;

  /**
   * Calls the GPT-5 API for smart contract generation or other tasks.
   * @param request The GPT generation request.
   * @returns A promise that resolves to the GPT generation response.
   * @throws {CustomError} If the request fails.
   */
  getGptGenerate(request: GPTGenerateRequest): Promise<GPTGenerateResponse>;
}

class ApiClientImpl implements ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: { [key: string]: string };

  constructor(
    baseUrl: string,
    authHeaders: { [key: string]: string } = {}
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

  async getNftPrice(tokenId: string): Promise<NftPriceResponse> {
    try {
      const response = await this.axiosInstance.get(`/api/nft/price?tokenId=${tokenId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching NFT price:', error);
      throw new CustomError({
        code: error.response?.status || 500,
        message: error.response?.data?.message || 'Failed to fetch NFT price',
        details: error.response?.data,
      });
    }
  }

  async getNftData(): Promise<NftDataResponse> {
    try {
      const response = await this.axiosInstance.get('/api/nft/data');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching NFT data:', error);
      throw new CustomError({
        code: error.response?.status || 500,
        message: error.response?.data?.message || 'Failed to fetch NFT data',
        details: error.response?.data,
      });
    }
  }

  async postRiskAssessment(request: RiskAssessmentRequest): Promise<RiskAssessmentResponse> {
    try {
      const response = await this.axiosInstance.post('/api/risk/assessment', request);
      return response.data;
    } catch (error: any) {
      console.error('Error generating risk assessment:', error);
      throw new CustomError({
        code: error.response?.status || 500,
        message: error.response?.data?.message || 'Failed to generate risk assessment',
        details: error.response?.data,
      });
    }
  }

  async getGptGenerate(request: GPTGenerateRequest): Promise<GPTGenerateResponse> {
    try {
      const response = await this.axiosInstance.post('/api/gpt/generate', request);
      return response.data;
    } catch (error: any) {
      console.error('Error generating GPT response:', error);
      throw new CustomError({
        code: error.response?.status || 500,
        message: error.response?.data?.message || 'Failed to generate GPT response',
        details: error.response?.data,
      });
    }
  }
}

export default ApiClient;