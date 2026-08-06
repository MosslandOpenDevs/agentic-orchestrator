# `origin/main` 전체 점검 보고서

## 결론

현재 `origin/main`은 **배포 준비 완료로 보기 어렵습니다**.

- 기준 커밋: `3ec4f7a87703eda3541184e8fcbd981418dc872a`
- 원격 확인 시각 기준 최신 커밋: 2026-08-05 14:30:18 +09:00
- 판정: **P1 13건을 해소하기 전에는 공개 쓰기 기능 및 자동 배포를 중단하거나 제한하는 것이 안전**
- 발견 건수: P0 0 / P1 13 / P2 12 / P3 2

가장 먼저 막아야 할 경로는 다음 네 가지입니다.

1. 공개 Next.js 프록시가 익명 요청에 서버 API 키를 붙여 plan 승인과 LLM 프로젝트 생성을 허용합니다.
2. LLM 토론 메시지를 sanitize하지 않은 HTML로 렌더링해 stored XSS가 가능합니다.
3. 파일 SQLite의 모든 세션이 하나의 연결과 트랜잭션을 공유해 동시 요청의 rollback이 다른 요청의 변경을 지울 수 있습니다.
4. 자동 배포와 자체 QA가 모두 fail-open 경로를 가지고 있어, 검증되지 않았거나 구현조차 없는 결과가 운영/DONE 상태로 진입할 수 있습니다.

## 범위와 방법

다음 영역을 최신 `origin/main` 전체 트리 기준으로 점검했습니다.

- Python API, DB, scheduler, signal/trend/debate/project/QA 파이프라인
- Next.js 웹사이트 및 서버 프록시 route
- PM2와 pull 기반 자동 배포
- CI, lockfile, 공급망과 알려진 취약점
- `src/projects/plan-mossland-defi-real-time-market-insights`의 backend/frontend/contracts/Docker Compose
- 단위 테스트, lint, formatting, typecheck, production build 및 선택적 최소 재현

심각도는 다음 의미로 사용합니다.

- P1: 공개 노출 또는 운영 배포 전에 우선 수정해야 하는 보안·데이터 무결성·핵심 기능 차단 문제
- P2: 다음 수정 주기에 포함해야 하는 기능·신뢰성·운영 문제
- P3: 낮은 위험의 완성도·공급망 강화 문제

## P1 — 우선 수정

### 1. 익명 사용자가 서버 API 키 권한으로 plan을 승인하고 프로젝트 생성을 실행할 수 있음

위치:

- [approve proxy](/Users/m/Downloads/github/agentic-orchestrator/website/src/app/proxy/plans/[id]/approve/route.ts:5)
- [generate proxy](/Users/m/Downloads/github/agentic-orchestrator/website/src/app/proxy/plans/[id]/generate-project/route.ts:5)
- [backend key check](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:113)
- [project generation endpoint](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:1474)
- [plan approval endpoint](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:1651)

두 Next.js route는 사용자 인증·권한 확인, CSRF/Origin 확인, rate limit 없이 공개 POST를 받은 뒤 서버의 `MOSS_API_KEY`를 `X-API-Key`로 주입합니다. 백엔드가 API 키로 보호하려던 두 mutation이 웹 프록시를 통해 익명 기능으로 바뀝니다. 공격자는 plan 상태를 변경하고 비용이 큰 LLM 생성, DB 및 파일 쓰기를 반복 실행할 수 있습니다.

서버 프록시 앞에 실제 사용자 session/RBAC를 두고 CSRF/Origin, JSON content type, rate limit, idempotency를 검증해야 합니다. 공유 master key는 브라우저 사용자의 권한 모델로 사용하면 안 됩니다.

### 2. LLM 토론 메시지가 stored XSS로 렌더링됨

위치:

- [markdown renderer](/Users/m/Downloads/github/agentic-orchestrator/website/src/lib/markdown.tsx:15)
- [DebateConversation](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/visualization/DebateConversation.tsx:112)
- [LiveDebateViewer](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/visualization/LiveDebateViewer.tsx:225)
- [LLM response persistence](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/debate/multi_stage.py:848)

