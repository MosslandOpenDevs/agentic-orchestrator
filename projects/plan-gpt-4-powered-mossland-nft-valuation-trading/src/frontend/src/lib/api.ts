import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface BaseError {
  statusCode: number;
  message: string;
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authHeaders: Record<string, string>;

  constructor(baseUrl: string, authHeaders: Record<string, string>) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authHeaders = authHeaders;
  }

  public setAuthHeaders = (headers: Record<string, string>) => {
    this.authHeaders = headers;
  }

  // Request Interceptors
  private addInterceptors = (onSuccess: (response: AxiosResponse) => void, onError: (error: Error) => void) => {
    this.axiosInstance.interceptors.request.use(
      (config) => {
        if (this.authHeaders) {
          for (const key in this.authHeaders) {
            if (this.authHeaders.hasOwnProperty(key)) {
              (config.headers as any)[key] = this.authHeaders[key];
            }
          }
        }
        return config;
      },
      (error) => {
        onError(error);
        return Promise.reject(error);
      }
    );

    this.axiosInstance.interceptors.response.use(
      (response) => {
        onSuccess(response);
        return response;
      },
      (error) => {
        console.error("Axios Error:", error);
        throw error;
      }
    );
  }

  // Generic Error Type
  public handleErrors = (response: AxiosResponse) => {
    if (response.status < 200 || response.status >= 300) {
      throw new Error(`HTTP error! Status: ${response.status}, Response: ${response.data}`);
    }
    return response;
  };

  // User API
  public getUsers = async (userId: string): Promise<any> => {
    try {
      const response = await this.axiosInstance.get(`/api/users/${userId}`);
      return this.handleErrors(response);
    } catch (error) {
      console.error("Error fetching user:", error);
      throw new Error(`Failed to fetch user: ${error}`);
    }
  };

  // Portfolio API
  public getPortfolios = async (portfolioId: string): Promise<any> => {
    try {
      const response = await this.axiosInstance.get(`/api/portfolios/${portfolioId}`);
      return this.handleErrors(response);
    } catch (error) {
      console.error("Error fetching portfolio:", error);
      throw new Error(`Failed to fetch portfolio: ${error}`);
    }
  };

  // Asset API
  public getAssetPrice = async (assetId: string): Promise<any> => {
    try {
      const response = await this.axiosInstance.get(`/api/assets/${assetId}/price`);
      return this.handleErrors(response);
    } catch (error) {
      console.error("Error fetching asset price:", error);
      throw new Error(`Failed to fetch asset price: ${error}`);
    }
  };

  // User Authentication API
  public authenticateUser = async (
    username: string,
    signature: string
  ): Promise<any> => {
    try {
      const response = await this.axiosInstance.post('/api/users/auth', {
        username,
        signature,
      });
      return this.handleErrors(response);
    } catch (error) {
      console.error("Error authenticating user:", error);
      throw new Error(`Failed to authenticate user: ${error}`);
    }
  };
}

export default ApiClient;