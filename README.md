# Mossland Agentic Orchestrator

[한국어](README.ko.md) | **English**

An autonomous multi-agent orchestration system for discovering, planning, and implementing micro Web3 services for the Mossland ecosystem.

**Version**: v0.6.19

## Key Features

- **Multi-Stage Debate**: 34 AI agents with diverse personas debate through 3 phases (Divergence → Convergence → Planning)
- **[Diverse Signal Sources](#signal-sources)**: 11 adapters across RSS, GitHub, on-chain, social, news, and market data
- **Hybrid LLM Routing**: Local Ollama models + Cloud API fallback with intelligent routing
- **Human-in-the-Loop**: Humans select which ideas to develop via label promotion
- **PM2 Scheduling**: Automated task scheduling with PM2 (signals, trends, debates, backlog, health checks)
- **CLI-Style Dashboard**: Retro terminal-themed web interface at https://ao.moss.land
- **REST API**: FastAPI backend for programmatic access
- **DB Resilience**: a lost or emptied SQLite file degrades gracefully instead of taking every endpoint down — startup schema self-heal, `/status` degradation, and integrity-checked rolling backups (~daily, 7 kept, regression-aware retention)
- **Self-Deploying**: production follows `main` on its own — a 5-minute pull loop gated on green CI, with pre-deploy DB snapshots and automatic rollback ([Deployment](#deployment))
- **Structured LLM Output**: trend analysis and idea scoring enforce JSON schemas at decode time (Ollama `format`), with truncation detection and salvage parsing behind them

## Dashboard

A Next.js CLI-style dashboard for monitoring the orchestrator in real time, live at **https://ao.moss.land**. To run it locally: `cd website && pnpm install && pnpm dev`, then open http://localhost:3000.

| Page | Description |
|------|-------------|
| `/` | Dashboard with pipeline, activity feed, and statistics |
| `/trends` | Trend analysis results from signal sources |
| `/backlog` | Ideas and plans backlog with GitHub links |
| `/system` | System architecture and multi-agent debate visualization |
| `/agents` | 34 AI agent personas across 3 debate phases |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SIGNAL COLLECTION - 11 adapters                                        │
│  RSS, GitHub Events, On-Chain, Social, News API, Twitter/X,             │
│  Discord, Lens, Farcaster, Coingecko, Threads                           │
│                                    │                                    │
│                                    ▼                                    │
│                        ┌───────────────────────┐                        │
│                        │  Signal Aggregator    │                        │
│                        │  + Scorer             │                        │
│                        └───────────┬───────────┘                        │
├────────────────────────────────────┼────────────────────────────────────┤
│                                    ▼                                    │
│                     MULTI-STAGE DEBATE (34 agents)                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Phase 1: DIVERGENCE   (16)  Engineers, Designers, PMs, Marketers  │  │
│  │ Phase 2: CONVERGENCE   (8)  VCs, Mentors, Founders, Experts       │  │
│  │ Phase 3: PLANNING     (10)  CPO, PMs, Leads, UX, QA, DevRel       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                   LLM ROUTER (Ollama-only by default)                   │
│  ┌─────────────────────────────┐    ┌────────────────────────────────┐  │
│  │ Local (Ollama)              │    │ Cloud API (opt-in via flag)    │  │
│  │ - gemma3:4b (all tasks)     │    │ - Claude / OpenAI / Gemini     │  │
│  │ - JSON schemas enforced     │    │ Disabled when                  │  │
│  │   at decode time (format)   │    │ MOSS_LOCAL_LLM_ONLY=true       │  │
│  └─────────────────────────────┘    └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Clone and install
git clone https://github.com/MosslandOpenDevs/agentic-orchestrator.git
cd agentic-orchestrator

# Create Python virtual environment (Python 3.12 or newer required)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services with PM2

```bash
# Install PM2 globally
npm install -g pm2

# Build the dashboard first (moss-ao-web runs `next start`, which needs a build)
cd website && pnpm install && pnpm build && cd ..

# Start all services
pm2 start ecosystem.config.js

# Or start specific services
pm2 start ecosystem.config.js --only moss-ao-web
pm2 start ecosystem.config.js --only moss-ao-api
```

Once PM2 is up, the dashboard is at http://localhost:3000 and the API reference at http://localhost:3001/docs.

## PM2 Services

| Service | Schedule | Description |
|---------|----------|-------------|
| `moss-ao-signals` | Every 30 min | Collect signals from all adapters |
| `moss-ao-trends` | Every 2 hours | Analyze signals into trends (local LLM) |
| `moss-ao-debate` | Every 6 hours | Run multi-stage AI debate |
| `moss-ao-backlog` | Every 4 hours | Process pending backlog items |
| `moss-ao-web` | Always on | Next.js dashboard (port 3000) |
| `moss-ao-api` | Always on | FastAPI backend (port 3001) |
| `moss-ao-health` | Every 5 min | Health monitoring + rolling DB backup (~daily) |
| `moss-ao-deploy` | Every 5 min | Pull-based auto-deploy, opt-in ([docs/deployment.md](docs/deployment.md)) |

```bash
pm2 status                  # all services
pm2 logs moss-ao-api        # tail one service
pm2 restart moss-ao-web     # restart one service
pm2 stop all                # stop everything
pm2 monit                   # resource monitor
```

## Deployment

Production deploys itself: the opt-in `moss-ao-deploy` job fetches `main` every
5 minutes and acts only when it moved — deploying commits GitHub Actions has
passed, after a DB snapshot, building only what the diff touches, and rolling
back (rebuild included) if the post-deploy health check fails. `git clean` is
never used, so untracked server state (`data/orchestrator.db`, `.env`) survives
every deploy. Back-end deploys wait while a debate is running; docs-only
commits restart nothing.

```bash
bash scripts/deploy.sh --check   # dry run: report what would happen
bash scripts/deploy.sh           # deploy now, without waiting for the next tick
```

Setup, configuration, and troubleshooting: [docs/deployment.md](docs/deployment.md).

## API Endpoints

The FastAPI backend provides REST API access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status |
| `/signals` | GET | List recent signals |
| `/debates` | GET | List debate results |
| `/agents` | GET | List agent personas |
| `/docs` | GET | Swagger documentation |

## Multi-Stage Debate System

Every debate runs three phases. **Pool** is the persona pool size (`personas/catalog.py`);
each round draws a smaller, personality-balanced subset — the **Per round** column, sized
by `debate.normal.*_agents_per_round` in `config.yaml`.

| Phase | Pool | Per round | Purpose | Personas |
|-------|------|-----------|---------|----------|
| 1. Divergence | 16 | 8 | Generate diverse ideas and perspectives | Frontend / Backend / Blockchain engineers, Security Researcher, DevOps, Product and UX Designers, Product Managers, Growth Marketer, Brand Strategist, Business Analyst, Community Manager |
| 2. Convergence | 8 | 4 | Synthesize and evaluate ideas | Crypto VC and Traditional VC partners, two Accelerator Mentors, serial and first-time founders, Tech and Market Domain Experts |
| 3. Planning | 10 | 3 | Create actionable implementation plans | CPO, Senior PM, Technical Lead, Frontend / Backend / Blockchain Leads, UX Researcher, QA Lead, Developer Relations, Project Manager |

Every persona also carries a 4-axis personality profile scored 0-10. Balancing a round's
subset across these axes is what stops it from being eight agents of one temperament.

- **Creativity**: Innovation vs. Convention
- **Analytical**: Data-driven vs. Intuitive
- **Risk Tolerance**: Aggressive vs. Conservative
- **Collaboration**: Team-oriented vs. Independent

## Signal Sources

Eleven adapters feed the collector, all configured in `config.yaml`. **Auth** names the
credential an adapter needs; `—` means it works with no credential at all.

| Adapter | What it pulls | Tracked scope | Auth |
|---------|---------------|---------------|------|
| RSS | Feed articles across AI, Crypto, Finance, Security, Dev | 31 active feeds (listed below) | — |
| GitHub Events | Repository activity, trending projects, issue and PR analysis | — | — |
| On-Chain | Whale transaction alerts, DEX volume and stablecoin flows (DefiLlama), DeFi protocol metrics | — | — |
| Social Media | Reddit posts and X posts via Nitter RSS, community sentiment analysis | 11 subreddits | — |
| News API | Real-time news aggregation, keyword-based filtering | — | — |
| Twitter / X | Account timelines via a Nitter RSS instance pool | 19 accounts (incl. `MosslandMOC`) | `TWITTER_BEARER_TOKEN` (optional — adds API v2 keyword search) |
| Discord | Announcement-channel messages | 7 servers (Ethereum, Polygon, Arbitrum, Optimism, Aave, Uniswap, OpenAI) | `DISCORD_BOT_TOKEN` |
| Lens Protocol | GraphQL API — popular publications, profile posts, trending topics | 10 profiles | — |
| Farcaster | Casts via the Neynar API, Warpcast public API fallback | 10 users, 10 channels | `NEYNAR_API_KEY` |
| Coingecko | Trending coins, top gainers/losers, global market stats | 16 coins incl. Mossland (MOC) | — |
| Threads | Public profile scraping of Meta Threads accounts | 3 accounts | — |

RSS feeds live in the top-level `feeds:` section of `config.yaml` — the single list shared by
signal collection and trend analysis. Add or fix feeds there; no code change is needed.

- **AI** (9): OpenAI News, Google AI, arXiv AI, TechCrunch AI, Hacker News, Hugging Face, DeepMind, BAIR, Lil'Log
- **Crypto** (7): CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate, Ethereum Blog, Solana
- **Finance** (3): CNBC Business News, CNBC Finance, Bloomberg Tech
- **Security** (4): The Hacker News, Krebs on Security, Trail of Bits, Schneier
- **Dev** (8): The Verge, Ars Technica, Stack Overflow Blog, GitHub Blog, Meta Engineering, Netflix Tech, Cloudflare, AWS Blog

Four more crypto feeds (Chainlink, Polygon, Paradigm, a16z Crypto) are kept with
`enabled: false` — their URLs are dead and no replacement feed is published.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub PAT (Issues, Labels) | **Yes** |
| `GITHUB_OWNER` | Repository owner | **Yes** |
| `GITHUB_REPO` | Repository name | **Yes** |
| `ANTHROPIC_API_KEY` | Claude API key | For cloud mode |
| `OPENAI_API_KEY` | OpenAI API key | For cloud mode |
| `GEMINI_API_KEY` | Gemini API key | For cloud mode |
| `OLLAMA_HOST` | Ollama server URL | For local mode |
| `MOSS_LOCAL_LLM_ONLY` | Pin the LLM router to Ollama. Defaults to `true`; set `false` to enable the cloud keys above | No (default `true`) |

## Project Structure

```
agentic-orchestrator/
├── ecosystem.config.js      # PM2 configuration
├── .venv/                   # Python virtual environment
├── src/agentic_orchestrator/
│   ├── adapters/            # 11 signal sources: rss, github_events, onchain,
│   │                        #   social, news, twitter, discord, lens,
│   │                        #   farcaster, coingecko, threads
│   ├── api/                 # FastAPI backend
│   │   └── main.py
│   ├── cache/               # Caching layer
│   ├── db/                  # Database models, repositories & rolling backups
│   ├── debate/              # Multi-stage debate system
│   │   ├── protocol.py
│   │   └── multi_stage.py
│   ├── llm/                 # LLM routing
│   │   └── router.py
│   ├── personas/            # 34 agent definitions
│   ├── providers/           # LLM providers (Ollama, APIs)
│   ├── scheduler/           # PM2 task implementations
│   │   ├── __main__.py
│   │   └── tasks.py
│   └── signals/             # Signal processing
├── website/                 # Next.js dashboard
│   ├── src/
│   │   ├── app/             # Pages
│   │   └── components/      # React components
│   └── package.json
└── logs/                    # PM2 log files
```

## Development

```bash
# Test tooling lives in the dev extra
pip install -e ".[dev]"
pytest tests/ -v
```

```bash
cd website && pnpm build   # rebuild the dashboard after a change
```

```bash
# Scheduler tasks, run by hand
python -m agentic_orchestrator.scheduler signal-collect
python -m agentic_orchestrator.scheduler analyze-trends    # local LLM
python -m agentic_orchestrator.scheduler run-debate
python -m agentic_orchestrator.scheduler process-backlog
python -m agentic_orchestrator.scheduler health-check
python -m agentic_orchestrator.scheduler backup-db         # snapshot into data/backup/, auto ~daily
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Mossland Projects

- **[Alpha](https://alpha.moss.land?utm_source=github&utm_medium=referral&utm_campaign=ao-readme)** — Korean crypto × AI media + community. Channel stance, daily AI briefs, RAG Q&A, AI personas, and a 12-tool MCP server.
  - [`MosslandOpenDevs/alpha-mcp`](https://github.com/MosslandOpenDevs/alpha-mcp) — install for Claude, Cursor and Cline
- **[SignalMap](https://signalmap.moss.land)** — multi-source narrative pipeline (Korean YouTube + news + macro). The canonical entity/topic/event store Alpha consumes.
- **[Mossland Projects index](https://github.com/mossland/Projects)** — full ecosystem timeline since 2018.

---

*Built for the Mossland ecosystem - human-guided, AI-powered innovation.*
