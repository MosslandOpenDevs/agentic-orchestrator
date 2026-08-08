# MOSS.AO - Claude Code 참조 문서

이 문서는 Claude Code가 프로젝트 작업 시 참조할 수 있는 정보를 담고 있습니다.

## 프로젝트 개요

**MOSS.AO (Mossland Agentic Orchestrator)**는 AI 에이전트들이 토론을 통해 아이디어를 생성하고 기획안을 작성하는 멀티에이전트 오케스트레이션 시스템입니다.

- **공개 URL:** https://ao.moss.land
- **GitHub:** https://github.com/MosslandOpenDevs/agentic-orchestrator

## 핵심 철학

### 1. 다양한 시그널 소스 (12개 어댑터)

**목적:** 최신 트렌드를 빠르게 파악 → 신선한 아이디어의 기반 마련

```
RSS, GitHub, OnChain, Social, News, Twitter, Discord, Lens, Farcaster, Coingecko, Threads,
SignalMap
                                    ↓
                        최신 트렌드 실시간 수집
                                    ↓
                        신선한 아이디어 기반 확보
```

앞의 11개는 서드파티 API를 직접 읽는다. **SignalMap만 다른 모스랜드 서비스의 발행
계층을 읽으며**, canonical entity·topic·event ID를 함께 가져온다 — AO는 그 ID를
소비할 뿐 새로 만들지 않는다 (`docs/signalmap.md`).

### 2. 멀티에이전트 1차 (발산 단계)

**목적:** 뻔하지 않고, 다양한 시선으로 → 신선하고 창의적인 다양한 아이디어 도출

- **SCAMPER 창의성 기법**: 대체, 결합, 적용, 수정, 전용, 제거, 역발상
- **측면사고 프롬프트**: Blue Sky, 역설 접근, 교차 영역 혁신
- **다양성 인식 에이전트 선택**: 4축 성격 균형 (창의성, 분석력, 리스크, 협업)
- **도전자 역할 보장**: 집단사고 방지를 위한 반대 의견 에이전트

### 3. 멀티에이전트 2차 (수렴/기획 단계)

**목적:** 다양한 전문적 시각으로 → 구체적이고 실현 가능한 고품질 아이디어로 발전

- **가중치 평가**: 참신성 30%, 실현가능성 25%, 관련성 20%, 영향력 15%, 시급성 10%
- **상세 기획안 필수 섹션**: 프로젝트 개요, 기술 아키텍처, 실행 계획, 리스크, KPI
- **자동 점수화**: score ≥ 7.0 → 플랜 자동 생성, score < 4.0 → 아카이브

## 프로젝트 구조

```
agentic-orchestrator/
├── src/agentic_orchestrator/    # Python 백엔드
│   ├── adapters/                # 시그널 어댑터 (12개)
│   │   ├── base.py              # BaseAdapter / AdapterConfig / SignalData
│   │   ├── rss.py               # RSS 피드 (config.yaml `feeds`에서 로드)
│   │   ├── github_events.py     # GitHub Trending/Releases
│   │   ├── onchain.py           # DefiLlama, Whale Alert, DEX
│   │   ├── social.py            # Reddit, Nitter
│   │   ├── news.py              # NewsAPI, Cryptopanic, HN
│   │   ├── twitter.py           # Twitter/X (Nitter RSS 풀)
│   │   ├── discord.py           # Discord 서버 공지
│   │   ├── lens.py              # Lens Protocol (GraphQL)
│   │   ├── farcaster.py         # Farcaster (Neynar API)
│   │   ├── coingecko.py         # Coingecko (시장 데이터, 트렌딩)
│   │   ├── threads.py           # Meta Threads (공개 프로필 스크래핑)
│   │   └── signalmap.py         # SignalMap 발행 피드 (커서·epoch·canonical ID)
│   ├── api/                     # FastAPI 서버 (포트 3001)
│   │   └── main.py              # API 엔드포인트 정의
│   ├── db/                      # SQLAlchemy 모델 & 리포지토리
│   │   ├── models.py            # 데이터베이스 모델
│   │   ├── repositories.py      # 데이터 액세스 레이어
│   │   ├── connection.py        # DB 연결 관리
│   │   └── backup.py            # SQLite 롤링 백업 (v0.6.10)
│   ├── debate/                  # 멀티스테이지 토론 시스템
│   │   ├── multi_stage.py       # 3단계 토론 (발산→수렴→기획)
│   │   └── protocol.py          # 토론 프로토콜 정의
│   ├── llm/                     # LLM 라우터
│   │   └── router.py            # Ollama, Claude, OpenAI 라우팅
│   ├── personas/                # AI 에이전트 페르소나 (34명)
│   ├── project/                 # Plan → Project 자동 생성
│   │   ├── parser.py            # Plan 마크다운 파싱
│   │   ├── templates.py         # 기술 스택별 템플릿
│   │   ├── generator.py         # LLM 코드 생성
│   │   └── scaffold.py          # 프로젝트 생성 오케스트레이션
│   ├── scheduler/               # PM2 스케줄 작업
│   │   ├── __main__.py          # CLI 엔트리포인트
│   │   ├── tasks.py             # 작업 구현 (signal, debate, backlog, project)
│   │   ├── backlog_triage.py    # 백로그 소비자: scored 아이디어 재평가→종결 (v0.6.16)
│   │   └── issue_lifecycle.py   # GitHub 이슈 미러 닫기 (파이프라인 연동 + 에이징)
│   ├── translation/             # 양방향 번역 모듈
│   │   └── translator.py        # ContentTranslator (EN↔KO)
│   ├── scripts/                 # 유틸리티 스크립트
│   │   └── migrate_bilingual.py # 기존 데이터 번역 마이그레이션
│   ├── signals/                 # 신호 수집기 (어댑터는 위 adapters/ 참조)
│   │   ├── aggregator.py        # 신호 수집 조율 (12개 어댑터 구성)
│   │   ├── scorer.py            # 신호 점수화
│   │   └── storage.py           # 신호 DB 저장
│   └── trends/                  # 트렌드 분석
│       ├── feeds.py             # RSS 페치 (config.yaml `feeds`에서 로드)
│   │   ├── analyzer.py          # 트렌드 분석 (Ollama)
│   │   ├── models.py            # FeedConfig / FeedItem
│   │   └── storage.py           # 트렌드 마크다운 저장
│   └── pathutil.py              # 공개 응답용 경로 축약 (호스트 접두사 제거)
├── website/                     # Next.js 프론트엔드 (포트 3000)
│   ├── src/app/                 # App Router 페이지
│   │   ├── page.tsx             # 대시보드 (/)
│   │   ├── ideas/page.tsx       # 아이디어 백로그
│   │   ├── debates/page.tsx     # 토론 목록 (실시간 폴링)
│   │   ├── agents/page.tsx      # 에이전트 목록
│   │   └── system/page.tsx      # 시스템 상태
│   ├── src/components/          # React 컴포넌트
│   │   ├── modals/              # 모달 시스템 (ModalProvider, TerminalModal)
│   │   └── details/             # 상세 보기 컴포넌트
│   └── src/lib/                 # 유틸리티
│       ├── api.ts               # API 클라이언트
│       ├── types.ts             # TypeScript 타입
│       ├── i18n.tsx             # 다국어 지원 (EN/KO)
│       ├── markdown-html.ts     # renderMarkdown(sanitize) / stripMarkdown(평문)
│       └── metadata.ts          # 통합 title/공유(OG·Twitter) 규칙 단일 소스
├── data/                        # 데이터 디렉토리
│   ├── orchestrator.db          # SQLite 데이터베이스
│   └── trends/                  # 트렌드 분석 결과 (마크다운)
├── projects/                    # 자동 생성된 프로젝트
│   └── {project-name}/          # LLM 생성 프로젝트 스캐폴드
├── docs/                        # 설계 문서
│   ├── pipeline.md              # 아이디어 생성 파이프라인
│   ├── labels.md                # GitHub 라벨 가이드
│   ├── projects.md              # 프로젝트 관리 가이드
│   ├── deployment.md            # 자동 배포 절차·가드·문제 해결
│   ├── signalmap.md             # SignalMap 피드 소비자 계약
│   └── direction.md             # 장기 방향 (Decision Intelligence)
└── ecosystem.config.js          # PM2 설정
```

