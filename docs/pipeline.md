# MOSS.AO 아이디어 생성 파이프라인

이 문서는 MOSS.AO의 아이디어 생성 파이프라인을 설명합니다.

## 파이프라인 개요

```
┌──────────────────────────────────────────────────────────────────┐
│                        입력 소스                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   RSS Feeds ──┐                                                  │
│               │    ┌─────────────────┐                           │
│   GitHub    ──┼───▶│ Signal Collector│──▶ signals DB             │
│               │    └─────────────────┘         │                 │
│   OnChain   ──┘                                │                 │
│                                                ▼                 │
│                                    ┌───────────────────┐         │
│                                    │  Trend Analyzer   │         │
│                                    │    (Ollama)       │         │
│                                    └─────────┬─────────┘         │
│                                              │                   │
│                                              ▼                   │
│   ┌───────────────┐              ┌───────────────────┐           │
│   │ IdeaGenerator │              │ TrendBased Ideas  │           │
│   │   (Claude)    │              │    (Claude)       │           │
│   └───────┬───────┘              └─────────┬─────────┘           │
│           │                                │                     │
│           │    ┌───────────────────────────┘                     │
│           │    │                                                 │
│           ▼    ▼                                                 │
│   ┌─────────────────────────────────────────────────────┐        │
│   │               Multi-Stage Debate                     │        │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │        │
│   │  │Divergence│─▶│Convergence│─▶│ Planning │           │        │
│   │  │16 agents │  │ 8 agents │  │10 agents │           │        │
│   │  └──────────┘  └──────────┘  └──────────┘           │        │
│   └─────────────────────────┬───────────────────────────┘        │
│                             │                                    │
│                             ▼                                    │
│                  ┌───────────────────┐                           │
│                  │   Auto-Scorer     │                           │
│                  │    (Ollama)       │                           │
│                  └─────────┬─────────┘                           │
│                            │                                     │
│           ┌────────────────┼────────────────┐                    │
│           ▼                ▼                ▼                    │
│     ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│     │ promoted │    │  scored  │    │ archived │                 │
│     │ (≥7.0)   │    │ (4-7)    │    │ (<4.0)   │                 │
│     └────┬─────┘    └────┬─────┘    └────┬─────┘                 │
│          │               │               │                       │
│          ▼               ▼               ▼                       │
│   ┌────────────────────────────────────────────────┐             │
│   │                  SQLite DB                      │             │
│   │              ideas table                        │             │
│   └────────────────────────────────────────────────┘             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

> 토론 단계의 16/8/10은 **페르소나 풀 정원**(`personas/catalog.py`)이며, 한 라운드에
> 동시에 참여하는 인원이 아니다. 프로덕션에서는 매 라운드 풀에서 각각 8/4/3명을
> 성격 균형에 맞춰 선발한다 (`config.yaml`의 `debate.normal.*_agents_per_round`).

## 아이디어 생성 방법

> 1·2는 스케줄 밖의 수동 CLI 경로이고, 사람이 돌리면 지금도 GitHub 이슈를 만든다.
> 스케줄된 파이프라인(3·4)은 이슈를 만들지 않는다 — 아래 [GitHub 이슈 (은퇴)](#github-이슈-은퇴).

### 1. IdeaGenerator (수동 생성)

**파일**: `src/agentic_orchestrator/backlog.py:36-200`

```
CLI 명령 → ClaudeProvider → GitHub Issue 생성
```

- **CLI**: `agentic-orchestrator backlog generate --count 3`
- **LLM**: Claude API 사용
- **출력**: GitHub Issue (`type:idea`, `status:backlog`)
- **특징**: Mossland 생태계 맞춤 프롬프트, 1-2주 MVP 가능한 아이디어

### 2. TrendBasedIdeaGenerator (트렌드 기반)

**파일**: `src/agentic_orchestrator/backlog.py:419-530`

```
RSS 피드 → 트렌드 분석 → Claude로 아이디어 생성 → GitHub Issue
```

- **CLI**: `agentic-orchestrator backlog run-cycle`
- **LLM**: Claude API
- **출력**: GitHub Issue + `source:trend` 라벨
- **특징**: 최신 트렌드에서 영감을 얻은 아이디어

### 3. Multi-Stage Debate (에이전트 토론)

**파일**: `src/agentic_orchestrator/debate/multi_stage.py`

```
토픽 선택 → 3단계 토론 → 아이디어 리스트 생성
   │      │
   │      ├─ Divergence: 다양한 아이디어 생성
   │      ├─ Convergence: 평가/병합/필터링
   │      └─ Planning: 실행 계획 작성
   │
   └─ 최근 8세션에 다룬 주제와 유사한 트렌드는 건너뛰고 차순위를 고른다
      (`_select_debate_trend`). 트렌드는 2시간마다 재분석되므로 이 기억이
      없으면 시끄러운 헤드라인 하나가 하루치 토론을 전부 가져간다 —
      2026-08-22에는 네 슬롯 전부가 같은 뉴스였다.
