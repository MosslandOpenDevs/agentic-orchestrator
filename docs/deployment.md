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
     GitHub Actions CI (test + lint + website)
              ↓  (초록불일 때만)
   서버: moss-ao-deploy (5분마다, :04/:09/…/:59)
              ↓
   git fetch → "마지막 성공 SHA"와 비교, 변경 없으면 즉시 종료 (무로그)
              ↓
   가드: 실패 백오프 · 브랜치 · 로컬 수정 · 로컬 커밋 · CI 상태 · 토론 진행 중
              ↓
   DB 스냅샷 (data/backup/) → git reset --hard → 빌드(.next.new 스테이징) → PM2 재시작
              ↓
   헬스체크 (:3001/ready, :3000) → 성공 시에만 성공 SHA 기록 / 실패 시 자동 롤백
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

- **배포 기준은 HEAD가 아니라 "마지막 성공 SHA"** — `git reset --hard`는 빌드·헬스체크
  **전에** HEAD를 전진시키므로, 배포 도중 폴러가 죽으면(OOM SIGKILL·재부팅) HEAD만 새
  커밋에 가 있고 실제로는 옛 빌드가 돌아가는 상태가 됩니다. 예전 스크립트는 이때 다음
  틱부터 "up to date"로 읽어 실패를 영구히 은폐했습니다. 이제 성공한 배포의 SHA를
  `.git/moss-ao-deployed-sha`에 (헬스체크 통과 후에만) 기록하고 이 값을 비교 기준으로
  씁니다. 상태와 HEAD가 어긋나면 미완 배포로 간주하고 재시도합니다.
- **실패 백오프** — 같은 대상 SHA로 배포가 실패하면 시도 횟수를
  `.git/moss-ao-deploy-attempt`에 (작업 시작 **전에** — SIGKILL도 세도록) 기록하고,
  다음 재시도까지 `5분 × 2^(n-1)`(최대 60분, `DEPLOY_RETRY_*`로 조정)을 기다립니다.
  강제 DB 스냅샷·빌드·이중 재시작·롤백·웹훅으로 이루어진 풀 사이클을 5분마다 반복하지
  않기 위해서입니다. 원격에 새 커밋이 오면 즉시 리셋되고, `--force`는 백오프를 무시합니다.
- **데이터 보존** — `git clean`을 절대 사용하지 않습니다. `git reset --hard`는 추적되지 않는
  파일을 건드리지 않으므로 `data/orchestrator.db`, `data/backup/`, `.env`,
  `website/.env.local`이 그대로 남습니다. 2026-07 DB 유실 사고의 재발 방지선이며
  `tests/test_deploy.py`가 이 불변식을 실제로 검증합니다.
- **배포 전 DB 스냅샷 (fail-closed)** — 코드 배포 직전 `scheduler backup-db`(강제 스냅샷)를
  실행합니다. 헬스체크가 쓰는 약 1일 주기 `maybe_backup_database()`와 달리 항상 찍습니다.
  **스냅샷이 실패하면 배포하지 않습니다** — 이 스냅샷이 바로 지금 적용할 변경의 복원
  지점이라, 실패한 채로 배포하면 되돌아갈 곳 없이 2026-07 사고를 반복하게 됩니다.
  `backup-db`의 종료 코드가 계약입니다: `0`=기록됨, `2`=찍을 것이 없음(빈/없는 DB —
  정상), 그 외=실패(배포 중단 + 알림). 단, **문서만 바뀐 동기화는 스냅샷을 생략**합니다 —
  아무것도 재시작하지 않고 `reset --hard`는 untracked DB를 건드릴 수 없어 보호할 대상이
  없는데, 스냅샷마다 7슬롯 백업 창이 돌기 때문입니다.