## 인프라 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         인터넷                                  │
│                            │                                    │
│                            ▼                                    │
│                    ao.moss.land                                 │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                        │
│              │   AWS Lightsail         │                        │
│              │   (Nginx Reverse Proxy) │                        │
│              └───────────┬─────────────┘                        │
│                          │                                      │
│            ┌─────────────┴─────────────┐                        │
│            │                           │                        │
│            ▼                           ▼                        │
│     /api/* 요청                   /* 요청                       │
│            │                           │                        │
│            ▼                           ▼                        │
│  ┌─────────────────────────────────────────────┐                │
│  │           개발/운영 서버                     │                │
│  │  ┌─────────────────┐  ┌─────────────────┐   │                │
│  │  │ FastAPI Backend │  │ Next.js Frontend│   │                │
│  │  │   Port: 3001    │  │   Port: 3000    │   │                │
│  │  └─────────────────┘  └─────────────────┘   │                │
│  └─────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

**실제 IP 주소는 `CLAUDE.local.md` 파일 참조 (gitignore 처리됨)**

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | API 인덱스 (버전, 엔드포인트 목록) |
| GET | `/health` | 라이브니스 — 프로세스 생존만 확인 (DB 미사용) |
| GET | `/ready` | 레디니스 — 실제 테이블을 읽어 확인, 실패 시 503 (배포 게이트가 사용) |
| GET | `/status` | 시스템 상태 및 통계 |
| GET | `/signals` | 수집된 신호 목록 |
| GET | `/signals/timeline` | 신호 수집 타임라인 (`period=24h\|7d`) |
| GET | `/signals/{id}` | 시그널 상세 정보 |
| GET | `/trends` | 분석된 트렌드 |
| GET | `/ideas` | 아이디어 백로그 |
| GET | `/ideas/{id}` | 아이디어 상세 |
| GET | `/ideas/{id}/lineage` | 아이디어 계보 (시그널→트렌드→토론→플랜) |
| GET | `/debates` | 토론 세션 목록 |
| GET | `/debates/{id}` | 토론 상세 (메시지 포함) |
| GET | `/plans` | 기획 문서 목록 |
| GET | `/plans/pending-approval` | 승인 대기 중인 Draft 플랜 목록 |
| GET | `/plans/{id}` | 기획 문서 상세 |
| POST | `/plans/{id}/generate-project` | Plan에서 프로젝트 생성 (비동기) |
| GET | `/plans/{id}/project` | Plan의 프로젝트 조회 |
| GET | `/projects` | 생성된 프로젝트 목록 |
| GET | `/projects/{id}` | 프로젝트 상세 |
| GET | `/jobs/{id}` | 비동기 작업 상태 조회 |
| POST | `/plans/{id}/approve` | Draft 플랜 수동 승인 (generate_project=true로 즉시 프로젝트 생성 가능) |
| GET | `/agents` | 에이전트 목록 |
| GET | `/adapters` | 시그널 어댑터 목록 및 상태 |
| GET | `/pipeline/live` | 실시간 파이프라인 상태 및 전환율 |
| GET | `/usage` | API 사용량 통계 |
| GET | `/activity` | 최근 활동 로그 (실제 DB 데이터 기반) |

> **라우트 등록 순서 주의:** Starlette/FastAPI는 **등록 순서대로** 매칭하므로,
> `/signals/timeline`처럼 리터럴 경로는 반드시 같은 접두사의 파라미터 라우트
> (`/signals/{signal_id}`)보다 **먼저** 선언해야 한다. 순서가 뒤바뀌면 리터럴
> 라우트는 영구히 도달 불가능해지고 `signal_id="timeline"`으로 바인딩된다.
> `tests/test_api.py::TestLiteralRouteOrdering::test_no_literal_route_is_shadowed`가
> 전체 라우트 테이블을 검사해 이 회귀를 차단한다.

> **호스트 경로는 응답에 싣지 않는다.** `Project.directory_path`에는 스캐폴드가 쓴
> 절대 경로(`/home/<계정>/agentic-orchestrator/projects/<name>`)가 들어가는데,
> 이 API는 public 저장소 앞의 공개 사이트가 소비한다. `pathutil.public_project_path()`가
> 저장소 기준 경로(`projects/<name>`)로 좁히고, `Project.to_dict()`와
> `ProjectGenerationResult.to_dict()`(= `GET /jobs/{id}`가 그대로 반환) 두 곳이 이를
> 거친다. **컬럼 값은 그대로 둔다** — 스캐폴드·빌드 게이트·git이 실제 경로를 쓴다.
> 쓰기 시점이 아니라 직렬화 시점에 좁히므로 기존 행도 마이그레이션 없이 덮인다.
> 새 필드가 경로·호스트명·계정을 담게 되면 같은 처리를 해야 한다
> (`tests/test_project_path_privacy.py`). 실값은 `CLAUDE.local.md` 참조.
>
> **예외 메시지가 뒷문이다.** `str(e)`는 실패한 절대 경로를 그대로 달고 나온다
> (`[Errno 2] ...: '/home/<계정>/.../main.py'`). 응답에 실리는 자리 —
> `GET /jobs/{id}`(**인증 없음**), `/adapters`의 오류 필드 — 는 반드시
> `pathutil.redact_paths()`를 거칠 것. 같은 이유로 httpx의 `HTTPStatusError`를
> 문자열에 통째로 끼워 넣지 말 것: 메시지가 `for url '<base_url>/...'`로 끝나고
> 그 `base_url`이 사무실 LAN Ollama 주소다 (`providers/ollama.py`는 상태 코드만
> 남긴다).

## 데이터베이스 스키마

**위치:** `data/orchestrator.db` (SQLite)

### 주요 테이블

| 테이블 | 설명 | 주요 컬럼 |
|--------|------|-----------|
| `signals` | 수집된 신호 | source, category, title, title_ko, score, sentiment |
| `trends` | 분석된 트렌드 | name, name_ko, description, description_ko, score |
| `ideas` | 생성된 아이디어 | title, title_ko, summary, summary_ko, status, score |
| `debate_sessions` | 토론 세션 | topic, phase, status, participants |
| `debate_messages` | 토론 메시지 | agent_id, agent_name, message_type, content, content_ko |
| `plans` | 기획 문서 | title, title_ko, final_plan, final_plan_ko, status |
| `projects` | 생성된 프로젝트 | plan_id, name, directory_path, tech_stack, status |
| `api_usage` | API 사용량 | provider, model, cost_usd, request_count |

### 중요 스키마 노트

- **`debate_sessions.idea_id`**: `nullable=True` (독립 토론 지원)
- **`ideas.score`**: 토론 중 에이전트들이 부여한 평균 점수
- **`*_ko` 필드**: 한글 번역 필드 (양방향 번역 지원)

### DB 자기치유 & 롤링 백업 (v0.6.10)

프로덕션 DB는 git에 없는 단일 SQLite 파일이라 유실되면 모든 DB 엔드포인트가
한꺼번에 500이 났다 (2026-07 장애). 세 겹의 방어가 추가됨:

1. **기동 시 스키마 자기치유**: API의 FastAPI lifespan 훅과 스케줄러 CLI 명령
   (`backup-db` 제외 — 백업은 대상 DB를 변경하면 안 됨)이 시작 시 멱등적
   `ensure_schema()`(= `create_tables()` + 부팅 레이스 재시도)를 실행. 빈/유실
   DB → "no such table" 500 대신 비어 있지만 동작하는 DB로 강등되고,
   파이프라인이 다시 채움.
2. **`/status` graceful degradation**: 통계 쿼리 실패 시 500 대신
   `status="degraded"` + 0 stats로 200 응답 (moss.land 거버넌스 위젯 계약 유지).
3. **롤링 백업** (`db/backup.py`): `moss-ao-health`(5분 주기)가 약 24시간 간격으로
   `data/orchestrator.db` → `data/backup/`에 스냅샷 (최신 7개 보관). 증분 복사로
   writer 블로킹 방지, `.tmp` 작성 → `quick_check` 통과 후 원자적 rename(부분/손상
   파일이 간격을 막거나 슬롯을 차지할 수 없음), 실패 시 다음 5분 틱에 재시도.
   **회귀 인지 프루닝**: 히스토리(ideas/plans/debate_sessions) 행 수가 직전 스냅샷
   대비 급감하면 프루닝을 중단해 사고 이전 백업을 보존 — 시그널이 30분 만에
   빈 DB를 다시 채워도 안전. DB가 없거나/비었거나/데이터가 없거나/무결성 실패면
   건너뜀. 수동 실행: `python -m agentic_orchestrator.scheduler backup-db`,
   복원은 `python -m agentic_orchestrator.scheduler restore-db`

**복원 절차**: 손으로 파일을 복사하지 말고 명령을 쓸 것.

```bash
# 1) 무엇이 있는지 본다 (스냅샷별 시각·크기·행 수·무결성)
python -m agentic_orchestrator.scheduler restore-db --list

# 2) 쓰기 프로세스를 멈추고
pm2 stop moss-ao-api moss-ao-signals moss-ao-trends moss-ao-debate moss-ao-backlog moss-ao-health

# 3) 복원한다 (기본값은 최신 스냅샷; --from 으로 지정 가능)
python -m agentic_orchestrator.scheduler restore-db

# 4) 다시 올린다
pm2 restart all
```

`restore-db`는 스냅샷 검증(무결성 + 실제 행 존재) → 다른 프로세스가 쓰는 중이면 거부 →
**현재 DB를 `orchestrator.db.pre-restore-<시각>`으로 따로 보관**(복원 자체를 되돌릴 수
있게) → 교체 파일을 먼저 만든 뒤 sidecar 제거 후 스왑 → 결과 검증 순으로 진행한다.
종료 코드: `0` 완료, `2` 복원할 스냅샷 없음, `1` 거부/실패.

> **왜 손으로 복사하면 안 되는가.** DB는 WAL 모드다. 쓰기 프로세스가 정상 종료가 아니라
> 강제 종료(OOM kill, `kill -9`, 크래시 — 즉 백업을 꺼내야 하는 바로 그 상황)로 죽으면
> `data/orchestrator.db-wal`이 살아남는다. 그 옆에 스냅샷을 `cp`로 덮어쓰면 SQLite가
> 옛 WAL을 새 파일 위에 **재생**한다. 복원은 조용히 무효가 되고 `PRAGMA integrity_check`는
> `ok`를 반환한다 — 복원했다고 믿은 채 잃은 데이터를 그대로 안고 가게 된다.
> `tests/test_restore.py::TestTheHazard`가 이 현상(스냅샷 1행 → 복원 후 401행, 무결성 ok)을
> 실제로 재현해 고정해 둔다.

배포 시 `git clean -fdx`는 반드시 `-e data -e .env`와 함께 사용할 것.

### 커넥션 풀과 저널 모드

파일 SQLite는 **커넥션을 세션마다 따로** 잡는다 (`db/connection.py`). 예전에는
파일 DB에도 `StaticPool`을 써서 프로세스 안의 모든 `Session`이 커넥션 하나 =
트랜잭션 하나를 공유했고, 그래서 한 요청의 rollback이 다른 요청의 미커밋 쓰기를
지우고 긴 프로젝트 생성이 API 전체를 자기 트랜잭션에 묶어 둘 수 있었다.
인메모리 DB(`:memory:`)만 `StaticPool`을 유지한다 — 커넥션이 곧 데이터베이스라
공유하지 않으면 매번 빈 DB가 되기 때문이다.

커넥션이 갈라진 만큼 동시성이 실제로 발생하므로 파일 DB에는
`journal_mode=WAL`(읽기와 쓰기 동시 진행)과 `busy_timeout=30s`(잠금 대기 시
"database is locked" 대신 대기)를 함께 건다. `PRAGMA foreign_keys=ON`은 그대로다.

## 환경 변수

### 웹사이트 (`website/.env.local`)

```bash
# 프로덕션: /api 사용 (Nginx 프록시 경유)
NEXT_PUBLIC_API_URL=/api

# 로컬 개발 시: 직접 백엔드 호출
# NEXT_PUBLIC_API_URL=http://localhost:3001
```

**중요:** `NEXT_PUBLIC_*` 변수는 빌드 시점에 포함되므로, 변경 후 반드시:
1. `npm run build`
2. `pm2 restart moss-ao-web`

## RSS 피드 소스 (v0.6.11)

**단일 소스: `config.yaml`의 최상위 `feeds:` 섹션.** 코드에 피드를 하드코딩하지 말 것.

두 경로가 같은 리스트를 읽는다:

| 소비자 | 파일 | 용도 |
|--------|------|------|
| 시그널 수집 | `adapters/rss.py` `RSSAdapter` (via `signals/aggregator.py`) | 30분마다 신호 수집 |
| 트렌드 분석 | `trends/feeds.py` `FeedFetcher` | 2시간마다 트렌드 생성 |

현재 등록: **35개 항목 중 31개 활성** (ai 9, crypto 7+4비활성, finance 3, security 4, dev 8).

```yaml
feeds:
  ai:
    - name: "OpenAI News"
      url: "https://openai.com/news/rss.xml"
    - name: "Dead Feed"
      url: "https://example.com/gone.xml"
      enabled: false   # 로드 시 제외됨 (fetch 루프까지 가지 않음)
```

- 키: `name`(필수), `url`(필수), `enabled`(기본 true)
- `feeds` 값은 반드시 `카테고리 → 피드 리스트` 매핑이어야 한다. 플랫 리스트나 문자열로
  잘못 쓰면 로드 시 거부되고 `FALLBACK_FEEDS`로 강등된다 (예외로 죽지 않음)
- `trends/models.py`의 `FeedConfig`에 `weight` 필드가 남아 있지만 **읽는 코드가 없다** —
  설정해도 아무 효과 없음. 트렌드 가중치를 실제로 쓰려면 먼저 소비 코드를 구현할 것
- 피드 추가/수정은 config.yaml만 편집 → 코드 변경·재배포 불필요 (프로세스 재시작은 필요)
- `RSSAdapter.FALLBACK_FEEDS`(5개)는 config.yaml을 못 읽을 때만 쓰는 비상용 — 여기에 피드를 추가하지 말 것
- 구버전 `trends.feeds` 위치도 하위 호환으로 계속 읽지만 deprecated 경고를 남긴다

> **배경 (v0.6.11 이전):** 리스트가 두 벌로 갈라져 있었다. `config.yaml`의 `trends.feeds`(16개)는
> 트렌드 분석만 사용했고, 실제 신호 수집은 `adapters/rss.py`에 하드코딩된 32개를 사용했다
> (`aggregator.py`가 `RSSAdapter()`를 인자 없이 생성). 두 리스트는 서로 다른 URL로 표류했고
> 하드코딩 쪽 4개(Chainlink, Polygon, Paradigm, a16z Crypto)는 죽은 URL이었다.
> 0.6.11에서 중복(같은 호스트·다른 URL 8건)을 정리한 합집합으로 병합해 config.yaml을
> 단일 소스로 만들고, 죽은 4개는 `enabled: false`로 남겨 이력을 보존했다.

## SignalMap 신호 피드 (v0.6.24)

12번째 어댑터이자 **다른 모스랜드 서비스를 읽는 유일한 어댑터**다. SignalMap이
canonical entity·topic·event ID를 소유하고 AO·Media·Alpha가 소비한다 — AO는
canonical ID를 만들지 않는다. 전체 계약은 **`docs/signalmap.md`** 참조.

```
GET https://signalmap.moss.land/api/signal/v1/manifest
GET https://signalmap.moss.land/api/signal/v1/signals?since=<cursor>&limit=<n>
```

운영에서 반드시 알아야 할 네 가지:

| 항목 | 내용 |
|------|------|
| **커서** | `"<updatedAt>\|<id>"`. **재구성하지 말고 응답의 `cursor.next`를 그대로 되돌려줄 것** — 첫 발행의 11,859건이 전부 같은 `updatedAt`이라 타임스탬프만으로는 무한루프이거나 유실이다 (2026-08-06 실측). `cursor.next`는 배타적이고 `limit`은 2000에서 조용히 클램프된다 |
| **epoch** | 리비전 원장의 세대. 바뀌면 모든 레코드가 `revision: 1`로 돌아오므로 저장된 커서를 버리고 **전체 재동기화**한다. 이 방어가 없으면 이후의 모든 업데이트를 영구히 무시하면서 폴링은 계속 200을 반환한다 |
| **`sourceWatermark`** | 알림 대상. `generatedAt`은 수집이 죽어도 움직이고 레코드 수는 **줄지 않고 늘기를 멈출 뿐**이라 조용한 날과 구별되지 않는다. watermark만이 구별한다 → `GET /status`의 `components.signal_feed` + WARNING 로그 |
| **`verified: false`** | 발행 중간에 읽어 두 릴리스가 섞였다는 뜻. 커서를 전진시키지 않고 중단, 다음 틱에 재시도 |

지켜야 할 규칙 셋 (어댑터가 코드로 강제한다):

1. **외래키는 canonical ID만.** `clusters.json`의 cluster id는 재클러스터링 시
   바뀌고 원본 라벨은 회차마다 다르다 → `raw_data.unstable_labels.*`에 이름으로
   표시해 둔다
2. **정치 안전 모드(`policy.politicalSafety`) 레코드는 기본적으로 적재하지 않는다.**
   `evidence.claims`가 설계상 비어 있고 재구성이 금지돼 있는데, AO 하류는 전부
   "텍스트를 모델에 주고 뜻을 묻는" 일이라 프롬프트 어디서든 규칙이 깨질 수 있다.
   적재하지 않으면 깨질 수 없다 (`include_political_safety: false`)
3. **`stance`는 묶음의 갈림 축에 대한 상대 위치다.** `axis.comparable: false`면
   합산·발산 점수·"입장을 바꿨다" 판정 모두 금지. 현재 AO에 stance 집계 코드는 없다

`Signal` 저장 시: `collected_at`은 **폴링 시각이 아니라 상류 사건 시각**(`occurredAt`),
`Signal.topics`/`entities`는 canonical ID만, 정체성은 `SignalData.external_id`(발행자
id)를 따르므로 상류에서 제목이 수정돼도 행이 갈라지지 않고 `revision`이 오르면
기존 행이 갱신된다.

설정은 `config.yaml`의 최상위 `signalmap:` 섹션, 상태는 `data/signalmap_state.json`
(커서·epoch·watermark). 전체 재동기화는 그 파일을 지우면 되고 멱등하다.

## PM2 프로세스 관리

```bash
# 상태 확인
pm2 status

# 주요 프로세스
moss-ao-web      # Next.js 프론트엔드 (포트 3000) - 상시 실행
moss-ao-api      # FastAPI 백엔드 (포트 3001) - 상시 실행
moss-ao-signals  # 신호 수집기 (TEST: 10분, PROD: 30분)
moss-ao-trends   # 트렌드 분석 (TEST: 30분, PROD: 2시간)
moss-ao-debate   # 토론 스케줄러 (TEST: 1시간, PROD: 6시간)
moss-ao-backlog  # 백로그 처리 (TEST: 30분, PROD: 4시간)
moss-ao-health   # 헬스체크 (5분마다)
moss-ao-deploy   # 자동 배포 폴러 (5분마다, .env의 MOSS_AO_AUTO_DEPLOY=1일 때만 등록)

# 재시작 (환경변수 갱신 포함)
pm2 restart moss-ao-web --update-env
pm2 restart moss-ao-api --update-env

# 프로세스 삭제 후 재시작 (캐시된 환경변수 문제 시)
pm2 delete moss-ao-web && pm2 start ecosystem.config.js --only moss-ao-web

# 로그 확인
pm2 logs moss-ao-api --lines 50
pm2 logs moss-ao-debate --lines 100

# 설정 저장
pm2 save
```

### 현재 운영 모드: PRODUCTION (v0.6.9)

`ecosystem.config.js`의 `TEST_MODE = false`로 프로덕션 스케줄 적용 중.
`config.yaml`의 `debate.test_mode: false`, `throttling.test_mode: false` 모두 프로덕션 모드:

| 작업 | 주기 | Cron |
|------|------|------|
| Signals | 30분마다 | `5,35 * * * *` |
| Trends | 2시간마다 | `15 */2 * * *` |
| Debate | 6시간마다 | `25 */6 * * *` |
| Backlog | 4시간마다 | `45 */4 * * *` |

> 분(minute)이 정각이 아니라 :05/:15/:25/:45로 **스태거**되어 있다 — 정각 동시
> 기동이 단일 인스턴스 Ollama 큐를 폭주시켜 HTTP 503을 냈던 이력 때문
> (`ecosystem.config.js`의 `SCHEDULES` 주석 참조). 문서/예측에 크론을 쓸 때
> 정각 기준으로 계산하지 말 것 — 예: 백로그 틱은 16:00이 아니라 16:45다.

토론 에이전트 설정 (`config.yaml`의 `debate.normal`, `debate.test_mode: false`):

| 단계 | 페르소나 풀 (전체 정원) | 라운드당 참여 | 라운드 수 |
|------|------------------------|--------------|----------|
| Divergence | 16명 | 8명 | 3 |
| Convergence | 8명 | 4명 | 2 |
| Planning | 10명 | 3명 | 2 |

- **예상 시간**: ~30분+
- Planning은 단일 GPU Ollama 타임아웃 방지를 위해 라운드당 5→3으로 하향

> **풀 정원 vs 라운드당 참여 인원은 서로 다른 숫자다.**
> 정원(16/8/10)은 `personas/catalog.py`의 `DIVERGENCE_AGENTS`/`CONVERGENCE_AGENTS`/
> `PLANNING_AGENTS` 리스트 길이(합계 34명)이고, 라운드당 참여 인원(8/4/3)은
> `config.yaml`의 `debate.normal.*_agents_per_round` 값이다.
> `multi_stage.py`의 `_select_agents_for_round()`가 매 라운드 풀에서 4축 성격 균형
> (+ 도전자 1명 보장)을 맞춰 부분집합을 새로 뽑으므로, 라운드마다 참여자가 달라지고
> 한 단계 전체로는 정원 수까지 서로 다른 페르소나가 등장할 수 있다.
> 두 숫자 중 하나만 보고 문서가 틀렸다고 판단하지 말 것.

### 자동 배포

프로덕션 서버는 `main`을 스스로 따라갑니다. `moss-ao-deploy`(5분 주기)가
`scripts/deploy.sh`를 실행해 `origin/main`이 움직였을 때만 배포하고, 그 외에는
`git fetch` 한 번으로 종료합니다. 전체 절차·설정·문제 해결은 **`docs/deployment.md`** 참조.

- **풀(pull) 방식인 이유**: 앱 서버는 테일넷 안에만 있어 외부에서 SSH가 불가능하고,
  저장소는 public이라 self-hosted 러너가 위험하며, 저장소 admin 권한도 없다.
  풀 방식은 포트·배포키·GitHub 설정이 하나도 필요 없다 (public repo는 익명 fetch 가능).
- **활성화**: 서버 `.env`에 `MOSS_AO_AUTO_DEPLOY=1` → `pm2 start ecosystem.config.js
  --only moss-ao-deploy && pm2 save`. 이 플래그가 없으면 PM2 앱 목록에 등록조차 되지 않아
  다른 체크아웃이 자기 자신을 배포하는 사고가 나지 않는다.
- **가드**: CI 초록불일 때만 (체크 0건·`skipped`·`stale`은 초록이 아니라 **연기**;
  `DEPLOY_REQUIRE_CI_JOBS`로 필수 job까지 지정 가능) / 서버에 로컬 수정·로컬 커밋이
  있으면 중단 / 토론 실행 중이면 백엔드 배포는 다음 틱으로 연기 — **단 무한정은 아니다**:
  스케줄러 작업이 작업별 한도(signals/trends/backlog/debate = 30/60/90/120분)를 넘겨
  실행 중이면 busy가 아니라 **wedged**로 보고 배포를 진행한다. 이 작업들은 Ollama가
  멈춰도 죽지 않고 HTTP 대기에 앉아 `online`으로 남기 때문에, 무조건 연기하면 멈춘
  작업 하나가 배포를 영구히 막는다 (2026-08-06). 시작 시각 불명·pm2 출력 파싱 실패는
  busy로 계산(연기하는 쪽으로 실패). 덮어쓰기: `DEPLOY_SCHEDULER_STALE_MIN` /
  배포 전 강제 DB 스냅샷,
  **실패 시 배포 중단**(복원 지점 없이 배포하지 않음) / API가 떠 있는데 레디니스만
  실패하면(=DB 문제) 배포를 연기 / 배포 후 `/ready`(DB를 실제로 읽음) 실패 시 자동
  롤백(재빌드 포함).
- **배포 상태는 HEAD가 아니라 "마지막 성공 SHA"** (`.git/moss-ao-deployed-sha`, 헬스체크
  통과 후에만 기록): 배포 도중 죽으면(OOM SIGKILL·재부팅) 다음 틱이 미완 배포로 감지해
  재시도한다. 같은 SHA가 반복 실패하면 지수 백오프(5분→…→60분)로 풀 사이클 반복을 막고,
  새 커밋이 오면 즉시 리셋. 프론트 빌드는 라이브 `.next`가 아니라 `website/.next.new`에
  스테이징 후 성공 시에만 스왑(`next.config.ts`의 `NEXT_DIST_DIR`). 락은 소유 PID를 기록해
  SIGKILL로 죽은 폴러의 락을 다음 틱에 즉시 회수한다.
- **`git clean` 금지**: `git reset --hard`만 사용한다. DB(`data/`)·`.env`는 untracked라
  reset은 건드리지 않지만 clean은 지운다 (2026-07 사고). `tests/test_deploy.py`가 이
  불변식을 실제 실행으로 검증하므로 스크립트에 clean을 추가하면 테스트가 깨진다.
- **스케줄러는 재시작하지 않는다**: signals/trends/debate/backlog/health는 cron 틱마다
  파이썬을 새로 띄우므로 다음 실행에서 새 코드를 자동으로 집는다. 재시작하면 진행 중인
  작업만 죽는다. 상시 실행되는 `moss-ao-api`·`moss-ao-web`만 재시작 대상이다.
- **`ecosystem.config.js`·`.env` 변경은 수동 반영**: cron·env 정의는 자동 재등록되지 않는다.
  **삭제 후 재등록**이 유일하게 확실한 방법이다 (로그인 셸에서):

  ```bash
  for app in moss-ao-signals moss-ao-health moss-ao-trends moss-ao-backlog \
             moss-ao-deploy moss-ao-debate moss-ao-web moss-ao-api; do
    pm2 delete "$app" || true
  done
  pm2 start ecosystem.config.js && pm2 save
  ```

  루프인 이유: `moss-ao-deploy`는 `.env`에 `MOSS_AO_AUTO_DEPLOY=1`이 있어야만 등록되는데,
  `pm2 delete a b c`는 **없는 이름을 만나면 거기서 중단**한다 (PM2 7.0.3 실측). 한 줄로
  쓰면 그 뒤의 `moss-ao-debate`·`web`·`api` — 하필 유료 티어 소비자와 그것을 보고하는
  프로세스 — 가 삭제되지 않고, 이어지는 `pm2 start`는 그것들을 재시작만 해서 낡은 env가
  그대로 남는다. env 갱신하려던 작업이 조용히 절반만 되는 것이다.

- **`pm2 restart ecosystem.config.js --update-env`는 `.env` 값을 갱신하지 못한다**
  (PM2 7.0.3에서 실측, 2026-08-06). 설정 파일을 인자로 주면 PM2는 파일의 `env:` 블록만
  적용하고 **호출한 셸의 환경은 병합하지 않는다** — 앱 이름을 주는
  `pm2 restart moss-ao-api --update-env` 형태는 병합한다. `MOSS_LOCAL_LLM_ONLY`처럼
  `.env`에만 있는 키는 `env:` 블록에 없고 `pm2 start` 시점의 `process.env` 스냅샷으로만
  들어가므로, 하필 안내돼 온 그 명령이 갱신하지 못하는 유일한 형태였다. 그 결과
  `.env`가 `false`인데 프로세스는 `true`를 들고 하루치 토론이 통째로 로컬 gemma로
  돌았다 (아래 [유료 티어 조용한 강등](#유료-티어가-조용히-죽지-않게-하는-법) 참조).
- **PM2 관리 프로세스 안에서 `pm2 ... --update-env` 금지**: PM2는 프로세스 자신의
  설정 키(`cron_restart` 등)를 환경변수로 주입하므로, `--update-env`가 그것을 대상
  앱 설정으로 병합해 api/web이 5분마다 재시작되는 사고가 났다 (2026-08-05).
  deploy.sh는 시작 시 해당 키를 unset하고 `--update-env` 없이 재시작한다.
  상세·정리법: `docs/deployment.md`의 "cron_restart 오염" 절.
- 즉시 배포: `bash scripts/deploy.sh` / 가드 무시: `--force` / 미리보기: `--check`

## 가용성 모니터링 (v0.6.20)

**AO의 가장 흔한 다운 원인은 코드가 아니라 사무실 네트워크다.** 앱은 사무실
VM에서 돌고 Lightsail nginx가 테일넷 너머로 프록시하므로 (호스트 주소·계정
실값은 `CLAUDE.local.md` — public 저장소에 안 적는다), 경로가 끊기면
3000·3001이 동시에 사라지고 **모든 요청이 nginx 504**가 된다. PM2도 호스트도 DB도 멀쩡한 채로. 2026-08-04와 08-06에 각각 약
16분씩 이렇게 죽었고 둘 다 사후에 nginx error.log를 손으로 뒤져 재구성했다.

**08-06 건의 원인은 사무실 공유기로 확정됐다** (현장 확인: 통신사 모뎀에 PC 직결 시
인터넷 정상 → 회선·모뎀 무혐의, 상위 공유기를 켜니 약 5분 뒤 복구. 프로브의
복구 시각 `08:36:13`과 일치). **08-04 건은 원인 미상이다** — 길이는 거의 같지만
오후 4시라 같은 경위로 보기 어렵다. 두 건을 묶어 단정하지 말 것.

> **캐리어 유지 ≠ 네트워크 정상.** 08-06 내내 VM의 `eth0`는 링크가 한 번도
> 끊기지 않았다. VM이 공유기가 아니라 그 아래 스위치에 물려 있기 때문이다.
> 링크 상태만 보고 "라우터 바깥 문제"로 결론내면 틀린다 — 실제로 그렇게
> 오판했고, 현장 확인이 뒤집었다.

`scripts/monitor/`가 그 측정을 **고장 도메인 양쪽에 나눠서** 한다 (상세: 같은
디렉터리의 README.md).

| 프로버 | 위치 | 역할 |
|--------|------|------|
| `probe_uptime.py` | Lightsail nginx 박스 (사무실 밖) | 30초마다 앱서버 테일넷 `:3001/health`. 끊겨도 계속 기록. **상태 전환 시에만** Discord 알림 |
| `probe_netpath.py` | 사무실 VM (끊기는 쪽) | 30초마다 게이트웨이 → `1.1.1.1`(생 IP) → DNS → `tailscale ping`. 알림 없음 |
| `report.py` | 아무 데나 | 두 CSV를 조인해 다운마다 원인 판정 |

둘 다 **사용자 crontab** (`* * * * *`, 스크립트가 그 안에서 30초 간격 2샘플,
`flock`으로 중복 방지). 사무실 VM에는 sudo 권한이 없어 systemd는 쓰지 않는다.

```bash
scripts/monitor/pull-report.sh --since 2026-08-01
```

원인 판정은 **바깥으로 나가며 처음 실패한 계층**이다: 게이트웨이 불통 → LAN/라우터,
게이트웨이 정상 + 1.1.1.1 불통 → ISP, DNS만 불통 → 리졸버, tailscale만 불통 → 터널,
**전 계층 정상인데 다운 → 네트워크 무혐의, 우리 버그**.

> **주의 1.** 다운 확정은 **연속 2샘플 실패**를 요구하고 1샘플짜리는 `순간 블립`으로
> 따로 센다. nginx 로그를 08-04~06 구간에서 클러스터링하면 에러 뭉치 19개가 나오지만
> 실제 다운은 2건뿐이고 나머지는 에러 1~2건짜리다 — 합쳐 세면 "3일에 2번"이
> "하루 6번"이 되어 숫자의 신뢰를 잃는다.
>
> **주의 2. tailscale의 `health` 경고를 다운의 근거로 쓰지 말 것.** 2026-08-06
> 19:26~19:41에 컨트롤 플레인이 끊겼지만 데이터 경로는 살아 있어 nginx 에러가
> **0건**이었다 — 사이트는 안 죽었다. journald의 tailscaled 로그만 보면 다운
> 횟수를 2배로 세게 된다.

Discord 웹훅은 각 박스의 `~/ao-monitor/config.env`(600, git 미추적)에 있고,
비어 있으면 기록만 하고 알림은 보내지 않는다. 확인: `python3 ~/ao-monitor/probe_uptime.py --test-notify`

증거로 쓰던 기존 로그의 보존도 함께 늘렸다 — nginx logrotate 14 → **90일**
(백업: `/etc/logrotate.d/nginx.bak-ao-monitor`). 사무실 VM의 journald는 아직 3일치이며
연장에 sudo가 필요하다: `/etc/systemd/journald.conf`에 `MaxRetentionSec=90d`.

## 개발 워크플로우

> 아래는 서버에 직접 들어가 손으로 반영할 때의 절차다. 자동 배포가 켜진 뒤로는
> `main` 머지만으로 같은 일이 5분 내에 수행된다.

### 백엔드 변경 시

```bash
# 1. 코드 수정
# 2. API 서버 재시작
pm2 restart moss-ao-api

