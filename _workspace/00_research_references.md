# 00 — Research References (Phase R 정식 재실행)

> **출처/상태:** `research-scout` 2차 실행 (2026-06-01). **WebSearch/WebFetch 라이브 검증 완료.** GitHub 스타 수는 2026년 조회 기준, 논문은 **2023~2026 최신 + arXiv(오픈액세스, 접속 가능) 출처로 한정.**
> 정책: repo는 스타/인용 인기순, 논문은 최신성 우선 + 접속 가능한 곳만.

## 1. 멀티에이전트 시뮬 / RL 환경 (스타순)
| repo | URL | ⭐ stars | 관련성 (디지털 트윈 해군 워게임) |
|------|-----|---------|------|
| Ray (RLlib) | github.com/ray-project/ray | **42.7k** | MAPPO/PPO 분산 학습·대규모 self-play 스케일링 |
| Gymnasium | github.com/Farama-Foundation/Gymnasium | **12.0k** | 단일 에이전트 환경 API 베이스, 공간(space) 정의 표준 |
| PufferLib | github.com/PufferAI/PufferLib | **5.8k** | 고처리량 벡터화, Gym/PettingZoo 호환 래핑 |
| OpenSpiel | github.com/google-deepmind/open_spiel | **5.2k** | 불완전정보 게임 self-play(CFR/NFSP) 검증 |
| PettingZoo | github.com/Farama-Foundation/PettingZoo | **3.4k** | 멀티에이전트 API 표준(블루/레드·부분관측). 최신 1.26.1(2026-04) |

> 참고: Unity ML-Agents ~18.8k (3D 시뮬). JSBSim(6-DOF 동역학)·Stone Soup(DSTL 다표적 추적)은 충실도 보강용.

## 2. LLM 에이전트 오케스트레이션 (스타순 + 상태)
| repo | URL | ⭐ stars | 비고 |
|------|-----|---------|------|
| CrewAI | github.com/crewAIInc/crewAI | **52.6k** | 역할기반(CO/TAO/ASW 참모진 매핑 적합). 활발한 개발 |
| AutoGen | github.com/microsoft/autogen | ~38k | ⚠️ **유지보수 모드 — Microsoft Agent Framework로 이관**. 신규는 비권장 |
| LangGraph | (LangChain) | CrewAI 추월(2026 초) | 그래프 기반, 엔터프라이즈 채택 증가 → **신규 권장 후보** |

> **결정 변경:** 리서치 1차의 "AutoGen" 권장을 **CrewAI(역할기반) 또는 LangGraph(그래프 기반)**로 교체. AutoGen 유지보수 모드 때문.

## 3. AI 워게이밍 / 안전성 논문 (2023~2026, arXiv 오픈액세스만)
| 논문 | arXiv | 연도 | 한 줄 takeaway |
|------|-------|------|----------------|
| Escalation Risks from LMs in Military & Diplomatic Decision-Making (Rivera et al.) | 2401.03408 | 2024 | 대부분 LLM이 **예측 불가하게 에스컬레이션** → HITL 가드레일 필수 근거 |
| War and Peace (WarAgent) (Hua et al.) | 2311.17227 | 2023 | LLM 멀티에이전트로 WWI/WWII 등 국가 의사결정 시뮬 |
| Simulating Influence Dynamics with LLM Agents | 2503.08709 | 2025 | 적대적 LLM 에이전트로 영향·역영향 워게임 시뮬 |
| Shall We Play a Game? LMs for Open-ended Wargames (Matlin, Riedl et al.) | 2509.17192 | 2025 | 개방형 워게임 + **온톨로지 프레임워크** + 안전·해석성 |
| WARBENCH / WGSR-Bench (LLM 군사 의사결정 벤치마크) | 2603.21280 | 2026 | 상황인식·상대모델링·정책생성 전략추론 평가 벤치 |

