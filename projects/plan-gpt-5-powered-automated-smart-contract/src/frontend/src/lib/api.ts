import axios, { AxiosInstance, AxiosRequestConfig, CanceledError } from 'axios';

interface Contract {
  address: string;
  name: string;
  // Add other contract properties here
}

interface VulnerabilityReport {
  contractAddress: string;
  vulnerabilities: string[];
}

interface RiskAssessment {
  contractAddress: string;
  riskScore: number;
  // Add other risk assessment properties here
}

interface ApiClient {
  /**
   * Retrieves a list of all smart contracts.
   * @returns A Promise resolving to an array of Contract objects.
   */
  getContracts(): Promise<Contract[]>;

  /**
   * Retrieves details for a specific smart contract.
   * @param contractAddress The address of the contract.
   * @returns A Promise resolving to a Contract object.
   */
  getContract(contractAddress: string): Promise<Contract>;

  /**
   * Generates a vulnerability report for a smart contract using GPT-5.
   * @param contractAddress The address of the contract.
   * @returns A Promise resolving to a VulnerabilityReport object.
   */
  generateVulnerabilityReport(contractAddress: string): Promise<VulnerabilityReport>;

  /**
   * Retrieves the dynamic risk assessment for a smart contract.
   * @param contractAddress The address of the contract.
   * @returns A Promise resolving to a RiskAssessment object.
   */
  getRiskAssessment(contractAddress: string): Promise<RiskAssessment>;
}

class ApiClientImpl implements ApiClient {
  private readonly axiosInstance: AxiosInstance;
  private readonly baseApiUrl: string;

  constructor(baseApiUrl: string) {
    this.baseApiUrl = baseApiUrl;
    this.axiosInstance = axios.create({
      baseURL: baseApiUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.axiosInstance.interceptors.request.use(
      (config) => {
        // Add authentication headers here if needed
        // Example: config.headers['Authorization'] = 'Bearer ' + this.authToken;
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response) {
          // Handle non-2xx responses
          console.error('API Error:', error.response);
          // You can throw a custom error here based on the response status code
          // Example: throw new ApiError(error.response.status, error.response.data);
          return Promise.reject(error);
        } else if (error instanceof CanceledError) {
          console.error('Request canceled:', error.message);
          throw new ApiError(408, 'Request timed out');
        } else {
          console.error('API Error:', error);
          throw new ApiError(500, 'Internal Server Error');
        }
      }
    );
  }

  async getContracts(): Promise<Contract[]> {
    try {
      const response = await this.axiosInstance.get('/api/contracts');
      return response.data as Contract[];
    } catch (error) {
      throw new ApiError(500, 'Failed to retrieve contracts');
    }
  }

  async getContract(contractAddress: string): Promise<Contract> {
    try {
      const response = await this.axiosInstance.get(`/api/contracts/${contractAddress}`);
      return response.data as Contract;
    } catch (error) {
      throw new ApiError(500, `Failed to retrieve contract ${contractAddress}`);
    }
  }

  async generateVulnerabilityReport(contractAddress: string): Promise<VulnerabilityReport> {
    try {
      const response = await this.axiosInstance.post('/api/vulnerabilities', { contractAddress });
      return response.data as VulnerabilityReport;
    } catch (error) {
      throw new ApiError(500, 'Failed to generate vulnerability report');
    }
  }

  async getRiskAssessment(contractAddress: string): Promise<RiskAssessment> {
    try {
      const response = await this.axiosInstance.get(`/api/risk/${contractAddress}`);
      return response.data as RiskAssessment;
    } catch (error) {
      throw new ApiError(500, `Failed to retrieve risk assessment for ${contractAddress}`);
    }
  }
}

interface ApiError {
  statusCode: number;
  message: string;
}

export { ApiClient, ApiError };