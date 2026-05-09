import fetch, { Response } from 'node-fetch';

interface BaseResponse<T> {
  data: T | null;
  error: string | null;
}

class ENSClient {
  private baseUrl: string;
  private apiKey: string | undefined;

  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request<T>(method: string, endpoint: string, options?: RequestInit): Promise<BaseResponse<T>> {
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {})
      };

      const response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });

      if (!response.ok) {
        const errorData = await response.json();
        return { data: null, error: errorData.message || `HTTP error! Status: ${response.status}` };
      }

      const data = await response.json() as T;
      return { data, error: null };
    } catch (error) {
      console.error('Request error:', error);
      return { data: null, error: 'Request error' };
    }
  }

  // GET /api/domains
  async getDomains(): Promise<string[]> {
    return this.request('GET', '/api/domains');
  }

  // GET /api/domains/:domainId
  async getDomain(domainId: string): Promise {
    return this.request('GET', `/api/domains/${domainId}`);
  }

  // POST /api/mint
  async mint(domainId: string): Promise {
    return this.request('POST', '/api/mint', {
      method: 'POST',
      body: JSON.stringify({ domainId }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // GET /api/users
  async getUsers(): Promise {
    return this.request('GET', '/api/users');
  }
}

export default ENSClient;