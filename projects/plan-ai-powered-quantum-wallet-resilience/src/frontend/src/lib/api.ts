import axios, { AxiosInstance, AxiosInterceptorManager, AxiosResponse } from 'axios';

interface Contract {
  address: string;
  name: string;
  // Add other contract properties here
}

interface AnalyzeRequest {
  contractCode: string;
  // Add other analyze request parameters here
}

interface AnalyzeResponse {
  analysisResult: string;
  // Add other analyze response properties here
}

interface RemediateRequest {
  contractCode: string;
  // Add other remediate request parameters here
}

interface RemediateResponse {
  remediatedContractCode: string;
  // Add other remediate response properties here
}

class ContractApiClient {
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
  addRequestInterceptor(callback: (config: any) => void) {
    this.interceptors.request.use(callback);
  }

  addResponseInterceptor(callback: (response: AxiosResponse) => void) {
    this.interceptors.response.use(callback);
  }

  // Error Interceptors
  addErrorInterceptor(callback: (error: any) => void) {
    this.interceptors.request.use(
      (config) => {
        // Handle request errors here
        return config;
      },
      (error) => {
        callback(error);
        return Promise.reject(error);
      }
    );
  }


  // Contract Endpoints
  async getContracts(): Promise<Contract[]> {
    try {
      const response = await this.axiosInstance.get<Contract[]>('/api/contracts');
      return response.data;
    } catch (error) {
      console.error('Error fetching contracts:', error);
      throw new Error('Failed to fetch contracts');
    }
  }

  async getContract(contractAddress: string): Promise<Contract> {
    try {
      const response = await this.axiosInstance.get<Contract>(`/api/contracts/${contractAddress}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching contract ${contractAddress}:`, error);
      throw new Error(`Failed to fetch contract ${contractAddress}`);
    }
  }

  // Analysis Endpoint
  async analyzeContract(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    try {
      const response = await this.axiosInstance.post<AnalyzeResponse>('/api/analyze', request);
      return response.data;
    } catch (error) {
      console.error('Error analyzing contract:', error);
      throw new Error('Failed to analyze contract');
    }
  }

  // Remediate Endpoint
  async remediateContract(request: RemediateRequest): Promise<RemediateResponse> {
    try {
      const response = await this.axiosInstance.post<RemediateResponse>('/api/remediate', request);
      return response.data;
    } catch (error) {
      console.error('Error remediating contract:', error);
      throw new Error('Failed to remediate contract');
    }
  }
}

export default ContractApiClient;