`marked.parse()` 결과를 sanitize 없이 `dangerouslySetInnerHTML`에 넣습니다. `marked`는 raw HTML을 정화하지 않으며 sanitizer 의존성도 없습니다. 외부 signal이나 issue에서 유도된 prompt injection 또는 악성 모델 응답에 HTML event handler 등이 포함되면 토론을 보는 사용자의 `ao.moss.land` origin에서 실행될 수 있습니다.

raw HTML을 비활성화한 Markdown renderer를 쓰거나 DOMPurify 계열 sanitizer를 적용하고, CSP와 악성 Markdown 회귀 테스트를 추가해야 합니다.

### 3. 파일 SQLite의 모든 세션이 동일 연결과 트랜잭션을 공유함

위치: [Database._init_engine](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/connection.py:54)

파일 SQLite에도 `StaticPool`을 적용합니다. 최소 재현에서 두 SQLAlchemy session의 DBAPI connection이 같았고, 두 번째 session이 첫 번째 session의 미커밋 행을 읽은 뒤 rollback하자 첫 번째 session이 commit해도 행이 사라졌습니다.

```text
same_connection True
s2_sees_uncommitted 1
after_other_rollback 0
```

FastAPI 동시 요청과 장시간 background generation이 겹치면 실제 데이터 유실로 이어질 수 있습니다. `StaticPool`은 in-memory SQLite에만 제한하고, 파일 DB는 기본 pool을 사용해야 합니다. WAL, `busy_timeout`, 동시 session 격리 테스트도 필요합니다.

### 4. 시간 감쇠가 분석에는 반영되지 않으면서 원본 Signal 점수만 반복 훼손함

위치:

- [score mutation](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/scheduler/tasks.py:79)
- [scheduled use](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/scheduler/tasks.py:230)
- [FeedItem conversion](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/scheduler/tasks.py:253)
- [commit](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/scheduler/tasks.py:306)

`Signal.score` 자체에 decay를 곱한 뒤 session을 commit합니다. 반복 실행 시 `1.0 → 0.4 → 0.16 → 0.064`로 비가역적으로 누적됐습니다. 하지만 이후 `FeedItem`에는 score 필드가 없어 이 값이 trend analyzer에 전달되지 않습니다. 분석 가중 효과는 없고 API 정렬과 필터에 쓰는 저장 점수만 손상됩니다.

원본 score를 변경하지 말고 transient `effective_score`를 계산해 analyzer 입력 계약에 포함해야 합니다.

### 5. 구현·테스트·리뷰어가 전혀 없어도 자체 QA가 통과함

위치:

- [missing implementation passes tests](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/stages/quality.py:183)
- [missing pytest passes](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/stages/quality.py:235)
- [no code gets 7/10](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/stages/quality.py:266)
- [no reviewer gets 7/10](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/stages/quality.py:299)
- [overall gate](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/stages/quality.py:491)

빈 프로젝트 재현 결과는 `tests=True`, review `7.0`, security issues `0`, overall `True 7.0`이었습니다. 기본 요구 점수도 7점이므로 구현이 없어도 승인됩니다. 최대 반복 횟수에 도달한 실패 결과도 DONE으로 보낼 수 있습니다.

`missing`, `skipped`, `unavailable`을 `passed`와 분리하고, 명시적 waiver 없이는 구현 파일·필수 테스트·검증 도구가 모두 존재하고 성공해야 gate를 통과하도록 바꿔야 합니다.

### 6. 외부 입력에서 파생된 LLM 생성 테스트를 운영 호스트에서 직접 실행함

위치: [QualityStage._run_tests](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/stages/quality.py:190)

생성된 `test_*.py`를 운영 process의 cwd, 환경 변수, 파일 권한, 네트워크를 그대로 상속한 `python -m pytest`로 실행합니다. pytest는 collection/import 단계부터 임의 Python 코드를 실행하므로, 외부 signal·plan·LLM 출력이 운영 DB, 저장소, secret, 네트워크에 접근하는 경로가 됩니다.

생성 코드는 비특권 disposable container/VM에서 network 차단, secret 제거, read-only source, 제한된 tmp, CPU/메모리/시간 제한을 적용해 실행해야 합니다.

### 7. 실패한 프로젝트 재시도가 작업 없이 성공으로 종료됨

위치:

- [unconditional existing-project early return](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/project/scaffold.py:138)
- [API retry decision](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:1503)
- [job completion mapping](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:1461)

