# 02 — Build Log (Phase B)

## 구현 현황 (MVP 완료)
| 마일스톤 | 모듈 | 상태 | 완료 정의 검증 |
|----------|------|------|----------------|
| 1. 상태 모델 + 트윈 | `twin/state_store.py` (Entity, StateStore) | ✅ | roundtrip 테스트 통과 |
| 2. 환경 골격 | `env/naval_env.py` (reset/step) | ✅ | reset→step 스모크 통과 |
| 3. 탐지·교전 | `env/naval_env.py` (부분관측, fire/hit/kill) | ✅ | 사격→피해 반영 확인 |
| 4. 규칙기반 정책 | `agents/rule_based.py` | ✅ | act() 유효 Action 반환 |
| 5. 1판 실행 + 리플레이/메트릭 | `eval/runner.py`, `run_match.py` | ✅ | winner 판정·리플레이 생성 |
| + HTML 실행 레이아웃 | `viz.py` | ✅ | 자체포함 HTML 재생 뷰어 |

## 기술 결정
- **의존성 0 (stdlib만):** random/math/json/sqlite3/dataclasses. PettingZoo/numpy 미설치 환경에서도 즉시 실행. 인터페이스는 PettingZoo `ParallelEnv` 형태라 추후 무손실 교체 가능.
- **결정성:** 모든 난수 `random.Random(seed)` 캡슐화. 같은 (seed, scenario) → 동일 결과 (테스트로 강제).
- **시나리오 포맷:** MVP는 JSON(무의존). pyyaml 설치 시 .yaml 자동 지원(loader 분기).
- **좌표:** lat/lon(deg), AIS 호환. 소면적 equirectangular 근사로 방위·거리·기동 계산.

## 검증 (qa-verifier)
- 스모크/결정성 테스트 6개 전부 통과 (`tests/test_smoke.py`).
- 경계면 교차검증: 계약1↔state_store, 계약2/3↔env(self.side 추가로 아군/적 구분 버그 수정), 계약5↔정책↔env, 계약4↔loader/runner.
- **수정된 버그:** 초기 정책이 self의 side를 몰라 아군을 적으로 오인 → env `_observations()`의 self에 `side` 추가로 해소.

## 알려진 한계 / 다음 단계
- L2 RL: 현재 규칙기반. `Policy.act()` 시그니처 유지한 채 RLlib/PufferLib MAPPO self-play로 교체 예정.
- L3 LLM 지휘: 인터페이스 미구현. CrewAI/LangGraph 역할기반 참모진 + **HITL 가드레일·행동 검증 게이트** 필수(Rivera et al. 2024).
- 물리: 미사일 비행시간·기동 제약·기상 미반영(MVP 단순화). JSBSim 6-DOF·Stone Soup 추적으로 충실도 보강 가능.
- 트윈: SQLite 스냅샷(Lv2~3). 라이브 AIS 동기화(Eclipse Hono/Ditto)는 미연결 — mda-gotham vessels.db 연계 후보.
