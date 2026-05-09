import fetch, { Response } from 'node-fetch';

interface BaseResponse<T> {
  data: T | null;
  error: string | null;
}

class ENSClient {
  private baseUrl: string;
  private apiKey: string | null;

  constructor(baseUrl: string, apiKey: string | null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request<T>(method: string, endpoint: string, headers: Record<string, string> = {}) {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
          'Authorization': `Bearer ${this.apiKey}`,
        },
      });

      if (!response.ok) {
        let errorBody = null;
        try {
          errorBody = await response.json();
        } catch (e) {
          errorBody = await response.text();
        }

        throw new Error(
          `HTTP error! Status: ${response.status}, ${response.statusText || 'Unknown error'}.  ${errorBody}`
        );
      }

      const data = await response.json() as T;
      return { data, error: null } as BaseResponse<T>;
    } catch (error) {
      console.error('Request error:', error);
      return { data: null, error: (error as Error).message } as BaseResponse<T>;
    }
  }

  async getDomains(): Promise<BaseResponse<string[]>> {
    return await this.request('GET', '/api/domains');
  }

  async getDomain(domainId: string): Promise<BaseResponse<any>> {
    return await this.request('GET', `/api/domains/${domainId}`);
  }

  async mintDomain(domainId: string): Promise<BaseResponse<any>> {
    return await this.request('POST', '/api/mint', { domainId });
  }

  async getClaudeAssets(): Promise<BaseResponse<any>> {
    return await this.request('GET', '/api/claude/assets');
  }
}

export default ENSClient;