# 로그 확인
pm2 logs moss-ao-api --lines 30
```

### 프론트엔드 변경 시

```bash
# 1. 코드 수정
cd website

# 2. 빌드 (NEXT_PUBLIC_* 변수 포함)
npm run build

# 3. PM2 재시작
pm2 restart moss-ao-web

# 또는 개발 모드로 실행
npm run dev
```

### 데이터베이스 스키마 변경 시

SQLite는 ALTER COLUMN을 지원하지 않으므로 테이블 재생성 필요:

```sql
-- 1. 새 테이블 생성 (수정된 스키마)
CREATE TABLE table_new (...);

-- 2. 데이터 복사
INSERT INTO table_new SELECT ... FROM table_old;

-- 3. 기존 테이블 삭제
DROP TABLE table_old;

-- 4. 이름 변경
ALTER TABLE table_new RENAME TO table_old;

-- 5. 인덱스 재생성
CREATE INDEX ...;
```

## UI/UX 패턴

### 디자인 시스템

- **테마:** 다크 터미널 스타일
- **주요 색상:**
  - `#39ff14` (녹색) - 활성, 성공
  - `#00ffff` (시안) - 정보, 링크
  - `#ff6b35` (주황) - 경고, 토론
  - `#bd93f9` (보라) - 특수 기능
