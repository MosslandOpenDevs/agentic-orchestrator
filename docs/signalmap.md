# SignalMap 신호 피드 — AO 소비자 계약

AO의 12번째 시그널 어댑터(`adapters/signalmap.py`)가 소비하는
**SignalMap 발행 계층**의 계약과, 그 계약이 AO 코드의 어느 결정으로 번역됐는지를
적는다. 아래 수치와 필드는 2026-08-06 릴리스
(`2026-08-06T140035.659Z`)에서 실제로 응답을 받아 확인한 것이다.

> **소유권 한 줄.** SignalMap이 canonical entity·topic·event ID를 **소유**하고,
> AO·Media·Alpha·NPC는 이를 **인덱싱·소비**한다. 어느 소비자도 canonical ID를
> 새로 만들지 않는다. AO는 이 경계 위에서 읽기 전용 소비자다.

---

## 1. 엔드포인트

```
GET /api/signal/v1/manifest
GET /api/signal/v1/signals?since=<cursor>&limit=<n>&kind=<kind>
GET /api/signal/v1/clusters
GET /api/signal/v1/channels
GET /api/signal/v1/taxonomy/{topic|entity|event}
```

호스트는 `https://signalmap.moss.land` (config.yaml `signalmap.base_url`,
환경변수 `SIGNALMAP_BASE_URL`로 재정의).

- 구 경로 `/api/ao/v1/*`은 **같은 바이트를 계속 서빙**하지만 신규 통합은
  `signal` 접두사를 쓴다. 이름이 바뀐 이유는 이 발행 계층이 AO 전용이 아니라
  지도·MOSS Media·Alpha를 함께 먹이기 때문이고, 첫 소비자 이름을 데이터 계층에
  박아두면 결합이 생기기 때문이다.
- **인증은 현재 열려 있다** (발행 측 `AO_EXPORT_TOKEN` 미설정). 사이트에 이미
  공개된 내용만 담기기 때문. 토큰이 걸리면 AO 쪽은 `.env`에
  `SIGNALMAP_EXPORT_TOKEN`을 넣는 것이 마이그레이션의 전부다
  (`SignalMapAdapter._auth_headers`).

---

## 2. manifest — 릴리스 1개를 기술하는 문서

```jsonc
{
  "epoch":           "2026-08-06T14:00:35.659Z",  // ★ 리비전 원장의 세대
  "generatedAt":     "2026-08-06T14:00:35.659Z",  // 재발행마다 움직임
  "releaseId":       "2026-08-06T140035.659Z",    // 정렬 가능, 캐시 키
  "sourceWatermark": "2026-08-06T06:20:39.000Z",  // ★ 알림 대상
  "cursor":  { "field": "updatedAt", "tiebreak": "id", "max": "..." },
  "counts":  { "signals": 6747, "pulses": 5112, "topics": 31,
               "entities": 274, "events": 69, "clusters": 3424, "channels": 83 },
  "metrics": { "rawTopicLabelCount": 6301, "topicClusterCount": 3424,
               "canonicalTopicCount": 31, "activeIssueCount": 265, ... },
  "models":  { "summarizer": "grok-4.3", "embedding": "text-embedding-3-small" },
  "quality": { "status": "passed", "notes": [] },
  "files":   [ { "path": "signals.ndjson", "bytes": 19483700, "sha256": "..." }, ... ]
}
```

### `epoch` — 저장된 리비전을 무효화하는 단 하나의 필드

리비전 원장은 **서버별**이다. 발행 측이 원장을 다시 만들면 모든 레코드가
`revision: 1`로 돌아온다. `"들어온 revision > 저장된 revision"` 조건으로 업서트를
막는 소비자는, epoch이 바뀐 뒤 **앞으로 오는 모든 업데이트를 영구히 무시**한다 —
그리고 폴링은 계속 200을 반환하고 새 레코드 0건을 보고하므로 아무 경보도 울리지
않는다.

AO의 처리: `_apply_manifest()`가 저장된 epoch과 다르면 **커서를 버리고
backfill 모드로 되돌린다**. 저장된 리비전과의 비교(`_apply_revision_update`)는
그대로 엄격한 단조 비교로 남는다 — 두 방어가 서로를 대신하지 않는다.

### `sourceWatermark` — 알림을 걸 자리

