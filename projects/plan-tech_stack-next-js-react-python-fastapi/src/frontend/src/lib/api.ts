import fetch, { Response } from 'node-fetch';

interface Contract {
  id: string;
  address: string;
  name: string;
  // Add other contract properties as needed
}

interface Transaction {
  id: string;
  blockNumber: number;
  timestamp: number;
  to: string;
  value: number;
  // Add other transaction properties as needed
}

interface Prediction {
  id: string;
  contractAddress: string;
  vulnerabilityType: string;
  severity: string;
  description: string;
  createdAt: Date;
  // Add other prediction properties as needed
}

interface CreatePredictionRequest {
  contractAddress: string;
  vulnerabilityType: string;
  severity: string;
  description: string;
}

class ApiClient {
  private baseUrl: string;
  private authToken: string | undefined;

  constructor(baseUrl: string, authToken?: string) {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
  }

  private async request<T>(method: string, endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.authToken ? { 'Authorization': `Bearer ${this.authToken}` } : {}),
    };

    try {
      const response = await fetch(url, { method, headers, ...options });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! Status: ${response.status}, Response: ${JSON.stringify(errorData)}`);
      }

      return await response.json() as T;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  async getContracts(): Promise<Contract[]> {
    return this.request<Contract[]>('GET', '/api/contracts');
  }

  async getContractTransactions(address: string): Promise<Transaction[]> {
    return this.request<Transaction[]>('GET', `/api/contracts/${address}/transactions`);
  }

  async createPrediction(data: CreatePredictionRequest): Promise<Prediction> {
    return this.request<Prediction>('POST', '/api/predictions', {
      body: JSON.stringify(data),
    });
  }
}

export default ApiClient;