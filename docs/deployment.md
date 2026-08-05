# MOSS.AO 자동 배포 (Auto-Deploy)

`main`에 머지되면 운영 서버가 스스로 최신 코드를 받아 빌드·재시작하는 **풀(pull) 방식**
배포입니다. 서버에서 5분마다 `scripts/deploy.sh`가 돌면서 `origin/main`이 움직였을 때만
동작하고, 그 외에는 `git fetch` 한 번으로 즉시 종료합니다.

## 왜 풀 방식인가

CI에서 서버로 밀어넣는(push) 방식이 아니라 서버가 당겨오는(pull) 방식을 쓴 이유는
이 인프라의 제약 세 가지 때문입니다.

| 제약 | 확인된 사실 | 영향 |
|------|-------------|------|
| 앱 서버에 공개 인바운드 경로가 없음 | PM2·Ollama가 도는 앱 서버는 Tailscale 테일넷 안에서만 접근 가능. 공개 도메인 `ao.moss.land`는 별도 Lightsail의 Nginx가 프록시 (호스트명·IP는 `CLAUDE.local.md` 참조) | 외부 CI 러너가 SSH로 들어올 방법이 없음 |
| 저장소가 **public** | `MosslandOpenDevs/agentic-orchestrator` | self-hosted 러너를 붙이면 포크 PR로 임의 코드가 사내 서버에서 실행될 수 있음 (GitHub도 공개 저장소에는 권장하지 않음) |
| 저장소 admin 권한 없음 | 현재 권한은 `MAINTAIN` (`viewerCanAdminister: false`) | 러너 등록·Actions 정책 변경이 API에서 403 |

풀 방식은 이 셋을 모두 우회합니다. **포트를 열지 않고, 배포 키도 없고, GitHub 쪽 설정이
아예 필요 없습니다.** public 저장소는 인증 없이 `git fetch`가 되므로 서버는 아웃바운드
연결만 사용합니다. Tailscale은 사람이 서버에 들어갈 때 쓰는 관리 경로로 남고, 배포 경로에
관여하지 않습니다.