API는 `error` project를 재시도 대상으로 허용하지만 scaffold는 상태와 무관하게 기존 project를 찾으면 `success=True`로 조기 반환합니다. 재현에서는 `project_path=None`과 “already exists” error를 가진 성공 결과가 나왔고 background job은 `completed`가 됐습니다.

기존 project 조기 반환을 `generating`과 완료 상태로 제한하고 `error`는 정상 재생성 대상으로 처리해야 합니다. API부터 background result까지 잇는 회귀 테스트가 필요합니다.

### 8. SignalStorage 조회·백업·내보내기가 detached ORM 객체로 실패함

위치:

- [session configuration](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/connection.py:38)
- [get_recent](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/signals/storage.py:30)
- [backup_signals](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/signals/storage.py:117)
- [export_for_analysis](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/signals/storage.py:202)

기본 `expire_on_commit=True` session에서 ORM row를 반환한 뒤 context manager가 commit·close합니다. 호출자가 속성이나 `to_dict()`를 읽으면 `DetachedInstanceError`가 발생했습니다. source/category/search 조회와 JSON/CSV backup/export가 모두 같은 구조입니다.

session 안에서 DTO/dict로 직렬화해 반환하거나 읽기 session 수명을 호출자까지 유지해야 합니다.

### 9. GitHub check가 없거나 skipped여도 “CI green”으로 운영 배포함

위치: [deploy CI gate](/Users/m/Downloads/github/agentic-orchestrator/scripts/deploy.sh:163)

`check_runs=[]`은 `none`으로 분류한 뒤 195행에서 배포를 계속합니다. `skipped`, `neutral`, `stale`도 실패 집합에 없으므로 success로 처리되며, 필수 job 이름과 GitHub Actions 발행자도 확인하지 않습니다.

최소 재현에서는 다음과 같이 미검증 target으로 HEAD가 이동했습니다.

```text
CI: no checks reported for this commit -- proceeding
DEPLOYED 3be5cb84 -> 5103254a
```

체크 0개는 대기/실패로 처리하고, 요구되는 정확한 job 집합이 모두 `conclusion=success`인지 검증해야 합니다.

### 10. DB와 schema가 깨져도 배포 성공으로 판정하고 사전 백업 실패도 무시함

위치:

- [snapshot fail-open](/Users/m/Downloads/github/agentic-orchestrator/scripts/deploy.sh:269)
- [deploy health check](/Users/m/Downloads/github/agentic-orchestrator/scripts/deploy.sh:341)
- [unconditional API health](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:174)
- [schema create_all](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/connection.py:75)

배포 전 DB snapshot 실패 후에도 진행하며 readiness는 DB를 보지 않고 항상 200을 반환하는 `/health`만 호출합니다. schema 관리는 `create_all()`뿐이라 기존 table의 column 변경·삭제·타입 변경을 migration하지 않습니다. 핵심 endpoint가 모두 500이어도 배포기가 `DEPLOYED`를 기록하고 rollback하지 않을 수 있습니다.

snapshot 실패를 fail-closed로 바꾸고 versioned migration과 schema revision을 도입해야 합니다. DB와 필수 의존성을 검사해 503을 반환하는 readiness endpoint를 별도로 두십시오.

### 11. 고정 설치되는 Next.js와 sharp에 알려진 high 취약점이 남아 있음

위치:

- [Next.js lock entry](/Users/m/Downloads/github/agentic-orchestrator/website/package-lock.json:5216)
- [sharp lock entry](/Users/m/Downloads/github/agentic-orchestrator/website/package-lock.json:5891)

배포가 사용하는 `npm ci`는 Next.js `16.2.9`와 sharp `0.34.5`를 고정 설치합니다. `npm audit --omit=dev`는 두 package를 high로 판정했습니다. Next.js에는 해당 범위의 middleware/proxy bypass, Server Action DoS/SSRF, cache confusion 등의 advisory가 포함되고 sharp는 libvips 계열 취약점의 영향을 받습니다.

Next.js를 최소 `16.2.11` 이상으로 올리고 sharp가 `0.35.0` 이상으로 해소되는 lockfile을 재생성한 뒤 audit과 production build를 다시 수행해야 합니다. 실제 사용 기능과 무관한 advisory가 있더라도 공개 App Router 서버의 직접 dependency가 취약 범위에 고정된 상태는 유지하면 안 됩니다.