- **폰트:** JetBrains Mono (모노스페이스)

### 모달 시스템

```typescript
// 모달 열기
const { openModal } = useModal();
openModal('idea', { id: 'idea-123', title: 'My Idea' });

// 모달 타입
type ModalType = 'signal' | 'trend' | 'idea' | 'debate' | 'plan' | 'agent' | 'stats' | 'pipeline';
```

### 다국어 지원 (i18n)

```typescript
// UI 라벨 번역
const { t, locale, setLanguage } = useI18n();
<span>{t('dashboard')}</span>

// 콘텐츠 로컬라이제이션 (아이디어, 트렌드, 플랜 등)
const getLocalizedText = (en: string | null, ko: string | null): string => {
  if (locale === 'ko' && ko) return ko;
  return en || '';
};
<h3>{getLocalizedText(idea.title, idea.title_ko)}</h3>

// 지원 언어: 'en', 'ko'
```

**양방향 번역 (ContentTranslator):**
- 콘텐츠 언어 자동 감지 (한글/영어)
- 한글 원본 → 영어 번역 (main field) + 한글 유지 (`*_ko` field)
- 영어 원본 → 영어 유지 (main field) + 한글 번역 (`*_ko` field)
- LLM: `gemma3:4b` (로컬, 무료)

### 마크다운 — 렌더링과 평문화는 서로 다른 함수다