대신 감수하는 것: **푸시 즉시가 아니라 최대 5분(+CI 시간) 지연**됩니다. 즉시 배포가
필요하면 아래 [수동 배포](#수동-배포)로 앞당기거나, [GitHub Actions + Tailscale
업그레이드 경로](#업그레이드-경로-github-actions--tailscale)를 참고하세요.

## 흐름

```
git push → main 머지
              ↓
        GitHub Actions CI (test + lint)
              ↓  (초록불일 때만)
   서버: moss-ao-deploy (5분마다, :04/:09/…/:59)
              ↓
   git fetch → 변경 없으면 즉시 종료 (무상태·무로그)
              ↓
   가드: 브랜치 확인 · 로컬 수정 확인 · CI 상태 · 토론 진행 중 여부
              ↓
   DB 스냅샷 (data/backup/) → git reset --hard → 빌드 → PM2 재시작
              ↓
   헬스체크 (:3001/health, :3000) → 실패 시 이전 커밋으로 자동 롤백
```

### 변경 범위에 따라 필요한 작업만 수행

| 변경된 경로 | 수행 |
|-------------|------|
| `src/`, `config.yaml`, `prompts/` | `pm2 restart moss-ao-api` |
| `pyproject.toml` | 의존성 설치 + API 재시작 — 체크아웃이 uv 관리면 `uv sync`, 아니면 `pip install -e .` |
| `website/` | `npm run build` + `pm2 restart moss-ao-web` |
| `website/package*.json` | `npm ci` + 빌드 + 재시작 |
| 문서만 (`*.md` 등) | 체크아웃만 갱신, 재시작 없음 |

스케줄러 프로세스(`moss-ao-signals`·`trends`·`debate`·`backlog`·`health`)는 **재시작하지
않습니다.** 이들은 cron 틱마다 `.venv/bin/python`을 새로 띄우므로 다음 실행에서 새 코드를
자동으로 집어갑니다. 재시작하면 진행 중인 작업만 죽습니다.

## 안전장치

- **데이터 보존** — `git clean`을 절대 사용하지 않습니다. `git reset --hard`는 추적되지 않는
  파일을 건드리지 않으므로 `data/orchestrator.db`, `data/backup/`, `.env`,
  `website/.env.local`이 그대로 남습니다. 2026-07 DB 유실 사고의 재발 방지선이며
  `tests/test_deploy.py`가 이 불변식을 실제로 검증합니다.
- **배포 전 DB 스냅샷** — 매 배포 직전 `scheduler backup-db`(강제 스냅샷)를 실행합니다.
  헬스체크가 쓰는 약 1일 주기 `maybe_backup_database()`와 달리 항상 찍습니다.
- **CI 게이트** — GitHub check-runs API로 해당 커밋이 초록불일 때만 배포합니다.
  진행 중이면 다음 틱으로 미루고, 빨간불이면 배포하지 않습니다. API를 못 읽어도(네트워크
  장애 등) 눈감고 배포하지 않고 미룹니다.
- **로컬 수정 보호** — 서버 체크아웃에서 추적 중인 파일이 손으로 수정돼 있으면 배포를
  중단합니다(`--force`로만 덮어씀). `reset --hard`가 조용히 지우는 사고를 막습니다.
- **토론 중 대기** — `moss-ao-debate` 등이 실행 중이면 백엔드 배포를 다음 틱으로 미룹니다
  (토론 1회 ~30분). 프론트엔드 전용 변경은 영향이 없으므로 그대로 진행합니다.
- **동시 실행 방지** — 락 디렉터리 사용. 90분 이상 묵은 락은 자동 회수합니다.
- **자동 롤백** — 빌드 실패나 배포 후 헬스체크 실패 시 이전 커밋으로 되돌리고 **재빌드까지**
  수행해 일관된 상태로 복구합니다. 롤백마저 실패하면 `CRITICAL` 로그와 알림을 남깁니다.

## 설치 (서버에서 1회)

```bash
cd ~/agentic-orchestrator   # 실제 체크아웃 경로
git checkout main && git pull
```

`.env`에 아래 한 줄을 추가합니다. 이 플래그가 없으면 `moss-ao-deploy` 프로세스는 아예
등록되지 않으므로, 랩톱이나 다른 체크아웃이 실수로 자기 자신을 배포하는 일이 없습니다.

```bash
echo 'MOSS_AO_AUTO_DEPLOY=1' >> .env
```

동작을 먼저 확인한 뒤(아무것도 바꾸지 않습니다):

```bash
bash scripts/deploy.sh --check
```

등록하고 저장합니다:

```bash
pm2 start ecosystem.config.js --only moss-ao-deploy && pm2 save
```

확인:

```bash
pm2 status moss-ao-deploy
tail -f logs/deploy.log
```

## 설정 (`.env`)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MOSS_AO_AUTO_DEPLOY` | (없음) | `1`이어야 `moss-ao-deploy`가 PM2에 등록됨 |
| `DEPLOY_BRANCH` | `main` | 추적할 브랜치 |
| `DEPLOY_REQUIRE_CI` | `1` | `0`이면 CI 결과와 무관하게 배포 |
| `DEPLOY_ALERT_WEBHOOK` | (없음) | 실패·롤백 시 알릴 Slack/Discord 웹훅 |
| `GITHUB_TOKEN` | (없음) | 선택. CI 상태 조회의 rate limit 완화용 |
| `DEPLOY_VERBOSE` | `0` | `1`이면 변경 없는 틱도 로그에 남김 |

그 외 조정 가능한 값(`DEPLOY_HEALTH_RETRIES`, `DEPLOY_API_URL`, `UV_BIN` 등)은
`scripts/deploy.sh` 상단 주석에 정리돼 있습니다.

### uv / pip 자동 판별

의존성 설치는 체크아웃 형태를 보고 고릅니다. `uv.lock`이 있거나 `.venv/pyvenv.cfg`에
`uv = ...`가 적혀 있으면 `uv sync`, 아니면 `pip install -e .`입니다. 운영 서버의
`.venv`는 uv가 만든 것이라 **내부에 pip이 아예 없어서** `pip install -e .`는 실패합니다
(`uv.lock`은 저장소에 커밋돼 있지 않고 서버에만 있으므로, 이 판별은 커밋이 아니라
머신의 속성입니다).

## 운영

### 수동 배포

5분을 기다리지 않고 즉시 반영:

```bash
bash scripts/deploy.sh
```

가드를 모두 무시(브랜치·로컬 수정·CI·토론 진행 중):

```bash
bash scripts/deploy.sh --force
```

### 일시 중지 / 재개

```bash
pm2 stop moss-ao-deploy     # 중지 (수동 배포는 계속 가능)
pm2 start moss-ao-deploy    # 재개
pm2 delete moss-ao-deploy && pm2 save   # 완전 해제
```

### 수동 롤백

자동 롤백은 "직전 커밋"까지만 되돌립니다. 더 이전으로 가려면:

```bash
pm2 stop moss-ao-deploy          # 다시 앞으로 끌려가지 않도록 먼저 중지
git reset --hard <커밋>
pip install -e . && (cd website && npm run build)
pm2 restart moss-ao-api moss-ao-web --update-env
```

DB까지 되돌려야 하면 `CLAUDE.md`의 복원 절차(최신 `data/backup/orchestrator-*.db`를
`data/orchestrator.db`로 복사)를 따릅니다.

### 로그

| 파일 | 내용 |
|------|------|
| `logs/deploy.log` | 배포 이력 (커밋·단계·롤백) |
| `logs/deploy-out.log` | PM2 stdout |
| `logs/deploy-error.log` | PM2 stderr |

## 문제 해결

| 증상 | 원인 / 조치 |
|------|-------------|
| 로그에 `ABORT ... local modifications` | 서버 체크아웃에서 추적 파일이 수정됨. `git status`로 확인 후 정리하거나 `--force` |
| `CI: still running -- deferring` 반복 | CI가 아직 진행 중이거나 멈춤. Actions 탭 확인 |
| `CI: status unavailable` 반복 | GitHub API 접근 실패(레이트 리밋 등). `GITHUB_TOKEN` 설정 검토 |
| `scheduler busy` 로 계속 밀림 | 토론이 오래 걸리는 중. 급하면 `--force` |
| `ecosystem.config.js changed` 안내 | PM2 프로세스 정의(cron·env)는 자동 재등록되지 않음. `pm2 restart ecosystem.config.js --update-env && pm2 save` 를 직접 실행 |
| `CRITICAL rollback ... unhealthy` | 배포도 롤백도 헬스체크 실패. `pm2 logs moss-ao-api` 확인 후 수동 개입 |
| 배포는 됐는데 화면이 그대로 | 프론트엔드는 `NEXT_PUBLIC_*`가 빌드 시점에 박히므로 빌드 필요. `logs/deploy.log`에 `npm run build`가 있는지 확인 |

## 업그레이드 경로: GitHub Actions + Tailscale

푸시 즉시(수 초 내) 배포가 필요해지면, GitHub Actions 러너를 임시 테일넷 노드로 붙여
서버에 SSH하는 방식으로 바꿀 수 있습니다. 다만 **현재 권한으로는 불가능**하며 아래가
선행돼야 합니다.

1. **테일넷 관리자 협조** — `tag:ci` 태그와 해당 태그의 SSH 접근을 허용하는 ACL, 그리고
   OAuth 클라이언트 발급. 테일넷은 조직 공용이라 소유자가 따로 있습니다.
2. **저장소 admin 권한** — Actions 시크릿(`TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`,
   `DEPLOY_SSH_KEY`) 등록에 필요. 현재 `MAINTAIN`이라 403.
3. **서버에 배포 전용 계정/키** — 러너가 로그인할 계정과 `authorized_keys` 등록.

이 경우에도 실제 배포 동작은 서버의 `scripts/deploy.sh`를 그대로 호출하는 형태를
권장합니다(워크플로는 `ssh <서버> 'cd ~/agentic-orchestrator && bash scripts/deploy.sh --force'`).
가드·헬스체크·롤백 로직이 한 군데에만 있어야 두 경로가 갈라지지 않습니다.

self-hosted 러너를 서버에 직접 설치하는 방식은 **권장하지 않습니다.** 저장소가 public이라
포크 PR이 사내 서버에서 코드를 실행할 위험이 있고, 등록에도 admin 권한이 필요합니다.

## 관련 문서

- `scripts/deploy.sh` — 스크립트 본체 (상단 주석에 전체 옵션)
- `tests/test_deploy.py` — 동작 검증 테스트 (가드·롤백·데이터 보존)
- `CLAUDE.md` — DB 백업/복원 절차, PM2 운영
- `docs/pipeline.md` — 파이프라인 개요