### 12. 추적 중인 생성 프로젝트가 backend/frontend/contracts 어느 쪽도 빌드·배포될 수 없음

대표 위치:

- [backend Dockerfile](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/src/backend/Dockerfile:5)
- [frontend Dockerfile](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/src/frontend/Dockerfile:5)
- [frontend next config](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/src/frontend/next.config.js:1)
- [backend entrypoint](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/src/backend/src/index.ts:34)
- [contract manifest](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/contracts/package.json:5)
- [contract deploy script](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/contracts/scripts/deploy.ts:7)

세 package 모두 lockfile이 없어 Docker의 첫 `npm ci`부터 실패합니다. 추가로:

- backend는 production dependencies만 설치한 뒤 devDependency인 `tsc`를 실행하며, Compose port와 app 기본 port가 다릅니다.
- backend TypeScript는 누락 dependency/file과 strict initialization 문제로 109개 오류가 발생했습니다.
- frontend TypeScript는 client boundary, 누락 package, export/type 오용 등 102개 오류가 발생했습니다.
- frontend image는 없는 `public/`과 설정하지 않은 `.next/standalone`을 복사합니다.
- Express는 `/health`만 구현했지만 문서는 인증과 sentiment/security API를 구현된 것처럼 설명합니다.
- Solidity는 선언하지 않은 OpenZeppelin을 import하고 deploy/test가 각각 존재하지 않는 contract 이름을 사용합니다.

생성 완료 조건을 clean install, typecheck, framework build, contract compile/test, Docker build가 모두 성공하는 경우로 강화해야 합니다. 현재 artifact는 `ready`가 아니라 명시적인 failed/incomplete 상태여야 합니다.

### 13. 생성 프로젝트의 PostgreSQL superuser가 기본 암호로 모든 host interface에 노출됨

위치: [docker-compose.yml](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/docker-compose.yml:29)

`postgres/postgres`를 고정하고 `5432:5432`로 publish합니다. host 5432에 접근 가능한 사용자는 DB 관리자 권한을 얻을 수 있습니다.

DB port publish를 제거하고 내부 network에서만 접근시키며, secret으로 주입한 강한 비밀번호와 최소권한 app role을 사용해야 합니다. 로컬 접근이 필요해도 최소한 loopback에만 bind해야 합니다.

## P2 — 다음 수정 주기

### 14. 정상 참조 데이터가 있으면 retention sweep 전체가 FK 오류로 rollback됨

위치:

- [trend retention](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/repositories.py:228)
- [debate retention](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/repositories.py:454)
- [Idea foreign keys](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/models.py:223)
- [Plan debate FK](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/models.py:367)
- [scheduled transaction](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/scheduler/tasks.py:1520)

오래된 Trend는 `Idea.source_trend_id`가, DebateSession은 `Idea/Plan.debate_session_id`가 참조하지만 delete policy가 없습니다. SQLite FK 활성화 상태에서 두 경로 모두 `FOREIGN KEY constraint failed`가 재현됐습니다. 두 삭제가 한 transaction이어서 하나가 실패하면 모두 rollback됩니다.

참조 부모를 유지하거나 nullable FK에 `ON DELETE SET NULL`을 적용하는 등 보존 정책을 명시해야 합니다.

### 15. 수동 승인 metadata는 저장되지 않고 project job 예외는 DB session을 누수함

위치:

- [in-place JSON mutation](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:1712)
- [plain JSON column](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/db/models.py:387)
- [background session lifecycle](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:1427)

기존 `extra_metadata` dict를 in-place 수정하지만 column은 `MutableDict`가 아닌 일반 JSON이어서 변경이 추적되지 않습니다. 재현에서는 status는 approved가 됐지만 `manually_approved`와 `approved_at`은 사라졌습니다. 새 dict를 재할당해야 합니다.

또한 background task는 성공 경로에서만 `session.close()`를 호출합니다. router/scaffold/commit 예외 경로에는 rollback/finally close가 없어 반복 실패 시 connection과 transaction이 남을 수 있습니다.

### 16. 음수 pagination limit으로 공개 API 상한을 우회할 수 있음

위치: [API pagination declarations](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:350)

signals, debates, trends, ideas, plans, activity, projects의 `limit`은 `le=`만 있고 `ge=1`이 없습니다. SQLite의 `LIMIT -1`은 제한 없음이므로 `GET /signals?limit=-1`이 200과 `limit=-1`을 반환하고 전체 matching row를 직렬화합니다.