DB에 들어 있는 텍스트는 대부분 LLM이 쓴 **마크다운**이다. 화면에 꽂기 전에 둘 중
하나를 반드시 거쳐야 한다 (`website/src/lib/markdown-html.ts`).

| 상황 | 함수 | 비고 |
|------|------|------|
| 본문 — 요약·플랜·토론 메시지 | `<MarkdownContent content={...} />` | `renderMarkdown` + `dangerouslySetInnerHTML`. **`marked.parse()`를 직접 쓰지 말 것** (sanitize 안 함 — stored XSS 이력) |
| 제목 — `<h3>` 등 문자열을 그대로 넣는 자리 | `stripMarkdown(...)` | 평문 반환, JSX 텍스트 노드용 |

- 그냥 `{idea.summary}`로 넣으면 `- **핵심 분석**:` 이 별표째 보이고 줄바꿈이
  뭉개진다.
- 제목도 안전하지 않다: 번역기가 헤딩 마커를 남겨 `plan.title_ko`가
  `## 계획: …`으로 들어오는 실제 사례가 있다 (`<h3>`가 `##`까지 그린다).
  `getLocalizedText(...)` 결과를 그대로 쓰지 말고 `stripMarkdown()`으로 감쌀 것.

## 자주 발생하는 문제와 해결책

### 1. ERR_CONNECTION_REFUSED (API 연결 오류)

**원인:** 브라우저가 `localhost:3001`에 직접 연결 시도

**해결:**
```bash
# .env.local 확인
cat website/.env.local
# NEXT_PUBLIC_API_URL=/api 이어야 함

# 재빌드 및 재시작
cd website && npm run build
pm2 restart moss-ao-web
```

### 2. 토론이 데이터베이스에 저장되지 않음

**원인:** `debate_sessions.idea_id`가 NOT NULL로 설정됨

**해결:** 스키마 마이그레이션으로 nullable 변경 (이미 수정됨)

### 3. PM2 환경변수가 갱신되지 않음

**원인:** PM2가 환경변수를 캐시함

**해결:**
```bash
pm2 delete moss-ao-web
pm2 start ecosystem.config.js --only moss-ao-web
pm2 save
```

### 4. 포트 충돌

**원인:** 이전 프로세스가 포트 점유

**해결:**
```bash
# 포트 사용 프로세스 확인
lsof -i :3000
lsof -i :3001

# 프로세스 종료
kill <PID>
```

### 5. 빌드 실패 (TypeScript 오류)

**해결:**
```bash
cd website
npm run build 2>&1 | head -50  # 오류 확인
# 타입 오류 수정 후 재빌드
```

### 6. Ollama 타임아웃 오류

**증상:** "Ollama timeout after 300s" 에러 발생

**원인:** 여러 에이전트가 동시에 Ollama 요청, 쓰로틀링 큐 대기 중 타임아웃

**해결:**
- `config.yaml`의 `throttling.ollama` 설정 조정:
  - `request_timeout: 600` (600초로 증가)
  - `requests_before_cooling: 10` (쿨링 전 더 많은 요청 허용)
  - `cooling_period_seconds: 60` (쿨링 시간 단축)
- `config.yaml`의 `debate.test_mode: true`로 에이전트 수 감소
- 사용 중인 Ollama 모델 확인: `curl "$OLLAMA_HOST/api/ps"`

