import axios, { AxiosInstance, AxiosInterceptorManager, AxiosRequestConfig, Canceled } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class EnsApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private interceptors: AxiosInterceptorManager<AxiosInstance>;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.interceptors = this.axiosInstance.interceptors;
  }

  // Request Interceptors
  use(fn: (id: number, config: any) => void): this {
    this.interceptors.request.use(fn);
    return this;
  }

  // Response Interceptors
  onResponse<T>(fn: (response: Response) => void): this {
    this.interceptors.response.use(fn);
    return this;
  }

  // Error Interceptors
  onCancel<T>(fn: (error: Canceled) => void): this {
    this.interceptors.response.use(null, fn);
    return this;
  }

  // Helper function to handle responses
  private handleResponse<T>(response: Response): BaseResponse<T> {
    try {
      const data = response.data;
      if (response.status >= 200 && response.status < 300) {
        return { data, success: true, error: undefined };
      } else {
        return { data: undefined, success: false, error: response.statusText };
      }
    } catch (error) {
      return { data: undefined, success: false, error: error instanceof Error ? error.message : String(error) };
    }
  }

  // GET /api/ens/domains/{domainId}
  async getDomain(domainId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/ens/domains/${domainId}`);
      return this.handleResponse(response);
    } catch (error) {
      console.error("Error fetching domain:", error);
      throw new Error(`Failed to fetch domain: ${error}`);
    }
  }

  // POST /api/nft/mint
  async mintNFT(domainId: string, data: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post(`/api/nft/mint`, data);
      return this.handleResponse(response);
    } catch (error) {
      console.error("Error minting NFT:", error);
      throw new Error(`Failed to mint NFT: ${error}`);
    }
  }

  // GET /api/nft/{nftId}
  async getNFT(nftId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/nft/${nftId}`);
      return this.handleResponse(response);
    } catch (error) {
      console.error("Error fetching NFT:", error);
      throw new Error(`Failed to fetch NFT: ${error}`);
    }
  }

  // GET /api/users/{userId}
  async getUser(userId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get(`/api/users/${userId}`);
      return this.handleResponse(response);
    } catch (error) {
      console.error("Error fetching user:", error);
      throw new Error(`Failed to fetch user: ${error}`);
    }
  }
}

export default EnsApiClient;