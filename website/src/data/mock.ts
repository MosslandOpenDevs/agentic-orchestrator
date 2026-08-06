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
