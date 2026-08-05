# 변경 이력

**한국어** | [English](CHANGELOG.md)

Mossland Agentic Orchestrator의 모든 주요 변경 사항을 이 파일에 문서화합니다.

이 형식은 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)를 기반으로 하며,
이 프로젝트는 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 준수합니다.

## [Unreleased]

### 추가
- **트렌드 분석에 structured outputs 적용.** Ollama는 v0.5.0(2024-12)부터 `format` 필드로 JSON 스키마를 디코딩 수준에서 강제한다 — 문법에 어긋나는 토큰은 샘플링 자체가 불가능하다. 운영 서버(0.32.5)는 처음부터 이 기능이 있었는데 코드가 안 썼을 뿐이다. provider에 `format_schema` 추가, router가 `response_schema`를 모든 Ollama 호출 지점(스키마 유실이 조용히 지나갈 두 폴백 경로 포함)에 배관, 트렌드 분석 호출에 `TrendAnalyzer.TRENDS_RESPONSE_SCHEMA` 부착. 운영 서버 E2E: 첫 응답 토큰이 `{`, 스마트 쿼트는 합법인 문자열 값 *안에만* 등장, 엄격 `json.loads`가 관용 수리 없이 통과, 같은 temperature에서 품질 유지(요약 700-950자). 관용 파서는 심층 방어로 유지 — 스키마 유효 ≠ 의미 유효이고, `max_tokens` 절단은 여전히 문서를 자를 수 있다. 파서가 읽는 모든 필드가 스키마에 존재하는지 검사하는 일관성 테스트를 두어, 문법이 파이프라인이 저장하는 필드를 금지하는 일이 없게 했다. 신규 테스트 7개; 3단 배관(provider 페이로드, router 전달, analyzer 부착)을 단계별로 뮤테이션 검증.

### 수정
- **트렌드 분석이 매 사이클 조용히 0건을 생성.** 2026-08-05 실서버에서 확인한 두 겹의 결함. 첫째: 어떤 Ollama 요청도 `num_ctx`를 보내지 않아 공유 서버가 gemma3:4b를 자체 기본값 4096으로 로드했다. 트렌드 프롬프트만 ~3,300토큰이라 생성이 정확히 `prompt_eval + eval == 4096`에서 `done_reason="length"`로 끊겼는데, provider가 그 필드를 버려서 로그 한 줄 남지 않았다. 둘째: JSON 추출기가 *닫힌* ` ```json ` 펜스를 요구했고(절단은 닫는 펜스부터 먹는다), gemma3가 문자열 구분자로 곡선 따옴표(“ ”)를 쓰는 습관 — 완결된 응답에서도 관찰됨 — 을 `json.loads`가 용납하지 않는다. 둘 중 하나만으로도 응답 전체가 버려졌고, 숫자 목록 텍스트 폴백도 매칭되지 않아 `Saved 0 trends`가 됐다.
- 수정 사항(각각 뮤테이션 검증): 모든 generate/chat/stream 호출이 `num_ctx`를 전송(기본 16384, `throttling.ollama.num_ctx`로 조정 가능); 트렌드 호출에 명시적 출력 예산 `max_tokens=4096`; `OllamaResponse`에 `done_reason`과 `truncated` 프로퍼티 추가, 절단된 생성은 토큰 수와 함께 WARNING 로그; 파싱은 계층화 — 엄격한 펜스 → 문자열 인지 중괄호 균형 슬라이스 → 스마트 쿼트 정규화 + 후행 쉼표 제거를 곁들인 완화 재파싱(수리는 엄격 파싱 실패 후에만 실행되므로 정상 콘텐츠는 절대 변형되지 않음) → `"trends"` 배열의 객체 단위 salvage(절단된 꼬리에서 완결된 선행 객체들을 회수). "```json 이후 끝까지" 층도 시도했으나 salvage가 완전히 덮는 것이 증명되어 제거.
- 머지 전 운영 서버에서 E2E 검증: 이전에 4096에서 죽던 동일한 실제 프롬프트(`eval=798`, reason=`length`, 0건)가 이제 자연 종료(`eval=1397`, reason=`stop`)하고 점수화된 트렌드로 파싱된다.
- `tests/test_trend_json_parsing.py` (24개)가 양쪽을 고정: 페이로드 옵션(`num_ctx` 상시 존재·설정 가능, `max_tokens` → `num_predict`), 절단 감지와 경고, 그리고 실제 프로덕션 실패 형태(산문 서두 + 펜스 + 스마트 쿼트 + 절단)를 포함한 파서 시험대. 6가지 뮤테이션 — `num_ctx` 제거, `done_reason` 제거, 쿼트 정규화 비활성, salvage 비활성, 경고 무음화, analyzer의 `max_tokens` 제거 — 이 각각 대응 테스트를 실패시킨다.
- `scripts/deploy.sh`가 의존성 설치 방식을 체크아웃 형태에 맞춰 고른다: `uv.lock`이 있거나 `.venv/pyvenv.cfg`에 uv가 만든 환경이라고 적혀 있으면 `uv sync`, 아니면 `pip install -e .`. 테스트가 아니라 운영 서버를 직접 확인하다가 발견했다 — 그 `.venv`는 uv가 만든 것이라 **내부에 pip이 아예 없고**, 따라서 원래의 `pip install -e .`는 이 스크립트가 존재하는 이유인 바로 그 머신에서 실패했을 것이다. 그것도 `pyproject.toml`을 건드리는 커밋에서만, 즉 롤백이 가장 반갑지 않은 시점에. 서버의 `uv.lock`은 저장소에 커밋돼 있지 않으므로 이 판별은 커밋이 아니라 머신의 속성이다. 두 분기와 `uv sync` 실패 시 롤백 경로를 모두 커버했고, 판별 로직은 양방향(강제로 uv 켜기/끄기)으로 뮤테이션 검증했다.

### 추가
- **풀(pull) 방식 자동 배포** (`scripts/deploy.sh` + 옵트인 PM2 잡 `moss-ao-deploy`): 사람이 서버에 들어가 `git pull` + `npm run build` + `pm2 restart`를 치는 대신, 운영 서버가 5분마다 스스로 `main`을 따라간다. CI에서 밀어넣는(push) 방식을 쓰지 않은 이유는 기록해 둘 가치가 있다 — 앱 서버는 공개 인바운드 경로가 없고(테일넷 안에서만 접근 가능하며 공개 도메인 `ao.moss.land`는 별도 Lightsail의 Nginx가 프록시), 이 저장소는 public이라 self-hosted 러너를 붙이면 포크 PR이 사내 머신에서 코드를 실행할 수 있으며, 운영 계정 권한은 admin이 아닌 `MAINTAIN`이라 러너·시크릿 등록이 403이다. 당겨오는 방식은 이 중 아무것도 필요 없다: public repo는 익명 fetch가 되므로 서버는 포트를 열지 않고, 배포 키도 없고, GitHub 쪽 설정이 아예 없다. Tailscale은 원래대로 사람이 서버에 들어가는 관리 경로로 남고 배포 경로에는 관여하지 않는다.
- 배포기는 diff가 요구하는 일만 한다: `pyproject.toml`이 바뀌면 `pip install -e .`, 락파일이 바뀌면 `npm ci`, `website/` 변경이면 `npm run build`(`NEXT_PUBLIC_*`가 빌드 시점에 박히므로 재시작만 하면 이전 번들이 계속 나간다), 재시작 대상은 `moss-ao-api`·`moss-ao-web`뿐. 스케줄러 잡은 **의도적으로 재시작하지 않는다** — signals/trends/debate/backlog/health는 cron 틱마다 `.venv/bin/python`을 새로 띄우므로 새 코드를 알아서 집어가고, 재시작하면 진행 중인 작업만 죽는다. 따라서 문서만 바뀐 커밋은 아무것도 재시작하지 않는다.
- 가드 — 각각은 그것이 없을 때의 구체적인 사고에 대응한다: GitHub Actions가 초록불인 커밋만 배포(진행 중이면 다음 틱으로 연기, API를 못 읽어도 눈감고 배포하지 않고 연기), 서버에서 추적 파일이 손으로 수정돼 있으면 중단(`git reset --hard`가 조용히 지운다), 토론(~30분) 실행 중에는 백엔드 배포를 연기(라이브 import 밑에서 패키지를 다시 깔면 깨질 수 있다 — 프론트엔드 전용 변경은 그대로 진행), 겹치는 틱이 섞이지 않도록 하는 stale 회수형 락, 매 배포 직전 강제 DB 스냅샷, 그리고 빌드나 배포 후 헬스체크가 실패하면 **재빌드까지 포함한** 자동 롤백(복구된 커밋이 일관되게 서비스되도록).
- `docs/deployment.md`: 설치, 설정(`MOSS_AO_AUTO_DEPLOY`, `DEPLOY_*`), 운영, 수동 롤백, 문제 해결, 그리고 즉시 배포(GitHub Actions + Tailscale)로 가려면 무엇이 선행돼야 하는지(`tag:ci`와 OAuth 클라이언트를 위한 테일넷 관리자, 시크릿을 위한 저장소 admin) — 그때도 워크플로가 이 스크립트를 그대로 호출해야 가드와 롤백이 두 벌로 갈라지지 않는다는 점을 함께 기록.

### 변경
- `ecosystem.config.js`: `pm2 deploy` 블록 제거. 애초에 실행 가능한 적이 없었다 — 존재하지 않는 호스트(`server1.moss.land`), 잘못된 저장소(`MosslandOpenDevs/`가 아닌 `mossland/`), 이 프로젝트에 없는 `requirements.txt`를 가리켰고, 테일넷 밖에서는 앱 서버로 SSH 자체가 불가능하므로 원리적으로도 동작할 수 없었다. 남겨두면 존재하지 않는 배포 경로가 있는 것처럼 읽힌다.