```

- **스케줄**: PM2 (TEST: 1시간마다, PROD: 6시간마다)
- **LLM**: Ollama (원격) - gemma3:4b (채팅) + qwen3-embedding:0.6b (임베딩)
- **출력**: `Idea` 객체 리스트
- **특징**: 다양한 페르소나가 토론

#### TEST 모드 vs PRODUCTION 모드

| 설정 | TEST 모드 | PRODUCTION 모드 |
|------|-----------|-----------------|
| Divergence 에이전트/라운드 | 2 | 8 |
| Divergence 라운드 | 2 | 3 |
| Convergence 에이전트/라운드 | 2 | 4 |
| Convergence 라운드 | 1 | 2 |
| Planning 에이전트/라운드 | 2 | 5 |
| Planning 라운드 | 1 | 2 |
| **예상 시간** | ~7분 | ~30분+ |

`config.yaml`의 `debate.test_mode`로 전환 (현재: `false` - 프로덕션 모드)

### 4. Auto-Scoring System (자동 점수화)

**파일**: `src/agentic_orchestrator/scheduler/tasks.py:207-426`

```
토론 결과 → 클러스터링 → 자동 점수화 → 2차 심사 → DB 저장
                              │
                              ├─ score >= 7.0 → 유료 reviewer 에게 제출
                              │                  └─ CONFIRM 만 promoted
                              │                     (DEMOTE·심사 불가 → 보류,
                              │                      REJECT → archived)
                              ├─ score < 4.0  → archived
                              └─ 중간 점수    → scored (백로그 → 4h마다 트리아지)
```

> **로컬 점수 7.0은 승격이 아니라 심사 자격이다.** 2차 심사(`scoring/second_pass.py`)
> 의 명시적 CONFIRM 없이는 어느 경로에서도 `promoted` 가 되지 않는다. 이 게이트가
> 21일간 CONFIRM 을 한 번도 내지 않아 승격·플랜 생성이 통째로 멈춘 적이 있다
> (2026-08-05~26). 파이프라인이 조용하면 `GET /usage` 의 `promotion_review` 부터 볼 것.

- **트리거**: 토론 완료 후 자동 실행
- **LLM**: Ollama (로컬)
- **출력**: DB 저장. 플랜 행은 기획 문서가 있을 때만 — 토론의 `final_plan` 을 그 사이클에서
  처음 승격된 아이디어 하나가 가져가고, 나머지 승격은 플랜 행 없이 `promoted` 로 남는다
- **특징**: 점수 기반 자동 승격/아카이브. `scored`는 종착역이 아니다 —
  아래 백로그 트리아지가 며칠 안에 promoted 또는 archived로 종결시킨다.

### 5. IdeationStage (레거시)

**파일**: `src/agentic_orchestrator/stages/ideation.py`

```
스테이트 시작 → Claude로 3개 아이디어 생성 → 최적 선택 → 문서 저장
```

- **CLI**: `agentic-orchestrator run --stage ideation`
- **LLM**: Claude API
- **출력**: Markdown 문서 (`ideas.md`, `selected_idea.md`)
- **특징**: 단일 프로젝트 워크플로우용 (구버전)

## 콘텐츠 품질 요구사항

### 제목 규칙

모든 트렌드, 아이디어, 플랜 제목은 다음 요구사항을 충족해야 합니다:

| 항목 | 요구사항 |
|------|----------|
| 최소 길이 | **30자 이상** |
| 내용 | 구체적인 기술명, 프로젝트명, 수치 포함 |
| 형식 | 실행 가능한 액션 또는 명확한 가치 제안 |

**예시:**
- ❌ 나쁜 예: "AI 트렌드", "DeFi 도구", "NFT 서비스"
- ✅ 좋은 예: "OpenAI GPT-5 에이전트 SDK 출시로 자율 AI 워크플로우 자동화 시대 개막"
- ✅ 좋은 예: "Mossland NFT 홀더를 위한 실시간 메타버스 자산 가치 트래커 개발"

### 아이디어 필수 섹션

토론 발산 단계에서 생성되는 아이디어는 다음 형식을 따릅니다:

```markdown
## 아이디어: [구체적인 제목 30자 이상]

