import type { SystemStats, ActivityItem, Trend, Idea, Plan, PipelineStage } from '@/lib/types';

export const mockStats: SystemStats = {
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

export const mockActivity: ActivityItem[] = [
  { time: '08:00', type: 'trend', message: 'Trend analysis completed (254 articles from 17 feeds)' },
  { time: '08:01', type: 'idea', message: 'Generated idea #8: DeFi Protocol Risk Monitor' },
  { time: '08:02', type: 'idea', message: 'Generated idea #7: AI Trading Signal Aggregator' },
  { time: '08:03', type: 'debate', message: 'Debate started for Plan #4 - Round 1/5' },
  { time: '08:04', type: 'debate', message: 'Founder presented initial plan (Claude)' },
  { time: '08:05', type: 'debate', message: 'VC feedback received (GPT) - market concerns' },
  { time: '08:06', type: 'debate', message: 'Accelerator feedback (Gemini) - MVP scope' },
  { time: '08:07', type: 'plan', message: 'Plan #4 finalized after 3 debate rounds' },
  { time: '08:08', type: 'system', message: 'Cycle completed. Next run in ~6h (debate cycle)' },
];

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

const GITHUB_REPO = 'https://github.com/MosslandOpenDevs/agentic-orchestrator';

export const mockIdeas: Idea[] = [
  { id: 8, title: 'DeFi Protocol Risk Monitor', status: 'backlog', source: 'trend', created: '2026-01-05', issueUrl: `${GITHUB_REPO}/issues/8` },
  { id: 7, title: 'AI Trading Signal Aggregator', status: 'backlog', source: 'trend', created: '2026-01-05', issueUrl: `${GITHUB_REPO}/issues/7` },
  { id: 6, title: 'MOC Token Analytics Dashboard', status: 'planned', source: 'traditional', created: '2026-01-04', issueUrl: `${GITHUB_REPO}/issues/6` },
  { id: 5, title: 'Cross-chain Yield Optimizer', status: 'planned', source: 'trend', created: '2026-01-04', issueUrl: `${GITHUB_REPO}/issues/5` },
  { id: 4, title: 'NFT Metadata Indexer', status: 'backlog', source: 'traditional', created: '2026-01-03', issueUrl: `${GITHUB_REPO}/issues/4` },
  { id: 3, title: 'Community Governance Portal', status: 'backlog', source: 'traditional', created: '2026-01-03', issueUrl: `${GITHUB_REPO}/issues/3` },
  { id: 2, title: 'Memecoin Sentiment Tracker', status: 'backlog', source: 'trend', created: '2026-01-04', issueUrl: `${GITHUB_REPO}/issues/2` },
  { id: 1, title: 'Wallet Activity Monitor', status: 'backlog', source: 'traditional', created: '2026-01-03', issueUrl: `${GITHUB_REPO}/issues/1` },
];

export const mockPlans: Plan[] = [
  { id: 4, title: 'Cross-chain Yield Optimizer', ideaId: 5, status: 'approved', debateRounds: 3, created: '2026-01-04', issueUrl: `${GITHUB_REPO}/issues/12` },
  { id: 3, title: 'MOC Token Analytics Dashboard', ideaId: 6, status: 'approved', debateRounds: 4, created: '2026-01-04', issueUrl: `${GITHUB_REPO}/issues/11` },
  { id: 2, title: 'NFT Metadata Indexer', ideaId: 4, status: 'rejected', debateRounds: 2, created: '2026-01-03', issueUrl: `${GITHUB_REPO}/issues/10` },
  { id: 1, title: 'Community Governance Portal', ideaId: 3, status: 'rejected', debateRounds: 1, created: '2026-01-03', issueUrl: `${GITHUB_REPO}/issues/9` },
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