모든 limit query에 `ge=1`을 추가하고 공통 pagination model로 통일해야 합니다.

### 17. Ollama health와 동시성 제한이 모두 실제 장애를 숨김

위치:

- [throttle](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/providers/ollama.py:199)
- [health model lookup](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/providers/ollama.py:468)
- [health response](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/providers/ollama.py:496)

model 조회의 network/HTTP/JSON 오류를 빈 list로 바꾼 뒤 health는 이를 무조건 `healthy`로 포장합니다. 동시에 throttle은 여러 coroutine이 같은 대기 시간을 계산한 뒤 lock 밖에서 함께 sleep해 거의 동시에 반환하고, `max_concurrent_requests`는 사용되지 않습니다.

오류 원인을 보존해 빈 model/default model 부재를 degraded로 보고하고, atomic time-slot reservation과 semaphore로 간격 및 동시성 제한을 구현해야 합니다.

### 18. `/adapters` 요청 하나가 11개 외부 서비스 probe를 순차 실행함

위치: [adapters endpoint](/Users/m/Downloads/github/agentic-orchestrator/src/agentic_orchestrator/api/main.py:978)

인증 없는 GET마다 adapter 11개를 만들고 외부 health check를 순차 await합니다. 각 probe는 최대 약 10초 timeout을 가질 수 있어 public endpoint가 제3자 API 호출 증폭기와 worker 점유 수단이 됩니다.

background job에서 주기적으로 수집한 cache만 반환하거나, 짧은 전체 deadline 아래 제한된 병렬 probe를 사용해야 합니다.

### 19. 웹의 ID·상태 계약 불일치로 상세 보기와 live/project UI가 잘못 동작함

대표 위치:

- [idea ID loss](/Users/m/Downloads/github/agentic-orchestrator/website/src/lib/api.ts:686)
- [backlog detail call](/Users/m/Downloads/github/agentic-orchestrator/website/src/app/backlog/page.tsx:226)
- [status mapping](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/IdeaCard.tsx:14)
- [live debate detail](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/details/DebateDetail.tsx:45)
- [project state machine](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/details/PlanDetail.tsx:77)

`ApiIdea.id`를 버리고 `index+1`로 바꿔 UUID 기반 `/ideas/{id}`가 404를 냅니다. frontend status vocabulary는 backend enum과 달라 `in-dev`가 항상 비고 실제 상태가 Backlog로 오표시됩니다. Debate detail은 실제 `active` 대신 `in-progress`를 검사하고 refresh callback을 전달하지 않아 live modal이 멈춥니다. Project UI도 force regenerate에 `false`를 보내고, polling error/빈 job ID/`ready_with_warnings`를 종료 상태로 처리하지 못합니다.

ID와 display index를 분리하고 backend schema에서 공유 type/enum을 생성하는 것이 가장 안전합니다. Project job에는 명시적인 state machine과 취소 가능한 polling을 적용해야 합니다.

### 20. 전역 NpcCityStrip이 자매 서비스의 유효하지만 예상 밖 JSON 하나로 모든 page render를 깨뜨림

위치:

- [NpcCityStrip](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/NpcCityStrip.tsx:30)
- [root layout use](/Users/m/Downloads/github/agentic-orchestrator/website/src/app/layout.tsx:71)

응답을 type cast만 하고 `headlines`가 array인지, 각 record와 `npc`가 존재하는지 검증하지 않습니다. `{headlines:{}}`나 부분 record에서 catch 밖의 `.length`, `.slice`, field dereference가 throw하며 이 component는 모든 route의 root layout에 있습니다.

runtime schema/`Array.isArray`와 record validation, guarded fallback 또는 error boundary가 필요합니다.

### 21. 장애·빈 DB·transparency 지표를 실제 운영 데이터처럼 위장함

위치:

- [mock fallback](/Users/m/Downloads/github/agentic-orchestrator/website/src/lib/api.ts:624)
- [footer status](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/Footer.tsx:195)
- [random score breakdown](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/visualization/ScoreBreakdown.tsx:30)
- [random sparkline](/Users/m/Downloads/github/agentic-orchestrator/website/src/components/visualization/TrendSparkline.tsx:20)

