import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface Portfolio {
  id: string;
  name: string;
  description?: string;
  value: number;
}

interface Transaction {
  id: string;
  portfolioId: string;
  date: string;
  type: 'buy' | 'sell' | 'dividend';
  amount: number;
  price: number;
}

interface MarketIndicator {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface PortfolioCreateRequest {
  name: string;
  description?: string;
  value: number;
}

interface PortfolioResponse {
  data: Portfolio;
}

interface TransactionResponse {
  data: Transaction[];
}

interface MarketIndicatorResponse {
  data: MarketIndicator[];
}

interface PortfolioClient {
  getPortfolios(): Promise<Portfolio[]>;
  getPortfoliosById(portfolioId: string): Promise<Portfolio | null>;
  createPortfolio(portfolio: PortfolioCreateRequest): Promise<Portfolio>;
  getTransactionsById(portfolioId: string): Promise<Transaction[]>;
  getMarketIndicators(): Promise<MarketIndicator[]>;
}

class PortfolioApiClient implements PortfolioClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authenticationHeaders: Record<string, string> = {};

  constructor(axiosInstance: AxiosInstance, baseUrl: string) {
    this.axiosInstance = axiosInstance;
    this.baseUrl = baseUrl;
  }

  setAuthenticationHeaders(headers: Record<string, string>) {
    this.authenticationHeaders = { ...headers };
  }

  async getPortfolios(): Promise<Portfolio[]> {
    try {
      const response = await this.axiosInstance.get<Portfolio[]>(`${this.baseUrl}/api/portfolios`);
      return response.data;
    } catch (error) {
      console.error('Error fetching portfolios:', error);
      throw new Error(`Failed to fetch portfolios: ${error}`);
    }
  }

  async getPortfoliosById(portfolioId: string): Promise<Portfolio | null> {
    try {
      const response = await this.axiosInstance.get<Portfolio>(`${this.baseUrl}/api/portfolios/${portfolioId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching portfolio ${portfolioId}:`, error);
      if (error instanceof CanceledError) {
        return null;
      }
      throw new Error(`Failed to fetch portfolio ${portfolioId}: ${error}`);
    }
  }

  async createPortfolio(portfolio: PortfolioCreateRequest): Promise<Portfolio> {
    try {
      const response = await this.axiosInstance.post<Portfolio>(`${this.baseUrl}/api/portfolios`, portfolio);
      return response.data;
    } catch (error) {
      console.error('Error creating portfolio:', error);
      throw new Error(`Failed to create portfolio: ${error}`);
    }
  }

  async getTransactionsById(portfolioId: string): Promise<Transaction[]> {
    try {
      const response = await this.axiosInstance.get<Transaction[]>(`${this.baseUrl}/api/transactions/${portfolioId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching transactions for portfolio ${portfolioId}:`, error);
      throw new Error(`Failed to fetch transactions for portfolio ${portfolioId}: ${error}`);
    }
  }

  async getMarketIndicators(): Promise<MarketIndicator[]> {
    try {
      const response = await this.axiosInstance.get<MarketIndicator>(`${this.baseUrl}/api/marketIndicators`);
      return response.data;
    } catch (error) {
      console.error('Error fetching market indicators:', error);
      throw new Error(`Failed to fetch market indicators: ${error}`);
    }
  }
}

export default PortfolioApiClient;