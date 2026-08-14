# Mossland Agentic Orchestrator

**한국어** | [English](README.md)

모스랜드 생태계를 위한 마이크로 Web3 서비스를 발굴, 기획, 구현하는 자율 멀티 에이전트 오케스트레이션 시스템입니다.

**버전**: v0.6.19

## 주요 기능

- **멀티 스테이지 토론**: 34개 AI 에이전트가 3단계(발산 → 수렴 → 기획)를 거쳐 토론
- **[다양한 시그널 소스](#시그널-소스)**: RSS, GitHub, 온체인, 소셜, 뉴스, 마켓 데이터에 SignalMap canonical 내러티브 스토어를 더한 12개 어댑터
- **하이브리드 LLM 라우팅**: 로컬 Ollama 모델 + 클라우드 API 폴백 지능형 라우팅
- **휴먼 인 더 루프**: 라벨 프로모션을 통해 개발할 아이디어를 사람이 선택
- **PM2 스케줄링**: PM2를 통한 자동화된 작업 스케줄링 (시그널, 트렌드, 토론, 백로그, 헬스체크)
- **CLI 스타일 대시보드**: https://ao.moss.land 레트로 터미널 테마 웹 인터페이스
- **REST API**: 프로그래밍 방식 접근을 위한 FastAPI 백엔드
- **DB 복원력**: DB 파일이 유실/비워져도 전체 엔드포인트가 죽는 대신 우아하게 강등 — 기동 시 스키마 자기치유, `/status` degradation, 무결성 검사를 거친 롤링 백업(약 1일 주기, 7개 보관, 회귀 인지 보존)
- **자동 배포**: 프로덕션이 `main`을 스스로 추적 — CI 초록불에만 반응하는 5분 풀 루프, 배포 전 DB 스냅샷과 자동 롤백 포함 ([배포](#배포))
- **구조화 LLM 출력**: 트렌드 분석·아이디어 점수화가 디코드 시점에 JSON 스키마를 강제(Ollama `format`), 그 뒤에 절단 감지와 salvage 파싱을 이중 방어로 유지

## 대시보드

오케스트레이터를 실시간으로 모니터링하는 Next.js 기반 CLI 스타일 대시보드이며, 배포 주소는 **https://ao.moss.land**입니다. 로컬 실행은 `cd website && npm ci && npm run dev` 후 http://localhost:3000 에서 확인할 수 있습니다.

| 페이지 | 설명 |
|--------|------|
| `/` | 파이프라인, 활동 피드, 통계가 있는 대시보드 |
| `/trends` | 시그널 소스에서 수집한 트렌드 분석 결과 |
| `/backlog` | GitHub 링크가 있는 아이디어 및 계획 백로그 |
| `/system` | 시스템 아키텍처 및 멀티 에이전트 토론 시각화 |
| `/agents` | 3개 토론 단계의 34개 AI 에이전트 페르소나 |

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│  시그널 수집 - 어댑터 12개                                              │
│  RSS, GitHub Events, On-Chain, Social, News API, Twitter/X,             │
│  Discord, Lens, Farcaster, Coingecko, Threads, SignalMap                │
│                                    │                                    │
│                                    ▼                                    │
│                        ┌───────────────────────┐                        │
│                        │  시그널 집계기        │                        │
│                        │  + 스코어러           │                        │
│                        └───────────┬───────────┘                        │
├────────────────────────────────────┼────────────────────────────────────┤
│                                    ▼                                    │
│                    멀티 스테이지 토론 (34 에이전트)                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 1단계: 발산   (16)  엔지니어, 디자이너, PM, 마케터                │  │
│  │ 2단계: 수렴    (8)  VC, 멘토, 창업자, 전문가                      │  │
│  │ 3단계: 기획   (10)  CPO, PM, 리드, UX 리서치, QA, DevRel          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                    LLM 라우터 (기본값: Ollama 전용)                     │
│  ┌─────────────────────────────┐    ┌────────────────────────────────┐  │
│  │ 로컬 (Ollama)               │    │ 클라우드 API (옵션)            │  │
│  │ - gemma3:4b (전 작업)       │    │ - Claude / OpenAI / Gemini     │  │
│  │ - JSON 스키마를 디코드      │    │ MOSS_LOCAL_LLM_ONLY=true       │  │
│  │   시점에 강제 (format)      │    │ 설정 시 비활성화               │  │
│  └─────────────────────────────┘    └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 빠른 시작

### 1. 설치

```bash
# 클론 및 설치
git clone https://github.com/MosslandOpenDevs/agentic-orchestrator.git
cd agentic-orchestrator

# Python 가상환경 생성 (Python 3.12 이상 필요)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .

# 환경 설정
cp .env.example .env
# .env 파일에 API 키 입력
```

### 2. PM2로 서비스 시작

```bash
# PM2 전역 설치
npm install -g pm2

# 대시보드 먼저 빌드 (moss-ao-web은 next start 실행이라 빌드 산출물 필요)
cd website && npm ci && npm run build && cd ..

# 모든 서비스 시작
pm2 start ecosystem.config.js

# 또는 특정 서비스만 시작
pm2 start ecosystem.config.js --only moss-ao-web
pm2 start ecosystem.config.js --only moss-ao-api
```

PM2가 기동되면 대시보드는 http://localhost:3000, API 문서는 http://localhost:3001/docs 에서 확인할 수 있습니다.

## PM2 서비스

| 서비스 | 스케줄 | 설명 |
|--------|--------|------|
| `moss-ao-signals` | 30분마다 | 모든 어댑터에서 시그널 수집 |
| `moss-ao-trends` | 2시간마다 | 시그널을 트렌드로 분석 (로컬 LLM) |
| `moss-ao-debate` | 6시간마다 | 멀티 스테이지 AI 토론 실행 |
| `moss-ao-backlog` | 4시간마다 | 대기 중인 백로그 항목 처리 |
| `moss-ao-web` | 항시 실행 | Next.js 대시보드 (포트 3000) |
| `moss-ao-api` | 항시 실행 | FastAPI 백엔드 (포트 3001) |
| `moss-ao-health` | 5분마다 | 헬스 모니터링 + 롤링 DB 백업 (약 1일 주기) |
| `moss-ao-deploy` | 5분마다 | 풀 방식 자동 배포, 옵트인 ([docs/deployment.md](docs/deployment.md)) |

```bash
pm2 status                  # 전체 서비스 상태
pm2 logs moss-ao-api        # 특정 서비스 로그
pm2 restart moss-ao-web     # 서비스 재시작
pm2 stop all                # 전체 중지
pm2 monit                   # 리소스 모니터링
```

## 배포

프로덕션은 스스로 배포합니다: 옵트인 `moss-ao-deploy` 잡이 5분마다 `main`을
확인해 움직였을 때만 동작합니다 — GitHub Actions를 통과한 커밋만, DB 스냅샷을
찍은 뒤, diff가 건드린 것만 빌드하고, 배포 후 헬스체크가 실패하면 (재빌드
포함) 롤백합니다. `git clean`은 절대 쓰지 않으므로 서버의 untracked 상태
(`data/orchestrator.db`, `.env`)는 모든 배포에서 보존됩니다. 토론이 실행되는
동안에는 백엔드 배포를 다음 틱으로 미루며, 문서만 바뀐 커밋은 아무것도
재시작하지 않습니다.

```bash
bash scripts/deploy.sh --check   # 드라이런: 무엇을 할지 보고만
bash scripts/deploy.sh           # 다음 틱을 기다리지 않고 즉시 배포
```

배포기는 무엇을 초록불로 볼지에 대해 의도적으로 보수적입니다: CI 체크가 아직
0건이거나 전부 skip된 커밋은 검증 없이 올리지 않고 다음 틱으로 미루며, 배포 전
DB 스냅샷이 실패하면 되돌아갈 곳 없이 배포하는 대신 아예 거부합니다. API가 떠
있는데 레디니스만 실패하는 상태(=DB 문제)라면, 장애가 지속되는 내내 5분마다
재시작하고 롤백하는 대신 배포를 미룹니다.

설치·설정·문제 해결: [docs/deployment.md](docs/deployment.md).

## DB 백업과 복원

데이터베이스는 의도적으로 git에 넣지 않는 단일 SQLite 파일이라, `data/backup/`에
롤링 스냅샷을 둡니다 — 약 24시간마다 하나, 최신 7개 보관, 헬스체크가 찍고 코드
배포 직전에는 강제로 한 번 더 찍습니다.

복원은 파일을 복사하지 말고 명령으로 하십시오:

```bash
python -m agentic_orchestrator.scheduler restore-db --list   # 무엇이 있는지
python -m agentic_orchestrator.scheduler restore-db          # 최신, 또는 --from PATH
```

스냅샷을 검증하고, 다른 프로세스가 쓰는 중이면 거부하고, 교체되는 DB를 따로
보관하며(복원 자체를 되돌릴 수 있게), WAL sidecar를 제거한 뒤 파일을 바꿉니다.

> **스냅샷을 `data/orchestrator.db` 위에 `cp` 하지 마십시오.** DB는 WAL 모드입니다.
> 쓰기 프로세스가 정상 종료가 아니라 크래시나 OOM kill로 죽었다면 — 즉 백업을
> 꺼내야 하는 바로 그 상황이라면 — `orchestrator.db-wal`이 살아남고, SQLite가 방금
> 복사해 넣은 파일 위에 그것을 재생합니다. 복원은 조용히 무효가 되고
> `PRAGMA integrity_check`는 여전히 `ok`를 반환합니다.
> `tests/test_restore.py::TestTheHazard`가 이 현상을 그대로 재현합니다.

## API 엔드포인트

FastAPI 백엔드는 REST API 접근을 제공합니다:

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/health` | GET | 라이브니스 — 프로세스 생존 확인 (DB를 건드리지 않음) |
| `/ready` | GET | 레디니스 — 실제 테이블을 읽고, 못 읽으면 503. 배포기가 게이트로 사용 |
| `/status` | GET | 시스템 상태 |
| `/signals` | GET | 최근 시그널 목록 |
| `/debates` | GET | 토론 결과 목록 |
| `/agents` | GET | 에이전트 페르소나 목록 |
| `/docs` | GET | Swagger 문서 |

## 멀티 스테이지 토론 시스템

모든 토론은 3단계로 진행된다. **정원**은 페르소나 풀 크기(`personas/catalog.py`)이며,
매 라운드는 성격 균형을 맞춘 더 작은 부분집합만 참여시킨다 — **라운드당** 열의 값으로,
`config.yaml`의 `debate.normal.*_agents_per_round`에서 설정한다.

| 단계 | 정원 | 라운드당 | 목적 | 페르소나 |
|------|------|----------|------|----------|
| 1. 발산 | 16 | 8 | 다양한 아이디어와 관점 생성 | 프론트엔드 / 백엔드 / 블록체인 엔지니어, 보안 리서처, DevOps, 프로덕트·UX 디자이너, 프로덕트 매니저, 그로스 마케터, 브랜드 전략가, 비즈니스 애널리스트, 커뮤니티 매니저 |
| 2. 수렴 | 8 | 4 | 아이디어 통합 및 평가 | 크립토 VC·전통 VC 파트너, 액셀러레이터 멘토 2인, 연쇄 창업가와 초기 창업가, 기술·시장 도메인 전문가 |
| 3. 기획 | 10 | 3 | 실행 가능한 구현 계획 생성 | CPO, 시니어 PM, 테크니컬 리드, 프론트엔드 / 백엔드 / 블록체인 리드, UX 리서처, QA 리드, 개발자 릴레이션, 프로젝트 매니저 |

### 토론은 어떤 모델로 도는가

토론은 유료 API가 허용된 유일한 작업이며, 거기까지 가려면 **독립적인 스위치 두 개**가
모두 켜져 있어야 합니다. 둘 다 켜지기 전에는 1원도 쓰지 않습니다:

1. `.env`의 `MOSS_LOCAL_LLM_ONLY=false` — 미설정이거나 true(기본값)인 동안 라우터는
   유료 프로바이더를 아예 만들지 않고, 호출자가 `force_api`를 줘도 무시합니다.
2. `config.yaml`의 `llm.paid_tiers.debate.enabled: true` — 여기서 모델을 지정합니다
   (현재 `gpt-5.4-mini`). 토론의 네 호출 지점만 `paid_tier=debate`를 달고 있습니다.

둘 다 켜져 있으면 발산·수렴·기획·점수화가 그 모델로 돕니다. 하나라도 꺼져 있거나,
프로바이더가 없거나, 예산을 다 썼거나, 로컬 모델이 명시되면 토론은 **실패하지 않고
로컬 `gemma3:4b`로 강등**됩니다. 그 외 파이프라인(트렌드, 번역, 트리아지 점수화)은
언제나 로컬입니다.

알아 둘 두 가지:

- **티어가 켜져 있으면 비용이 실제로 발생합니다.** 일·월 상한의 단일 소스는
  `config.yaml`의 `budget`이며(환경변수가 우선), 상한을 다 쓰면 토론이 중단되는 게
  아니라 로컬로 강등됩니다.
- **로컬로 돌 때는 GPU 하나가 처리량을 결정합니다.** 라운드가 얼마나 빨리 요청을 낼 수
  있는지는 `throttling.ollama`(`min_request_interval`, `max_concurrent_requests`)가
  정하고 둘 다 실제로 적용되므로, 로컬 모드 토론은 유료 모드보다 확연히 느립니다.
  90분 주기 예산에 근접하면 조정할 곳은 그 값들입니다.

각 페르소나는 0-10으로 점수화된 4축 성격 프로필도 함께 가진다. 라운드 부분집합을 이
축들에 걸쳐 균형 잡는 것이 같은 성향의 에이전트만 모이는 것을 막아준다.

- **창의성**: 혁신 vs. 관습
- **분석력**: 데이터 중심 vs. 직관
- **리스크 허용도**: 공격적 vs. 보수적
- **협업**: 팀 중심 vs. 독립적

## 시그널 소스

어댑터 12개가 시그널을 수집하며 모두 `config.yaml`에서 설정한다. **인증**은 해당 어댑터에
필요한 자격 증명이며, `—`는 자격 증명 없이도 동작한다는 뜻이다.

| 어댑터 | 수집 내용 | 추적 범위 | 인증 |
|--------|-----------|-----------|------|
| RSS | AI, Crypto, Finance, Security, Dev 카테고리 피드 기사 | 활성 피드 31개 (아래 목록) | — |
| GitHub Events | 저장소 활동, 트렌딩 프로젝트, 이슈·PR 분석 | — | — |
| 온체인 | 웨일 트랜잭션 알림, DEX 거래량·스테이블코인 흐름(DefiLlama), DeFi 프로토콜 메트릭 | — | — |
| 소셜 미디어 | Reddit 게시물과 Nitter RSS 기반 X 게시물, 커뮤니티 감성 분석 | 서브레딧 11개 | — |
| News API | 실시간 뉴스 집계, 키워드 기반 필터링 | — | — |
| Twitter / X | Nitter RSS 인스턴스 풀을 통한 계정 타임라인 | 계정 19개 (`MosslandMOC` 포함) | `TWITTER_BEARER_TOKEN` (선택 — API v2 키워드 검색 추가) |
| Discord | 공지 채널 메시지 | 서버 7개 (Ethereum, Polygon, Arbitrum, Optimism, Aave, Uniswap, OpenAI) | `DISCORD_BOT_TOKEN` |
| Lens Protocol | GraphQL API — 인기 퍼블리케이션, 프로필 게시물, 트렌딩 토픽 | 프로필 10개 | — |
| Farcaster | Neynar API 기반 캐스트, Warpcast 공개 API 폴백 | 유저 10개, 채널 10개 | `NEYNAR_API_KEY` |
| Coingecko | 트렌딩 코인, 상승/하락 상위 종목, 글로벌 시장 통계 | Mossland(MOC) 포함 코인 16개 | — |
| Threads | Meta Threads 계정 공개 프로필 스크래핑 | 계정 3개 | — |
| SignalMap | 다른 모스랜드 서비스의 발행 피드 — 한국어 YouTube 내러티브 요약과 마켓 펄스, **canonical** 토픽·엔티티·이벤트 ID 포함 (AO는 소비만 하고 만들지 않음) | 시그널 6,747 + 펄스 5,112, 커서 페이징 | `SIGNALMAP_EXPORT_TOKEN` (선택 — 현재 발행은 열려 있음) |

RSS 피드는 `config.yaml`의 최상위 `feeds:` 섹션에 정의되며, 시그널 수집과 트렌드 분석이 이
목록 하나를 공유한다. 피드 추가·수정은 이 파일만 편집하면 되고 코드 변경은 필요 없다.

- **AI** (9개): OpenAI News, Google AI, arXiv AI, TechCrunch AI, Hacker News, Hugging Face, DeepMind, BAIR, Lil'Log
- **Crypto** (7개): CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate, Ethereum Blog, Solana
- **Finance** (3개): CNBC Business News, CNBC Finance, Bloomberg Tech
- **Security** (4개): The Hacker News, Krebs on Security, Trail of Bits, Schneier
- **Dev** (8개): The Verge, Ars Technica, Stack Overflow Blog, GitHub Blog, Meta Engineering, Netflix Tech, Cloudflare, AWS Blog

이 외 크립토 피드 4개(Chainlink, Polygon, Paradigm, a16z Crypto)는 URL이 죽었고 대체 피드도
없어 `enabled: false`로 남겨두었다.

## 환경 변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub PAT (Issues, Labels) | **예** |
| `GITHUB_OWNER` | 저장소 소유자 | **예** |
| `GITHUB_REPO` | 저장소 이름 | **예** |
| `ANTHROPIC_API_KEY` | Claude API 키 | 클라우드 모드용 |
| `OPENAI_API_KEY` | OpenAI API 키 | 클라우드 모드용 |
| `GEMINI_API_KEY` | Gemini API 키 | 클라우드 모드용 |
| `OLLAMA_HOST` | Ollama 서버 URL | 로컬 모드용 |
| `MOSS_LOCAL_LLM_ONLY` | LLM 라우터를 Ollama 전용으로 고정. 기본값 `true`, `false`로 설정해야 위 클라우드 키 사용 | 아니오 (기본 `true`) |
| `MOSS_API_KEY` | 변경 API 라우트에 요구되는 공유 비밀 (`X-API-Key`). 미설정이면 해당 라우트는 503 | 쓰기용 |
| `MOSS_ENABLE_BROWSER_PROJECT_GENERATION` | 공개 대시보드의 생성 버튼이 `MOSS_API_KEY`를 쓰도록 허용. 기본 꺼짐 — 사이트에 사용자 계정이 없으므로 켜면 아무 방문자나 생성을 돌릴 수 있음 | 아니오 (기본 꺼짐) |
| `MOSS_RUN_GENERATED_TESTS` | 레거시 스위치이며 무시됨. 모델이 쓴 테스트는 더 이상 오케스트레이터 프로세스에서 실행되지 않음 | 효과 없음 |

## 프로젝트 구조

```
agentic-orchestrator/
├── ecosystem.config.js      # PM2 설정
├── .venv/                   # Python 가상환경
├── src/agentic_orchestrator/
│   ├── adapters/            # 시그널 소스 12종: rss, github_events, onchain,
│   │                        #   social, news, twitter, discord, lens,
│   │                        #   farcaster, coingecko, threads, signalmap
│   ├── api/                 # FastAPI 백엔드
│   │   └── main.py
│   ├── cache/               # 캐싱 레이어
│   ├── db/                  # 데이터베이스 모델, 레포지토리 & 롤링 백업
│   ├── debate/              # 멀티 스테이지 토론 시스템
│   │   ├── protocol.py
│   │   └── multi_stage.py
│   ├── llm/                 # LLM 라우팅
│   │   └── router.py
│   ├── personas/            # 34개 에이전트 정의
│   ├── providers/           # LLM 프로바이더 (Ollama, APIs)
│   ├── scheduler/           # PM2 태스크 구현
│   │   ├── __main__.py
│   │   └── tasks.py
│   └── signals/             # 시그널 처리
├── website/                 # Next.js 대시보드
│   ├── src/
│   │   ├── app/             # 페이지
│   │   └── components/      # React 컴포넌트
│   └── package.json
└── logs/                    # PM2 로그 파일
```

## 개발

의존성은 잠겨 있습니다. CI와 운영이 모두 `uv.lock`에서 설치하므로, 한 커밋은
어디서든 같은 의존성 그래프로 해석됩니다:

```bash
uv sync --frozen --extra dev      # 또는: pip install -e ".[dev]"
uv run pytest tests/ -v
```

대시보드에도 자체 검사가 있고 CI가 전부 돌립니다 — 예전에는 빌드 실패가 운영
서버에서 배포 도중에야 드러났습니다:

```bash
cd website
npm ci
npm run lint && npm run typecheck && npm test && npm run build
```

```bash
# 스케줄러 태스크 수동 실행
python -m agentic_orchestrator.scheduler signal-collect
python -m agentic_orchestrator.scheduler analyze-trends    # 로컬 LLM
python -m agentic_orchestrator.scheduler run-debate
python -m agentic_orchestrator.scheduler process-backlog
python -m agentic_orchestrator.scheduler health-check
python -m agentic_orchestrator.scheduler backup-db         # data/backup/에 스냅샷, 약 1일 주기 자동
python -m agentic_orchestrator.scheduler restore-db --list # 스냅샷에서 복원 (위 절 참조)
```

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

## 관련 모스랜드 프로젝트

- **[Alpha](https://alpha.moss.land?utm_source=github&utm_medium=referral&utm_campaign=ao-readme)** — 한국어 크립토 × AI 미디어 + 커뮤니티. 채널 스탠스, 데일리 AI 브리프, RAG Q&A, AI 페르소나, 12개 툴 MCP 서버.
  - [`MosslandOpenDevs/alpha-mcp`](https://github.com/MosslandOpenDevs/alpha-mcp) — Claude·Cursor·Cline 설치 방법
- **[SignalMap](https://signalmap.moss.land)** — 멀티 소스 내러티브 파이프라인 (한국어 YouTube + 뉴스 + 매크로). Alpha가 사용하는 canonical 엔티티/토픽/이벤트 스토어.
- **[모스랜드 프로젝트 인덱스](https://github.com/mossland/Projects)** — 2018년부터의 전체 생태계 타임라인.

---

*모스랜드 생태계를 위해 구축됨 - 사람이 가이드하고, AI가 구동하는 혁신.*
