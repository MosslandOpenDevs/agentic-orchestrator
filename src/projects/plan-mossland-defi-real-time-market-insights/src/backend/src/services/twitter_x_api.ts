import axios from 'axios';
import { OAuth2Client } from 'google-auth-library';
import { Cache } from './cache'; // Assume a simple cache implementation exists
import pRetry from 'p-retry';

const TWITTER_API_URL = 'https://api.twitter.com/2/tweets/search/recent';
const CACHE_TTL = 60 * 5; // 5 minutes

interface TwitterResponse {
    data: Tweet[];
}

interface Tweet {
    id: string;
    text: string;
    created_at: string;
}

class TwitterService {
    private oauth2Client: OAuth2Client;
    private cache: Cache<TwitterResponse>;

    constructor() {
        this.oauth2Client = new OAuth2Client(
            process.env.TWITTER_CLIENT_ID!,
            process.env.TWITTER_CLIENT_SECRET!,
            process.env.TWITTER_REDIRECT_URI!
        );
        this.cache = new Cache(CACHE_TTL);
    }

    private async getAccessToken(): Promise<string> {
        const { tokens } = await this.oauth2Client.getAccessToken();
        return tokens.access_token;
    }

    private async fetchTweets(query: string): Promise<TwitterResponse | undefined> {
        try {
            const cachedData = this.cache.get(query);
            if (cachedData) {
                return cachedData;
            }
            const accessToken = await this.getAccessToken();
            const response = await axios.get<TwitterResponse>(TWITTER_API_URL, {
                params: { query },
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                },
            });
            this.cache.set(query, response.data);
            return response.data;
        } catch (error) {
            console.error('Error fetching tweets:', error);
            throw error;
        }
    }

    public async searchTweetsWithRetry(query: string): Promise<TwitterResponse | undefined> {
        try {
            const result = await pRetry(() => this.fetchTweets(query), { retries: 3 });
            return result;
        } catch (error) {
            console.error('Failed to fetch tweets after multiple attempts:', error);
            throw error;
        }
    }

    public async analyzeSentiment(query: string): Promise<number | undefined> {
        const tweets = await this.searchTweetsWithRetry(query);
        if (!tweets || !tweets.data.length) return 0;

        // Placeholder for sentiment analysis logic
        let totalScore = 0;
        for (const tweet of tweets.data) {
            const score = this.calculateSentiment(tweet.text); // Assume a method that calculates sentiment score
            totalScore += score;
        }
        return totalScore / tweets.data.length;
    }

    private calculateSentiment(text: string): number {
        // Placeholder logic for calculating sentiment score
        if (text.includes('love')) return 1;
        if (text.includes('hate')) return -1;
        return 0;
    }
}

export default TwitterService;