### 테스트
- `tests/test_deploy.py` 추가 (29개). 배포 스크립트는 `git push`와 프로덕션 사이에 서 있는 물건이라, 실제로 실행해서 검증한다: 매 테스트가 일회용 origin/체크아웃 쌍을 만들고 스텁 `pm2`·`npm`·`curl`을 `PATH` 앞에 두어, 진짜 스크립트가 가짜 인프라 위에서 진짜 코드 경로를 타게 한다. 커버 범위: 무변경 fast path(5분마다 도는 만큼 조용하고 공짜여야 한다), 변경 경로별 빌드/재시작 선택, 위의 모든 가드, 헬스체크 실패 후 롤백과 빌드 실패 후 롤백, 그리고 롤백조차 정상 복구되지 않는 `CRITICAL` 케이스.
- 가장 중요한 테스트는 배포 후에도 추적되지 않는 서버 상태가 살아남는지다: `data/orchestrator.db`, `data/backup/`, `.env`, `website/.env.local`은 모두 서버에 untracked로 존재하고, 2026-07 장애가 바로 그 DB의 유실이었다. `git reset --hard`는 이들을 건드리지 않고 `git clean`은 지우므로, 이 불변식을 두 겹으로 고정했다 — 동작으로(배포 후에도 파일이 그대로) 그리고 정적으로(스크립트 코드 어디에도 `git clean`이 없음).
- 이 로직이 회귀할 수 있는 6가지 방식을 스크립트 사본에 각각 적용해 뮤테이션 검증했다 — `git clean` 추가, 로컬 수정 가드 제거, 롤백 제거, CI 실패 무시, 토론 진행 중 가드 제거, 무변경 fast path 상실 — 모두 대응 테스트가 실패하는 것을 확인했다.
- `tests/test_version_resolution.py` 추가 (10개) — `__init__.py`의 버전 해석 *로직*을 검증. 0.6.12의 `TestVersionReporting`은 표면(`/health`, `/`, `/openapi.json`)이 `__version__`과 일치하는지만 보므로, 해석기를 소스 트리보다 **설치 메타데이터를 먼저** 읽도록 바꿔도 네 테스트가 모두 통과한다 (뮤테이션으로 확인). 이게 중요한 이유: metadata-first는 0.6.12가 고친 드리프트를 조용히 되살린다 — `importlib.metadata`는 `pip install` 시점의 스냅샷이라, editable 설치 후 체크아웃만 버전이 올라가면 계속 낡은 값을 보고하며, 재설치 없는 `git pull` + `pm2 restart`가 바로 문서화된 배포 절차다. 이제 다음이 커버된다: 소스 트리 우선 순위, wheel 설치용 메타데이터 폴백, `0.0.0+unknown` 센티널 *및* 경고 로그, 패키지가 site-packages에 있을 때 남의 `pyproject.toml`을 가져다 쓰지 못하게 막는 `[project].name` 가드, 그리고 깨진/버전 없는/존재하지 않는 `pyproject.toml`에 대한 강등 동작(import 시 예외를 던지지 않고 강등돼야 함). 이름이 일치하는 합성 트리는 실제로 채택되는지 확인하는 포지티브 컨트롤을 두어, 네거티브 케이스가 엉뚱한 이유로 통과하는 일이 없도록 했다.
- 하드코딩 리터럴 가드를 `api/main.py`뿐 아니라 `__init__.py`까지 확대 — 리터럴 재도입을 다음 버전 업이 아니라 그것을 넣는 커밋에서 잡는다.
- 10개 테스트 전부 뮤테이션 검증 완료: 이 로직이 회귀할 수 있는 9가지 방식 — `__version__` 자체를 다시 하드코딩하는, 이 수정을 되돌리는 가장 뻔한 경로 포함 — 을 소스 사본에 각각 적용해, 대응하는 테스트가 실패하는 것을 확인했다.
- 설치 형태에 무관하게 동작하는 것을 세 가지 모두에서 확인했다: 순수 `PYTHONPATH=./src` 실행, CI의 `pip install -e ".[dev]"`, 그리고 non-editable `pip install .`. 마지막 경우 import되는 패키지는 체크아웃이 아니라 site-packages 사본이므로 `parents[2]`가 venv 디렉토리가 되고, 소스 트리를 거부하는 것이 *정상*이다 — 이 체크아웃을 전제로 하는 단 하나의 단언은 그 사유와 함께 skip되며, 존재하지도 않는 드리프트 버그를 보고하지 않는다.

## [0.6.14] - 2026-08-04

### 문서
- **README 재구성 — 375줄 → 266줄, 헤딩 38개 → 16개.** v0.6.13 정확성 패스는 사실을 고쳤지만 기존 형식을 그대로 유지했고, 문서화되지 않았던 어댑터 6개를 "어댑터당 h3 하나" 스타일 그대로 추가하면서 `## 시그널 소스`가 불릿 2개짜리 하위 섹션 11개 연속이 됐다. 9.9줄마다 헤딩이 하나였다. 검증된 사실은 하나도 제거하지 않았고, 같은 내용을 표 두 개가 담는다.
  - `## 시그널 소스`: h3 11개를 표 하나로. **인증** 열이 새로 생겨 각 어댑터에 필요한 자격 증명(`TWITTER_BEARER_TOKEN`, `DISCORD_BOT_TOKEN`, `NEYNAR_API_KEY`, 또는 불필요)이 산문에 묻히지 않고 한눈에 보인다. 추적 수치는 전부 유지.
  - `## 멀티 스테이지 토론 시스템`: h3 4개를 표 하나로. **풀 정원과 라운드당 인원**을 인접한 열에 함께 표기해(풀 16/8/10, 라운드당 8/4/3 — `debate.normal.*_agents_per_round`), 독자가 서로 다른 섹션의 두 숫자를 대조할 필요가 없다.
  - `## 대시보드`, `### PM2 명령어`, `## 개발`의 h3 자식들을 제거했다. 대부분 명령어 한 줄짜리 코드 펜스였다.
- **README가 존재하지 않는 에이전트 페르소나 12개를 나열하고 있었다.** `Innovator`, `Skeptic`, `Pragmatist`, `Synthesizer`, `Evaluator`, `Prioritizer`, `Risk Assessor`, `Resource Planner`는 `personas/catalog.py`에서 일치 0건이다. 실제 구성은 프론트엔드·백엔드·블록체인 엔지니어, VC와 액셀러레이터 멘토, CPO·리드·QA·DevRel이다. v0.6.13은 단계별 *숫자*만 고치고 *이름*은 확인하지 않았다. 토론 표와 아키텍처 다이어그램 모두 실제 역할군으로 교체.
- **아키텍처 다이어그램이 낡았고 구조적으로 깨져 있었다.** 본문은 어댑터 11개라는데 5개만 그렸고, 영문 35줄 중 20줄(한글은 35줄 중 22줄)의 표시 폭이 어긋나 박스 테두리가 맞지 않았다. 두 파일 모두 27줄 전부 정확히 75칸으로 다시 그렸고, 동아시아 문자 폭을 반영해 프로그램으로 검증했으며, 이제 어댑터 11개를 모두 표기한다.
- 네 곳(주요 기능 불릿, 아키텍처 다이어그램, 시그널 소스, 프로젝트 구조 트리)에 중복되던 어댑터 목록을 정리했다. 주요 기능 불릿은 고유명사 11개를 다시 나열하는 대신 `#signal-sources`로 링크하고, 프로젝트 구조 트리는 어댑터 파일 11개를 주석 한 줄로 접었다.
- `## 관련 모스랜드 프로젝트` 불릿을 정리했다. 파일에서 압도적으로 긴 줄이었다(372자, 2위는 257자). `` (`alpha.moss.land`) `` / `` (`signalmap.moss.land`) `` 괄호는 바로 앞 링크의 href를 그대로 반복하는데 두 README 어디에도 다시 나오지 않는 구문이었고, alpha-mcp 참조는 하위 불릿으로 내렸다. 링크 4개 모두 보존.
- EN/KO 줄 패리티 유지: 두 파일 모두 267줄, 헤딩 줄 번호 동일.

## [0.6.13] - 2026-08-04

### 수정
- **이슈 본문이 JSON 중간에서 잘리지 않는다.** `_auto_score_and_save_ideas`가 GitHub 이슈 본문을 `idea_content[:500]`으로 만들었다. 토론 출력은 ```` ```json ```` 펜스 객체라 이 슬라이스가 블록을 열어둔 채 잘랐고, 그 뒤의 모든 섹션(Auto-Score Results, Decision, Context)이 닫히지 않은 코드 스팬 안에 렌더링됐다. **열린 이슈 12건**이 이 상태이며 그중 7건이 `curated:keep`이다 (#529, #570, #583, #668, #698, #730, #731, #750, #762, #1011, #1252, #2437). 표본이 아니라 열린 이슈 전체를 펜스 개수 홀짝으로 검사해 확정했다. DB의 `summary`/`summary_ko`도 같은 방식으로 잘렸으나 `description`은 항상 온전해 유실된 데이터는 없다. 이제 `_format_idea_summary()`가 JSON을 파싱해 마크다운으로 렌더하고, 실패 시 `_truncate_markdown()`이 문단/줄/문장 경계에서 자르며 열린 펜스를 반드시 닫는다. 두 경로 모두 길이 상한을 지킨다. 기존 이슈 본문은 바뀌지 않으며, 백필하려면 프로덕션 DB가 필요하다.
- **제목에 마크다운이 새지 않는다.** 제목 정리가 `title.replace("#", "")`뿐이라 강조 마커가 그대로 남았다. GitHub는 제목에 마크다운을 렌더하지 않으므로 열린 이슈 27건이 `[IDEA] **Foo**`처럼 별표를 노출하고 있었다. `_clean_issue_title()`이 `*`, `` ` ``, `_`를 제거하고 남은 공백을 정리하며, 이슈 제목을 만드는 4곳 전부에 적용된다. (기존 27건의 제목은 트래커에서 직접 수정했다.)
- **`status == "archived"` 분기가 택소노미 밖 라벨을 만들었다.** 형제 분기 둘은 `Labels` 상수를 쓰는데 이 분기만 raw 문자열 `"archived"`를 붙여, 파이프라인이 재가동되면 레지스트리 밖 라벨이 생성될 상태였다. 처음부터 문서에만 있고 정의된 적 없던 `Labels.STATUS_ARCHIVED = "status:archived"`를 `ALL_LABELS`에 추가하고 사용하도록 수정.
- **`website/src/lib/version.ts`가 0.6.10에 멈춰 있었다.** 파일 자체 주석이 동기화를 지시하고 있음에도 0.6.11과 0.6.12 모두 `pyproject.toml`만 올렸다.
- **EN/KO README 줄 패리티 복원.** 0.6.11이 설명 문단을 영문 4줄·한글 3줄로 넣으면서 1줄이 어긋났다. 한글 문단을 내용 그대로 4줄로 재배치해 두 파일 모두 375줄, 헤딩 줄 번호도 다시 일치한다.