### 1. 핵심 분석 (100자 이상)
- 현재 시장/기술 상황 분석
- 왜 지금 이 아이디어가 필요한지 구체적 근거

### 2. 기회 또는 리스크 (150자 이상)
- 정량적 데이터나 구체적 사례 포함
- 경쟁 서비스와의 차별점

### 3. 구체적 제안 (200자 이상)
- 핵심 기능 3-5개 나열
- 기술 스택 제안 (예: Next.js, Solidity, Python)
- MVP 범위 정의

### 4. 실행 로드맵 (100자 이상)
- 1주차, 2주차 등 구체적 일정
- 필요 리소스 (개발자 수, 예상 비용 등)

### 5. 성공 지표
- 측정 가능한 KPI 2-3개
- 목표 수치 포함 (예: "출시 1개월 내 DAU 500명")
```

### 기획안 필수 섹션

Planning 단계에서 생성되는 기획안은 다음 구조를 따릅니다:

```markdown
## 1. 프로젝트 개요
- 프로젝트 명: [구체적이고 설명적인 이름]
- 한 줄 설명: [50자 이내]
- 목표: [3개 이상]
- 대상 사용자: [예상 사용자 수 포함]
- 예상 기간: [MVP vs 풀버전]
- 예상 비용: [인건비, 인프라 비용]

## 2. 기술 아키텍처
- 프론트엔드: [기술 + 선택 이유]
- 백엔드: [기술 + 선택 이유]
- 데이터베이스: [기술 + 선택 이유]
- 블록체인 연동: [체인, 프로토콜]
- 외부 API: [사용할 서비스]

## 3. 상세 실행 계획
### Week 1: [테마]
- [ ] Task 1: [구체적 작업]
- [ ] Task 2: [구체적 작업]
- **마일스톤**: [완료 조건]

## 4. 리스크 관리
| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|----------|--------|----------|

## 5. 성과 지표 (KPI)
| 지표 | 목표 | 측정 방법 | 측정 주기 |
|------|------|----------|----------|

