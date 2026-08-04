# Mossland Agentic Orchestrator

[한국어](README.ko.md) | **English**

An autonomous multi-agent orchestration system for discovering, planning, and implementing micro Web3 services for the Mossland ecosystem.

**Version**: v0.6.12

## Key Features

- **Multi-Stage Debate**: 34 AI agents with diverse personas debate through 3 phases (Divergence → Convergence → Planning)
- **Diverse Signal Sources**: 11 adapters — RSS, GitHub Events, On-Chain data, Social Media, News API, Twitter/X, Discord, Lens, Farcaster, Coingecko, Threads
- **Hybrid LLM Routing**: Local Ollama models + Cloud API fallback with intelligent routing
- **Human-in-the-Loop**: Humans select which ideas to develop via label promotion
- **PM2 Scheduling**: Automated task scheduling with PM2 (signals, trends, debates, backlog, health checks)
- **CLI-Style Dashboard**: Retro terminal-themed web interface at https://ao.moss.land
- **REST API**: FastAPI backend for programmatic access
- **DB Resilience**: startup schema self-heal, graceful `/status` degradation, and rolling SQLite backups (~daily, keep 7, integrity-checked, regression-aware retention) — a lost or emptied database file degrades gracefully instead of taking every endpoint down

## Dashboard

A Next.js-based CLI-style dashboard for monitoring the orchestrator in real-time.

**URL**: https://ao.moss.land

### Pages

| Page | Description |
|------|-------------|
| `/` | Dashboard with pipeline, activity feed, and statistics |
| `/trends` | Trend analysis results from signal sources |
| `/backlog` | Ideas and plans backlog with GitHub links |
| `/system` | System architecture and multi-agent debate visualization |
| `/agents` | 34 AI agent personas across 3 debate phases |

### Running Locally

```bash
cd website
pnpm install
pnpm dev
```

Open http://localhost:3000 to view the dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL COLLECTION                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │   RSS   │ │ GitHub  │ │On-Chain │ │ Social  │ │News API │           │
│  │ Adapter │ │ Events  │ │ Adapter │ │ Media   │ │ Adapter │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       └───────────┴───────────┼───────────┴───────────┘                 │
│                               ▼                                          │
│                    ┌──────────────────┐                                  │
│                    │ Signal Aggregator │                                  │
│                    │   + Scorer        │                                  │
│                    └────────┬─────────┘                                  │
├─────────────────────────────┼───────────────────────────────────────────┤
│                             ▼                                            │
│                  MULTI-STAGE DEBATE (34 Agents)                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Phase 1: DIVERGENCE (16 agents)                                 │     │
│  │   Innovator, Skeptic, Pragmatist, Visionary...                 │     │
│  ├────────────────────────────────────────────────────────────────┤     │
│  │ Phase 2: CONVERGENCE (8 agents)                                 │     │
│  │   Synthesizer, Evaluator, Prioritizer, Risk Assessor...        │     │
│  ├────────────────────────────────────────────────────────────────┤     │
│  │ Phase 3: PLANNING (10 agents)                                   │     │
│  │   Architect, Project Manager, Technical Lead...                │     │
│  └────────────────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────────────┤
│                  LLM ROUTER (Ollama-only by default)                     │
│  ┌──────────────────────────┐    ┌──────────────────────────────────┐   │
│  │   Local (Ollama)         │    │   Cloud API (opt-in via flag)   │   │
│  │   - gemma3:4b (chat)     │    │   - Claude / OpenAI / Gemini    │   │
│  │   - qwen3-embedding:0.6b │    │   Disabled when                 │   │
│  │     (embeddings)         │    │   MOSS_LOCAL_LLM_ONLY=true      │   │
│  │                          │    │                                  │   │
│  └──────────────────────────┘    └──────────────────────────────────┘   │
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

### 3. Access the Dashboard

- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:3001/docs

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

### PM2 Commands

```bash
# View all services
pm2 status

# View logs
pm2 logs moss-ao-web
pm2 logs moss-ao-api

# Restart a service
pm2 restart moss-ao-web

# Stop all services
pm2 stop all

# Monitor resources
pm2 monit
```

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

The counts below are **persona pool sizes** (`personas/catalog.py`), not the number
of agents active in a single round. Each round draws a smaller, personality-balanced
subset from the pool — in production 8 / 4 / 3 agents per round respectively, set by
`debate.normal.*_agents_per_round` in `config.yaml`.

### Phase 1: Divergence (16 Agents)
Generate diverse ideas and perspectives:
- **Innovator**: Creative breakthrough ideas
- **Skeptic**: Critical analysis and risk identification
- **Pragmatist**: Practical implementation focus
- **Visionary**: Long-term strategic thinking
- And 12 more specialized agents...

### Phase 2: Convergence (8 Agents)
Synthesize and evaluate ideas:
- **Synthesizer**: Combine related ideas
- **Evaluator**: Score and rank proposals
- **Prioritizer**: Determine execution order
- **Risk Assessor**: Identify potential issues
- And 4 more specialized agents...