- **CI 게이트** — GitHub check-runs API로 해당 커밋이 초록불일 때만 배포합니다.
  진행 중이면 다음 틱으로 미루고, 빨간불이면 배포하지 않습니다. API를 못 읽어도(네트워크
  장애 등) 눈감고 배포하지 않고 미룹니다.
  **체크가 0건인 것은 초록불이 아닙니다** — 푸시 직후 GitHub이 아직 체크를 등록하지 않은
  상태가 대부분이라(폴러는 5분마다 돕니다) 진행 중과 동일하게 다음 틱으로 미룹니다.
  예전에는 이때 그냥 배포해서 검증되지 않은 커밋이 운영에 올라갔습니다. 마찬가지로
  `skipped`/`stale`처럼 **아무것도 검증하지 않은 결론**은 실패 목록에 없다는 이유로
  초록불 취급됐지만 이제 미룹니다. 초록으로 인정하는 결론은 `success`와 `neutral`뿐입니다.
  `DEPLOY_REQUIRE_CI_JOBS`에 job 이름을 지정하면 그 job들이 실제로 통과했는지까지
  확인합니다 (미지정 시 보고된 체크만 검사).
- **로컬 수정 보호** — 서버 체크아웃에서 추적 중인 파일이 손으로 수정돼 있으면 배포를
  중단합니다(`--force`로만 덮어씀). `reset --hard`가 조용히 지우는 사고를 막습니다.
- **로컬 커밋 보호** — HEAD가 `origin/main`의 조상이 아니면(서버에 로컬 커밋이 있거나
  분기) `merge-base --is-ancestor` 검사가 배포를 중단합니다. `reset --hard`가 서버의
  의도적 로컬 커밋을 조용히 버리는 것을 막습니다. reflog에는 남지만, 조용한 파괴는
  파괴입니다. `--force`로만 덮어씁니다.
- **프론트 빌드 원자화** — `npm run build`는 라이브 `.next`(moss-ao-web이 서빙 중)가
  아니라 스테이징 디렉터리 `website/.next.new`에 빌드하고(`next.config.ts`가
  `NEXT_DIST_DIR`를 읽음), 빌드가 통째로 성공했을 때만 web 재시작 직전에 rename 두 번으로
  교체합니다. 실패하거나 도중에 죽은 빌드가 라이브 디렉터리를 반쯤 덮어쓴 채 남을 수
  없습니다. 이전 빌드 캐시는 스테이징 디렉터리로 시딩해 증분 빌드를 유지합니다.
- **토론 중 대기** — `moss-ao-debate` 등이 실행 중이면 백엔드 배포를 다음 틱으로 미룹니다
  (토론 1회 ~30분). 프론트엔드 전용 변경은 영향이 없으므로 그대로 진행합니다.
- **동시 실행 방지** — 락 디렉터리에 소유 프로세스의 PID를 기록합니다. 소유자가 죽어
  있으면(SIGKILL은 EXIT trap을 건너뛰어 락을 못 지웁니다) 다음 틱이 **즉시** 회수하고,
  PID를 읽을 수 없는 락만 90분 백스톱을 기다립니다. 같은 이유로 폴러의
  `max_memory_restart`도 1G→3G로 올렸습니다 — Next 빌드가 폴러 프로세스의 메모리 예산
  안에서 돌고, 한도 초과 시 PM2가 SIGKILL로 죽이기 때문입니다.
- **헬스체크는 readiness를 봅니다** — `/health`가 아니라 **`/ready`** 를 호출합니다.
  `/health`는 프로세스 생존만 보고하므로 2026-07 사고 때 모든 DB 엔드포인트가 500을
  내는 동안에도 200을 유지했고, 그 상태로 배포가 성공 판정될 수 있었습니다. `/ready`는
  실제 테이블을 읽고 안 되면 503을 반환합니다. 배포 **전에도** 같은 것을 봅니다: API가
  떠 있는데 레디니스만 실패하는 상태(=DB 문제)라면, 어떤 코드를 올려도 그 게이트를
  통과할 수 없으므로 재시작·롤백을 5분마다 반복하는 대신 배포를 미룹니다.
  > 롤백 시에는 `/ready`가 없던 커밋으로 돌아갈 수 있으므로 `/health`도 함께 받아들입니다.
- **자동 롤백** — 빌드 실패나 배포 후 헬스체크 실패 시 **마지막 성공 SHA**로 되돌리고
  **재빌드까지** 수행해 일관된 상태로 복구합니다 (미완 배포 재시도 중이라면 HEAD는 이미
  깨진 커밋에 가 있으므로, "직전 HEAD"가 아니라 마지막 성공 지점이 기준입니다).
  롤백마저 실패하면 `CRITICAL` 로그와 알림을 남깁니다.
