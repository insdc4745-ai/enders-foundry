---
name: enders-foundry-orchestrator
description: 엔더스파운드리(디지털 트윈 해군 워게임 AI 시뮬레이션) 하네스의 오케스트레이터. 리서치→설계→구축→운영 워크플로우로 전문 에이전트 팀을 조율한다. "엔더스파운드리", "디지털 트윈 워게임", "해군 시뮬레이션 구축/설계/운영", "워게임 만들어/돌려", "시뮬레이션 다시/재실행/업데이트/보완", "시나리오 생성/난이도 올려" 등 관련 작업 요청 시 반드시 사용. 신규 구축·부분 재실행·후속 보완을 모두 처리한다.
---

# Ender's Foundry Orchestrator — 디지털 트윈 해군 워게임 하네스

리서치로 검증된 패턴 위에서, 디지털 트윈 해군 워게임 시뮬레이션을 설계·구축하고 그 위에서 시나리오를 운영·생성하는 에이전트 팀을 조율한다.

## 실행 모드: 하이브리드 (Phase별 전환)
| Phase | 모드 | 에이전트 | 산출물 |
|-------|------|----------|--------|
| R. 리서치 | 서브(팬아웃) | research-scout | `_workspace/00_research_references.md` |
| D. 설계 | 생성-검증 | sim-architect + qa-verifier | `_workspace/01_architecture.md` |
| B. 구축 | 에이전트 팀 | sim-builder + qa-verifier | `src/`, `_workspace/02_build_log.md` |
| O. 운영 | 에이전트 팀 | scenario-operator + sim-builder | `scenarios/`, `_workspace/03_operation_report.md` |

> 모든 Agent 호출에 `model: "opus"` 명시. 에이전트 정의는 `.claude/agents/`, 스킬은 `.claude/skills/`.

## Phase 0: 컨텍스트 확인 (항상 먼저)
1. `_workspace/` 산출물 존재 여부 확인.
2. 실행 모드 판별:
   - `_workspace/` 없음 → **초기 실행** (Phase R부터 전체).
   - `_workspace/` 있음 + 사용자가 부분 수정 요청(예: "설계만 고쳐", "시나리오 더") → **부분 재실행** (해당 Phase 에이전트만 재호출).
   - `_workspace/` 있음 + 새 입력/요구 변경 → **새 실행** (`_workspace/`를 `_workspace_prev/`로 이동 후 재시작).
3. 어떤 Phase부터 실행할지 사용자에게 1줄 확인.

## Phase R: 리서치 (서브 에이전트)
- `research-scout`(general-purpose, opus, `run_in_background` 가능)를 `foundry-research` 스킬로 호출.
- **권한 주의:** WebSearch/WebFetch 권한이 없으면 라이브 수치 수집 불가 → 훈련 지식 기반 + "미검증" 경고로 진행하고, 사용자에게 "네트워크 권한 환경에서 재실행하면 정식 수치 확보 가능"을 알린다.
- 산출: `_workspace/00_research_references.md`(카테고리 랭킹 + 합성). 합성을 다음 Phase 입력으로.

## Phase D: 설계 (생성-검증)
- `sim-architect`(opus)를 `wargame-architecture` 스킬로 호출 → `_workspace/01_architecture.md` 초안.
- `qa-verifier`(general-purpose, opus)가 인터페이스 계약 일관성·완결성 리뷰.
- 피드백 반영 후 계약 확정. **6개 인터페이스 계약이 모두 정의됐는지** 확인하고 다음 Phase로.

## Phase B: 구축 (에이전트 팀)
- `TeamCreate`로 팀 구성: `sim-builder` + `qa-verifier`.
- `TaskCreate`로 MVP 구현 작업을 모듈 단위로 분할(상태→환경→물리→에이전트→실행→평가).
- 빌더가 모듈 완성 직후마다 QA에 검증 요청(점진적 QA, `SendMessage`). 불일치는 즉시 해소.
- 계약 변경이 필요하면 빌더가 보고 → 오케스트레이터가 `sim-architect` 재호출로 계약 개정.
- 산출: 동작하는 MVP(1판 완주) + `_workspace/02_build_log.md`.

## Phase O: 운영 (에이전트 팀)
- 팀 재구성: `scenario-operator` + `sim-builder`(결함 수정 대기).
- `scenario-operator`를 `scenario-engine` 스킬로 호출 → 시나리오 작성, N회 반복 실행, 통계·전술 분석, 난이도 커리큘럼 진행.
- 시뮬레이터 결함은 `sim-builder`에 핫픽스 요청.
- 산출: `scenarios/*.yaml` + `_workspace/03_operation_report.md`.

## 데이터 전달 프로토콜
- **파일 기반(주):** 모든 Phase 산출물은 `_workspace/{NN}_{artifact}.md`. 최종 코드는 `src/`, 시나리오는 `scenarios/`.
- **태스크 기반(팀):** Phase B/O는 `TaskCreate`/`TaskUpdate`로 진행·의존성 관리.
- **메시지 기반(팀):** 빌더↔QA, 운영자↔빌더 실시간 조율은 `SendMessage`.
- 파일명 컨벤션: `{phase순번}_{내용}.{ext}`. 중간 산출물(`_workspace/`)은 감사 추적용으로 보존.

## 에러 핸들링
- 에이전트 1회 재시도 후 재실패 → 해당 결과 없이 진행하고 최종 보고에 **누락 명시**.
- 인터페이스 계약 불일치 → 임의 수정 금지, `sim-architect`에 개정 요청.
- 상충 데이터/패턴 → 삭제하지 않고 출처·트레이드오프 병기, MVP는 단순한 쪽 채택.
- 시뮬레이터 비정상 종료 → 시드·시나리오 기록, 재현 케이스로 보존.

## 도메인 안전 게이트 (필수)
- 본 시뮬레이션은 **비공식 연구·교육용 합성 환경**이다. 실제 무기체계 파라미터가 아닌 공개/합성 데이터를 전제로 하며, 이 가정을 설계서·운영보고서 상단에 명시한다.
- L3 LLM 지휘 계층 구현 시 **HITL 가드레일 + 행동 검증 게이트**를 반드시 둔다(에스컬레이션 위험 차단).

## 테스트 시나리오
**정상 흐름:** "엔더스파운드리 구축해줘" → Phase 0(초기 실행 판별) → R(리서치 합성) → D(아키텍처+QA) → B(MVP 1판 완주) → O(시나리오 3개 실행·분석) → 최종 보고 + 피드백 요청.
**에러 흐름:** Phase B에서 빌더가 환경 API 시그니처 불일치 발견 → QA가 경계면 결함 보고 → 오케스트레이터가 `sim-architect` 재호출로 계약 개정 → 빌더 재구현 → QA 회귀 확인 → 진행.
**부분 재실행:** "시나리오 더 어렵게" → Phase 0이 `_workspace/` 감지 → Phase O만 재실행(`scenario-operator`가 난이도 곡선 상위 등급 생성).

## 실행 후 (Phase 7 진화)
실행 완료 후 사용자에게 피드백을 요청한다("결과·팀 구성에서 바꿀 점?"). 피드백 유형별로 스킬/에이전트/오케스트레이터를 수정하고, `CLAUDE.md` 변경 이력에 기록한다.
