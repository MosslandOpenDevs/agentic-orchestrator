import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

type UserSettings = {
  userId: string;
  settings: Record<string, any>;
};

type BlockchainInteractionLog = {
  interactionType: string;
  details: Record<string, any>;
};

class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

class UnauthorizedError extends ApiError {
  constructor() {
    super("Unauthorized access");
    this.name = "UnauthorizedError";
  }
}

const axiosInstance: AxiosInstance = axios.create({
  baseURL: process.env.API_BASE_URL,
});

axiosInstance.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('authToken');
    if (token && !config.headers['Authorization']) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.status === 401) {
      throw new UnauthorizedError();
    }
    throw new ApiError("An error occurred");
  }
);

class Client {
  async getUserSettings(userId: string): Promise<UserSettings> {
    const response = await axiosInstance.get(`/api/user-settings/${userId}`);
    return response.data;
  }

  async logBlockchainInteraction(interactionLog: BlockchainInteractionLog): Promise<void> {
    await axiosInstance.post('/api/blockchain-interaction', interactionLog);
  }
}

export default Client;