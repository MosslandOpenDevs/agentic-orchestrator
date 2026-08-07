# AO 가용성 모니터

ao.moss.land이 언제, 얼마나, **왜** 죽었는지 기록한다.

## 왜 필요했나

AO 앱은 사무실 VM(`atrn-vm-linux`, 192.168.1.41)에서 돌고, Lightsail의 nginx가
테일넷 너머로 프록시한다. 사무실 회선이 끊기면 3000·3001 두 포트가 동시에
사라지고 모든 요청이 504가 되는데 — **끊긴 쪽에서는 그 사실을 알릴 수 없고,
바깥에서는 아무도 안 보고 있었다.**

2026-08-04와 2026-08-06에 각각 약 16분씩 다운됐지만 둘 다 사후에 nginx
error.log를 손으로 뒤져서야 재구성됐다. 그 로그는 logrotate가 14일 뒤 지운다.

관측 창이 3일뿐이라 표본이 2건이었고, 그래서 "라우터인지 ISP인지"를 끝내
확정하지 못했다. 이 모니터는 그 두 가지 결핍 — 기록이 안 남는 것, 원인을
구분 못 하는 것 — 을 메운다.

## 구조

```
Lightsail (nginx 호스트, 사무실 밖)
  probe_uptime.py  ──30초──▶ 100.109.139.25:3001/health
                              └─▶ data/uptime-YYYY-MM.csv
                              └─▶ 상태 전환 시에만 Discord

사무실 VM (감시 대상, 끊기는 쪽)
  probe_netpath.py ──30초──▶ [1] 게이트웨이 192.168.1.1
                              [2] 인터넷 1.1.1.1 (생 IP, DNS 무관)
                              [3] DNS github.com
                              [4] tailscale ping → Lightsail
                              └─▶ data/netpath-YYYY-MM.csv   (알림 없음)

어디서든
  report.py        ── 두 CSV를 시간으로 조인 → 다운별 원인 판정
```

**측정 위치가 핵심이다.** 바깥 프로버는 사용자가 겪는 것을 재고 끊겨도 살아
있다. 안쪽 프로버는 바깥에서 구분 불가능한 원인을 가른다. 안쪽은 알림을 보내지
않는다 — 알림을 보내야 할 바로 그 순간에 회선이 없기 때문이다.

## 원인 판정

바깥에서 다운으로 확정된 구간의 안쪽 샘플을 보고, **바깥쪽으로 나가면서 처음
실패한 계층**을 원인으로 삼는다.

| 관측 | 판정 |
|------|------|
| 게이트웨이 불통 | LAN / 스위치 / 라우터 자체 |
| 게이트웨이 정상, 1.1.1.1 불통 | 라우터 WAN 또는 ISP |
| 인터넷 정상, DNS 불통 | DNS만의 문제 |
| DNS 정상, tailscale 불통 | 터널 문제 (회선 아님) |
| **전 계층 정상인데 다운** | **네트워크 아님 — 앱이나 호스트** |

마지막 줄이 특히 중요하다. 다음 사고에서 전 계층이 정상으로 찍히면 사무실
회선은 무혐의고 버그는 우리 쪽이다.

한 샘플이 아니라 **구간의 과반**이 실패해야 그 계층을 원인으로 인정한다. 16분
다운 중 ICMP 한 방 빠졌다고 원인이 바뀌면 안 되기 때문이다.

## 단발 실패는 따로 센다

nginx 로그를 2026-08-04~06 구간에서 클러스터링하면 에러 뭉치가 19개 나오지만
실제 분 단위 다운은 2개뿐이고 나머지 17개는 에러 1~2건짜리 순간 블립이었다.
이걸 합쳐 세면 "3일에 2번"이 "하루 6번"이 되고, 그 숫자로는 아무도 설득할 수
없다. 그래서 **연속 2샘플 이상 실패해야 다운으로 확정**하고 1샘플짜리는
`순간 블립`으로 따로 표시한다. 알림 임계값도 같은 값이라 리포트와 알림이
서로 다른 말을 하지 않는다.

## 설치

두 박스 모두 `~/ao-monitor/`에 스크립트와 `config.env`를 두고, **사용자
crontab**으로 돌린다 (sudo 불필요 — 사무실 VM에는 애초에 sudo 권한이 없다).
cron이 1분마다 띄우고 스크립트가 그 안에서 30초 간격으로 2샘플을 찍는다.
`flock`으로 중복 실행을 막으므로 한 번이 길어져도 꼬이지 않는다.

