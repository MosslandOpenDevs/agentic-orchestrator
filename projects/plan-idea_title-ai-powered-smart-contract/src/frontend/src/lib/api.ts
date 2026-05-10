import axios, { AxiosInstance, AxiosInterceptorManager, AxiosResponse, AxiosError } from 'axios';

interface Contract {
  address: string;
  name: string;
  // Add other contract properties here
}

interface VulnerabilityReport {
  id: number;
  contractAddress: string;
  vulnerabilityType: string;
  severity: string;
  description: string;
  // Add other vulnerability report properties here
}

interface RiskAssessment {
  contractAddress: string;
  riskScore: number;
  riskCategory: string;
  // Add other risk assessment properties here
}

interface ContractApiOptions {
  baseUrl: string;
  interceptors?: AxiosInterceptorManager<AxiosInstance>;
}

export class ContractApiClient {
  private axiosInstance: AxiosInstance;

  constructor(options: ContractApiOptions) {
    this.axiosInstance = axios.create({
      baseURL: options.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    options.interceptors?.forEach(interceptor => {
      this.axiosInstance.interceptors.request.use(interceptor);
    });
  }

  async getContracts(): Promise<Contract[]> {
    try {
      const response = await this.axiosInstance.get<Contract[]>('/api/contracts');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching contracts:', error);
      throw new ContractApiError('Failed to fetch contracts', 500, error);
    }
  }

  async getContractByAddress(address: string): Promise<Contract> {
    try {
      const response = await this.axiosInstance.get<Contract>(`/api/contracts/${address}`);
      return response.data;
    } catch (error: any) {
      console.error(`Error fetching contract by address ${address}:`, error);
      throw new ContractApiError(`Failed to fetch contract by address ${address}`, 404, error);
    }
  }

  async getVulnerabilityReports(): Promise<VulnerabilityReport[]> {
    try {
      const response = await this.axiosInstance.get<VulnerabilityReport[]>('/api/vulnerabilities');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching vulnerability reports:', error);
      throw new ContractApiError('Failed to fetch vulnerability reports', 500, error);
    }
  }

  async getRiskAssessmentByAddress(address: string): Promise<RiskAssessment> {
    try {
      const response = await this.axiosInstance.get<RiskAssessment>(`/api/risk-assessment/${address}`);
      return response.data;
    } catch (error: any) {
      console.error(`Error fetching risk assessment by address ${address}:`, error);
      throw new ContractApiError(`Failed to fetch risk assessment by address ${address}`, 404, error);
    }
  }
}

class ContractApiError extends Error {
  constructor(message: string, statusCode: number, error?: any) {
    super(message);
    this.statusCode = statusCode;
    this.error = error;
  }
}