수집된 가장 최신 항목의 시각이다. **`generatedAt`은 수집이 죽어도 계속 움직이고,
레코드 수는 줄지 않고 늘기를 멈출 뿐이라 "조용한 날"과 구별되지 않는다.**
watermark만이 구별한다.

- 로그: 폴링마다 확인, `watermark_stale_hours`(기본 30h, daily-ingest가 06:00 KST)
  초과 시 WARNING
- **나이는 watermark 값 자체로 잰다** — "우리가 변화를 본 시점"이 아니라. 후자를
  쓰면 상태 파일이 사라졌을 때 죽은 상류에게 30시간의 침묵을 새로 주게 되고, 이미
  멈춘 피드를 처음 동기화할 때 새것으로 보인다. 값이 *전진했지만 여전히 사흘 전*인
  경우도 같은 판정을 받는다
- `GET /status` → `components.signal_feed.status = "degraded"` + `reason`
- 최상위 `status`는 **바꾸지 않는다.** 상류가 멈춘 것은 아이디어 품질 문제이지
  사이트 장애가 아니다 — `llm_router` 컴포넌트와 같은 규칙이다.

### `quality.status`

`degraded`면 발행은 됐지만 조인이 일부 빈다(`notes` 확인) → WARNING 후 계속 수집.
`fatal` 조건은 **아예 발행되지 않고** 직전 릴리스가 유지되므로 소비자가 볼 일이 없다.

### `models`

바뀌면 그 모델 결과에 의존해 캐싱한 파생물은 재계산 대상이다. AO는 현재 파생물을
캐싱하지 않으므로 기록만 한다.

---

## 3. 커서 — `updatedAt` + `id` 타이브레이크

와이어 형식은 `"<updatedAt>|<id>"`이고, 응답의 `cursor.next`를 **그대로** 다음
요청의 `since`에 넣는다.

```
GET /api/signal/v1/signals?limit=1000
GET /api/signal/v1/signals?limit=1000&since=<cursor.next>
```

라이브 확인 사항 (2026-08-06):

| 성질 | 확인 결과 |
|------|-----------|
| 배타성 | `cursor.next`는 **배타적** — 다음 페이지는 그 레코드 *다음*부터 시작 |
| `limit` 상한 | `limit=5000` 요청 → `count: 2000`으로 조용히 클램프 |
| 타이브레이크 필요성 | 첫 발행의 11,859건이 **전부 같은 `updatedAt`**(= epoch) |

마지막 줄이 핵심이다. 타임스탬프만으로 페이징하면 같은 페이지를 영원히 받거나
동률의 나머지를 통째로 건너뛴다. **커서는 재구성하지 말고 서버가 준 문자열을
그대로 되돌려줄 것.** `tests/test_signalmap.py::TestCursorPaging`이 이 성질을 고정한다.

### AO의 페이징 정책

- `kind` 파라미터를 **쓰지 않는다.** 종류별 요청은 종류별 커서를 뜻하고, 하나의
  리비전 원장 위에 커서가 둘이면 동기화할 대상도 둘, 레코드를 잃을 경로도 둘이다.
  커서 하나로 전부 걷고 `signalmap.kinds`로 클라이언트에서 거른다.
- 커서는 **페이지마다** 디스크에 저장한다(`data/signalmap_state.json`).
  타임아웃이나 OOM kill로 중간에 죽어도 19MB를 다시 읽지 않는다.
- 한 회차는 `max_pages_per_run × page_limit`으로 제한된다. 첫 동기화는 여러
  회차에 걸쳐 완료되고, 그동안은 `min_interval_minutes` 스로틀이 무시된다.
- `hasMore: true`인데 커서가 전진하지 않으면 **회전 대신 중단**한다.

---

## 4. `verified` — 발행 중간에 읽었는가

데이터 파일이 manifest보다 먼저 쓰이므로, 발행 도중에 읽으면 서로 다른 릴리스의
조각을 잡을 수 있다. 응답 본문의 `verified: false`와 응답 헤더
`x-signalmap-export-verified: false`가 그 상태를 알린다.

AO의 처리: **둘 중 하나라도 false면 커서를 전진시키지 않고 회차를 중단**하고,
`last_success_at`도 갱신하지 않는다(→ 다음 틱이 스로틀에 걸리지 않고 즉시 재시도).
단일 파일만 읽는 소비자는 무시해도 되지만, AO는 manifest와 signals를 함께 읽어
epoch을 비교하므로 교차 조인에 해당한다.