## 6. 향후 확장 계획
- Phase 2 기능: [...]
- 장기 비전: [...]
```

### 평가 상세 기준

Convergence 단계에서 각 아이디어는 5가지 차원으로 평가됩니다:

| 차원 | 평가 기준 |
|------|----------|
| 실현 가능성 | MVP 구현 가능성, 기술 스택 성숙도, 팀 역량 대비 복잡도 |
| 영향력 | 생태계 시너지, 신규 사용자 유입 잠재력, 수익 모델 |
| 혁신성 | 시장 솔루션 대비 차별점, 기술적 새로움, 비즈니스 모델 혁신 |
| 리스크 | 기술적/시장적/규제적 리스크 |
| 시급성 | 시장 타이밍, 경쟁사 동향, 로드맵 적합성 |

각 평가 항목에 대해 **50자 이상의 구체적 근거**를 작성해야 합니다.

---

## 점수화 기준

Auto-Scorer는 4가지 차원으로 아이디어를 평가합니다:

| 차원 | 설명 | 가중치 |
|------|------|--------|
| **Feasibility** | 1-2주 내 MVP로 구현 가능한가? | 25% |
| **Relevance** | Mossland/Web3 생태계와 관련이 있는가? | 25% |
| **Novelty** | 기존 솔루션과 차별화되는가? | 25% |
| **Impact** | 사용자 가치가 있는가? | 25% |

**총점 = (Feasibility + Relevance + Novelty + Impact) / 4**

### 점수에 따른 상태 결정

| 총점 범위 | 상태 | 액션 |
|----------|------|------|
| 7.0 이상 (+ CONFIRM) | `promoted` | 토론의 기획 문서를 실은 승격 하나만 플랜 행 |
| 4.0 - 7.0 | `scored` | 백로그 대기 → 트리아지가 재평가 |
| 4.0 미만 | `archived` | 아카이브 |

### 백로그 트리아지 — 아이디어 생산·소비 균형 (v0.6.16)

**파일**: `src/agentic_orchestrator/scheduler/backlog_triage.py` (moss-ao-backlog, 4시간 주기)

토론은 하루 ~96개 아이디어를 만들고(절반은 생성 즉시 dedup) 트리아지 이전에는
소비자가 없었다:
`scored`(약 85%)는 영원히 백로그에 남았다. 트리아지는 그 반대쪽 절반이다 — 매 백로그
주기마다 **가장 오래된** `scored` 아이디어를 오늘의 트렌드 기준으로 재채점해 종결 결정을 강제한다:

```
scored (6h 이상 경과, 오래된 순 per_run개)
   │  IdeaScorer 재채점 (현재 트렌드 컨텍스트)
   ├─ score >= 7.0 (+ CONFIRM) → promoted (플랜 행 없음 — 트리아지에는 planning 단계가 없다)
   ├─ score < 4.0  → archived
   └─ 중간 점수    → 스트라이크 1개; max_strikes(기본 2) 도달 시 archived
