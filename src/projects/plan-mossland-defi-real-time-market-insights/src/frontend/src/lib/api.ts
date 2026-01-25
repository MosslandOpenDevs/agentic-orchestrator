import axios, { AxiosInstance } from 'axios';
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';

export interface SentimentAnalysisResult {
  sentiment: string;
  score: number;
}

export interface SecurityAlert {
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
}

interface CustomError extends Error {
  status?: number;
}

const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
});

axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response) => response,
  (error: CustomError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
    }
    throw error;
  }
);

export const fetchSentimentAnalysis = async (): Promise<SentimentAnalysisResult> => {
  try {
    const response = await axiosInstance.get('/api/sentiment-analysis');
    return response.data as SentimentAnalysisResult;
  } catch (error) {
    throw new CustomError((error.response?.data.message || error.message), { cause: error });
  }
};

export const submitSecurityAlert = async (alert: SecurityAlert): Promise<void> => {
  try {
    await axiosInstance.post('/api/security-alerts', alert);
  } catch (error) {
    throw new CustomError((error.response?.data.message || error.message), { cause: error });
  }
};