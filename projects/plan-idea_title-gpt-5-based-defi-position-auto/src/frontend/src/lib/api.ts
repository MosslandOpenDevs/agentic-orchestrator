import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface Contract {
  address: string;
  name: string;
  // Add other contract properties here
}

interface VulnerabilityReport {
  contractAddress: string;
  vulnerabilities: string[];
  // Add other vulnerability report properties here
}

interface RiskAssessment {
  contractAddress: string;
  riskScore: number;
  // Add other risk assessment properties here
}

interface ApiClient {
  getContracts(): Promise<Contract[]>;
  getContract(contractAddress: string): Promise<Contract>;
  postVulnerabilities(contractAddress: string): Promise<VulnerabilityReport>;
  getRisk(contractAddress: string): Promise<RiskAssessment>;
  post(): Promise<void>;
  put(): Promise<void>;
  delete(): Promise<void>;
}

class ApiService implements ApiClient {
  private axiosInstance: AxiosInstance;
  private baseUrl: string;
  private authToken: string | undefined;

  constructor(baseUrl: string, authToken?: string) {
    this.baseUrl = baseUrl;
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authToken = authToken;
  }

  async getContracts(): Promise<Contract[]> {
    try {
      const response = await this.axiosInstance.get('/api/contracts');
      return response.data as Contract[];
    } catch (error) {
      console.error('Error fetching contracts:', error);
      throw new Error('Failed to fetch contracts');
    }
  }

  async getContract(contractAddress: string): Promise<Contract> {
    try {
      const response = await this.axiosInstance.get(`/api/contracts/${contractAddress}`);
      return response.data as Contract;
    } catch (error) {
      console.error(`Error fetching contract ${contractAddress}:`, error);
      throw new Error(`Failed to fetch contract ${contractAddress}`);
    }
  }

  async postVulnerabilities(contractAddress: string): Promise<VulnerabilityReport> {
    try {
      const response = await this.axiosInstance.post(`/api/vulnerabilities`, { contractAddress });
      return response.data as VulnerabilityReport;
    } catch (error) {
      console.error(`Error generating vulnerability report for ${contractAddress}:`, error);
      throw new Error(`Failed to generate vulnerability report for ${contractAddress}`);
    }
  }

  async getRisk(contractAddress: string): Promise<RiskAssessment> {
    try {
      const response = await this.axiosInstance.get(`/api/risk/${contractAddress}`);
      return response.data as RiskAssessment;
    } catch (error) {
      console.error(`Error fetching risk assessment for ${contractAddress}:`, error);
      throw new Error(`Failed to fetch risk assessment for ${contractAddress}`);
    }
  }

  async post(): Promise<void> {
    try {
      await this.axiosInstance.post('/api/contracts', {});
    } catch (error) {
      console.error('Error posting:', error);
      throw new Error('Failed to post');
    }
  }

  async put(): Promise<void> {
    try {
      await this.axiosInstance.put('/api/contracts/1', {});
    } catch (error) {
      console.error('Error putting:', error);
      throw new Error('Failed to put');
    }
  }

  async delete(): Promise<void> {
    try {
      await this.axiosInstance.delete('/api/contracts/1');
    } catch (error) {
      console.error('Error deleting:', error);
      throw new Error('Failed to delete');
    }
  }
}

export default ApiClient;