```bash
# 1) Lightsail (바깥 프로버)
ssh mossland 'mkdir -p ~/ao-monitor/data'
scp scripts/monitor/probe_uptime.py mossland:ao-monitor/
scp scripts/monitor/config.env.example mossland:ao-monitor/config.env
ssh mossland 'chmod 600 ~/ao-monitor/config.env'

# 2) 사무실 VM (안쪽 프로버)
ssh atrn@100.109.139.25 'mkdir -p ~/ao-monitor/data'
scp scripts/monitor/probe_netpath.py atrn@100.109.139.25:ao-monitor/
scp scripts/monitor/config.env.example atrn@100.109.139.25:ao-monitor/config.env

# 3) crontab에 한 줄씩 추가 (기존 항목 보존!)
#    Lightsail:  * * * * * /usr/bin/python3 $HOME/ao-monitor/probe_uptime.py >/dev/null 2>&1
#    사무실 VM:  * * * * * /usr/bin/python3 $HOME/ao-monitor/probe_netpath.py >/dev/null 2>&1
```

### Discord 웹훅

`~/ao-monitor/config.env`의 `AO_MONITOR_DISCORD_WEBHOOK=`에 URL을 채운다
(Discord 서버 설정 → 연동 → 웹후크 → 새 웹후크 → URL 복사). 비워두면 기록만
하고 알림은 보내지 않는다.

웹훅은 **Lightsail에만** 넣는다. 사무실 VM의 프로버는 알림 기능이 없어서 거기
넣은 값은 아무 데도 읽히지 않는다 (양쪽에 같은 `config.env` 템플릿이 깔려 있어
헷갈리기 쉽다).

확인:

```bash
ssh mossland 'python3 ~/ao-monitor/probe_uptime.py --test-notify'
```

> **함정: Cloudflare가 Python의 기본 User-Agent를 막는다.** 디스코드는
> Cloudflare 뒤에 있고, `Python-urllib/3.x` UA로 오는 요청에 **HTTP 403 +
> `error code: 1010`** 을 돌려준다. curl로는 204가 떨어지므로 **웹훅은 멀쩡한데
> 스크립트의 알림만 전부 죽는다** — 이 모니터가 없애려는 바로 그 침묵이다.
> 그래서 `USER_AGENT` 상수를 명시적으로 보낸다 (2026-08-07 실측: 동일 요청,
> 기본 UA → 403, 지정 UA → 204). 이 헤더를 지우지 말 것.
>
> 알림 전송이 실패하면 `data/notify.log`에 시각·제목·사유가 남는다. "알림이
> 안 왔다"가 "사고가 없었다"인지 "채널이 죽었다"인지 구별하려면 이 파일을 본다.
> 비어 있으면 실패한 적이 없다는 뜻이다.

## 리포트

```bash
scripts/monitor/pull-report.sh                    # 전체
scripts/monitor/pull-report.sh --since 2026-08-01 # 특정 시점 이후
scripts/monitor/pull-report.sh --json             # 기계용
```

두 호스트에서 CSV를 끌어와 조인한다. 사무실 VM이 꺼져 있으면 안쪽 데이터 없이
가용성만 나오고 원인은 `불명`으로 표시된다.

## 보존 기간

이 모니터의 CSV는 스스로 월별로 쪼개지고 지우지 않는다 (분당 2행 ≈ 연 36MB).
반면 **증거로 쓰던 기존 로그 둘은 계속 증발한다**:

- nginx `error.log` — logrotate 기본 14일. `/etc/logrotate.d/nginx`의
  `rotate 14` → `rotate 90`
- 사무실 VM journald — 현재 3일치. `/etc/systemd/journald.conf`에
  `MaxRetentionSec=90d` 추가 후 `systemctl restart systemd-journald`
  (sudo 필요)

## 한계

- **Lightsail이 죽으면 바깥 프로버도 같이 죽는다.** 그 경우 moss.land도 함께
  죽으므로 바로 드러나지만, 그 구간은 기록에 남지 않는다. 이것까지 덮으려면
  외부 SaaS(UptimeRobot 등)를 한 겹 더 얹어야 한다.
- 다운 길이는 샘플 간격(30초) 단위로 반올림된다. 16분짜리에는 무의미하지만
  30초 미만 순단은 아예 못 잡을 수도 있다.
- tailscale의 `health` 경고는 다운의 근거로 쓰지 않는다. 2026-08-06 19:26~19:41에
  컨트롤 플레인이 끊겼지만 데이터 경로는 살아 있어 nginx 에러가 0건이었다 —
  그 로그만 보면 다운 횟수를 2배로 세게 된다.
