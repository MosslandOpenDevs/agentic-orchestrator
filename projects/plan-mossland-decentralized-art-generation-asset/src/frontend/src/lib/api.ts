import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class NFTClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: { [key: string]: string };

  constructor(baseUrl: string, authHeaders: { [key: string]: string }) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authHeaders = authHeaders;
  }

  // Request Interceptor
  private addInterceptors = () => {
    this.axiosInstance.interceptors.request.use(
      (config) => {
        if (config.headers) {
          config.headers = {
            ...config.headers,
            ...this.authHeaders,
          };
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
  };

  // Response Interceptor
  private addResponseInterceptors = () => {
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response) {
          // Handle non-2xx responses
          if (error.response.status === 401) {
            throw new AuthenticationError('Unauthorized - Invalid credentials or token.');
          }
          if (error.response.status === 404) {
            throw new NotFoundError(`Resource not found: ${error.response.data.message || ''}`);
          }
          if (error.response.status === 500) {
            throw new ServerError('Internal Server Error');
          }
          throw new CustomError('Request failed', {
            status: error.response.status,
            data: error.response.data,
          });
        } else if (error.request) {
          // Handle network errors or other request issues
          throw new CustomError('Request failed', {
            status: 500,
            message: 'Network error or other request issue',
          });
        } else {
          // Handle unexpected errors
          throw new CustomError('Request failed', {
            status: 500,
            message: 'An unexpected error occurred',
          });
        }
      }
    );
  };

  async generateNFT(prompt: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post<BaseResponse<any>>('/api/generate-nft', { prompt });
      this.addResponseInterceptors();
      return response.data;
    } catch (error) {
      this.addResponseInterceptors();
      throw new CustomError('Failed to generate NFT', {
        error: error.message,
      });
    }
  }

  async getNFTMetadata(tokenId: string): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get<BaseResponse<any>>(`/api/nft/${tokenId}`);
      this.addResponseInterceptors();
      return response.data;
    } catch (error) {
      this.addResponseInterceptors();
      throw new CustomError('Failed to retrieve NFT metadata', {
        error: error.message,
      });
    }
  }

  async mintNFT(data: any): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.post<BaseResponse<any>>('/api/mint', data);
      this.addResponseInterceptors();
      return response.data;
    } catch (error) {
      this.addResponseInterceptors();
      throw new CustomError('Failed to mint NFT', {
        error: error.message,
      });
    }
  }

  async getUsers(): Promise<BaseResponse<any>> {
    try {
      const response = await this.axiosInstance.get<BaseResponse<any>>('/api/users');
      this.addResponseInterceptors();
      return response.data;
    } catch (error) {
      this.addResponseInterceptors();
      throw new CustomError('Failed to retrieve users', {
        error: error.message,
      });
    }
  }
}

interface AuthenticationError extends CustomError {
  message: string;
}

interface NotFoundError extends CustomError {
  message: string;
}

interface ServerError extends CustomError {
  message: string;
}

interface CustomError {
  message: string;
  status?: number;
  data?: any;
}

export default NFTClient;