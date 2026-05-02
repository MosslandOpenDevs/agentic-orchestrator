import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class NFTClient {
  private readonly axiosInstance: AxiosInstance;
  private readonly baseUrl: string;
  private readonly authHeaders: { [key: string]: string };

  constructor(
    baseUrl: string,
    authHeaders: { [key: string]: string } = {}
  ) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
    });

    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Add authentication headers here if not already present
        if (config.headers && this.authHeaders) {
          for (const key in this.authHeaders) {
            if (!config.headers[key]) {
              config.headers[key] = this.authHeaders[key];
            }
          }
        }
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );
  }

  async generateNFT(prompt: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/generate-nft', { prompt });
      return { data: response.data, success: true };
    } catch (error: any) {
      console.error('Generate NFT error:', error);
      if (error.response) {
        return { data: undefined, success: false, error: error.response.data.error || error.response.statusText };
      }
      return { data: undefined, success: false, error: 'Failed to generate NFT' };
    }
  }

  async getNFTMetadata(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/nft/${tokenId}`);
      return { data: response.data, success: true };
    } catch (error: any) {
      console.error('Get NFT metadata error:', error);
      if (error.response) {
        return { data: undefined, success: false, error: error.response.data.error || error.response.statusText };
      }
      return { data: undefined, success: false, error: 'Failed to retrieve NFT metadata' };
    }
  }

  async mintNFT(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post('/api/mint', { tokenId });
      return { data: response.data, success: true };
    } catch (error: any) {
      console.error('Mint NFT error:', error);
      if (error.response) {
        return { data: undefined, success: false, error: error.response.data.error || error.response.statusText };
      }
      return { data: undefined, success: false, error: 'Failed to mint NFT' };
    }
  }
}

export default NFTClient;