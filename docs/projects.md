# Projects Guide

이 문서는 MOSS.AO에서 생성된 프로젝트를 관리하는 방법을 설명합니다.

> **상태**: 구현돼 있습니다 (`project/scaffold.py`,
> `POST /plans/{id}/generate-project`). 일시정지된 것은 스케줄러의 인라인
> 자동 생성 한 곳뿐입니다 (`project.auto_generate.enabled: false`).
> 저장소의 `projects/` 폴더가 비어 있는 것은 생성물을 커밋하지 않기 때문입니다.

## 개요

MOSS.AO의 핵심 파이프라인:

```
Signals → Trends → Debate → Ideas → Plans → Projects
                                              ↑
                                    (스케줄러 자동 생성만 일시정지;
                                     API·버튼 경로는 동작)
```

Plan이 승인되면 `projects/` 폴더에 실제 프로젝트 스캐폴드가 자동 생성됩니다.

## 폴더 구조

```
projects/
├── README.md                           # 프로젝트 목록 및 상태
├── project-name-a/
│   ├── README.md                       # 프로젝트 소개, 배경, 빠른 시작
│   ├── PLAN.md                         # 원본 Plan 문서 (from debate)
│   ├── src/                            # 소스 코드
│   │   ├── frontend/                   # 프론트엔드 (if applicable)
│   │   └── backend/                    # 백엔드 (if applicable)
│   ├── docs/                           # 추가 문서
│   ├── package.json                    # (JS/TS 프로젝트)
│   └── pyproject.toml                  # (Python 프로젝트)
└── project-name-b/
    └── ...
```

## 프로젝트 README 템플릿

각 프로젝트의 `README.md`는 다음 구조를 따릅니다:

```markdown
# Project Name

> 한 줄 설명

## 배경

### 어떻게 이 프로젝트가 시작되었나?

이 프로젝트는 MOSS.AO의 멀티에이전트 토론 시스템에서 생성되었습니다.

- **토론 세션**: {debate_session_id}
- **토론 주제**: {debate_topic}
- **생성 일시**: {created_at}
- **Plan 점수**: {plan_score}/10

### 토론 참여 에이전트

| 단계 | 참여 에이전트 |
|------|---------------|
| 발산 | Agent1, Agent2, ... |
| 수렴 | Agent3, Agent4, ... |
| 기획 | Agent5, Agent6, ... |

## 프로젝트 개요

- **목표**: ...
- **대상 사용자**: ...
- **예상 기간**: ...
- **기술 스택**: ...

## 빠른 시작

### 설치

\`\`\`bash
# 의존성 설치
npm install  # or pip install -e .

# 개발 서버 실행
npm run dev  # or python -m project_name
\`\`\`

### 환경 변수

\`\`\`bash
cp .env.example .env
# Edit .env with your values
\`\`\`

## 아키텍처

{architecture_diagram}

## 로드맵

- [ ] Week 1: Foundation Setup
- [ ] Week 2: Core Features
- [ ] Week 3: Integration
- [ ] Week 4: Testing & Launch

## 관련 링크

- [원본 Plan](./PLAN.md)
- [MOSS.AO Dashboard](https://ao.moss.land)
- [Debate Session](https://ao.moss.land/debates/{debate_id})

---

*이 프로젝트는 [MOSS.AO](https://ao.moss.land)에서 자동 생성되었습니다.*
```

## 프로젝트 목록 (projects/README.md)

`projects/README.md` 파일은 모든 프로젝트의 목록과 상태를 관리합니다:

```markdown
# MOSS.AO Generated Projects

이 폴더는 MOSS.AO 멀티에이전트 토론 시스템에서 생성된 프로젝트들을 포함합니다.

## 프로젝트 목록

| 프로젝트 | 상태 | 생성일 | 점수 | 설명 |
|----------|------|--------|------|------|
| [project-a](./project-a/) | 🟢 Active | 2026-01-20 | 8.5 | Description... |
| [project-b](./project-b/) | 🟡 Planning | 2026-01-18 | 7.2 | Description... |
| [project-c](./project-c/) | ⚪ Paused | 2026-01-15 | 7.0 | Description... |

## 상태 범례

- 🟢 **Active**: 활발히 개발 중
- 🟡 **Planning**: 기획/설계 단계
- 🔵 **Review**: 리뷰/테스트 중
- ⚪ **Paused**: 일시 중단
- ✅ **Done**: 완료

## 프로젝트 생성 방법

프로젝트는 다음 경로로 자동 생성됩니다:

1. **토론 시스템**이 트렌드 기반 토론 진행
2. **아이디어 생성** 및 자동 점수화
3. **고점수 아이디어**가 승격 (≥7.0 + 2차 심사 CONFIRM) — 토론의 기획 문서를 실은 승격만 Plan 이 된다
4. **Plan 승인** 시 프로젝트 스캐폴드 생성

수동으로 프로젝트를 생성하려면:

\`\`\`bash
# 향후 구현 예정
PYTHONPATH=./src .venv/bin/python -m agentic_orchestrator.scheduler generate-project --plan-id <plan_id>
\`\`\`

## 관련 문서

- [Pipeline Guide](../docs/pipeline.md)
- [Labels Guide](../docs/labels.md)
- [MOSS.AO Dashboard](https://ao.moss.land)
```

## 계획된 구현

### Phase 1: 기본 스캐폴드 생성

- Plan 파싱 (마크다운 → 구조화된 데이터)
- 프로젝트 폴더 생성
- README.md, PLAN.md 자동 생성

### Phase 2: 코드 생성

- 기술 스택 감지 (Plan의 architecture 섹션)
- 보일러플레이트 코드 생성 (LLM 활용)
- 설정 파일 생성 (package.json, pyproject.toml 등)

### Phase 3: 자동화

- 웹 UI에서 "Generate Project" 버튼
- Plan 승인 시 자동 생성 옵션
- GitHub 연동 (자동 커밋/PR)

## 기술 스택별 템플릿

### Next.js + TypeScript

```
project-name/
├── src/
│   ├── app/
│   ├── components/
│   └── lib/
├── public/
├── package.json
├── tsconfig.json
└── next.config.js
```

### Python FastAPI

```
project-name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── main.py
│       └── api/
├── tests/
├── pyproject.toml
└── requirements.txt
```

### Solidity + Hardhat

```
project-name/
├── contracts/
├── scripts/
├── test/
├── hardhat.config.ts
└── package.json
```

## FAQ

### Q: 프로젝트는 어떤 기준으로 생성되나요?

Plan의 점수가 7.0 이상이고, 관리자가 승인한 경우 프로젝트가 생성됩니다.

### Q: 생성된 프로젝트를 수정해도 되나요?

네, 생성된 코드는 시작점일 뿐입니다. 자유롭게 수정하세요.

### Q: 프로젝트를 삭제하려면?

```bash
rm -rf projects/project-name/
```

그리고 `projects/README.md`에서 해당 항목을 제거하세요.