API 장애뿐 아니라 정상 empty array도 mock stats/activity/trends/ideas/plans로 바꾸고 provenance를 표시하지 않습니다. footer는 항상 `System Online`이며 transparency 화면은 `Math.random()`과 임의 휴리스틱으로 점수·history·consensus를 생성합니다. reload마다 값이 달라지고 운영/분석 데이터처럼 보입니다.

정상 empty와 error를 분리하고 `{data, source, error}`를 명시해야 합니다. simulation은 명확히 표시하고 deterministic seed를 사용하거나 실측 API 필드로 교체해야 합니다.

### 22. `ecosystem.config.js` 변경이 PM2에 적용되지 않은 채 동기화 완료됨

위치: [deploy change classification](/Users/m/Downloads/github/agentic-orchestrator/scripts/deploy.sh:204)

ecosystem 변경은 `ECOSYSTEM_CHANGED`만 세우고 backend/frontend 변경으로 보지 않습니다. HEAD를 target으로 옮긴 뒤 수동 명령을 한 번 안내하고 “docs only”로 종료합니다. 다음 poll은 이미 같은 HEAD이므로 command/env/cron 변경이 무기한 미적용될 수 있습니다.

`pm2 startOrReload`와 검증·rollback을 배포 transaction에 포함하거나 적용 완료 상태를 별도로 추적해야 합니다.

### 23. 데이터 migration을 재실행할 때 합성 signal이 계속 중복 삽입됨

위치: [migrate_to_db.py](/Users/m/Downloads/github/agentic-orchestrator/scripts/migrate_to_db.py:171)

`create_sample_signals()`는 stable key/upsert 없이 trend마다 합성 signal을 만들고 각 실행에서 commit합니다. 두 번 실행한 최소 재현에서 row 수가 1에서 2로 늘었습니다. 운영 migration에 demo 데이터 생성이 기본 포함된 점도 위험합니다.

demo 생성을 명시적 opt-in으로 분리하고 source trend ID 기반 unique key/upsert, 원자적 migration 또는 checkpoint를 사용해야 합니다.

### 24. CI와 lockfile이 실제 배포 artifact를 재현하거나 검증하지 못함

위치:

- [CI workflow](/Users/m/Downloads/github/agentic-orchestrator/.github/workflows/ci.yml:9)
- [Python dependencies](/Users/m/Downloads/github/agentic-orchestrator/pyproject.toml:27)
- [ignored uv.lock](/Users/m/Downloads/github/agentic-orchestrator/.gitignore:90)
- [website manifest](/Users/m/Downloads/github/agentic-orchestrator/website/package.json:1)
- [pnpm lock importer](/Users/m/Downloads/github/agentic-orchestrator/website/pnpm-lock.yaml:9)

CI는 Python lint/test만 실행하며 website, 생성 backend/frontend, Hardhat, Docker를 검증하지 않습니다. 그 결과 현재 main의 생성 package 세 개가 clean install부터 실패해도 green이 됩니다. root website에도 test script와 test/spec file이 없습니다.

문서가 사용하는 `pnpm install --frozen-lockfile`은 제거된 `gray-matter`와 Next/eslint 버전 불일치로 즉시 실패합니다. 반면 배포는 별도 `package-lock.json`의 `npm ci`를 사용합니다.

Python은 대부분 `>=`만 지정하고 `uv.lock`이 ignore되어 remote commit에 포함되지 않습니다. CI는 매번 최신 dependency graph를 해석하고 운영은 machine별 untracked lock 또는 pip 해석 결과를 사용하므로 같은 SHA의 CI·신규 배포·rollback이 서로 다른 package로 실행될 수 있습니다.

하나의 package manager/lockfile을 정하고, Python lock도 추적해 CI와 운영 모두 frozen install을 사용해야 합니다. website/build/typecheck/test, 생성 artifact, Hardhat, Docker job을 required checks로 추가하십시오.

### 25. 생성 프로젝트의 외부 API와 “on-chain alert” 구현이 문서 의미와 다름

위치:

- [Dune service](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/src/backend/src/services/dune_analytics.ts:62)
- [Twitter service](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/src/backend/src/services/twitter_x_api.ts:23)
- [OnChainMonitor](/Users/m/Downloads/github/agentic-orchestrator/src/projects/plan-mossland-defi-real-time-market-insights/contracts/contracts/OnChainMonitor.sol:18)