- **자기 갱신 안전** — 스크립트 전체가 `main()` 함수로 감싸여 마지막 줄에서 호출됩니다.
  bash는 스크립트를 실행하면서 읽으므로, 이 장치가 없으면 자기 자신이 배포되는 도중
  새 파일을 엉뚱한 바이트 오프셋부터 읽을 수 있습니다.

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
| `DEPLOY_REQUIRE_CI_JOBS` | (없음) | 반드시 통과해야 할 check-run 이름들(쉼표 구분). 예: `test (3.12),test (3.13),lint,website` |
| `DEPLOY_ALERT_WEBHOOK` | (없음) | 실패·롤백 시 알릴 Slack/Discord 웹훅 |
| `GITHUB_TOKEN` | (없음) | 선택. CI 상태 조회의 rate limit 완화용 |
| `DEPLOY_VERBOSE` | `0` | `1`이면 변경 없는 틱도 로그에 남김 |
| `DEPLOY_RETRY_BASE_MIN` | `5` | 첫 실패 후 재시도 대기(분). 실패마다 2배 |
| `DEPLOY_RETRY_MAX_MIN` | `60` | 백오프 상한(분) |

그 외 조정 가능한 값(`DEPLOY_HEALTH_RETRIES`, `DEPLOY_API_URL`, `UV_BIN`,
`DEPLOY_STATE_FILE`/`DEPLOY_ATTEMPT_FILE` 등)은 `scripts/deploy.sh` 상단 주석에
정리돼 있습니다. 배포 상태 파일 두 개는 `reset --hard`가 닿지 못하는 `.git/` 안에
삽니다 (`moss-ao-deployed-sha`, `moss-ao-deploy-attempt`).

### uv / pip 자동 판별

의존성 설치는 체크아웃 형태를 보고 고릅니다. **`.venv/pyvenv.cfg`에 `uv = ...`가 적혀
있으면 `uv sync`, 아니면 `pip install -e .`** 입니다. 운영 서버의 `.venv`는 uv가 만든
것이라 **내부에 pip이 아예 없어서** `pip install -e .`는 실패합니다.

> `uv.lock`은 이제 저장소에 **커밋**되어 있습니다 (CI와 운영이 같은 커밋에서 같은
> 의존성 그래프를 설치해야 하므로). 그래서 모든 체크아웃에 lockfile이 존재하며,
> 판별 기준은 lockfile이 아니라 venv가 스스로 기록한 생성 방식입니다. venv가 아직
> 없을 때만 lockfile 존재 여부로 판단합니다.

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

자동 롤백은 "마지막 성공 배포"까지만 되돌립니다. 더 이전으로 가려면:

```bash
pm2 stop moss-ao-deploy          # 다시 앞으로 끌려가지 않도록 먼저 중지
git reset --hard <커밋>
pip install -e . && (cd website && npm run build)
pm2 restart moss-ao-api moss-ao-web --update-env
```

수동으로 되돌린 뒤에는 상태 파일도 현재 HEAD로 맞춰 둡니다. 폴러가 재개되면 어차피
`origin/main`으로 다시 배포되지만(그래서 먼저 중지하는 것), 상태 파일이 실제로 돌고
있는 커밋을 가리켜야 그 배포의 변경 범위 계산과 로그·롤백 기준이 진실과 일치합니다:

```bash
git rev-parse HEAD > .git/moss-ao-deployed-sha
```

DB까지 되돌려야 하면 손으로 파일을 복사하지 말고 복원 명령을 쓰십시오 — WAL 모드라
스냅샷을 `cp`로 덮어쓰면 남아 있던 WAL이 그 위에 재생돼 복원이 조용히 무효가 됩니다
(`CLAUDE.md`의 복원 절차 참조):