---

## 5. 반드시 지켜야 할 세 가지

### ① 외래키는 canonical ID만

| 필드 | 안정성 | AO 저장 위치 |
|------|--------|--------------|
| `canonical.topicId` | **영구 안정** | `Signal.topics` (배열) |
| `canonical.entityIds` | **영구 안정** | `Signal.entities` (배열) |
| `canonical.eventIds` | **영구 안정** | `raw_data.canonical.event_ids` |
| `clusters.json`의 cluster id | 재클러스터링 시 **변경됨** | 저장하지 않음 |
| `raw.topic.label` 등 원본 라벨 | 요약기 회차마다 다름 | `raw_data.unstable_labels.*` |

- `canonical.*`의 `null`은 "아직 임계값을 넘는 canonical이 없음"이며 **원본 리스트와
  자리를 맞춘 자리표시자**다. ID가 아니므로 AO는 적재 시점에 제거한다.
  나중 회차에서 채워질 수 있고, 그때 `revision`이 오른다.
- 원본 라벨은 버리지 않되 `unstable_labels`라는 이름 아래 둔다 — 조인하지 말라는
  뜻을 키 이름에 박아둔 것이다.

### ② 정치 안전 모드 콘텐츠를 재구성하지 않는다

`policy.politicalSafety: true`인 레코드(좌/우 성향 뉴스 채널)는 `evidence.claims`가
**설계상 항상 비어 있다.** 자막을 다시 요약하는 것도, `title`+`summary`를 모델에
넘겨 "이 채널이 뭐라고 주장했나"를 묻는 것도 금지다. 입장이 필요하면 `quotes`와
`video.stance`를 쓴다.

**AO는 이 레코드를 기본적으로 적재하지 않는다** (`include_political_safety: false`).
정제해서 넣는 대신 버리는 이유는, AO의 하류 전 단계가 "텍스트를 모델에 주고 무슨
뜻인지 묻는" 일이기 때문이다 — 트렌드 분석, 토론, 기획 프롬프트 어디에서나 규칙이
깨질 수 있고, 그 위반은 완벽하게 그럴듯한 출력으로 나타나 눈에 띄지 않는다.
적재하지 않으면 나중에 프롬프트를 어떻게 바꿔도 위반할 수 없다.

옵트인(`true`)하면 그 순간부터 규칙 준수는 AO가 쓰는 **모든 프롬프트**의 문제가
된다. 그 경우에도 어댑터는 `claims`를 빈 배열로 강제하고
`raw_data.claims_withheld: true`를 남긴다 (상류가 실수로 보내더라도).

### ③ `stance`는 축에 대한 상대 위치다

`agree/disagree/observe/neutral`은 일반적 찬반이 아니라 **그 묶음의 갈림 축(첫 번째
편)에 대한 위치**다. 축은 `clusters.json`의 `axis.statement`에 있다.

- `axis.comparable: false`면 축에 명제가 둘 이상 섞인 것 → **합산 금지, 발산 점수
  금지, "입장을 바꿨다" 판정 금지.** 현재 코퍼스에서 영상 3편 이상 묶음의 상당수가
  여기 해당한다. MOSS Media에서 이 필터를 적용하니 입장 변화 후보가 38건 → 13건으로
  줄었고, 빠진 25건은 서로 다른 질문에 대한 답을 비교한 것이었다.
- AO는 stance를 `raw_data.video.stance`에 **불투명 라벨**로 두고
  `stance_axis_required: true`를 함께 기록한다. 현재 AO에는 stance를 집계하는 코드가
  없고, 만들 때는 반드시 `clusters.json`의 축을 함께 읽어야 한다.

> **claim 단위 stance는 아직 없다.** 영상 하나가 같은 이슈 안에서 A 주장에 찬성하고
> B 주장에 반대할 수 있는데, 영상당 stance 하나로는 표현되지 않는다. 요약기가
> claim을 추출하고 claim별로 입장을 매기는 파이프라인 변경이 필요한 후속 과제다.
> 그때까지 `stance`를 "claim에 대한 입장"으로 해석하지 말 것.

---

## 6. 레코드 → AO Signal 매핑

레코드 봉투:

```jsonc
{ "exportVersion": "v1", "epoch": "...", "verified": true,
  "count": 1, "hasMore": true,
  "cursor": { "since": null, "next": "<updatedAt>|<id>" },
  "records": [ ... ] }
```