Dune module은 import 시 hardcoded query를 실행하고, Twitter token을 Google OAuth client로 처리하며, `.env.example`의 변수 이름도 구현과 다릅니다. `OnChainMonitor`는 transaction proof 없이 owner가 전달한 임의 정수의 홀짝만으로 보안 alert를 만듭니다.

import-time side effect를 제거하고 typed config 및 실제 provider 인증을 구현해야 합니다. on-chain 증거가 필요하다면 chain/tx hash, 검증 가능한 oracle signature, replay protection을 사용해야 합니다.

## P3 — 낮은 우선순위

### 26. 선언한 OG image asset이 존재하지 않음

위치: [layout metadata](/Users/m/Downloads/github/agentic-orchestrator/website/src/app/layout.tsx:26)

`/og-image.png`를 선언하지만 `website/public`과 app metadata route에 해당 asset이 없습니다. social preview가 404가 됩니다. 1200×630 asset 또는 `opengraph-image` route를 추가해야 합니다.

### 27. GitHub Actions가 mutable tag를 사용하고 최소 permissions를 선언하지 않음

위치: [CI actions](/Users/m/Downloads/github/agentic-orchestrator/.github/workflows/ci.yml:19)

`actions/checkout@v4`, `actions/setup-python@v5`, `codecov/codecov-action@v3`를 commit SHA가 아닌 이동 가능한 tag로 실행하며 workflow-level `permissions`가 없습니다. 검증한 full SHA로 pin하고 `permissions: contents: read` 등 최소 권한을 선언해야 합니다.

## 실행 검증 결과

### 성공

- 원격 fetch 후 `HEAD == origin/main == 3ec4f7a87703eda3541184e8fcbd981418dc872a`
- Python: `473 passed`, 전체 line coverage `41%`
- Ruff: `All checks passed`
- Black: `108 files would be left unchanged`
- Python compileall: 성공
- Website `npm run lint`: 성공
- Website `npx tsc --noEmit`: 성공
- Website `npm run build`: 성공, 14개 static page와 dynamic route 생성
- Python production dependency audit: 알려진 취약점 없음
- `bash -n scripts/deploy.sh`, `shellcheck scripts/deploy.sh`, `node --check ecosystem.config.js`: 성공
- 실제 credential pattern scan: test/example placeholder 외 발견 없음

### 실패 또는 주의

- Website `pnpm install --frozen-lockfile`: stale lockfile로 실패
- Website `npm audit --omit=dev`: high 2 package
- 생성 backend/frontend/contracts `npm ci --dry-run`: 모두 lockfile 부재로 실패
- 생성 backend TypeScript: 109 errors
- 생성 frontend TypeScript: 102 errors
- Docker runtime이 없어 image build 자체는 실행하지 못했지만, 각 Dockerfile의 선행 `npm ci`가 재현상 실패
- Python 테스트는 77 warnings를 냈으며 FK cycle과 여러 unclosed SQLite connection 경고가 포함됨
- remote에는 Python lockfile이 없으므로 이번 Python 검증 환경의 정확한 dependency graph가 commit으로 재현되지는 않음

## 권장 수정 순서

1. 공개 `/proxy/plans/*`를 닫거나 사용자 session/RBAC를 적용하고, Markdown XSS를 제거합니다.
2. 파일 SQLite pool과 time-decay 영구 score mutation을 수정한 뒤 데이터 무결성 회귀 테스트를 추가합니다.
3. CI gate의 `none/skipped` fail-open, DB readiness, snapshot/migration을 고쳐 자동 배포를 fail-closed로 만듭니다.
4. QA의 missing/skipped pass와 host 직접 코드 실행을 제거합니다.
5. Next.js/sharp를 패치하고 npm/pnpm 및 Python lock 전략을 하나로 통일합니다.
6. 생성 프로젝트를 clean build/test/Docker gate를 통과할 때만 ready로 분류하도록 생성 파이프라인을 강화합니다.
7. 나머지 API/UI 계약, retention, telemetry, PM2 적용 문제를 수정합니다.

## 작업 트리

소스 코드는 변경하지 않았습니다. 이 보고서만 새로 작성했으며 기존의 추적되지 않은 `docs/reviews/` 파일은 보존했습니다.
