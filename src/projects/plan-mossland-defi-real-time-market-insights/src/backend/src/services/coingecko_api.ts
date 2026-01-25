import axios from 'axios';
import { RateLimiter } from 'limiter';
import * as dotenv from 'dotenv';
import pRetry from 'p-retry';

dotenv.config();

const API_KEY = process.env.COINGECKO_API_KEY;
if (!API_KEY) {
    throw new Error('COINGECKO_API_KEY environment variable is not set');
}

const BASE_URL = 'https://api.coingecko.com/api/v3';
const rateLimiter = new RateLimiter({
    tokensPerInterval: 60,
    interval: 'second',
});

class CoingeckoService {
    private axiosInstance;

    constructor() {
        this.axiosInstance = axios.create({
            baseURL: BASE_URL,
            headers: { 'x_cg_demo_api_key': API_KEY },
        });
    }

    async fetchCoinPrices(ids: string[], vsCurrencies: string[]): Promise<any> {
        return await pRetry(() => rateLimiter.removeTokens(1).then(() =>
            this.axiosInstance.get(`/simple/price`, {
                params: { ids, vs_currencies: vsCurrencies.join(',') }
            })
        ), { retries: 3 }).catch(error => {
            console.error('Error fetching coin prices:', error);
            throw new Error('Failed to fetch coin prices');
        });
    }

    async fetchMarketData(id: string): Promise<any> {
        return await pRetry(() => rateLimiter.removeTokens(1).then(() =>
            this.axiosInstance.get(`/coins/${id}`)
        ), { retries: 3 }).catch(error => {
            console.error('Error fetching market data:', error);
            throw new Error('Failed to fetch market data');
        });
    }
}

export default CoingeckoService;