| 레코드 필드 | AO |
|-------------|-----|
| `id` (예: `youtube:--84SSdFopg`) | `SignalData.external_id` → `Signal.id` 해시의 입력 |
| `title` | `Signal.title` (market.pulse는 날짜를 덧붙임, 아래 참조) |
| `summary` | `Signal.summary` |
| `evidence.url` | `Signal.url` |
| `occurredAt` | `Signal.collected_at` ← **폴링 시각이 아니라 상류 사건 시각** |
| `kind` / `sourceType` / `source.*` | `raw_data.kind`, `raw_data.channel.*` |
| `canonical.topicId` / `entityIds` | `Signal.topics` / `Signal.entities` |
| `evidence.quotes` / `references` | `raw_data.quotes` / `raw_data.references` |
| `video.*` / `market.*` | `raw_data.video` / `raw_data.market` |
| `revision` / `contentHash` | `raw_data.revision` / `raw_data.content_hash` |

### 왜 `external_id`인가

`SignalData.id`는 원래 `source:title:url`의 해시였다. 그 정체성은 **덧붙이기만 하는**
피드(RSS는 레코드 id가 없다)에는 맞지만, **레코드를 제자리에서 개정하는** 소스에는
틀리다. SignalMap은 canonical 토픽이 나중에 붙으면 같은 `id`에 `revision`을 올려
다시 발행하므로, 상류에서 제목이 한 번 수정되면 같은 레코드가 **관계없어 보이는 두
번째 행**으로 들어온다. 발행자가 id를 주면 정체성은 바이트가 아니라 발행자를 따른다.

`revision`이 오르면 `SignalAggregator._apply_revision_update`가 기존 행을 갱신한다.
비교는 **엄격한 단조**이며(같거나 낮으면 무시), canonical 링크는 **잃지 않는다** —
아직 매칭되지 않은 개정판이 이미 기록한 canonical 토픽을 지우지 못한다.

### 왜 `collected_at = occurredAt`인가

코퍼스는 수개월을 거슬러 올라가고 AO의 트렌드 창은 시간 단위다. backfill이
`utcnow()`를 찍으면 6개월 전 영상이 "오늘 수집된 신호"가 되고, 하류의 모든
시간창 쿼리가 그것을 믿는다. `max_age_days`(기본 30일)를 넘는 레코드는 **커서는
지나가되 저장하지 않는다** — 커서는 꼬리에 도달하기 위해 전부를 통과해야 한다.

### 왜 market.pulse 제목에 날짜를 붙이는가

`"비트코인 -1.90% · 5분"`은 수백 건의 pulse에서 반복된다. 구분자가 없으면
aggregator의 Jaccard 유사도 중복 제거가 서로 다른 시장 사건을 하나로 접는다.

---

## 7. 집계 계층 — 다시 만들지 말 것

`clusters.json` / `channels.json`은 AO에 필수가 아니다(현재 어댑터는 읽지 않는다).
다만 **묶음이나 채널 집계를 자체적으로 다시 만들지 말 것.** MOSS Media가 그러다
영상별 원본 라벨로 묶어서 "토픽" 6,301개를 셌고(지도는 3,424개), 채널은 표시명
교집합으로 9개를 통째로 놓쳤다. 필요하면 이 두 파일을 읽는다.

토픽은 네 층이고 넷 다 다른 숫자다:

```
6,301 원본 라벨 → 3,424 의미 묶음 → 31 canonical  ·  이 중 최근 7일 활성 265
```

"최근 활성"(265)은 사슬의 네 번째 칸이 아니라 **의미 묶음을 시간으로 자른 값**이라
canonical(31)보다 크다. 하나의 사슬로 읽으면 틀린다.

---

## 8. 설정

`config.yaml`의 최상위 `signalmap:` 섹션. 전체 키와 기본값은 그 파일의 주석 참조.

| 키 | 기본 | 의미 |
|----|------|------|
| `enabled` | `true` | 끄면 네트워크 요청 자체가 없음 |
| `kinds` | `[video.summary, market.pulse]` | 클라이언트 필터 (커서는 전부 걸음) |
| `page_limit` / `max_pages_per_run` | `1000` / `3` | 한 회차 예산 |
| `max_age_days` | `30` | 이보다 오래된 레코드는 걷되 저장 안 함 |
| `include_political_safety` | `false` | 위 규칙 ② |
| `min_interval_minutes` | `240` | backfill 중에는 무시됨 |
| `watermark_stale_hours` | `30` | 상류 수집 중단 판정선 |
| `state_file` | `data/signalmap_state.json` | 커서·epoch·watermark |