### Phase 3: Planning (10 Agents)
Create actionable implementation plans:
- **Architect**: System design
- **Project Manager**: Task breakdown
- **Technical Lead**: Technology decisions
- **Resource Planner**: Resource allocation
- And 6 more specialized agents...

### Agent Personality System

Each agent has a 4-axis personality profile:
- **Creativity**: Innovation vs. Convention (0-10)
- **Analytical**: Data-driven vs. Intuitive (0-10)
- **Risk Tolerance**: Aggressive vs. Conservative (0-10)
- **Collaboration**: Team-oriented vs. Independent (0-10)

## Signal Sources

### RSS Feeds
31 active feeds across 5 categories, defined in the top-level `feeds:` section of
`config.yaml` — the single source shared by signal collection and trend analysis:
- **AI** (9): OpenAI News, Google AI, arXiv AI, TechCrunch AI, Hacker News, Hugging Face, DeepMind, BAIR, Lil'Log
- **Crypto** (7): CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate, Ethereum Blog, Solana
- **Finance** (3): CNBC Business News, CNBC Finance, Bloomberg Tech
- **Security** (4): The Hacker News, Krebs on Security, Trail of Bits, Schneier
- **Dev** (8): The Verge, Ars Technica, Stack Overflow Blog, GitHub Blog, Meta Engineering, Netflix Tech, Cloudflare, AWS Blog

Four more crypto feeds (Chainlink, Polygon, Paradigm, a16z Crypto) are kept in
`config.yaml` with `enabled: false` — their URLs are dead and no replacement feed
is published. Add or fix feeds by editing `config.yaml`; no code change is needed.

### GitHub Events
- Repository activity tracking
- Trending projects monitoring
- Issue and PR analysis

### On-Chain Data
- Whale transaction alerts
- DEX volume and stablecoin flows (DefiLlama)
- DeFi protocol metrics

### Social Media
- Reddit (11 subreddits) and X (Twitter) posts via Nitter RSS
- Community sentiment analysis

### News API
- Real-time news aggregation
- Keyword-based filtering

### Twitter / X
- Nitter RSS instance pool across 19 tracked accounts (including `MosslandMOC`)
- Optional Twitter API v2 keyword search when `TWITTER_BEARER_TOKEN` is set

### Discord
- 7 tracked servers (Ethereum, Polygon, Arbitrum, Optimism, Aave, Uniswap, OpenAI)
- Announcement-channel messages require `DISCORD_BOT_TOKEN`

### Lens Protocol
- GraphQL API (popular publications, profile posts, trending topics)
- 10 tracked profiles

### Farcaster
- Neynar API (`NEYNAR_API_KEY`) with Warpcast public API fallback
- 10 tracked users and 10 channels

### Coingecko
- Trending coins, top gainers/losers, global market stats
- 16 tracked coins including Mossland (MOC)

### Threads
- Public profile scraping of 3 Meta Threads accounts (no authentication required)

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
│   ├── adapters/            # Signal source adapters
│   │   ├── rss.py
│   │   ├── github_events.py
│   │   ├── onchain.py
│   │   ├── social.py
│   │   ├── news.py
│   │   ├── twitter.py
│   │   ├── discord.py
│   │   ├── lens.py
│   │   ├── farcaster.py
│   │   ├── coingecko.py
│   │   └── threads.py
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

### Running Tests

```bash
# Test tooling lives in the dev extra
pip install -e ".[dev]"
pytest tests/ -v
```

### Building the Website

```bash
cd website
pnpm build
```

### Manual Task Execution

```bash
# Signal collection
python -m agentic_orchestrator.scheduler signal-collect

# Trend analysis (local LLM)
python -m agentic_orchestrator.scheduler analyze-trends

# Run debate
python -m agentic_orchestrator.scheduler run-debate

# Process backlog
python -m agentic_orchestrator.scheduler process-backlog

# Health check
python -m agentic_orchestrator.scheduler health-check

# Snapshot the SQLite DB into data/backup/ (also runs automatically ~daily)
python -m agentic_orchestrator.scheduler backup-db
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Mossland Projects

- **[Alpha](https://alpha.moss.land?utm_source=github&utm_medium=referral&utm_campaign=ao-readme)** (`alpha.moss.land`) — Korean crypto × AI media + community. Surfaces channel stance, daily AI briefs, RAG Q&A, AI personas, and a 12-tool MCP server. See also [`MosslandOpenDevs/alpha-mcp`](https://github.com/MosslandOpenDevs/alpha-mcp) for Claude/Cursor/Cline install.
- **[SignalMap](https://signalmap.moss.land)** (`signalmap.moss.land`) — multi-source narrative pipeline (Korean YouTube + news + macro). Provides the canonical entity/topic/event store consumed by Alpha.
- **[Mossland Projects index](https://github.com/mossland/Projects)** — full ecosystem timeline since 2018.

---

*Built for the Mossland ecosystem - human-guided, AI-powered innovation.*

*v0.6.12 - Route-ordering fix: /signals/timeline and /plans/pending-approval are reachable again; version reporting tracks pyproject.toml*