> **먼저 "혼잡"과 "멈춤(wedged)"을 구분할 것.** 둘은 증상이 같지만 처방이 정반대다
> (혼잡 = 기다린다, 멈춤 = 기다려도 영원히 안 온다). 진단 3단계:
>
> ```bash
> curl -s "$OLLAMA_HOST/api/ps"        # 컨트롤 플레인: 즉답이어야 정상
> timeout 45 curl -sN "$OLLAMA_HOST/api/generate" \
>   -d '{"model":"gemma3:1b","prompt":"hi","stream":true}'   # 스트리밍: 첫 토큰
> ```
>
> `/api/ps`는 0.1초에 답하는데 **스트리밍이 45초 동안 0바이트**면 혼잡이 아니라
> 러너가 걸린 것이다 (혼잡이면 느리게라도 토큰이 나온다). 모델을 바꿔도, num_ctx를
> 낮춰도 똑같이 걸린다면 확정. **복구는 모델 언로드**:
>
> ```bash
> curl -s "$OLLAMA_HOST/api/generate" -d '{"model":"gemma3:4b","keep_alive":0}'
> ```
>
> 즉시 `done_reason:"unload"`가 돌아오고 다음 요청에서 새 인스턴스가 뜬다 (2026-08-06
> 이 방법으로 해소 — GPU·드라이버는 정상이었고 상주 인스턴스만 걸려 있었다). 박스에
> SSH가 열려 있지 않아도 HTTP만으로 가능하다. 언로드 후에도 1b 모델조차 못 뜨면
> 그때는 GPU/드라이버 문제이므로 박스에 직접 접근해야 한다.

### 7. Ollama 모델 VRAM 메모리 부족

**증상:** 응답이 매우 느리거나 멈춤

**해결:**
```bash
# 현재 운영에서 실제로 호출되는 모델은 gemma3:4b(채팅) 하나다. qwen3-embedding:0.6b는
# 코드에 예약만 돼 있고 호출처가 없다 (서버에도 미설치 — 위 '작업별 LLM 모델' 절 참조).
# VRAM 점유 확인:
curl -s "$OLLAMA_HOST/api/ps"
```

### 8. 모든 DB 엔드포인트가 500 (`/health`만 200)

**증상:** `/status`, `/ideas`, `/signals`, `/debates` 전부 500, `/health`·`/agents`·`/adapters`는 200

**원인:** SQLite 파일(`data/orchestrator.db`) 유실/비워짐/손상 → 쿼리가 `no such table`로 실패

**해결 (v0.6.10+):**
- API·스케줄러가 기동 시 스키마를 자동 생성하므로 재시작만으로 500은 해소됨 (`pm2 restart moss-ao-api`)
- 데이터 복원: `python -m agentic_orchestrator.scheduler restore-db`
  (목록은 `--list`, 특정 스냅샷은 `--from`). 손으로 복사하지 말 것 — 위 '복원 절차' 참조
- `/status`가 `"degraded"`를 반환하면 DB가 실제로 죽어 있다는 뜻 — `pm2 logs moss-ao-api`에서 traceback 확인

## 콘텐츠 품질 요구사항

### 제목 요구사항 (모든 Trend, Idea, Plan)

- **최소 30자 이상** 구체적이고 설명적인 제목
- 일반적인 표현 대신 **구체적인 기술명, 프로젝트명, 수치** 포함

| 나쁜 예 | 좋은 예 |
|---------|---------|
| "AI 트렌드" | "OpenAI GPT-5 에이전트 SDK 출시로 자율 AI 워크플로우 자동화 시대 개막" |
| "DeFi 성장" | "Uniswap v4 훅스 도입으로 맞춤형 DEX 전략 가능" |
| "NFT 플랫폼" | "Mossland NFT 홀더를 위한 실시간 메타버스 자산 가치 트래커" |

### 아이디어 필수 섹션

토론에서 생성되는 아이디어는 다음 섹션을 반드시 포함:

1. **핵심 분석** (100자+) - 시장/기술 상황 분석
2. **기회/리스크** (150자+) - 정량적 데이터, 경쟁 서비스 차별점
3. **구체적 제안** (200자+) - 핵심 기능 3-5개, 기술 스택, MVP 범위
4. **실행 로드맵** (100자+) - 주차별 일정, 필요 리소스
5. **성공 지표** - 측정 가능한 KPI 2-3개 (목표 수치 포함)

### 기획안 필수 섹션

플랜 생성 시 다음 섹션 포함:

1. **프로젝트 개요** - 이름, 한 줄 설명, 목표, 대상 사용자, 예상 기간/비용
2. **기술 아키텍처** - 프론트엔드, 백엔드, DB, 블록체인 연동, 외부 API
3. **상세 실행 계획** - 주차별 Task 및 마일스톤
4. **리스크 관리** - 리스크 테이블 (발생 확률, 영향도, 대응 방안)
5. **성과 지표 (KPI)** - 지표, 목표, 측정 방법, 측정 주기
6. **향후 확장 계획** - Phase 2 기능, 장기 비전

## 아이디어 생성 파이프라인

자세한 내용은 `docs/pipeline.md` 참조.

### 파이프라인 개요

```
Signals (30분) → Trends (2시간) → Debate (6시간) → Ideas → Auto-Score → Plans
                      ↓                 ↑                                  ↓
                 (트렌드 기반 토픽)                               Projects (score ≥ 8.0)
```

### 아이디어 소스 유형

| 소스 | 설명 | LLM |
|------|------|-----|
| `trend_based` | 트렌드 분석 기반 생성 | Claude API |
| `debate` | 멀티에이전트 토론에서 생성 | Ollama (로컬) |
| `github_sync` | GitHub Issues에서 동기화 | - |

### 자동 점수화 및 프로젝트 생성 시스템

토론 완료 후 아이디어 자동 점수화:
- **score >= 8.0**: `promoted` → 플랜 자동 생성 + **프로젝트 자동 생성**
- **score 7.0-8.0**: `promoted` → 플랜 자동 생성 (프로젝트는 수동 버튼)
- **score 4.0-7.0**: `scored` → 백로그 대기 → **트리아지가 재평가** (아래)
- **score < 4.0**: `archived` → 아카이브 (**GitHub 이슈 생성 안 함**, v0.6.15)

### 백로그 트리아지 — 생산·소비 균형 (v0.6.16)

토론이 하루 ~40개 아이디어를 만드는데 소비자가 없어 `scored`(~85%)가 영원히
쌓였다. `scheduler/backlog_triage.py`(moss-ao-backlog 4시간 주기)가 그 소비자다:
**가장 오래된** `scored` 아이디어를 오늘의 트렌드 기준으로 재채점해 종결을 강제한다.

- 재채점 ≥ 7.0 → `promoted` + **draft 플랜** (자동 승인 없음, `POST /plans/{id}/approve`로
  사람이 승인; [Plan] 이슈도 새로 만들지 않음) → [Idea] 이슈는 lifecycle이 `completed`로 닫음
- 재채점 < 4.0 → `archived` → 이슈는 `not_planned` + 판정 코멘트로 닫힘
- 중간 점수 → 스트라이크 1개, `max_strikes`(기본 2) 도달 시 archived
  ("N회 재평가에도 승격 못 함")

모든 아이디어가 최대 `max_strikes`번 안에 종결되므로 열린 백로그(=열린 이슈)는
"생산율 × 결정 소요일"로 유계다. **사이징 규칙: `per_run × 6회/일`이 일일 생산량을
넘어야 한다** (기본 25×6=150터치/일 ≥ 75결정/일 > 생산 ~40/일; v0.6.17에서 상향,
min_age도 24h→6h로 낮춰 당일 소비 시작). 트리아지는 DB만 쓰고
(SQLite가 진실), 이슈 닫기는 같은 주기 바로 뒤의 issue lifecycle이 수행한다 (GitHub
장애 시 다음 주기에 자기치유). LLM 폴백(중립 5.0)은 감지해 스트라이크 없이 건너뛴다.
설정: `config.yaml`의 `backlog.triage`. 참고: `backlog.max_open_ideas` 캡은 이제
**열린(scored/pending) 아이디어 수**를 센다 — 예전처럼 전체 누적을 세면 삭제되지 않는
ideas 특성상 ~3주 만에 캡을 영구히 넘겨 미러가 조용히 죽는 원웨이 킬스위치였다.

### GitHub 이슈 라이프사이클 (v0.6.15)

GitHub 이슈는 DB의 가시성 미러일 뿐인데, 예전에는 생성만 있고 닫힘이 없어
2,866개까지 쌓였다 (닫힘률 0.07%). 이제 트래커가 파이프라인을 **따라간다**
(`scheduler/issue_lifecycle.py`, moss-ao-backlog 4시간 주기에서 실행):

- **파이프라인 연동 닫기** (`completed`): 아이디어가 플랜으로 승격되면 [Idea]
  이슈에 [Plan] 링크 코멘트 후 닫기 (승격 시점 인라인 + 백로그 주기 보정 스윕);
  플랜에서 프로젝트가 생성되면 [Plan] 이슈 닫기
- **아카이브 연동 닫기** (`not_planned`, v0.6.16): DB에서 `archived`가 된 아이디어
  (주로 트리아지 재평가/스트라이크아웃)의 이슈를 판정 코멘트와 함께 닫기.
  `curated:keep`/`source:trend` 라벨이나 사람 코멘트가 있으면 에이징과 동일하게 제외
- **에이징 스위프** (`not_planned`): 생성 후 14일간(v0.6.17에서 30→14) 코멘트 0개인 봇 이슈 자동
  닫기. **`curated:keep`·`source:trend` 라벨은 절대 닫지 않음** — 계속 열어둘
  이슈에는 `curated:keep`을 붙일 것. 사람 코멘트가 하나라도 있으면 제외.
  트리아지 도입 후에는 백스톱 역할 (정상 경로는 결정 기반 닫기)
- 설정: `config.yaml`의 `backlog.issue_lifecycle` (enabled/max_age_days/
  max_closes_per_run). 닫기는 가시성 전용 — DB 행은 그대로, 재오픈 가능
- 스윕은 search API가 아니라 **list API**를 사용한다 (search 인덱스가 일부
  이슈를 조용히 누락하는 저장소라서)

## 토론 시스템 (Multi-Stage Debate)

### 3단계 프로세스