환경변수: `SIGNALMAP_BASE_URL`(호스트 재정의), `SIGNALMAP_EXPORT_TOKEN`(Bearer).

### 상태 파일을 테이블이 아니라 파일로 둔 이유

스케줄러는 작업마다 새 프로세스를 띄우고, SQLite 파일은 백업에서 복원된 적이 여러 번
있다. 커서 유실은 **"처음부터 재동기화"로 강등돼야지 "조용히 건너뜀"이 되면 안 된다.**
파일이 사라지면 다음 회차가 epoch을 다시 찾고 처음부터 걷는다 — 발행자의 안정적인
레코드 id 덕분에 재적재는 멱등이다.

---

## 9. 운영

```bash
# 지금 어디까지 왔나 (네트워크·DB 접근 없음)
curl -s https://ao.moss.land/api/status | python3 -m json.tool | grep -A 10 signal_feed

# 어댑터 관점
curl -s https://ao.moss.land/api/adapters | python3 -m json.tool | grep -A 20 signalmap

# 커서 상태 원본
cat data/signalmap_state.json
```

| 증상 | 원인 | 조치 |
|------|------|------|
| `"unknown"` + `"never synced"` | 아직 **한 번도 돌지 않음** (오류도 없음) | 다음 시그널 틱(30분) 대기 |
| `"degraded"` + `"never synced; last attempt failed: …"` | 돌았고 **실패했음** | `last_error` 확인. 이 둘을 구별하는 것이 요점이다 — 2026-08-06 첫 배포 때 상류 manifest가 일시적 504를 반환했는데, 이 구별이 없던 동안 `/status`는 아직 안 돈 피드와 똑같아 보였다 |
| `"degraded"` + watermark 문구 | **상류 수집이 멈춤** | SignalMap 팀에 문의. AO 쪽 조치 없음 |
| `"degraded"` + `last poll failed` | 네트워크/HTTP 오류 | `last_error` 확인. 실패해도 그 회차에 이미 걷은 페이지는 **반환된다**(부분 성공) — 커서가 이미 그 뒤에 있으므로 버리면 영구 유실이다 |
| `"degraded"` + `aborted mid-walk: cursor_stalled` | 서버가 `hasMore: true`인데 커서가 전진하지 않음 | 발행 측 문제. 같은 커서로 계속 재시도하며 재적재는 멱등이라 피해는 없다 |
| `"degraded"` + `aborted mid-walk: epoch_changed` | 걷는 도중 재발행 | 자동 해소. 다음 회차가 manifest를 다시 읽고 재동기화한다(그래서 이 abort는 성공으로 기록되지 않는다 — 기록되면 스로틀에 걸려 재동기화가 4시간 밀린다) |
| `"degraded"` + `cancelled mid-walk` | 어댑터 타임아웃(180s) | 커서가 회차 시작 지점으로 **되감긴다**. 다음 회차가 다시 읽는다 — 다시 읽기는 싸고 건너뛰기는 영구적이다 |
| `backfilling: true`가 계속 유지 | 첫 동기화 진행 중(정상, 수 회차) 또는 페이지 예산이 너무 작음 | `records_emitted` 증가 확인 |
| 새 레코드가 0인데 상류는 발행 중 | **epoch 미스매치 방어가 안 도는 상황** | `state.epoch`과 manifest `epoch` 비교 |

**전체 재동기화 강제:** 상태 파일을 지우면 된다.

```bash
rm data/signalmap_state.json
```

멱등하다 — 이미 있는 행은 `Signal.id`가 같아 다시 만들어지지 않고, `revision`이
오른 것만 갱신된다.

---

## 10. 관련 문서

- 레코드·커서 계약(발행 측): `signalmap/docs/AO_EXPORT.md`
- 집계 계층·메트릭·소유권 경계: `signalmap/docs/PROJECTION.md`
- canonical ID 규칙: `signalmap/docs/CANONICALIZATION.md`
- AO 쪽 구현: `src/agentic_orchestrator/adapters/signalmap.py`,
  `tests/test_signalmap.py`
- AO가 이 피드를 장기적으로 어디에 쓸 것인가: [`docs/direction.md`](direction.md)
