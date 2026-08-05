import type { SystemStats, Trend, PipelineStage } from '@/lib/types';

export const mockStats: SystemStats = {
  systemStatus: 'unknown',
  totalIdeas: 8,
  totalPlans: 4,
  plansRejected: 2,
  inDevelopment: 0,
  trendsAnalyzed: 254,
  // Computed relative to load time so the demo dashboard never reads as
  // "months ago" when the backend is unreachable (placeholders the real API
  // overwrites). The dependent UI uses suppressHydrationWarning because the
  // rendered relative time is inherently client-clock dependent.
  lastRun: new Date(Date.now() - 6 * 60_000).toISOString(),
  nextRun: new Date(Date.now() + 24 * 60_000).toISOString(),
};

export const mockTrends: Trend[] = [
  {
    title: 'Bitcoin Price Rally to $91K',
    score: 9.2,
    category: 'crypto',
    articles: 6,
    summary: 'Bitcoin showing strong momentum above $90,000 despite ETF outflows',
    ideaSeeds: ['BTC sentiment analyzer', 'ETF flow tracker', 'Automated DCA bot'],
  },
  {
    title: 'DeFi 2026 Reboot Initiative',
    score: 9.0,
    category: 'defi',
    articles: 2,
    summary: 'Ethereum and Solana positioning for DeFi renaissance with neobank integration',
    ideaSeeds: ['Neobank-DeFi bridge SDK', 'Cross-chain yield aggregator'],
  },
  {
    title: 'Memecoin Market Resurgence',
    score: 8.7,
    category: 'crypto',
    articles: 4,
    summary: 'DOGE, PEPE, BONK seeing 10-25% gains with bullish technical signals',
    ideaSeeds: ['Memecoin momentum scanner', 'Anti-rug launchpad'],
  },
  {
    title: 'AI Pragmatism Era Begins',
    score: 8.4,
    category: 'ai',
    articles: 3,
    summary: 'Shift from hype to practical AI with smaller efficient models',
    ideaSeeds: ['Decentralized AI inference marketplace', 'AI trading agent framework'],
  },
  {
    title: 'XRP Regulatory Optimism',
    score: 8.5,
    category: 'crypto',
    articles: 2,
    summary: 'XRP jumped 8% above $2 anticipating friendlier SEC stance',
    ideaSeeds: ['Regulatory news aggregator', 'Cross-border payment comparison tool'],
  },
  {
    title: 'Nation-State Crypto Adoption',
    score: 8.1,
    category: 'crypto',
    articles: 2,
    summary: 'Turkmenistan legalized crypto mining, Iran accepts crypto payments',
    ideaSeeds: ['Emerging market crypto readiness tool', 'Mining site optimizer'],
  },
  {
    title: 'Data Privacy Tools Rise',
    score: 7.5,
    category: 'security',
    articles: 1,
    summary: 'Growing demand for Web3 privacy solutions and self-sovereign identity',
    ideaSeeds: ['ZK-based identity verification', 'Privacy-preserving KYC layer'],
  },
];

export const mockPipeline: PipelineStage[] = [
  { id: 'ideas', name: 'Ideas', count: 8, status: 'completed' },
  { id: 'plans', name: 'Plans', count: 4, status: 'active' },
  { id: 'dev', name: 'In Dev', count: 0, status: 'idle' },
];

export const debateRoles = [
  { name: 'Founder', perspective: '비전, 확신, 실행력', icon: '🚀' },
  { name: 'VC', perspective: '시장성, 투자 가치, 확장성', icon: '💰' },
  { name: 'Accelerator', perspective: '실행 가능성, MVP, 검증', icon: '⚡' },
  { name: 'Founder Friend', perspective: '동료 관점, 창의적 아이디어', icon: '🤝' },
] as const;

export const aiProviders = ['Claude', 'GPT', 'Gemini'] as const;

export const rssCategories = [
  { name: 'AI', feeds: ['OpenAI News', 'Google Blog', 'arXiv AI', 'TechCrunch', 'Hacker News'], count: 5 },
  { name: 'Crypto', feeds: ['CoinDesk', 'Cointelegraph', 'Decrypt', 'The Defiant', 'CryptoSlate'], count: 5 },
  { name: 'Finance', feeds: ['CNBC Finance'], count: 1 },
  { name: 'Security', feeds: ['The Hacker News', 'Krebs on Security'], count: 2 },
  { name: 'Dev', feeds: ['The Verge', 'Ars Technica', 'Stack Overflow Blog'], count: 3 },
] as const;