## 4. 디지털 트윈 (해양/국방, 2023~2026, arXiv)
| 논문/프레임워크 | 출처 | 연도 | 한 줄 |
|------|-----|------|------|
| Digital Twin of Autonomous Surface Vessels (Menges et al.) | arXiv 2401.04032 | 2024 | 예측모델+RL로 ASV 디지털 트윈, 안전 항해 |
| Digital Twin for ASV: Enabler for Safe Maritime Nav | arXiv 2411.03465 | 2024 | 트윈을 **Lv0~Lv5**로 분류, Lv5=충돌회피·경로추종 자율 |
| On Digital Twins in Defence (Giberna et al.) | arXiv 2508.05717 | 2026 | 국방 트윈 종합리뷰: 시뮬 충실도·상호운용·의사결정지원 |
| Eclipse Ditto / Azure DTDL / Eclipse Hono | (오픈소스/문서) | - | 트윈 상태 백엔드·온톨로지·텔레메트리 수집 |
| CesiumJS / OpenUSD(Omniverse) | (오픈소스) | - | 지리공간/3D 전역 렌더링 |

---

## Synthesis — 권장 아키텍처 (검증 수치 반영, 4계층)

가장 검증된 패턴은 **계층 인터페이스가 분리된 4계층 스택**:

1. **환경 코어** — 커스텀 해군 교전 env를 **PettingZoo**(3.4k) API로, 단일 베이스는 **Gymnasium**(12k). 충실도는 JSBSim·Stone Soup 차용, 적대적 풀이는 **OpenSpiel**(5.2k)로 검증.

2. **RL 전술 (self-play)** — **Ray/RLlib**(42.7k) + **PufferLib**(5.8k) 벡터화로 **MAPPO league self-play**. AlphaStar/DARPA ACE의 경험적 증거가 robust 레드/블루 전술의 핵심으로 가리킴.

3. **LLM 지휘 계층** — 고수준 명령(의도·ROE·전력배분)을 주입하는 LLM 지휘관. 오케스트레이션은 **CrewAI**(52.6k, 역할기반 CO/TAO/ASW) 또는 **LangGraph**(그래프 기반) — ⚠️ AutoGen은 유지보수 모드라 비권장. 지속성은 Generative-Agents식 기억. **핵심: Rivera et al.(2024, arXiv 2401.03408)·"Shall We Play a Game?"(2025, 2509.17192)가 에스컬레이션 위험과 온톨로지·안전을 강조 → 반드시 HITL 가드레일 + 행동 검증 게이트 뒤에 둔다.**

4. **디지털 트윈 + 온톨로지** — 권위 상태를 트윈 백엔드(MVP는 SQLite, 확장은 Eclipse Ditto/Azure DTDL)에 보관. ASV 디지털 트윈 연구(2401.04032, 2411.03465)의 Lv0~Lv5 성숙도 모델을 기준으로, MVP는 Lv2~3(동기화+예측) 목표. 라이브 AIS는 Eclipse Hono, 지리뷰는 CesiumJS. "On Digital Twins in Defence"(2508.05717, 2026)를 국방 적용 레퍼런스로.

**권장 구체 스택:** *PettingZoo + 커스텀 해군 env(JSBSim/Stone Soup 충실도) → Ray/RLlib + PufferLib MAPPO self-play → CrewAI/LangGraph LLM 지휘 계층 + 에스컬레이션 가드레일 → SQLite→Eclipse Ditto 트윈 저장소 + CesiumJS 지리뷰, Foundry식 typed ontology로 통합.*

**MVP 단순화 경로 (의존성 최소, 즉시 실행):** PettingZoo-API-형태의 standalone 해군 env + SQLite 상태(mda-gotham `vessels.db` 호환) + 규칙기반 블루/레드 → **1판 완주 + 리플레이/메트릭**. 이후 RLlib self-play와 CrewAI 지휘 계층을 증분 추가.
