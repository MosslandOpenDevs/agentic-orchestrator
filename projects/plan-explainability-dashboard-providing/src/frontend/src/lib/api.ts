import axios, { AxiosResponse, AxiosError } from 'axios';

interface BaseResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

class ApiClient {
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

    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Add authentication headers here if needed
        // Example: config.headers['Authorization'] = 'Bearer ' + token;
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.axiosInstance.interceptors.response.use(
      (response) => {
        return response as BaseResponse<any>;
      },
      (error) => {
        if (error.response) {
          return Promise.reject(
            new CustomError('API Error', 400, { message: error.response.data.message })
          );
        } else {
          return Promise.reject(new CustomError('Network Error', 500, { message: error.message }));
        }
      }
    );
  }

  async get<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.get(endpoint);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      throw new CustomError('GET Error', 400, { message: 'Failed to fetch data' });
    }
  }

  async post<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.post(endpoint, data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      throw new CustomError('POST Error', 400, { message: 'Failed to submit data' });
    }
  }

  async put<T>(endpoint: string, data: any): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.put(endpoint, data);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      throw new CustomError('PUT Error', 400, { message: 'Failed to update data' });
    }
  }

  async delete<T>(endpoint: string): Promise<BaseResponse<T>> {
    try {
      const response = await this.axiosInstance.delete(endpoint);
      return {
        data: response.data,
        success: true,
        error: undefined,
      };
    } catch (error) {
      throw new CustomError('DELETE Error', 400, { message: 'Failed to delete data' });
    }
  }

  // Example Endpoints
  async getNftCollections(): Promise<BaseResponse<any>> {
    return this.get('/api/nftCollections');
  }

  async getNftTransactions(portfolioId: string): Promise<BaseResponse<any>> {
    return this.get(`/api/nftTransactions?portfolioId=${portfolioId}`);
  }

  async riskAssessment(portfolioData: any): Promise<BaseResponse<any>> {
    return this.post('/api/riskAssessment', portfolioData);
  }

  async getNftPriceData(): Promise<BaseResponse<any>> {
    return this.get('/api/nftPriceData');
  }
}

class CustomError extends Error {
  constructor(message: string, statusCode: number, details?: any) {
    super(message);
    this.statusCode = statusCode;
    this.details = details;
  }
}

export default ApiClient;