```bash
python -m agentic_orchestrator.scheduler restore-db --list
python -m agentic_orchestrator.scheduler restore-db
```

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
| 로그에 `ABORT ... local commits` | 서버에 `origin/main`에 없는 커밋이 있음. push하거나 되돌린 뒤 재시도, 급하면 `--force`(로컬 커밋은 reflog로만 복구 가능해짐) |
| `incomplete deploy detected ... retrying` | 직전 배포가 도중에 죽었음(OOM·재부팅). 정상 자기치유 — 반복되면 `logs/deploy.log`에서 무엇이 죽는지 확인 |
| `backing off (retry Nm ...)` 반복 | 같은 커밋이 계속 실패해 재시도 간격을 늘리는 중. 원인 수정 커밋을 머지하면 즉시 재개, 급하면 `--force` |
| `lock owner (pid N) is gone -- reclaiming` | 이전 폴러가 SIGKILL로 죽어 락을 못 지웠음. 자동 회수 — 정보성 로그 |
| `CI: still running -- deferring` 반복 | CI가 아직 진행 중이거나 멈춤. Actions 탭 확인 |
| `CI: status unavailable` 반복 | GitHub API 접근 실패(레이트 리밋 등). `GITHUB_TOKEN` 설정 검토 |
| `scheduler busy` 로 계속 밀림 | 토론이 오래 걸리는 중. 급하면 `--force` |
| `REMINDER ecosystem.config.js changed ...` 반복 | PM2 프로세스 정의(cron·env)는 자동 재등록되지 않음. **로그인 셸에서** `pm2 restart ecosystem.config.js --update-env && pm2 save` 실행 후 `rm logs/.ecosystem-pending` (PM2 관리 프로세스 안에서 실행 금지 — 아래 [cron_restart 오염](#pm2-cron_restart-오염-2026-08-05-사고) 참조). 이 알림은 파일을 지울 때까지 매 틱 반복됩니다 — 예전에는 배포 한 번만 안내하고 사라져서 변경이 무기한 미적용으로 남을 수 있었습니다 |
| `CRITICAL rollback ... unhealthy` | 배포도 롤백도 헬스체크 실패. `pm2 logs moss-ao-api` 확인 후 수동 개입 |
| 배포는 됐는데 화면이 그대로 | 프론트엔드는 `NEXT_PUBLIC_*`가 빌드 시점에 박히므로 빌드 필요. `logs/deploy.log`에 `npm run build`가 있는지 확인 |
| **`ERROR npm run build failed` 직후 `CRITICAL rollback ... unhealthy` 반복** | `npm ci`가 devDependencies를 빠뜨림. 아래 절 참조 |
| **api/web 업타임이 5분을 못 넘기고 ↺ 만 증가** | PM2 `cron_restart` 오염. 아래 절 참조 |

### `npm ci`가 devDependencies를 빠뜨림 (2026-08-06 사고)

**증상**: `npm run build`가 실패하고 이어지는 롤백 빌드도 같은 이유로 실패해
`CRITICAL rollback did not come back healthy`가 5분마다 반복된다. 사이트는 정상 —
빌드는 스테이징 디렉터리에 만들어 통째로 교체하므로 실패한 빌드가 라이브 `.next`를
건드리지 않고, 떠 있던 프로세스가 마지막 정상 번들을 계속 서빙한다.

**원인**: 폴러는 `ecosystem.config.js`에서 `NODE_ENV=production`을 물려받는다. npm은
이를 `--omit=dev`로 해석하므로 `npm ci`가 382개 중 45개만 설치하고, `next build`는
devDependency(`@vercel/turbopack/postcss` 등)를 찾지 못해 죽는다.

**조치**: 이미 고쳐져 있다 — `scripts/deploy.sh`의 `npm ci --include=dev`와
`website/.npmrc`의 `include=dev`. 두 벌로 둔 이유가 핵심이다:

> **deploy.sh 수정은 자기 자신을 적용하지 못한다.** bash는 시작 시점에 스크립트를 통째로
> 파싱하고(`main()` 래퍼가 그것을 강제한다 — [안전장치](#안전장치) 참조), 그래서 수정을
> 실어 나르는 배포조차 **옛** deploy.sh로 실행된다. 그 배포가 실패하면 롤백되고 새
> 스크립트는 영영 쓰이지 않는다. 반면 `git reset --hard`는 빌드보다 **먼저** 끝나므로
> 저장소 안의 파일(`.npmrc`, `package.json`, `next.config.ts` …)은 첫 시도부터 새
> 버전이 적용된다. 배포 자체를 망가뜨리는 버그는 스크립트가 아니라 체크아웃 쪽에 고칠
> 지점이 있는지 먼저 보라.

확인:

```bash
cd ~/agentic-orchestrator/website && ls node_modules | wc -l   # 정상 297
```

### PM2 `cron_restart` 오염 (2026-08-05 사고)

**증상**: 상시 실행이어야 할 `moss-ao-api`/`moss-ao-web`이 5분마다 강제 재시작된다.
`pm2 ls`에서 업타임이 5분을 넘지 못하고 재시작 카운터(↺)만 계속 오르며,
`pm2 describe moss-ao-api`에 있어서는 안 될 `cron restart │ 4-59/5 * * * *`
(= **deploy의 cron**)가 보인다.

**원인** (서버에서 스크래치 앱으로 재현·검증 완료):

1. PM2는 관리 중인 프로세스의 환경에 **그 프로세스 자신의 설정 키를 일반
   환경변수로 주입**한다. `moss-ao-deploy` 안에서 도는 deploy.sh의 환경에는
   `cron_restart=4-59/5 * * * *`, `autorestart=false` 등이 실제로 들어 있다.
2. 과거 deploy.sh는 `pm2 restart moss-ao-api --update-env`를 사용했다.
   `--update-env`는 호출한 셸의 환경 전체를 대상 앱 정의에 병합하는데, PM2는
   환경변수와 설정 키를 같은 이름공간(`pm2_env`)에 두므로 deploy의
   `cron_restart` 환경변수가 api/web의 **설정**으로 저장된다. (같은 경로로
   deploy 전용 `GITHUB_TOKEN` 등도 api/web 환경에 새어 들어갔다.)
3. PM2는 재시작 시 `ecosystem.config.js`를 다시 읽지 않는다(업스트림
   [#3742](https://github.com/Unitech/pm2/issues/3742),
   [#4504](https://github.com/Unitech/pm2/issues/4504)). 한번 오염된 등록은
   영구히 남고, **배포가 일어날 때마다 재적용**된다 — 깨끗하게 재등록해도
   다음 배포에서 다시 오염됐던 이유.

**수정** (이 저장소에 반영됨): deploy.sh가 ① 시작 시 PM2가 주입하는 주요 설정
키 환경변수(`cron_restart`, `autorestart`, `watch` 등 9종 — 방어선)를 `unset`하고
② 재시작에서 `--update-env`를 쓰지 않는다(근본 수정 — 이 플래그가 없으면 주입
키가 남아 있어도 새지 않음을 검증했다). 앱의 env는 등록 시점의
`ecosystem.config.js`가 단일 소스다.
`tests/test_deploy.py::TestPm2EnvHygiene`가 두 가지 모두 회귀를 차단한다.

**서버에 남은 오염 제거**: `pm2 restart X --cron-restart 0`은 PM2 7.0.3에서
**동작하지 않는다** (cron이 그대로 남음). 확실한 방법은 삭제 후 재등록뿐:

```bash
pm2 delete moss-ao-api moss-ao-web
pm2 start ecosystem.config.js --only "moss-ao-api,moss-ao-web"
pm2 describe moss-ao-api   # "cron restart" 행이 아예 없어야 정상
pm2 save
```

**오염 탐지** (전체 앱 스캔 — `autorestart=True`인 장수명 앱에 cron이 보이면 오염):

```bash
pm2 jlist | python3 -c "
import json, sys
for a in json.load(sys.stdin):
    env = a[\"pm2_env\"]
    if env.get(\"cron_restart\"):
        print(a[\"name\"], env[\"cron_restart\"], \"autorestart=\" + str(env.get(\"autorestart\")))
"
```

**예방 규칙**:

- PM2 관리 프로세스 **안에서** `pm2 ... --update-env` 또는 `pm2 start`를 절대
  실행하지 말 것. 운영 안내 명령(`pm2 restart ecosystem.config.js --update-env`)은
  로그인 셸 전용이다.
- 이 deploy.sh를 복사해 쓰는 다른 프로젝트(Algora, bridge-2026/oracle,
  signalmap의 daily-ingest.sh 등)도 같은 수정이 필요하다 — 실제로 2026-08-05
  스윕에서 `algora-web`(1-59/5)·`oracle-web`(3-59/5)이 같은 방식으로 오염돼
  있었다.

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
