import axios from 'axios';
import { RateLimiter } from 'limiter';
import { Cache } from './cache'; // Assuming a cache implementation exists
import * as dotenv from 'dotenv';

dotenv.config();

const NANSER_API_KEY = process.env.NANSEN_API_KEY;
if (!NANSER_API_KEY) {
    throw new Error('NANSEN_API_KEY environment variable is not set');
}

const BASE_URL = 'https://api.nansen.ai/v1';
const RATE_LIMIT = 60; // Assuming a rate limit of 60 requests per minute
const RETRY_DELAY_MS = 500;
const MAX_RETRIES = 3;

class NansenService {
    private cache: Cache;
    private rateLimiter: RateLimiter;
    private axiosInstance: any;

    constructor() {
        this.cache = new Cache();
        this.rateLimiter = new RateLimiter({
            tokensPerInterval: RATE_LIMIT,
            interval: 'minute',
        });
        this.axiosInstance = axios.create({
            baseURL: BASE_URL,
            headers: { Authorization: `Bearer ${NANSER_API_KEY}` },
        });
    }

    private async requestWithRetry(url: string, retriesLeft = MAX_RETRIES): Promise<any> {
        try {
            await this.rateLimiter.removeTokens(1);
            const response = await this.axiosInstance.get(url);
            return response.data;
        } catch (error) {
            if (retriesLeft > 0 && error.response?.status === 429) {
                console.log(`Rate limited, retrying in ${RETRY_DELAY_MS}ms`);
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
                return this.requestWithRetry(url, retriesLeft - 1);
            } else if (retriesLeft > 0 && error.response?.status >= 500) {
                console.log(`Transient failure, retrying in ${RETRY_DELAY_MS}ms`);
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
                return this.requestWithRetry(url, retriesLeft - 1);
            } else {
                throw error;
            }
        }
    }

    async getWalletAnalytics(walletAddress: string): Promise<any> {
        const cacheKey = `wallet-analytics-${walletAddress}`;
        const cachedData = await this.cache.get(cacheKey);

        if (cachedData) {
            return JSON.parse(cachedData);
        } else {
            try {
                const response = await this.requestWithRetry(`/wallets/${walletAddress}/analytics`);
                await this.cache.set(cacheKey, JSON.stringify(response), 60 * 15); // Cache for 15 minutes
                return response;
            } catch (error) {
                console.error(`Failed to fetch wallet analytics: ${error.message}`);
                throw error;
            }
        }
    }

    async getWalletTransactions(walletAddress: string): Promise<any> {
        const cacheKey = `wallet-transactions-${walletAddress}`;
        const cachedData = await this.cache.get(cacheKey);

        if (cachedData) {
            return JSON.parse(cachedData);
        } else {
            try {
                const response = await this.requestWithRetry(`/wallets/${walletAddress}/transactions`);
                await this.cache.set(cacheKey, JSON.stringify(response), 60 * 15); // Cache for 15 minutes
                return response;
            } catch (error) {
                console.error(`Failed to fetch wallet transactions: ${error.message}`);
                throw error;
            }
        }
    }
}

export default NansenService;