```

- 모든 아이디어는 최대 `max_strikes`번의 재평가 안에 `promoted|archived`로
  종결 → 열린 백로그 크기는 "생산율 × 결정 소요일"로 유계
- **사이징 규칙**: 분모는 `per_run`이 아니다. 승격에는 2차 판정이 필요하고 후보
  거의 전부가 그것을 원하므로, 허용량이 소진되면 런이 멈춘다 → `20 × 6 = 120
  리뷰/일`. 그리고 **리뷰는 결정이 아니다** — DEMOTE는 스트라이크일 뿐이라
  아이디어 하나가 `archived`에 닿기까지 `max_strikes`번의 리뷰를 쓴다.
  `max_strikes=2` 기준 **~60결정/일 대 도달 ~50/일 = 1.2배**, 얇다.
  (v0.6.17에서 per_run 15→25, min_age 24h→6h — 24h 격리는 첫날 소비가 0이었다)
- 트리아지는 **DB만** 쓴다.
- LLM 폴백(중립 5.0 + reasoning 없음) 감지 시 스트라이크를 주지 않고 건너뜀 —
  Ollama 장애가 아이디어를 잘못 아카이브하면 안 됨
- 설정: `config.yaml`의 `backlog.triage` (enabled/per_run/min_age_hours/max_strikes)

## 스케줄링

`ecosystem.config.js`의 `TEST_MODE`로 TEST/PRODUCTION 스케줄 전환 (현재: **PRODUCTION 모드**)

### 현재 적용 중: PRODUCTION 모드

| 작업 | 주기 | Cron | 설명 |
|------|------|------|------|
| Signal Collection | 30분마다 | `5,35 * * * *` | RSS/API에서 신호 수집 |
| Trend Analysis | 2시간마다 | `15 */2 * * *` | 신호 분석 → 트렌드 생성 |
| **Debate** | **6시간마다** | `25 */6 * * *` | 트렌드 기반 토론 → 아이디어 생성 |
| Backlog | 4시간마다 | `45 */4 * * *` | 백로그 트리아지 + 리텐션 |
| Health Check | 5분마다 | `2-57/5 * * * *` | 시스템 상태 확인 |

> 분 단위가 정각이 아닌 이유: 정각 동시 기동이 Ollama 큐를 폭주시킨 이력이
> 있어 작업별로 :05/:15/:25/:45/:02로 스태거되어 있다 (`ecosystem.config.js`).

### TEST 모드 (빠른 테스트용)

`ecosystem.config.js`에서 `TEST_MODE = true`로 설정 시:

| 작업 | 주기 | Cron | 설명 |
|------|------|------|------|
| Signal Collection | 30분마다 | `5,35 * * * *` | RSS/API에서 신호 수집 |
| Trend Analysis | 1시간마다 | `15 */1 * * *` | 신호 분석 → 트렌드 생성 |
| Debate | 1시간마다 | `25 * * * *` | 트렌드 기반 토론 → 아이디어 생성 |
| Backlog | 1시간마다 | `45 * * * *` | 백로그 트리아지 + 리텐션 |
| Health Check | 5분마다 | `2-57/5 * * * *` | 시스템 상태 확인 |

> 분이 정각이 아닌 이유는 프로덕션과 같다 — 동시 기동이 단일 인스턴스 Ollama
> 큐를 폭주시킨다 (`ecosystem.config.js`의 `SCHEDULES` 주석). TEST 에서도
> signals 주기는 프로덕션과 **같다**.

## GitHub 이슈 (은퇴)

스케줄된 파이프라인은 아이디어·플랜을 GitHub 이슈로 미러링하지 않는다 — 이슈를 만들지도,
라벨·코멘트를 달지도, 닫지도 않는다. 공개 기록은 https://ao.moss.land 이다. 플랜 행이 기획
문서 없이도 쓰이던 시절의 draft 중 문서가 아니었던 행은 `placeholder` 로 남아 플랜 목록·카운트에서
빠진다 — `CLAUDE.md` 의 "GitHub 이슈 미러 은퇴" 절 참조. 기존 이슈의 라벨과, 지금도 이슈를 읽고
쓰는 수동 `ao backlog` CLI 는 [labels.md](labels.md) 참조.

## CLI 명령어

```bash
# 수동 아이디어 생성
agentic-orchestrator backlog generate --count 3

# 트렌드 분석 실행
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler analyze-trends

# 토론 실행
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler run-debate

# 특정 토픽으로 토론
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler run-debate --topic "AI Agent Marketplace"

# 백로그 처리
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler process-backlog
```

## 디버깅

### DB에서 아이디어 소스별 확인

```sql
SELECT source_type, COUNT(*) as count
FROM ideas
GROUP BY source_type
ORDER BY count DESC;
```

### 토론 결과 확인

```sql
SELECT id, topic, status,
       json_array_length(ideas_generated) as idea_count
FROM debate_sessions
ORDER BY started_at DESC
LIMIT 5;
```

---

## 프로젝트 생성

> **상태**: 구현됨 (`project/scaffold.py`, `POST /plans/{id}/generate-project`).
> 일시정지된 것은 **스케줄러의 인라인 자동 생성 한 곳**뿐이고
> (`project.auto_generate.enabled: false`), API·버튼 경로는 동작한다.
> 저장소의 `projects/` 폴더가 비어 보이는 것은 생성물을 커밋하지 않기 때문이다.

### 계획된 워크플로우

```
Plan (DB)
    ↓
프로젝트 이름 생성 (kebab-case)
    ↓
projects/{project-name}/
    ├── README.md          # 프로젝트 소개 + 배경
    ├── PLAN.md            # 원본 Plan 문서
    ├── src/               # 생성된 소스 코드
    └── docs/              # 추가 문서
```

자세한 내용은 [projects.md](projects.md) 참조.