### 문서
- **`docs/labels.md`를 실제 레지스트리 기준으로 다시 씀.** 코드 어디에도 없는 라벨 3개(`status:promoted`, `status:archived`, `source:debate`)를 문서화하고 있었고, 실제로 존재하며 사용 중인 4개(`processed:to-plan`, `curated:keep`, `rejected`, `reject:plan`)는 누락했다. "Setting Up Labels" 블록은 그 없는 3개를 만들고 실제 라벨 대부분을 빠뜨렸으므로, `Labels.ALL_LABELS`에서 생성되는 `ao backlog setup`을 안내하도록 교체.
  - `promote:to-plan`이 "Future / 미구현"으로 분류돼 있었다. 소비자(`find_ideas_to_promote` -> `BacklogOrchestrator.run_cycle`)는 완전히 구현돼 있고 2026-01-04에 마지막으로 정상 동작했다. 없는 것은 스케줄러 엔트리다 — `run_cycle`은 `ao backlog run` / `ao backlog process`에서만 도달 가능하고 어떤 PM2 잡도 호출하지 않는다 (`moss-ao-backlog`은 다른 작업이다).
  - `promote:to-plan`의 **상충하는 두 의미**를 문서화했다. 문서와 이슈 템플릿은 사람의 승인 게이트라고 설명하지만 `scheduler/tasks.py`는 score >= 7.0에 자동으로 붙인다. 이를 정리하지 않고 소비자를 스케줄에 올리면 모든 플랜이 두 번 생성되고 사람 승인 게이트가 사라진다. 임의로 바꾸지 않고 메인테이너 결정 사항으로 남겼다.
  - `promote:to-plan` 이슈 6건에 `status:` 라벨이 없는 이유를 기록했다 — `find_ideas_to_promote()`가 `[type:idea, promote:to-plan]`으로 조회하므로 `status:backlog`를 추가하면 배타적이어야 할 두 큐에 이중 계상된다. 현재 상태가 맞다.

