import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface BaseResponse<T> extends AxiosResponse {
  data: T;
}

interface User {
  id: number;
  username: string;
  email: string;
  // Add other user fields here
}

interface Portfolio {
  id: number;
  name: string;
  // Add other portfolio fields here
}

interface AssetPrice {
  asset_id: string;
  price: number;
  // Add other price data fields here
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

  public setAuthHeaders(headers: Record<string, string>) {
    this.authHeaders = headers;
  }

  public async getUsers(userId: number): Promise<User[]> {
    try {
      const response = await this.axiosInstance.get(`/api/users/${userId}`);
      return response.data as User[];
    } catch (error) {
      console.error('Error fetching users:', error);
      throw new ApiError('Failed to fetch users', 500, error);
    }
  }

  public async getPortfolios(portfolioId: number): Promise<Portfolio[]> {
    try {
      const response = await this.axiosInstance.get(`/api/portfolios/${portfolioId}`);
      return response.data as Portfolio[];
    } catch (error) {
      console.error('Error fetching portfolios:', error);
      throw new ApiError('Failed to fetch portfolios', 500, error);
    }
  }

  public async getAssetPrice(assetId: string): Promise<AssetPrice> {
    try {
      const response = await this.axiosInstance.get(`/api/assets/price/${assetId}`);
      return response.data as AssetPrice;
    } catch (error) {
      console.error('Error fetching asset price:', error);
      throw new ApiError('Failed to fetch asset price', 500, error);
    }
  }

  public async registerUser(user: User): Promise<User> {
    try {
      const response = await this.axiosInstance.post('/api/users/auth/register', user);
      return response.data as User;
    } catch (error) {
      console.error('Error registering user:', error);
      throw new ApiError('Failed to register user', 400, error);
    }
  }

  public async loginUser(user: User): Promise<User> {
    try {
      const response = await this.axiosInstance.post('/api/users/auth/login', user);
      return response.data as User;
    } catch (error) {
      console.error('Error logging in user:', error);
      throw new ApiError('Failed to log in user', 401, error);
    }
  }
}

interface ApiError extends Error {
  statusCode: number;
  message: string;
  details?: any;
}

export default ApiClient;