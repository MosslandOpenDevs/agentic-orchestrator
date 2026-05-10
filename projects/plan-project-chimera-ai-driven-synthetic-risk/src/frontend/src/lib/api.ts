import fetch, { Response } from 'node-fetch';

interface Contract {
  contractAddress: string;
  name: string;
  // Add other contract properties here
}

interface RiskScore {
  contractAddress: string;
  score: number;
  // Add other risk score properties here
}

interface ContractError {
  code: number;
  message: string;
}

interface ApiClient {
  /**
   * Retrieves a list of smart contracts.
   * @returns A Promise resolving to an array of Contract objects.
   */
  getContracts(): Promise<Contract[]>;

  /**
   * Retrieves details for a specific smart contract.
   * @param contractAddress The address of the contract.
   * @returns A Promise resolving to a Contract object or null if not found.
   */
  getContract(contractAddress: string): Promise<Contract | null>;

  /**
   * Retrieves a list of risk scores.
   * @returns A Promise resolving to an array of RiskScore objects.
   */
  getRiskScores(): Promise<RiskScore[]>;

  /**
   * Retrieves the risk score for a specific smart contract.
   * @param contractAddress The address of the contract.
   * @returns A Promise resolving to a RiskScore object or null if not found.
   */
  getRiskScore(contractAddress: string): Promise<RiskScore | null>;
}

class ApiClientImpl implements ApiClient {
  private readonly baseApiUrl: string;
  private readonly authHeaders: HeadersInit;

  constructor(baseApiUrl: string, authHeaders: HeadersInit) {
    this.baseApiUrl = baseApiUrl;
    this.authHeaders = authHeaders;
  }

  async getContracts(): Promise<Contract[]> {
    const url = `${this.baseApiUrl}/api/contracts`;
    try {
      const response = await fetch(url, { headers: this.authHeaders });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json() as Contract[];
      return data;
    } catch (error) {
      console.error('Error fetching contracts:', error);
      throw new Error(`Failed to fetch contracts: ${error}`);
    }
  }

  async getContract(contractAddress: string): Promise<Contract | null> {
    const url = `${this.baseApiUrl}/api/contracts/${contractAddress}`;
    try {
      const response = await fetch(url, { headers: this.authHeaders });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json() as Contract | null;
      return data;
    } catch (error) {
      console.error(`Error fetching contract ${contractAddress}:`, error);
      throw new Error(`Failed to fetch contract ${contractAddress}: ${error}`);
    }
  }

  async getRiskScores(): Promise<RiskScore[]> {
    const url = `${this.baseApiUrl}/api/riskscores`;
    try {
      const response = await fetch(url, { headers: this.authHeaders });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json() as RiskScore[];
      return data;
    } catch (error) {
      console.error('Error fetching risk scores:', error);
      throw new Error(`Failed to fetch risk scores: ${error}`);
    }
  }

  async getRiskScore(contractAddress: string): Promise<RiskScore | null> {
    const url = `${this.baseApiUrl}/api/riskscore/${contractAddress}`;
    try {
      const response = await fetch(url, { headers: this.authHeaders });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json() as RiskScore | null;
      return data;
    } catch (error) {
      console.error(`Error fetching risk score for ${contractAddress}:`, error);
      throw new Error(`Failed to fetch risk score for ${contractAddress}: ${error}`);
    }
  }
}

export default ApiClientImpl;