### 정리 (GitHub 트래커, 코드 변경 없음)
- 사용되지 않던 GitHub 기본 라벨 9개 삭제 (`bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`). 이슈 2,868건과 모든 PR에서 사용 0건임을 확인 후 삭제했다. 이제 라벨은 택소노미가 정의한 11개뿐이다.
- #65, #66을 중복으로 닫음: 둘 다 `type:idea` 라벨이 붙었지만 본문은 플랜 #12/#10의 기획 문서이고 제목은 아이디어 #11/#7의 중복인 백필 산출물이다. 원본과 플랜은 모두 열린 상태로 남아 있다.
- 홍보성 코멘트 3건을 스팸으로 접음 (#583, #1252, #2437). minimize는 코멘트를 삭제하지 않으므로 2026-06 keep-set의 "비봇 코멘트 보유" 보호 근거는 그대로다 — 사후 재검증했다.

## [0.6.12] - 2026-08-04

### 수정
- **라우트 등록 순서 때문에 두 개의 API 라우트가 영구히 도달 불가능했음.** Starlette/FastAPI는 라우트를 **등록된 순서대로** 매칭하므로, 같은 접두사의 파라미터 라우트보다 *뒤에* 선언된 리터럴 경로에는 절대 도달할 수 없다:
  - `GET /signals/timeline`이 `GET /signals/{signal_id}`보다 뒤에 등록되어, 모든 요청이 `signal_id="timeline"`으로 바인딩되고 `404 Signal not found`를 반환했다. 그 결과 System 페이지의 신호 타임라인 위젯(`website/src/app/system/page.tsx` → `components/visualization/SignalTimeline.tsx`, `getSignalTimeline()` 경유)은 한 번도 데이터를 렌더링한 적이 없었다.
  - `GET /plans/pending-approval`이 `GET /plans/{plan_id}`보다 뒤에 등록되어, CLAUDE.md에 문서화된 수동 플랜 승인 워크플로우가 동작하지 않았다 (`404 Plan not found: pending-approval`).

  이제 두 리터럴 라우트가 각각의 파라미터 라우트보다 앞에 온다. 핸들러 자체는 변경하지 않았고, 프론트엔드의 `SignalTimelineResponse` 타입은 이미 타임라인 핸들러의 응답 형태와 일치했다.
- **`/adapters`가 `CoingeckoAdapter`를 누락**하여, `signals/aggregator.py`가 실제로 등록하는 11개 어댑터 중 10개만 노출했다. 이제 해당 어댑터도 열거되며, `TRACKED_COINS` 속성이 다른 어댑터들과 동일한 `sources`/`source_count` 계약에 연결된다.
- **API 버전 문자열이 세 갈래로 드리프트**되어 있었다: `FastAPI(version=...)`와 `/health`는 `0.5.0`, `/`는 `0.6.0`, `cli --version`의 근거인 `__init__.py`는 `0.3.0`을 보고했으나 `pyproject.toml`은 `0.6.10`을 선언하고 있었다. 이제 `__version__`이 **소스 트리의 `pyproject.toml`을 먼저** 읽고(설치 메타데이터 → 경고 로그와 함께 `0.0.0+unknown` 순으로 폴백), 세 곳의 API 호출부가 모두 이를 참조한다.
  - 설치 메타데이터만 읽으면 안 되는 이유: `importlib.metadata`는 `pip install` 시점의 스냅샷이라 **버전을 올리는 바로 그 커밋에서 낡은 값이 된다**. 게다가 `ecosystem.config.js`의 모든 PM2 앱은 `.venv/bin/python`을 `PYTHONPATH: './src'`로 띄우므로 실제로 서빙되는 코드는 설치본이 아니라 **작업 트리**다 — 그 venv에 dist-info가 없으면 `/health`가 조용히 `0.0.0+unknown`을 노출하게 된다. 소스 트리를 먼저 읽으면 `git pull` + `pm2 restart`(CLAUDE.md의 문서화된 배포 절차)만으로 버전이 정확해진다.

### 테스트
- `tests/test_api.py::TestLiteralRouteOrdering` 추가 — `/signals/timeline`과 `/plans/pending-approval`이 (단일 리소스 핸들러가 아닌) 의도된 응답 *형태*와 *집계 수치*를 반환하는지, 파라미터 라우트가 여전히 정상 동작하고 알 수 없는 id에 404를 내는지 검증. 또한 등록된 모든 라우트를 순회해 리터럴 경로가 앞선 파라미터 라우트에 가려지면 실패하는 `test_no_literal_route_is_shadowed` 가드를 추가해 이 버그 유형의 재발을 차단. 이 가드는 **HTTP 메서드를 함께 비교**한다 — Starlette은 경로만 맞고 메서드가 다르면 계속 탐색하므로, 겹치는 동사가 없는 두 라우트는 서로를 가리지 않기 때문.
- `TestVersionReporting`(`/health`, `/`, `/openapi.json`, 패키지 버전이 모두 `pyproject.toml`과 일치)과 `TestAdaptersEndpoint`(`/adapters` 목록이 aggregator 등록 집합과 동일해야 함) 추가. `/adapters`는 어댑터 11개 전부에 `health_check()`를 호출하고 그중 다수가 실제 외부 HTTP를 발생시키므로, 두 테스트는 `health_check`를 스텁으로 대체해 테스트 스위트를 hermetic하게 유지한다.

## [0.6.11] - 2026-08-04

### 변경
- **RSS 피드 리스트를 하나로 통합.** 시그널 수집과 트렌드 분석이 서로 다른, 조용히 표류하던 두 리스트를 읽고 있었다: `config.yaml`의 `trends.feeds`(16개)는 트렌드 경로(`trends/feeds.py`)만 사용했고, 실제 시그널 수집은 `adapters/rss.py`의 `DEFAULT_FEEDS`에 하드코딩된 32개를 사용했다 (`signals/aggregator.py`가 `RSSAdapter()`를 `feeds=` 인자 없이 생성하기 때문). 이제 합집합(35개 항목)이 **`config.yaml`의 새 최상위 `feeds:` 섹션**에 있고 두 소비자가 이 하나를 읽는다. 피드 추가·수정·비활성화에 코드 변경이나 재배포가 필요 없다.
  - `RSSAdapter.DEFAULT_FEEDS`는 `RSSAdapter.load_configured_feeds()`와, 설정을 전혀 읽을 수 없을 때만 쓰는 5개짜리 `FALLBACK_FEEDS`로 대체 (사용 시 경고 로그). 구버전 `trends.feeds` 위치도 deprecation 경고와 함께 계속 읽으므로, 로컬 수정된 `config.yaml`을 쓰는 배포도 그대로 동작한다.
  - 피드 항목에 `enabled: false`를 쓸 수 있고, 두 소비자 모두 로드 시점에 걸러내므로 비활성 피드는 fetch 루프까지 가지 않는다.
  - 병합 과정에서 `config.yaml`에만 있던 살아 있는 소스 2개(arXiv AI, The Hacker News)가 추가됐고, 두 리스트가 서로 다른 URL로 담고 있던 호스트 8개를 정리했다. Hacker News는 양쪽이 서로 다른 호스트(`hnrss.org` 미러 vs 공식 `news.ycombinator.com`)로 갖고 있어 공식 쪽만 남겼다. 범위가 다른 경우 주제 특화 피드를 채택 (예: TechCrunch 전체 대신 TechCrunch AI).
- **죽은 피드 4개는 삭제 대신 비활성화**하고 관측된 실패를 주석으로 기록: Chainlink(200이지만 HTML 페이지로 리다이렉트), Polygon(404), Paradigm(525), a16z Crypto(404). 넷 다 하드코딩 리스트에 있어 30분마다 매 시그널 수집에서 실패하고 있었다. 발행처가 제공하는 대체 피드는 없음 (2026-08-04 확인).

### 수정
- **잘못된 형태의 `feeds:` 섹션이 시그널 수집 전체를 죽이지 않도록 강등 처리.** `RSSAdapter`가 `SignalAggregator._default_adapters()` 안에서 생성되기 때문에, 피드 로더에서 난 `AttributeError`가 `SignalAggregator()` 생성 자체를 실패시켰다. 즉 `feeds:`를 플랫 리스트나 스칼라로 쓰면(이제 운영자에게 편집하라고 안내하는 바로 그 파일에서 충분히 나올 수 있는 실수) RSS뿐 아니라 **11개 어댑터 전체**가 30분마다 아무 신호도 수집하지 못했다. 이제 두 소비자 모두 매핑이 아닌 `feeds:`를 경고와 함께 거부하고 fallback으로 강등한다 — 읽을 수 없거나 문법이 깨진 config에 대해 이미 지키고 있던 로더의 계약과 동일하게 맞췄다.
- **`custom_feeds`가 공유 리스트를 변경하던 문제.** `RSSAdapter.__init__`이 `self.feeds = feeds or self.DEFAULT_FEEDS`로 참조를 잡은 뒤 `custom_feeds`를 append해, 클래스 레벨 기본값(또는 호출자의 리스트)을 프로세스 수명 내내 오염시켰다. 이제 append 전에 복사한다.

### 문서
- **CLAUDE.md 정확성 점검** (#1935의 README 점검과 동일한 작업):
  - 프로젝트 구조 트리가 시그널 어댑터를 `signals/adapters/`에 두고 있었으나 실제 위치는 `src/agentic_orchestrator/adapters/`다. 실제 레이아웃으로 수정하고, 문서에 없던 `trends/` 패키지도 추가했다.
  - `rss.py`를 "RSS 피드 (28개 소스)"로 설명했으나 이 숫자는 두 리스트 어느 쪽과도 맞지 않았다.
  - **페르소나 풀 정원과 라운드당 참여 인원의 구분을 명시**했다 (CLAUDE.md·README 양쪽). `personas/catalog.py`는 16/8/10(총 34명) 풀을 정의하고, `config.yaml`의 `debate.normal`은 라운드당 8/4/3명을 돌리며, `multi_stage.py`의 `_select_agents_for_round()`가 매 라운드 성격 균형을 맞춘 부분집합을 뽑는다. 두 숫자 모두 옳지만 한쪽만 적어두어 두 문서가 서로 모순돼 보였다.
- CLAUDE.md에 `## RSS 피드 소스` 섹션 신설 — 단일 소스 계약, 피드별 키, 리스트가 갈라져 있던 배경 정리.

## [0.6.10] - 2026-07-02

### 수정
- **DB가 망가져도 `/status`가 하드 500을 내지 않음** (2026-07 장애: ao.moss.land의 모든 DB 기반 엔드포인트가 500을 반환하는 동안 `/health`만 200 — 프로덕션 SQLite 파일이 유실/비워졌고, `system_status()`가 헬스체크보다 *먼저* 통계 쿼리를 실행해 준비돼 있던 `degraded` 분기에 도달할 수 없었음). 이제 통계 쿼리 자체가 헬스 프로브 역할을 겸함: 실패 시 200과 함께 `status="degraded"`, `components.database.status="unhealthy"`, 0으로 채운 stats를 반환해 moss.land 거버넌스 위젯이 소비하는 `{ stats: { agents_active, ideas_generated, debates_today } }` 계약을 유지 (MosslandOpenDevs/pixel-agent-lab#1, 원인 2).

### 추가
- **기동 시 스키마 자기치유** (`db/connection.py` `ensure_schema()`): API(FastAPI lifespan 훅)와 `backup-db`를 제외한 모든 스케줄러 CLI 명령이 서빙/작업 전에 멱등적인 `create_tables()`(`CREATE TABLE IF NOT EXISTS`)를 실행하며, 동시에 부팅되는 PM2 프로세스들이 CREATE 레이스로 서로를 실패시키지 않도록 짧은 재시도를 포함. SQLite 파일이 유실되거나 비워져도 운영자 개입 전까지 모든 DB 엔드포인트가 "no such table" 500을 내는 대신, 비어 있지만 동작하는 DB로 강등되어 시그널/토론 파이프라인이 스스로 다시 채움. `backup-db`는 의도적으로 제외 — 백업 명령은 스냅샷 대상 DB를 절대 변경하면 안 됨.
- **롤링 로컬 DB 백업** (`db/backup.py`): 5분 주기 헬스 태스크가 약 24시간 간격으로 `data/orchestrator.db`를 `data/backup/`(gitignore 처리됨)에 스냅샷하고 최신 7개를 보관. 리뷰에서 확인된 모든 실패 모드에 대해 강화됨:
  - sqlite3 온라인 백업 API를 **증분 복사**(`pages`/`sleep`)로 사용해 대용량 복사 중에도 동시 writer가 굶지 않음(프로덕션 DB는 WAL 미사용) + 30초 busy timeout.
  - 스냅샷은 `.tmp` 이름으로 쓰고 **`PRAGMA quick_check` 통과 후에만 원자적으로 rename** — 복사 중 비정상 종료나 손상된 원본이 간격 게이트를 막거나 보관 슬롯을 차지하는 쓰레기 파일을 남길 수 없고, 실패한 시도는 하루를 조용히 건너뛰는 대신 다음 5분 틱에 재시도됨.
  - **회귀 인지 프루닝**: 히스토리 테이블(ideas/plans/debate_sessions — 파이프라인이 재생성할 수 없는 것들)이 직전 스냅샷 대비 50% 미만으로 급감하면 새 스냅샷은 기록하되 프루닝을 중단하고 큰 소리로 에러 로그. 이 가드가 없으면 30분 주기 시그널 태스크가 비워진 DB를 자동으로 다시 채워 "meaningful"하게 보이게 만들고, 일일 로테이션이 `keep`일 안에 사고 이전 백업을 전부 파괴함.
  - DB가 없거나, 비었거나, 데이터가 없거나, 무결성 검사에 실패하면 백업을 건너뜀. 수동 실행: `python -m agentic_orchestrator.scheduler backup-db`.

### 테스트
- `tests/test_db_resilience.py` 추가 (30개): /status 강등 + 위젯 계약, lifespan 자기치유(망가진 DB로 기동 포함), 스냅샷/건너뛰기/정리/간격 동작, 최초 백업 경로, 부분 복사 정리 + 다음 틱 재시도, 무결성 실패 폐기, 회귀 인지 프루닝, `ensure_schema` 재시도 시맨틱, 스케줄러 CLI 디스패치 보장(스키마 치유 순서, `backup-db` 읽기 전용 제외, 비정상 종료 코드).

### 운영자 노트
- **DB 유실 후 복원**: 쓰기 프로세스 중지(`pm2 stop moss-ao-signals moss-ao-trends moss-ao-debate moss-ao-backlog`) → 최신 `data/backup/orchestrator-*.db`를 `data/orchestrator.db`로 복사 → 재시작. 백업이 생기기 전에는 복원할 것이 없음 — 파이프라인이 빈 DB를 시간이 지나며 다시 채움.
- 배포 디렉토리를 `git clean -fdx`로 청소할 때 반드시 data 디렉토리를 제외할 것 (`git clean -fdx -e data -e .env`); 프로덕션 DB는 git에 한 번도 커밋된 적이 없음.

---

## [0.6.9] - 2026-06-27

### 추가
- **코드 생성 검증 게이트** (`project/verifier.py`, `project/repair.py`): 생성된 소스를 디스크 기록·커밋 전에 검증하고 자동 수리. 스캐폴드가 파일별 파이프라인 — 결정적 수리 → 검증 → (필요 시) 컴파일 오류를 모델에 되먹이는 LLM 재수리 1회 — 을 Solidity·Python·TypeScript/JavaScript에 대해 실행.
  - **`CodeVerifier`**: Python은 내장 `compile()`(항상 사용 가능); Solidity는 보수적 정적 검사(`pragma` 누락, 잘못된 `.length()` 호출, 중괄호/괄호 불균형으로 절단 감지) + import 없는 컨트랙트에 한해 선택적 `solc`; TS/JS는 선택적 `esbuild` 구문 검사. 툴체인이 없으면 거짓 실패가 아니라 `SKIPPED`로 graceful degrade. 작은 Solidity 토크나이저로 문자열/주석을 오판하지 않음.
  - **`CodeRepairer`**: 생성물에서 실제로 관측된 버그 클래스에 대한 결정적 수리 — SPDX/`pragma` 누락 보강, 잘못된 `.length()` → `.length` 프로퍼티, 제거된 `now` 전역 → `block.timestamp`, OpenZeppelin v5 관용구를 고정된 v4로 정규화(`utils/` → `security/` import, v5 `Ownable(...)` 베이스 호출 제거), 컨트랙트가 OZ를 import하면 `contracts/package.json`에 `@openzeppelin/contracts` 주입. 수리는 문자열 리터럴/주석 바깥에서만 수행.
- **`ready_with_warnings` 프로젝트 상태**: 완전 수리가 안 된 프로젝트는 조용히 `ready`로 두지 않고 `ready_with_warnings`로 표시하며 전달은 절대 차단하지 않음. 파일별 검증 요약은 `Project.extra_metadata["verification"]`에, 한 줄 요약은 `generation_log`와 `.moss-project.json`에 기록되고, 프로젝트 UI(배지 색상 + 상세 모달의 "Code Verification" 패널)에 노출.

### 수정
- **LLM 경로 컨트랙트에 Hardhat 툴체인 누락**: `generate_smart_contracts_full()`이 `.sol`(과 Hardhat을 전제한 deploy 스크립트·테스트)만 내보내고 `contracts/package.json`·`hardhat.config.ts`는 내보내지 않아 `hardhat compile`이 import를 해석할 수 없었음. 둘 다 내보내며 `@openzeppelin/contracts`를 고정.
- **Hardhat 템플릿** (`project/templates.py`, `project/generator.py`의 폴백 컨트랙트): 컨트랙트 `package.json` 템플릿이 `@openzeppelin/contracts@^4.9.6`을 선언하고, 폴백 `Main` 컨트랙트가 OZ v4 무인자 `Ownable` 생성자를 사용(이전엔 v4 import 경로와 v5 `Ownable(msg.sender)` 호출이 섞여 단일 OZ 버전으로 컴파일 불가).

### 테스트
- `tests/test_project_verifier.py`, `tests/test_project_repair.py`, `tests/test_project_verification_gate.py` 추가(신규 34개) — 검증기, 결정적 수리기, 의존성 주입, 스캐폴드 게이트의 결정적/LLM 재수리 경로 커버.

---

## [0.6.8] - 2026-04-30

### 보안
- **소스 파일에 남아있던 Tailscale IP 제거**: `e0a4f4e` 가 `ecosystem.config.js` 의 내부 Ollama IP 를 제거했지만, `ollama.py` 의 `OllamaConfig.base_url` 기본값, `os.getenv("OLLAMA_HOST", ...)` fallback, 코멘트, 그리고 `hierarchy.py` 의 코멘트에 동일 IP 가 남아 있었음. 4곳 모두 `localhost`/일반 표현으로 교체 → 공개 레포에서 내부 네트워크 토폴로지가 더 이상 노출되지 않음. (커밋 `8e2c9c2`)

### 수정
- **스케줄러가 다시 `OLLAMA_HOST` 를 인식**: `e0a4f4e` 보안 정리 이후 PM2 스케줄러 (debate / trends / backlog) 가 셸에서 `OLLAMA_HOST` 가 export 되어야만 정상 작동했고, 그러지 못한 경우 `localhost:11434` 로 폴백되어 모든 모델 호출이 HTTP 404 를 반환 → planning 페이즈가 17자짜리 빈 플랜을 만들어내는 증상. `ecosystem.config.js` 가 `env:` 블록 평가 전에 `.env` 를 직접 파싱해 `process.env` 에 주입하도록 인라인 파서 추가. 새 의존성 (`dotenv` 패키지) 도입하지 않음. (커밋 `48cf50f`)

### 추가
- **로컬 최상위 플래너로 `qwen2.5:14b` 추가**: 원격 Ollama 서버에 풀 후 `LLMHierarchy.LOCAL_MODELS` 에 `tier=FREE` 로 등록. `TASK_MODEL_MAP` 의 `final_plan`, `quality_check`, `technical_review`, `moderation`, `final_decision` 에 1순위로 매핑하고 `qwen3.5:9b` 를 자동 fallback 으로 둠. 발산/번역/분류 단계는 변경 없음 (해당 작업은 모델 크기보다 다양성이 중요). (커밋 `a8b3aea`)

### 운영 노트
- `.env` (gitignored) 에 `OLLAMA_HOST=http://<원격-호스트>:11434` 설정 필수. 미설정 시 모든 Ollama 호출이 `localhost` 로 빠짐.
- `qwen2.5:14b` (~9GB) 가 원격 서버에 존재해야 함. `curl -X POST $OLLAMA_HOST/api/pull -d '{"name":"qwen2.5:14b"}'` 로 풀 가능.

---

## [0.6.7] - 2026-04-13

### 보안
- **변경 엔드포인트 인증 추가**: `POST /plans/{id}/approve`와 `POST /plans/{id}/generate-project`는 이제 `MOSS_API_KEY` 환경변수와 일치하는 `X-API-Key` 헤더를 요구합니다. 키 미설정 시 fail-closed (HTTP 503).
- **CORS 강화**: `allow_origins=["*"] + allow_credentials=True` 조합을 `MOSS_CORS_ORIGINS` 환경변수 화이트리스트로 교체 (기본값: `https://ao.moss.land,http://localhost:3000,http://127.0.0.1:3000`). 메서드/헤더도 실제 사용되는 것만 허용.
- **Generate Project 버튼용 서버사이드 프록시**: `website/src/app/proxy/...` 아래에 `/proxy/plans/[id]/generate-project`, `/proxy/plans/[id]/approve` Next.js route handler 추가. 브라우저는 프록시를 호출하고, 프록시가 서버 측에서 API 키를 주입. **API 키는 브라우저에 절대 노출되지 않음.**
- **프로젝트 생성기 경로 탐색/심볼릭 링크 방어** (`project/templates.py`, `project/scaffold.py`): LLM이 출력한 파일 경로를 새 `_safe_relative_path()` 헬퍼로 검증 — `..`, 절대 경로, 제어 문자, Windows 드라이브 문자, 백슬래시 거부. resolve 후 프로젝트 루트 prefix 재검증, 부모 디렉토리/파일 경로의 symlink 검사. 프로젝트 이름 슬러그화는 `slugify_project_name()`으로 통합.
- **`.gitignore` 강화**: `data/orchestrator.db`, SQLite WAL/journal/SHM 형제 파일, `data/backup/`, `data/jobs.json`을 명시적으로 ignore 처리 (기존: 단순히 추적 안 됨에 의존).

### 변경됨
- 90일 보존 정책에 따라 `data/trends/2026/01/`의 트렌드 스냅샷 15개 제거.
- `.env.example`과 `website/.env.local`에 새 환경변수(`MOSS_API_KEY`, `MOSS_CORS_ORIGINS`, `MOSS_BACKEND_URL`) 안내.

---

## [0.6.6] - 2026-02-01

### 추가됨
- **Threads 어댑터**: Meta Threads 시그널 수집 어댑터 (`threads.py`) — 공개 프로필 페이지에서 내장 JSON을 추출하여 추적 계정(`@choi.openai`, `@unclejobs.ai`, `@feelfree_ai`)의 게시물 수집 (httpx 사용, 외부 라이브러리 불필요)
- Threads 어댑터를 aggregator, API `/adapters` 엔드포인트, 어댑터 exports에 등록

---

## [0.6.5] - 2026-02-01

### 수정됨

#### 백엔드 안정성 및 성능 (시스템 점검)
- **Ollama 쓰로틀 락 병목 (H3)**: `_wait_for_throttle`에서 `asyncio.sleep()` 중 락 해제, 다수 에이전트 동시 LLM 요청 시 직렬화 방지
- **토론 타임아웃 (H4)**: 프로덕션 모드에서 무한 실행 방지를 위한 45분 전체 타임아웃 (`DEBATE_TIMEOUT_SECONDS`) 추가
- **API 에러 응답 일관성 (H5)**: dict 기반 에러 응답(`{"error": "..."}`)을 `HTTPException(status_code=404)`로 통일 (토론 상세, 아이디어 상세, 아이디어 계보, 플랜 상세)
- **중복 프로젝트 생성 방지 (M1)**: `_create_project_record()`에 중복 체크 추가 - 동일 Plan에 "generating" 또는 "ready" 상태 프로젝트가 있으면 기존 ID 반환
- **Job 상태 영속화 (M2)**: 프로젝트 생성 작업 상태가 `data/project_jobs.json`에 저장되어 서버 재시작 시에도 유지
- **Plan 상세에 `title_ko` 누락 (M3)**: `/plans/{id}` 응답에 `title_ko`, `final_plan_ko` 필드 추가
- **Signal 페이지네이션 (M5)**: Python 슬라이싱을 SQL `LIMIT/OFFSET`으로 교체, `count_recent_filtered()` 추가
- **토론 페이지네이션**: debates 엔드포인트에서 SQL 레벨 페이지네이션 적용 (`get_all_sessions()`)
- **LLM Fallback 무한 루프 (L2)**: fallback도 실패 시 즉시 예외 발생하도록 try/except 추가
- **점수 기본값 5.0 문제 (L3)**: 점수 추출 실패 시 임의 5.0 할당 대신 경고 로깅 후 스킵

### 변경됨
- **config test_mode 통일 (H2)**: `debate.test_mode: false`로 설정하여 `throttling.test_mode: false`와 일치 (프로덕션 모드)
- **print → logger (L1)**: `ollama.py`, `router.py`, `aggregator.py`의 모든 `print()` 호출을 `logger.error()`/`logger.info()`로 교체

---

## [0.6.4] - 2026-01-25

### 추가됨

#### 외부 링크 접근을 위한 동적 상세 페이지
- **직접 URL 접근**: 외부 링크가 전용 상세 페이지로 연결
  - `/signals/{id}` - 시그널 상세 페이지
  - `/ideas/{id}` - 아이디어 상세 페이지
  - `/plans/{id}` - 플랜 상세 페이지
  - `/projects/{id}` - 프로젝트 상세 페이지
- **SEO 최적화 메타데이터**: 링크 공유를 위한 Open Graph 및 Twitter 카드 지원
- **새 백엔드 엔드포인트**: `GET /signals/{signal_id}` 단일 시그널 조회
- **공유 레이아웃 컴포넌트**: 네비게이션, 로딩/에러 상태가 포함된 `DetailPageLayout`
- **다국어 지원**: 상세 페이지에 EN/KO 로컬라이제이션 완전 지원

---

## [0.6.3] - 2026-01-25

### 추가됨

#### 프로덕션 수준 코드 생성
- **향상된 Plan 파서**: 포괄적인 추출을 위한 Deep LLM 파싱
  - 새 데이터클래스: `DataEntity`, `ExternalService`, `UIComponent`, `SmartContractSpec`
  - 상세 엔티티, 서비스, 컴포넌트 추출을 위한 `parse_deep_with_llm()`
  - 외부 서비스 탐지 (Twitter API, Coingecko, Etherscan, WebSocket 등)
- **풀 프로젝트 제너레이터**: 스캐폴드 대신 프로덕션 레디 코드
  - `generate_full_project()` - 고품질 생성을 위한 메인 진입점
  - 비즈니스 로직이 포함된 완전한 FastAPI/Express 백엔드
  - 모든 페이지와 컴포넌트가 포함된 완전한 Next.js/React 프론트엔드
  - Hardhat 테스트 프레임워크가 포함된 Solidity 스마트 컨트랙트
  - 외부 서비스 통합 레이어
  - 데이터베이스 스키마 및 마이그레이션
  - Docker 설정

#### 우선순위 기반 프로젝트 생성
- **고우선순위 Plan 자동 생성**: 점수 >= 8.0
  - Plan 자동 승인 및 프로젝트 생성 트리거
  - `config.yaml`에서 임계값 설정 가능 (`project.auto_generate.min_score`)
- **저우선순위 Plan 수동 승인**: 점수 < 8.0
  - "draft" 상태로 Plan 생성
  - 프로젝트 생성 전 수동 승인 필요

#### 수동 제어를 위한 새 API 엔드포인트
- `POST /plans/{plan_id}/approve` - Draft plan 수동 승인
  - 즉시 프로젝트 생성 트리거 옵션 (`generate_project=true`)
  - 사용자가 어떤 낮은 점수 Plan을 개발할지 제어 가능
- `GET /plans/pending-approval` - 수동 승인 대기 중인 draft plan 목록
  - 결정 컨텍스트를 위한 아이디어 점수 표시

### 변경됨
- 커밋 메시지가 "scaffold"에서 "production-quality code"로 변경
- 프로젝트 생성 파이프라인이 이제 완전한, 실행 가능한 코드 생성

---

## [0.6.2] - 2026-01-25

### 추가됨

#### 파이프라인 프로젝트 스테이지
- **파이프라인 모달 지원**: 파이프라인 상태 모달에서 Projects 스테이지 완전 지원
  - 상태 배지와 함께 프로젝트 가져오기 및 표시
  - "View All Projects" 버튼으로 `/projects` 페이지 이동
  - 도움말이 있는 빈 상태 표시
- **GitHub에서 코드 보기 버튼**: ProjectDetail 모달에 새 버튼 추가
  - 프로젝트 코드 디렉토리로 직접 링크: `github.com/.../tree/main/projects/{project-name}`
  - Issue 링크와 분리하여 명확하게 구분

#### GitHub 자동 푸시
- **자동 Git 커밋/푸시**: 생성된 프로젝트가 자동으로 커밋 및 푸시됨
  - 스캐폴드 생성 후 자동으로 `git add`, `git commit`, `git push` 실행
  - 커밋 메시지: `feat: auto-generate project scaffold for {project-name}`
  - 푸시 실패 시 프로젝트 생성은 차단되지 않음 (경고 로그만 출력)

### 수정됨
- **PipelineDetail Projects 스테이지**: Projects 클릭 시 "#" 텍스트만 표시되는 문제 수정
  - 데이터 가져오기에 `projects` stageId 처리 추가
  - 적절한 설명, 빈 상태 이모지, 네비게이션 추가

---

## [0.6.1] - 2026-01-25

### 추가됨

#### Projects UI 통합
- **프로젝트 페이지**: 상태 필터링(전체/완료/생성 중/오류)이 있는 새 `/projects` 페이지
  - 기술 스택 배지 (프론트엔드/백엔드/블록체인)
  - 디렉토리 경로 표시
  - 생성된 파일 수
  - 클릭하여 프로젝트 상세 모달 열기
- **대시보드 통합**: 최근 5개 프로젝트를 보여주는 "Recent Projects" 섹션
  - `/projects` 페이지 직접 링크
  - 상태 표시기 및 기술 스택 표시
- **아이디어 페이지 프로젝트 탭**: 빠른 접근을 위해 아이디어 페이지에 프로젝트 섹션 추가

### 수정됨
- **API 클라이언트 타임아웃**: 네트워크 지연 처리를 위해 타임아웃을 3초에서 10초로 증가
  - "Using mock stats/pipeline due to API error" 경고 해결
  - 느린 연결에서 조기 요청 중단 방지
- **Projects 테이블 생성**: `/projects` 엔드포인트 500 오류 수정
  - 데이터베이스에 누락된 `projects` 테이블 생성
  - 다른 모델과 함께 테이블 자동 생성

### 기술 사항
- 재사용 가능한 프로젝트 목록 표시를 위한 `ProjectsSection` 컴포넌트 추가
- `ApiClient`에 10초 타임아웃 업데이트 (AbortController)
- 데이터베이스 마이그레이션으로 `projects` 테이블 존재 보장

---

## [0.6.0] "Project Generator" - 2026-01-25

### 추가됨

#### Plan → Project 자동 생성
- **프로젝트 스캐폴드 모듈**: 승인된 Plan에서 자동 프로젝트 생성을 위한 새 `project/` 패키지
  - `parser.py` - Plan 마크다운을 구조화된 데이터로 파싱 (TechStack, APIEndpoint, ProjectTask)
  - `templates.py` - 기술 스택 템플릿 (Next.js, React, Vue, FastAPI, Express, Hardhat, Anchor)
  - `generator.py` - 작업별 모델 라우팅이 있는 LLM 기반 코드 생성
  - `scaffold.py` - 전체 프로젝트 생성 파이프라인 오케스트레이션
- **작업별 LLM 모델**: 다른 작업에 다른 모델 사용
  - `glm-4.7-flash` - 빠른 Plan 파싱 및 구조 추출
  - `qwen2.5:32b` - 메인 코드 생성 (컴포넌트, API, 모델)
  - `llama3.3:70b` - 복잡한 아키텍처 설계
  - `phi4:14b` - 간단한 작업 및 폴백
- **하이브리드 트리거 시스템**:
  - **자동 생성**: 점수 ≥ 8.0인 Plan은 자동으로 프로젝트 생성
  - **수동 버튼**: 낮은 점수의 Plan은 UI에서 생성 트리거 가능
- **데이터베이스 스키마**: `projects` 테이블 추가
  - `plan_id`, `name`, `directory_path`, `tech_stack` (JSON), `status`, `files_generated`
- **프로젝트 리포지토리**: 프로젝트를 위한 전체 CRUD 작업

#### 새 API 엔드포인트
- `POST /plans/{plan_id}/generate-project` - 비동기 프로젝트 생성 트리거
- `GET /plans/{plan_id}/project` - 특정 Plan의 프로젝트 조회
- `GET /projects` - 생성된 모든 프로젝트 목록
- `GET /projects/{project_id}` - 프로젝트 상세
- `GET /jobs/{job_id}` - 비동기 작업 상태 확인

#### 프론트엔드 업데이트
- **Generate Project 버튼**: 승인된 Plan을 위해 `PlanDetail.tsx`에 추가
- **프로젝트 상태 표시**: 생성 중 스피너, 준비 완료 상태의 기술 스택 배지, 오류 상태의 재시도 버튼
- **작업 폴링**: 생성 중 자동 상태 폴링
- **API 클라이언트 메서드**: `generateProject()`, `getProjects()`, `getProjectDetail()`, `getJobStatus()`, `getPlanProject()`

### 변경됨
- 스케줄러가 토론 완료 후 프로젝트 자동 생성 통합
- Plan 생성 시 `final_plan` 및 `final_plan_ko` 콘텐츠를 올바르게 저장
- 파이프라인 흐름 확장: Ideas → Plans → Projects (점수 ≥ 8.0인 경우)

### 설정
`config.yaml`에 새 `project` 섹션:
```yaml
project:
  auto_generate:
    enabled: true
    min_score: 8.0
    max_concurrent: 1
  llm:
    parsing: "glm-4.7-flash"
    code_generation: "qwen2.5:32b"
    architecture: "llama3.3:70b"
    fallback: "phi4:14b"
  output_dir: "projects"
```

### 기술 사항
- `ProjectScaffold`, `ProjectCodeGenerator`, `PlanParser`, `TemplateManager` 클래스 추가
- 데이터베이스 레이어에 `Project` 모델 및 `ProjectRepository` 추가
- 스케줄러에 `_auto_generate_project()` 및 `_load_project_config()` 추가
- `_auto_score_and_save_ideas()`가 프로젝트 생성을 위해 `final_plan_content` 전달하도록 수정
- `ApiProject`, `GenerateProjectResponse`, `ProjectJobStatus` TypeScript 타입 추가

---

## [0.5.1] "Bilingual" - 2026-01-24

### 추가됨

#### 이중 언어 콘텐츠 지원 (EN/KO)
- **양방향 번역**: ContentTranslator가 소스 언어를 감지하고 자동 번역
  - 한글 콘텐츠 → 영어 (메인 필드) + 한글 (`*_ko` 필드)
  - 영어 콘텐츠 → 영어 (메인 필드) + 한글 번역 (`*_ko` 필드)
- **데이터베이스 스키마**: Ideas와 Plans에 한글 필드 추가
  - `Idea`: `title_ko`, `summary_ko`, `description_ko`
  - `Plan`: `title_ko`, `final_plan_ko`
- **프론트엔드 로컬라이제이션**: UI가 EN/KO 토글에 따라 모든 콘텐츠 표시
  - 아이디어 목록, 상세 모달
  - 플랜 목록, 상세 모달
  - 트렌드 목록, 상세 모달
- **마이그레이션 스크립트**: 기존 데이터를 번역으로 채우는 `migrate_bilingual.py`
- **IdeaContent 컴포넌트**: 구조화된 JSON 아이디어 표시:
  - 색상 테두리가 있는 핵심 분석
  - 시각적 인디케이터가 있는 기회/리스크 그리드
  - 기능 목록과 기술 스택 배지가 있는 제안
  - 로드맵 타임라인
  - 목표 지표가 있는 KPI

### 수정됨
- **TrendHeatmap 크기**: 셀 높이를 `aspect-square`에서 `h-6`으로 축소
- **AdapterDetailModal**: 첫 오픈 시 빈 모달 수정 - 첫 번째 어댑터 자동 선택
- **트렌드 분석**: LLM 프롬프트를 영어 전용으로 변경 (한글은 번역으로 제공)
- **파이프라인 모달**: signals 및 trends 스테이지의 VIEW ALL 버튼 수정
- **날짜 로케일 표시**: EN 로케일에서 한국어 날짜 표시 문제 수정
  - `date.ts`에 `toBrowserLocale()` 헬퍼 추가 (en→en-US, ko→ko-KR)
  - 기본 로케일을 'ko-KR'에서 'en'으로 변경
  - 모든 날짜 포맷 함수가 사용자 로케일 준수
- **토론 JSON 콘텐츠**: 토론 모달에서 원시 JSON 표시 문제 수정
  - JSON 파싱 및 읽기 쉬운 필드 추출을 위한 `extractReadableContent()` 헬퍼 추가
  - LiveDebateViewer, DebateConversation, DebateTimeline 컴포넌트에 적용
- **마크다운 렌더링**: 토론 메시지에 마크다운 지원 추가
  - `marked` 라이브러리를 사용한 `MarkdownContent` 컴포넌트 생성
  - `**bold**`는 시안 색상, `*italic*`은 보라 색상으로 렌더링
  - 리스트, 코드 블록, 헤더, 인용문 스타일 적용

### 기술 사항
- `ContentTranslator` 클래스 추가: `ensure_bilingual()`, `translate_to_english()`, `translate_to_korean()` 메서드
- 한글/영어 감지를 위한 `_detect_language()` 헬퍼 추가
- `_auto_score_and_save_ideas()`를 양방향 번역 사용하도록 업데이트
- 프론트엔드 컴포넌트에 `getLocalizedText()` 헬퍼 추가
- 구조화된 JSON 파싱 및 표시를 위한 `IdeaContent.tsx` 컴포넌트 추가
- 성능을 위해 시그널 번역 비활성화 (시그널은 영어 전용)

---

## [0.5.0] - 2026-01-24

### 추가됨

#### 창의성 프레임워크 강화 (Phase 1)
- **SCAMPER 창의성 프롬프트**: 발산 단계에서 구조화된 SCAMPER 기법 사용
  - 라운드 1: 대체 & 결합 (구성요소 교체, 개념 병합)
  - 라운드 2: 적용 & 수정 (타 산업 영감, 규모 변경)
  - 라운드 3: 전용, 제거 & 역발상 (역설적 사고)
- **측면사고 프롬프트**: 라운드별 교차 적용되는 창의성 기법
  - Blue Sky Thinking (제약 없는 상상)
  - Paradox Approach (역문제 해결)
  - Cross-Domain Innovation (타 산업 패턴 차용)
- **온도 상향**: 발산 단계 온도를 0.95로 상향 (기존 0.9)하여 더 창의적인 출력 유도

#### Coingecko 시장 어댑터
- **트렌딩 코인**: 실시간 검색 트렌드 감지
- **상위 변동종목**: 상위 5개 상승/하락 종목 (24시간, >10% 변동 임계값)
- **거래량 급등**: 비정상 거래 활동 감지 (거래량 > 시가총액의 50%)
- **글로벌 시장 통계**: 전체 시가총액 변동, BTC 도미넌스 알림
- **추적 코인**: MOC (Mossland) 포함 16개 특정 코인

#### 시그널 시간 감쇠
- **신선도 가중치**: 시그널 점수가 경과 시간에 따라 감쇠
  - 0-1시간: 100% 가중치
  - 1-6시간: 90% 가중치
  - 6-12시간: 80% 가중치
  - 12-24시간: 60% 가중치
  - 24-48시간: 40% 가중치
  - 48시간+: 20% 가중치
- **감쇠 로깅**: 분석 주기별 감쇠 분포 디버그 정보 표시

#### 대시보드 UX 개선
- **스켈레톤 로더**: 트렌드 페이지와 아이디어 페이지에 적절한 로딩 스켈레톤 적용
  - 점수, 제목, 키워드 플레이스홀더가 있는 트렌드 카드
  - 스테이지 인디케이터가 있는 파이프라인 뷰
  - 배지와 콘텐츠 플레이스홀더가 있는 리스트 아이템

### 변경됨
- 시그널 애그리게이터에 Coingecko 어댑터 기본 포함
- 트렌드 분석 시 시그널 처리 전 시간 감쇠 적용

### 기술 사항
- `DebateProtocol`에 `SCAMPER_TECHNIQUES`, `LATERAL_THINKING` 딕셔너리 추가
- `DebateProtocol`에 `get_creativity_technique()` 메서드 추가
- `CoingeckoAdapter` 클래스 추가 (trending, movers, global stats, tracked coins 메서드)
- 스케줄러에 `_calculate_time_decay()`, `_apply_time_decay_to_signals()` 함수 추가
- `TrendSkeleton`, `PipelineSkeleton`, `ListItemSkeleton`, `ListSkeleton` React 컴포넌트 추가

---

## [0.4.2] - 2026-01-24

### 추가됨

#### 아이디어 창의성 및 다양성 향상
- **다양성 인식 에이전트 선택**: 성격 축 기반 균형 선택으로 각 토론 라운드에서 다양한 에이전트 타입 보장
- **도전자 역할 보장**: 집단사고 방지를 위해 각 라운드에 최소 1명의 도전자 성격 에이전트 포함
- **아이디어 유사도 피드백**: 아이디어 생성 시 Jaccard 유사도 점수와 차별화 힌트 제공
- **참신성 가중치 강화**: 수렴 단계에서 참신성 가중치를 30%로 상향 (기존 20%, 가장 중요한 기준)

#### 시그널 품질 향상
- **콘텐츠 검증 레이어**: 최소 길이, 언어 (한국어/영어), 스팸 패턴으로 시그널 필터링
- **의미론적 중복 제거**: Jaccard 유사도 기반 중복 제거로 다른 소스의 유사 콘텐츠 필터링
- **참여도 임계값**: 소셜 어댑터에서 저참여 게시물 필터링 (Reddit: 10+ 점수, 3+ 댓글; Farcaster: 3+ 좋아요 또는 1+ 리캐스트)
- **감성 분석**: 키워드 기반 감성 감지 (긍정/부정/중립)를 시그널 점수에 통합

### 변경됨
- 시그널 중복 제거가 3단계 접근 방식 사용: 해시 중복 제거 → 콘텐츠 검증 → 의미론적 중복 제거
- 수렴 평가 기준이 명시적 가중치 점수 공식으로 재구성됨
- Twitter API 검색이 참여도 메트릭으로 트윗 필터링

### 기술 사항
- `MultiStageDebate`에 `_select_agents_with_diversity()`, `_ensure_challenger_presence()` 메서드 추가
- 차별화 힌트를 위한 `_calculate_idea_similarity()`, `_get_similarity_feedback()` 메서드 추가
- `SignalAggregator`에 `_validate_signal_content()`, `_is_semantic_duplicate()` 메서드 추가
- `SignalScorer`에 `_analyze_sentiment()`, `_score_sentiment()` 메서드 추가
- 소셜 어댑터들에 `_meets_engagement_threshold()` 메서드 추가

---

## [0.4.1] - 2026-01-24

### 추가됨

#### 시그널 어댑터 확장 (총 9개 어댑터)
- **Twitter/X 어댑터**: 10개 Nitter 인스턴스 풀, 20개 이상 추적 계정
- **Discord 어댑터**: Bot API 및 웹훅 지원, 7개 추적 서버
- **Lens Protocol 어댑터**: GraphQL API, 10개 추적 프로필
- **Farcaster 어댑터**: Neynar API, 10개 추적 사용자 및 채널
- **온체인 확장**: DEX 거래량, 고래 알림, 스테이블코인 흐름 (DefiLlama)

#### 아이디어 품질 향상
- **JSON 출력 포맷**: 더 나은 파싱을 위한 구조화된 LLM 응답
- **콘텐츠 검증**: 최소 글자 수 요구 필수 섹션
- **제목 품질 점수**: 길이, 기술 키워드, Mossland 관련성 기반 0-10 점수

#### 대시보드 UX 개선
- **어댑터 상세 모달**: signals.conf 클릭 시 건강 상태 포함 상세 어댑터 정보 표시
- **스켈레톤 로딩**: 활동 피드 로딩 중 스켈레톤 애니메이션 표시
- **실제 활동 데이터**: `/activity` API가 목업 대신 실제 DB 데이터 반환

#### 새 API 엔드포인트
- `GET /adapters` - 상태, 소스, 건강 정보가 포함된 모든 시그널 어댑터 목록

### 변경됨
- 활동 피드가 더 이상 목업 데이터를 사용하지 않음; 실제 타임스탬프 (HH:MM:SS 형식) 표시
- 대시보드가 스켈레톤 로딩 상태와 함께 활동 데이터 로드

### 기술 사항
- `AdapterInfo` 타입 및 `fetchAdapters()` API 클라이언트 메서드 추가
- `ActivityFeed` 컴포넌트에 `isLoading` prop 추가

---

## [0.4.0] "Signal Storm" - 2026-01-22

### 추가됨

#### 멀티 스테이지 토론 시스템 (34 에이전트)
- **3단계 토론**: 발산 (12 에이전트) → 수렴 (12 에이전트) → 기획 (10 에이전트)
- **4축 성격 시스템**: 창의성, 분석력, 리스크 허용도, 협업 (0-10 척도)
- **토론 프로토콜**: `debate/protocol.py` - 단계, 메시지 타입, 설정
- **멀티 스테이지 오케스트레이션**: `debate/multi_stage.py` - 완전한 토론 흐름 관리

#### 다양한 시그널 소스 (5개 어댑터)
- **RSS 어댑터**: AI, Crypto, Finance, Security, Dev 5개 카테고리의 17개 피드
- **GitHub Events 어댑터**: 저장소 활동, 트렌딩 프로젝트, 이슈/PR 분석
- **온체인 어댑터**: MOC 토큰 트랜잭션, 스마트 컨트랙트 이벤트, DeFi 메트릭
- **소셜 미디어 어댑터**: X (트위터) 멘션, 커뮤니티 감성 분석
- **News API 어댑터**: 실시간 뉴스 집계, 키워드 기반 필터링

#### 하이브리드 LLM 라우터
- **로컬 모델**: Ollama 통합 (Qwen 32B, Llama 3, Mistral)
- **클라우드 API**: Claude, GPT-4, Gemini 폴백
- **지능형 라우팅**: 로컬과 클라우드 간 자동 폴백
- **예산 관리**: 비용 추적 및 제한

#### PM2 프로세스 관리
- **6개 서비스**: signals (30분), debate (6시간), backlog (매일), web, api, health (5분)
- **스케줄러 모듈**: `scheduler/tasks.py` - 비동기 태스크 구현
- **CLI 진입점**: `scheduler/__main__.py` - 커맨드 라인 인터페이스
- **생태계 설정**: `ecosystem.config.js` - PM2 설정

#### FastAPI 백엔드
- **REST API**: `/health`, `/status`, `/signals`, `/debates`, `/agents`, `/docs`
- **API 모듈**: `api/main.py` - FastAPI 애플리케이션
- **포트 3001**: 웹 대시보드와 분리

#### CLI 스타일 웹 인터페이스
- **레트로 터미널 테마**: JetBrains Mono 폰트, 스캔라인, 글로우 효과
- **터미널 컴포넌트**: `TerminalWindow.tsx`, 상태 표시기
- **에이전트 페이지**: `/agents` - 34개 에이전트 페르소나 표시
- **모바일 반응형**: 모든 화면 크기에 적응

### 변경됨

- CLI/터미널 미학으로 대시보드 재설계
- `$` 프롬프트 스타일로 네비게이션 업데이트
- 버전 "Signal Storm"으로 푸터 업데이트
- GitHub Actions 스케줄링을 PM2로 대체

### 제거됨

- `.github/workflows/backlog.yml` - PM2 moss-ao-backlog으로 대체
- `.github/workflows/orchestrator.yml` - PM2 moss-ao-debate으로 대체

### 기술 세부사항

- API 서버에 Python 3.12 필요
- 가상환경 설정: `.venv/`
- 충돌 방지를 위해 서비스 이름에 `moss-ao-` 접두사 사용

## [0.4.0] - 2026-01-04

### 추가됨

#### PLAN 생성을 위한 멀티 에이전트 토론 시스템
- **4개 토론 역할**: 창업자, VC (a16z/Sequoia 수준), Accelerator (YC/Techstars 수준), 창업가 친구
- **3개 AI 프로바이더**: Claude, ChatGPT, Gemini가 매 라운드 역할을 순환하며 다양한 관점 제공
- **역할 순환**: 각 라운드마다 다른 AI가 다른 역할 담당
- **조기 종료**: 창업자가 "충분히 개선됨" 판단 시 또는 최대 5라운드에서 토론 종료
- **토론 기록**: 전체 토론 히스토리가 접기/펼치기 가능한 GitHub 댓글로 저장

#### 토론 모듈 (`src/agentic_orchestrator/debate/`)
- `roles.py` - 이중 언어 프롬프트 (영어 + 한국어)가 포함된 역할 정의
- `moderator.py` - 라운드 순환 매트릭스 및 종료 로직
- `debate_session.py` - 전체 토론 세션 오케스트레이션
- `discussion_record.py` - GitHub 댓글 포맷팅

#### Plan 거부 워크플로우
- **`reject:plan` 라벨**: PLAN을 거부하고 원본 아이디어에서 재생성
- **`ao backlog reject <plan_number>`**: 계획 거부를 위한 CLI 명령어
- **자동 리셋**: 거부된 plan이 닫히고, 원본 아이디어에 `promote:to-plan` 복원

#### 이중 언어 지원
- 모든 토론 프롬프트가 영어로 작성되고 한국어 번역 요청 포함
- 토론 기록은 "English / 한국어" 형식으로 표시
- 기획서 추출에 `[PLAN_START]`/`[PLAN_END]` 마커 사용으로 신뢰성 향상

### 변경됨

- PlanGenerator가 3개 프로바이더 모두 사용 가능 시 멀티 에이전트 토론 사용
- 프로바이더 불가 시 단일 에이전트 생성으로 폴백
- `run_cycle()`에서 거부 처리가 프로모션 처리 전에 실행
- `_find_existing_plan_for_idea()`가 열린 이슈만 검색 (닫힌/거부된 이슈 무시)

### 설정

`config.yaml`에 새 `debate` 섹션:
```yaml
debate:
  enabled: true
  max_rounds: 5
  min_rounds: 1
  require_all_approval: false
```

## [0.3.0] - 2026-01-04

### 추가됨

#### 트렌드 기반 아이디어 생성
- **RSS 피드 통합**: AI, Crypto, Finance, Security, Dev 5개 카테고리의 17개 RSS 피드에서 기사 수집
- **트렌드 분석**: Claude를 사용하여 뉴스 기사에서 트렌딩 토픽 식별
- **다중 기간 분석**: 24시간, 1주, 1개월 기간에 걸쳐 트렌드 분석
- **트렌드 기반 아이디어**: 현재 트렌드를 기반으로 Web3 마이크로 서비스 아이디어 생성
- **트렌드 저장소**: YAML frontmatter가 포함된 Markdown 파일로 트렌드 분석 결과 저장

#### 새 트렌드 모듈
- `FeedFetcher` - feedparser를 사용한 RSS/Atom 피드 파싱
- `TrendAnalyzer` - Claude를 사용한 LLM 기반 트렌드 추출
- `TrendStorage` - `data/trends/YYYY/MM/`에 Markdown 파일 저장
- `TrendBasedIdeaGenerator` - 트렌딩 토픽에서 아이디어 생성

#### 새 라벨
- `source:trend` - 트렌드 분석에서 생성된 아이디어 표시

#### 새 CLI 명령어
- `ao backlog analyze-trends` - RSS 피드 수집 및 분석
- `ao backlog generate-trends` - 트렌드 기반 아이디어 생성
- `ao backlog trends-status` - 트렌드 분석 이력 표시

#### CLI 업데이트
- `ao backlog run`에 `--trend-ideas` 및 `--analyze-trends` 옵션 추가
- `ao backlog status`에서 트렌드 기반 아이디어 수 표시

#### GitHub Actions
- 스케줄을 매일 오전 8시 KST (23:00 UTC)로 변경
- 새 `run-with-trends` 명령 (기본 일일 실행)
- `generate-trends`, `analyze-trends`, `trends-status` 명령 추가

### 변경됨

- 기본 일일 실행: 전통적 아이디어 1개 + 트렌드 기반 아이디어 2개와 트렌드 분석
- 트렌드 데이터는 `data/trends/` 디렉토리에 저장 (90일 보존)

### 설정

`config.yaml`에 새 `trends` 섹션:
```yaml
trends:
  ideas:
    traditional_count: 1
    trend_based_count: 2
  periods: [24h, 1w, 1m]
  storage:
    directory: data/trends
    retention_days: 90
  feeds:
    ai: [OpenAI News, Google Blog, arXiv AI, TechCrunch, Hacker News]
    crypto: [CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate]
    finance: [CNBC Finance]
    security: [The Hacker News, Krebs on Security]
    dev: [The Verge, Ars Technica, Stack Overflow Blog]
```

### 의존성

- RSS/Atom 파싱을 위한 `feedparser>=6.0.0` 추가

## [0.2.1] - 2025-01-04

### 추가됨

#### 안정성 개선
- **멱등성 보호**: 라벨 및 기존 아티팩트 확인을 통해 중복 plan/dev 생성 방지
- **Lock 타임아웃 메커니즘**: 크래시된 프로세스의 stale lock 감지 및 제거
- **환경 변수 검증**: 필수 환경 변수의 조기 검증 및 도움말 오류 메시지 제공
- **부분 실패 롤백**: 후속 작업 실패 시 plan 이슈 자동 닫기

#### 새 테스트
- v0.2.1 기능(멱등성, lock 타임아웃, 환경 검증, 롤백)을 위한 22개의 새 테스트
- 총 테스트 수 83개에서 105개로 증가

### 변경됨

- Lock 파일에 stale lock 감지를 위한 PID 및 타임스탬프 포함
- Config.get()이 기본값과 함께 중첩 키 조회를 올바르게 지원
- CLI 명령이 실행 전에 환경 검증 수행

### 기술 세부사항

- Lock 타임아웃 기본값 300초 (config.yaml로 설정 가능)
- signal 0을 사용한 프로세스 생존 확인
- 롤백 시 닫힌 이슈에 `rollback:failed` 라벨 추가

## [0.2.0] - 2025-01-03

### 추가됨

#### 백로그 기반 워크플로우
- **GitHub Issues를 UI/DB로 사용**: 아이디어와 계획을 GitHub Issues로 저장
- **휴먼 인 더 루프**: 스테이지 전환을 위한 라벨 기반 프로모션 시스템
- **GitHubClient**: Issues 및 Labels를 위한 완전한 GitHub API 통합
- **BacklogOrchestrator**: 백로그 기반 워크플로우를 위한 새 오케스트레이터

#### 프로모션 시스템
- 아이디어를 계획 스테이지로 프로모션하는 `promote:to-plan` 라벨
- 계획을 개발 스테이지로 프로모션하는 `promote:to-dev` 라벨
- 추적을 위한 `processed:to-plan` 및 `processed:to-dev` 라벨
- 처리 후 자동 라벨 관리

#### 새 CLI 명령어
- `ao backlog run`: 전체 오케스트레이션 사이클 실행
- `ao backlog generate`: 새 아이디어 이슈 생성
- `ao backlog process`: 대기 중인 프로모션 처리
- `ao backlog status`: 백로그 상태 표시
- `ao backlog setup`: 저장소에 필요한 라벨 설정

#### GitHub 통합
- 아이디어(`idea.yml`) 및 계획(`plan.yml`)용 이슈 템플릿
- 자동 실행을 위한 스케줄 워크플로우(`backlog.yml`)
- 라벨 문서(`docs/labels.md`)

#### 동시성 제어
- 동시 실행 방지를 위한 파일 기반 잠금
- 처리된 라벨을 통한 중복 방지
- cron/스케줄 실행에 안전

### 변경됨

- 자동 진행에서 사람 가이드 방식으로 워크플로우 모델 변경
- 백로그 기반 워크플로우를 위해 README.md 재작성
- GitHub 설정 변수로 `.env.example` 업데이트

### 기술 세부사항

- 비동기 가능 HTTP 클라이언트로 `httpx` 사용
- 83개 단위 테스트 통과
- 테스트를 위한 완전한 드라이런 지원

## [0.1.0] - 2025-01-03

### 추가됨

#### 코어 오케스트레이터
- 스테이지가 있는 상태 머신: IDEATION → PLANNING_DRAFT → PLANNING_REVIEW → DEV → QA → DONE
- YAML 기반 상태 영속화 (`.agent/state.yaml`)
- 계획 및 개발 사이클에 대한 설정 가능한 제한이 있는 반복 추적
- 품질 메트릭 추적 (리뷰 점수, 테스트 결과)

#### LLM 프로바이더 어댑터
- **Claude Provider**: CLI 모드(Claude Code) 및 API 모드 모두 지원
- **OpenAI Provider**: 독립적인 리뷰를 위한 GPT 모델 (기본: gpt-5.2-chat-latest)
- **Gemini Provider**: 빠른 에이전틱 태스크 (기본: gemini-3-flash-preview)
- Rate limit에 대한 지수 백오프로 자동 재시도
- 모든 프로바이더에 대한 폴백 모델 지원
- 적절한 오류 처리와 함께 할당량 소진 감지

#### 스테이지 핸들러
- **Ideation**: 모스랜드 생태계를 위한 Web3 서비스 아이디어 생성
- **Planning Draft**: PRD, 아키텍처, 태스크, 수용 기준 생성
- **Planning Review**: OpenAI/Gemini를 사용한 외부 리뷰
- **Development**: Claude Code를 사용한 기능 구현
- **Quality Assurance**: 테스트, 코드 리뷰, 보안 검사 실행
- **Done**: 완료 보고서 생성

#### CLI 명령어
- `ao init`: 새 프로젝트 초기화
- `ao step`: 단일 파이프라인 스텝 실행
- `ao loop`: 가드레일과 함께 연속 모드로 실행
- `ao status`: 현재 상태 표시 (--json 지원)
- `ao resume`: 일시 중지된 상태에서 재개
- `ao reset`: 오케스트레이터 상태 초기화
- `ao push`: 리모트에 변경사항 푸시

#### 오류 처리
- 자동 대기 및 재시도로 Rate limit 감지
- 할당량 소진 알림 (`alerts/quota.md`)
- 로그 및 커밋에서 민감한 데이터 마스킹
- 무한 루프 방지를 위한 최대 재시도 제한

#### 인프라
- 모든 스테이지에 대한 프롬프트 템플릿
- GitHub Actions CI 워크플로우 (테스트, 린트)
- GitHub Actions 오케스트레이터 워크플로우 (스케줄/수동)
- 포괄적인 단위 테스트

### 설정
- `.env`를 통한 환경 변수
- YAML 설정 (`config.yaml`)
- 테스트를 위한 드라이런 모드
- 재현성을 위한 고정 모델 버전

## [미출시]

### 계획됨
- 향상된 스마트 컨트랙트 개발 지원
- 멀티 프로젝트 오케스트레이션
- 모니터링용 웹 대시보드
- Slack/Discord 알림
- 비용 추적 및 예산 제한