아래 인원은 **페르소나 풀 정원**(`personas/catalog.py`)이며, 프로덕션에서 실제로
매 라운드 참여하는 인원은 그보다 적다 (`config.yaml`의 `debate.normal`, 각각 8/4/3명).
자세한 구분은 [현재 운영 모드](#현재-운영-모드-production-v069) 절의 표 참조.

1. **Divergence (발산)** - 16명 풀에서 라운드당 8명이 아이디어 생성
2. **Convergence (수렴)** - 8명 풀에서 라운드당 4명이 아이디어 평가/병합
3. **Planning (기획)** - 10명 풀에서 라운드당 3명이 실행 계획 작성

### 에이전트 페르소나

- **발산 에이전트:** 창업가, 개발자, 마케터, 디자이너 등
- **수렴 에이전트:** VC, 시장 분석가, 기술 전문가 등
- **기획 에이전트:** PM, 테크 리드, QA 리드, DevRel 등

### 스케줄

| 작업 | 주기 | 설명 |
|------|------|------|
| Signal Collection | 30분마다 | RSS/API에서 신호 수집 |
| Trend Analysis | 2시간마다 | 신호 분석 → 트렌드 생성 (Ollama) |
| Debate | 6시간마다 | 트렌드 기반 토론 → 아이디어/플랜 자동 생성 |
| Backlog | 4시간마다 | 처리 상태 집계/리포트 |
| Health Check | 5분마다 | 시스템 상태 확인 |

## 개발 규칙

### 문서 업데이트 규칙

**중요:** 개발이 어느 정도 진척될 때마다 (기능 추가, 버그 수정, 구조 변경 등) 다음 MD 파일들을 업데이트하고 커밋해야 합니다:

1. **CLAUDE.md** - 프로젝트 구조, API 엔드포인트, 새로운 기능 반영
2. **CHANGELOG.md / CHANGELOG.ko.md** - 변경 이력 추가
3. **docs/pipeline.md** - 파이프라인 관련 변경 시
4. **README.md / README.ko.md** - 주요 기능 변경 시

```bash
# 문서 업데이트 후 커밋
git add *.md docs/*.md
git commit -m "docs: update documentation for recent changes"
```

### 버전 올릴 때

버전은 두 곳에 있습니다: `pyproject.toml`과 `website/src/lib/version.ts`.

**`pyproject.toml`의 버전을 바꾸면 `uv lock`도 함께 돌려서 `uv.lock`을 커밋해야
합니다.** lock이 프로젝트 자기 버전을 기록하므로 버전만 올려도 lock이 stale이 되고,
CI의 `uv lock --check`가 빨간불이 됩니다 — 그리고 배포 게이트는 CI가 초록일 때만
배포하므로, 그 상태로 두면 **모든 배포가 멈춥니다.**

```bash
uv lock && git add uv.lock
```

### 커밋 컨벤션

- `feat:` - 새로운 기능
- `fix:` - 버그 수정
- `docs:` - 문서 변경
- `refactor:` - 코드 리팩토링
- `style:` - UI/UX 변경
- `chore:` - 기타 변경

## Plan → Project 자동 생성

**상태:** ✅ 구현 완료 (v0.6.3: Production-Quality Code Generation)

승인된 Plan을 `projects/` 폴더에 실제 프로덕션 품질의 프로젝트로 변환하는 기능:

```
Plan (DB) → Deep LLM 파싱 → 엔티티/서비스 추출 → LLM 코드 생성 → projects/{project-name}/
```

### 향상된 Plan 파서 (v0.6.3)

- **Deep LLM Parsing**: 마크다운에서 상세 정보 추출
- **DataEntity**: 데이터 모델 및 관계 정의
- **ExternalService**: Twitter API, Coingecko, Etherscan 등 외부 서비스 감지
- **UIComponent**: 프론트엔드 컴포넌트 및 페이지 추출
- **SmartContractSpec**: 블록체인 스마트 컨트랙트 사양

### 프로덕션 품질 코드 생성 (v0.6.3)

생성되는 코드:
- **완전한 FastAPI/Express 백엔드**: 비즈니스 로직, 라우터, 모델 포함
- **완전한 Next.js/React 프론트엔드**: 모든 페이지와 컴포넌트 포함
- **Solidity 스마트 컨트랙트**: Hardhat 테스트 프레임워크 포함
- **외부 서비스 연동 레이어**: API 클라이언트, 웹소켓 핸들러
- **데이터베이스 스키마 및 마이그레이션**
- **Docker 설정**

### 코드 생성 검증 게이트 (v0.6.9)

작은 로컬 모델(gemma3:4b)이 만든 코드는 컴파일이 보장되지 않으므로, 디스크 기록·커밋
**전에** 검증·자동수리하는 게이트가 있습니다 (`project/verifier.py`, `project/repair.py`).
스캐폴드(`scaffold.py`의 `_verify_and_repair`)가 코드 파일마다 다음 파이프라인을 실행합니다:

```
결정적 수리(repair) → 검증(verify) → (실패 시) 컴파일 오류를 모델에 되먹이는 LLM 재수리 1회 → 재검증
```

- **정책: 차단하지 않음.** 수리 후에도 실패가 남으면 프로젝트를 `ready_with_warnings`로
  표시하고 전달은 계속합니다. 파일별 요약은 `Project.extra_metadata["verification"]`,
  한 줄 요약은 `generation_log`·`.moss-project.json`에 기록되고 Projects UI에 노출됩니다.
- **CodeVerifier** (graceful degradation): Python은 내장 `compile()`(항상 사용), Solidity는
  정적 검사(`pragma` 누락, 잘못된 `.length()`, 중괄호 불균형) + import 없는 컨트랙트 한정
  선택적 `solc`, TS/JS는 선택적 `esbuild`. 툴체인이 없으면 거짓 실패 대신 `SKIPPED`.
- **CodeRepairer** (결정적): SPDX/`pragma` 보강, `.length()`→`.length`, `now`→`block.timestamp`,
  OpenZeppelin v5→**v4 핀 고정** 정규화(`utils/`→`security/` import, v5 `Ownable(...)` 베이스 호출
  제거), OZ를 import하면 `contracts/package.json`에 `@openzeppelin/contracts@^4.9.6` 주입.
  수리는 문자열/주석 바깥에서만 수행.

> 참고: LLM 경로의 컨트랙트는 이제 `contracts/package.json`·`hardhat.config.ts`도 함께
> 내보내므로 `hardhat compile`이 OZ import를 해석할 수 있습니다.

### 트리거 전략

- **자동 생성 (score ≥ 8.0)**: 토론 완료 후 Plan이 자동 승인되고 프로젝트 생성
- **수동 승인 (score < 8.0)**: Plan이 "draft" 상태로 생성됨
  - `POST /plans/{id}/approve` API로 수동 승인
  - 승인 시 `generate_project=true` 옵션으로 즉시 프로젝트 생성 가능
  - `GET /plans/pending-approval` API로 승인 대기 목록 조회

### 지원 기술 스택

| 프론트엔드 | 백엔드 | 블록체인 |
|------------|--------|----------|
| Next.js + TypeScript | FastAPI + SQLAlchemy | Hardhat (Ethereum) |
| React (Vite) | Express.js + TypeScript | Anchor (Solana) |
| Vue 3 | | |

### 작업별 LLM 모델

원격 Ollama 서버에 설치된 모델만 사용합니다. 호스트는 `OLLAMA_HOST` 환경변수로 주입.
GPU(~8 GB)에 상주하는 모델은 두 개뿐이며 스왑이 발생하지 않도록 단일 채팅 모델로
모든 채팅·생성 작업을 처리합니다.

| 작업 | 모델 | 용도 |
|------|------|------|
| **토론 (Divergence/Convergence/Planning/품질게이트)** | `gpt-5.4-mini` (유료, v0.6.19) | 4B 로컬 모델이 품질 상한이던 유일한 작업. `config.yaml`의 `llm.paid_tiers.debate` + 서버 `.env`의 `MOSS_LOCAL_LLM_ONLY=false` 두 스위치가 모두 켜져야 과금됨. 예산 초과·API 장애 시 gemma로 자동 강등 |
| 채점 / 번역 / 트렌드 분석 / 프로젝트 생성 등 나머지 전부 | `gemma3:4b` (로컬, 무료) | 채점은 `num_ctx=4096` 고정 (v0.6.18) |
| 임베딩 / 의미 검색 | `qwen3-embedding:0.6b` (예약만 됨 — 아래 참조) | (현재 미사용) |

> 실제 모델 정의는 `src/agentic_orchestrator/llm/hierarchy.py`의 `LOCAL_MODELS`, 프로젝트 생성 모델은 `config.yaml`의 `project.llm`을 단일 소스로 참조합니다.

### 유료 모델로 가는 두 입구 — 둘 다 통제된다

과금 호출에 도달하는 경로는 서로 겹치지 않는 두 개다. 새 코드를 붙일 때 어느 쪽인지
먼저 확인할 것.

| 경로 | 흐름 | 누가 통제하나 |
|------|------|--------------|
| **라우터** (파이프라인 전체) | `HybridLLMRouter.route()` → `provider.generate()` → `_make_request()` | 라우터 자신: 로컬 온리 플래그, `paid_tiers` 허용목록, 예산 확인, `record_usage` |
| **레거시** (`ao` CLI 전용) | 스테이지·백로그의 `@property` → `provider.complete()` / `.chat()` → `_complete_with_retry()` → `_make_request()` | 팩토리의 `enforce_local_only()` + `BaseProvider._complete_with_retry`의 예산 확인·원장 기록 |

- **레거시 경로는 스케줄된 곳 어디에서도 _호출되지_ 않는다.** 단, **import는 된다** —
  `agentic_orchestrator/__init__.py`가 `orchestrator.py`를 무조건 import하고 그것이
  다시 `stages/*`를 끌어오므로, 패키지의 어떤 서브모듈을 import하든(uvicorn의
  `api.main`, 모든 scheduler 태스크) `stages/*`가 로드된다. import는 과금과 무관하다:
  게이트는 import 시점이 아니라 팩토리 **호출** 시점에 작동한다. 실제 진입점은
  `Orchestrator`·`BacklogOrchestrator`의 생성 지점이며 이는 `cli.py`에만 있다 —
  즉 서버에서 사람이 치는 `ao step` / `ao loop` / `ao backlog run` / `process`뿐이다
  (`docs/labels.md` 참조). **"import 안 된다"고 쓰지 말 것 — 틀린 문장이다.**
- **`create_claude_provider` / `create_openai_provider` / `create_gemini_provider`는
  `MOSS_LOCAL_LLM_ONLY`가 켜져 있으면 생성 자체를 거부한다** (`PaidProviderBlockedError`).
  `dry_run=True`만 면제 — 리허설은 네트워크에 나가지 않기 때문. 플래그가 미설정이거나
  값에 오타가 있으면 **닫힌 쪽**(지출 없음)으로 실패한다.
- **과금된 완성 결과는 전부 `api_usage` 원장에 기록되어 `/usage`에 잡힌다.** 기록 지점이
  `complete()`가 아니라 `_complete_with_retry`인 이유: Gemini가 `complete()`를 `super()`
  호출 없이 오버라이드하므로 상위에 걸면 Gemini만 빠진다. 라우터는 `generate()`로
  `_make_request`에 직접 가므로 이중 계상되지 않는다.
- **예산 소진 시 레거시 경로는 거부한다** (`BudgetExhaustedError`, `QuotaExhaustedError`
  서브클래스라 상태 머신이 일시정지·알림으로 처리). 라우터처럼 로컬로 강등할 수 없기
  때문 — 레거시 스테이지에는 Ollama 대안이 없다. 반대로 **원장(DB) 자체가 불가용이면
  열린 쪽으로 실패**한다: DB 장애가 파이프라인을 죽여선 안 된다.
- 유료 프로바이더를 팩토리 밖에서 직접 생성하면 게이트를 우회하게 된다. 유일한 예외는
  스스로 `if self.local_only: return`으로 가드하는 `llm/router.py`의
  `_init_api_providers`이며, `tests/test_paid_provider_gating.py`의 소스 불변식이
  그 외의 직접 생성을 차단한다.
- 플래그 파싱은 `providers/base.py`의 `local_llm_only()` 한 곳뿐 — 라우터와 팩토리가
  공유하므로 두 입구가 서로 다른 판단을 내릴 수 없다.

- **예산은 이제 하나의 통을 둘이 나눠 쓴다.** 레거시 실행이 `api_usage`에 기록되고
  라우터도 같은 원장에서 `can_use_api`를 읽으므로, 수동 `ao` 실행의 지출이 토론 티어의
  잔여 예산을 깎는다. 한도를 넘기면 레거시는 시끄럽게 실패(`BudgetExhaustedError`)하지만
  **토론 티어는 로컬 gemma로 강등된다** (v0.6.20부터 조용히는 아니다 — WARNING과
  `/usage`의 `llm_routing`에 잡힌다). 일 한도는 $2.00 → **$3.00**으로 올렸다:
  $2.00에서는 토론 4회(~$1.78) 뒤 여유가 ~$0.21뿐이라 레거시 기본 모델
  (`gpt-5.2-chat-latest`, 토론 모델의 3.3배 단가) 완성 2건이면 넘겼다. $3.00은 토론
  4회 + 재시도 + 같은 날 수동 `ao` 세션을 감당하고, 월 한도 $100도 넘지 않는다
  (31 × $3 = $93). 그보다 큰 수동 작업을 할 거면 `config.yaml`의
  `budget.daily_limit_usd`를 먼저 올릴 것.

> **서버는 `MOSS_LOCAL_LLM_ONLY=false`로 운영된다** (토론 유료 티어에 필요). 즉 거기서
> 수동 `ao` 실행을 묶는 것은 킬 스위치가 아니라 **원장과 예산 상한**이다 — 프로덕션에서는
> 두 병목 중 하나만 실제로 작동한다.

### 유료 티어가 조용히 죽지 않게 하는 법

유료 티어의 모든 전제조건은 **설계상 조용히 로컬로 강등된다** (API 장애가 토론을 죽여선
안 되므로). 그 설계의 대가는 *한 번도 켜진 적 없는 티어*와 *완벽히 동작하는 티어*가
구별되지 않는다는 것이다. 2026-08-05~06에 실제로 그렇게 됐다: PM2가 스케줄러에 낡은
`MOSS_LOCAL_LLM_ONLY=true`를 물려 하루치 토론이 전부 gemma3:4b로 돌았는데 에러도,
알림도 없었고 `/status`는 계속 정상이었다. 유일한 증거는 아무도 안 보는 $0.00 원장뿐.

강등은 그대로 두되, 침묵만 없앴다 (v0.6.20):

| 관측 지점 | 내용 |
|-----------|------|
| **토론 로그 WARNING** | 티어를 요청했는데 활성화되지 않으면 `Paid tier 'debate' requested but NOT active — ... Reason: <원인>`. 프로세스당 1회 (토론 1회 ≈ 38콜이라 중복 억제). 호출자가 `model`/`force_local`로 직접 옵트아웃한 경우는 DEBUG — 정상 동작이 WARNING 채널을 오염시키지 않게 |
| **`GET /status`** | `components.llm_router` = `{status, local_only, degraded_tiers, paid_tiers{...}}`. 설정 수준 판정이라 네트워크·DB를 건드리지 않는다 (이 엔드포인트는 공개·핫 경로). **최상위 `status`는 그대로 DB만 반영** — 티어가 죽은 건 장애가 아니라 품질 문제라 페이징 대상이 아니다 |
| **`GET /usage`** | `llm_routing` 블록. 여기선 예산까지 확인하므로 `$0.00`이 "쓸 일이 없었다"인지 "티어가 죽었다"인지 구별된다 |

원인 판정은 `llm/router.py`의 `describe_paid_tier()` 한 곳에서만 만들어지고 라우터와
엔드포인트가 이를 공유한다 — 런타임과 관측이 서로 다른 답을 내놓을 수 없다. 우선순위는
"운영자가 **먼저** 만져야 할 스위치" 순: 킬 스위치 → `enabled` → 모델/프로바이더 →
API 키 → 예산.

> **주의:** `/status`의 판정은 **API 프로세스 자신의 환경** 기준이다. API와 토론
> 스케줄러는 별개 PM2 앱이라 원칙적으로 어긋날 수 있다. 실제로는 둘 다 하나의
> `pm2 start ecosystem.config.js`에서 환경을 받으므로 2026-08-06에도 **같이** 틀렸고,
> 그래서 이 판정이 그때 사고를 잡아냈을 것이다.

> **임베딩은 현재 어떤 코드도 호출하지 않는다 (2026-08-05 확인).** `hierarchy.py`에
> `qwen3-embedding:0.6b`가 등록돼 있고 이 문서도 오랫동안 "RAG 인덱싱, 유사도 비교"에
> 쓴다고 적어 왔지만, 임베딩 API를 호출하는 코드 경로가 소스 어디에도 없다 — 시그널의
> "Semantic dedup"은 임베딩이 아니라 **제목 토큰 Jaccard 유사도**다
> (`signals/aggregator.py::_is_semantic_duplicate`). 실제 Ollama 서버에도 이 모델은
> 설치돼 있지 않다(`nomic-embed-text`만 있음). 임베딩 기반 기능을 만들려면 먼저 호출
> 코드를 구현하고 서버에 모델을 받아야 하며, 그 전까지 이 등록은 예약 슬롯일 뿐이다.
> 구조화 출력(JSON 스키마 강제)은 트렌드 분석·아이디어 점수화 경로에 적용돼 있다
> (`response_schema` → Ollama `format`).

### 생성되는 프로젝트 구조

```
projects/{project-name}/
├── README.md              # LLM 생성 (Plan 기반)
├── PLAN.md                # 원본 Plan 문서
├── .moss-project.json     # 메타데이터
├── src/
│   ├── frontend/          # Next.js (해당 시)
│   └── backend/           # FastAPI (해당 시)
├── contracts/             # Solidity (해당 시)
├── docs/
│   └── api.md
└── tests/
```

### 설정 (`config.yaml`)

```yaml
project:
  auto_generate:
    # 2026-08-06부터 false (토론 다양성 게이트 검증 중). 이 값을 true로 적어 둔
    # 문서를 믿고 "자동 생성이 돌고 있다"고 판단하지 말 것.
    #
    # 주의: 이 스위치가 막는 것은 스케줄러의 인라인 호출 한 곳뿐이다
    # (tasks.py의 _auto_generate_project). API/버튼 경로
    # (POST /plans/{id}/generate-project)는 이 값을 읽지 않으므로 "일시정지"
    # 상태에서도 프로젝트는 생성된다. 게다가 config.yaml을 못 읽으면 기본값
    # enabled: True로 열린 쪽으로 실패한다.
    enabled: false
    min_score: 8.0        # 자동 생성 최소 점수
    max_concurrent: 1     # 동시 생성 제한
  llm:
    parsing: "gemma3:4b"
    code_generation: "gemma3:4b"
    architecture: "gemma3:4b"
    fallback: "gemma3:4b"
  output_dir: "projects"
```

## 향후 구현 예정 기능

### GitHub 라벨 기반 승격 워크플로우

**상태:** 구현 예정

GitHub Issues에서 라벨을 추가하면 자동으로 처리:

- `promote:to-plan`: Idea → Plan 자동 생성
- `promote:to-dev`: Plan → Project 스캐폴드 생성

자세한 내용: `docs/labels.md`

## 참고 링크

- **프로젝트 문서:** `docs/` 디렉토리
- **API 문서:** http://localhost:3001/docs (Swagger UI)
- **실제 IP 주소:** `CLAUDE.local.md` (gitignore 처리됨)
- **민감한 정보:** `.env.local` 파일에 저장
