# 01 — Architecture (Phase D)

> **도메인 안전 가정 (필수):** 본 시뮬레이션은 **비공식 연구·교육용 합성(가상) 환경**이다. 실제 무기체계 성능 파라미터가 아닌 **공개·합성 데이터**를 사용한다. 좌표/AIS 필드는 mda-gotham `vessels.db` 스키마와 호환되도록 설계하되, 교전 파라미터(센서/무장 사거리·명중률·피해)는 **임의 합성값**이다. L3 LLM 지휘 계층(향후)은 HITL 가드레일 + 행동 검증 게이트 뒤에 둔다.

근거: `_workspace/00_research_references.md` 합성. MVP는 의존성 최소·즉시 실행 가능한 standalone 구현(PettingZoo API 형태)으로 시작해, 이후 RLlib self-play / CrewAI 지휘 계층으로 확장한다.

## 4계층 매핑 → MVP 범위
```
L4 디지털 트윈 상태 저장소   → MVP: SQLite (twin/state_store.py) [ref: 2401.04032 Lv2~3]
L3 LLM 지휘 계층            → MVP: 인터페이스 stub만 (가드레일 자리 표시)
L2 RL 전술                 → MVP: 규칙기반 정책 (RLlib 교체 가능한 act() 시그니처) [ref: RLlib]
L1 환경 코어               → MVP: PettingZoo-형 ParallelEnv (env/naval_env.py) [ref: PettingZoo/Gymnasium]
```

## 인터페이스 계약 (빌더·QA의 기준 — 변경은 아키텍트 협의)

### 계약 1 — 엔티티 상태 스키마 (디지털 트윈)
mda-gotham AIS 호환 (mmsi/lat/lon/sog/cog) + 교전 필드(합성):
```python
@dataclass
class Entity:
    mmsi: int          # 식별자 (AIS 호환)
    name: str
    side: str          # "blue" | "red"
    etype: str         # "destroyer" | "corvette" | "submarine" ...
    lat: float; lon: float        # 위치 (deg)
    heading: float     # 침로 (deg, 0=N, 시계방향)
    speed: float       # 속력 (knots)
    hp: float          # 잔존 전투력 (0=격침)
    sensor_nm: float   # 탐지 사거리 (해리, 합성)
    weapon_nm: float   # 교전 사거리 (해리, 합성)
    reload: int        # 재장전 잔여 step (0이면 발사 가능)
```

### 계약 2 — 환경 API (PettingZoo ParallelEnv 형태)
```python
class NavalWargameEnv:
    def reset(self, seed: int, scenario: dict) -> dict[str, Obs]: ...
    def step(self, actions: dict[str, Action]) -> tuple[
        dict[str, Obs], dict[str, float], dict[str, bool], dict[str, bool], dict[str, dict]
    ]: ...   # (obs, rewards, terminations, truncations, infos)
    @property
    def agents(self) -> list[str]: ...   # 살아있는 유닛 id
```
- `dt_seconds = 30` (1 step = 30초). `max_steps`는 시나리오가 정의.
- 시드 기반 결정성: 모든 난수는 `random.Random(seed)`로 캡슐화.

### 계약 3 — 관측(Obs) / 행동(Action) 공간 (부분관측)
```python
Obs = {
  "self": {mmsi, lat, lon, heading, speed, hp, reload},
  "contacts": [ {mmsi, side, bearing_deg, range_nm, etype} ... ],  # sensor_nm 이내만
  "step": int, "objective": str
}
Action = { "heading_cmd": float, "speed_cmd": float, "fire_target": int|None }
```
- 부분관측: contacts는 자기 sensor_nm 이내 적/아군만. (안개·전장의 불확실성 모델)

### 계약 4 — 시나리오 스키마 (JSON, MVP)
```json
{ "name": "...", "seed": 42, "dt_seconds": 30, "max_steps": 400,
  "blue": [ {엔티티 필드...} ], "red": [ ... ],
  "objectives": {"blue": "intercept|protect_zone", "red": "transit|strike"},
  "roe": "weapons_free|weapons_tight",
  "win": {"blue": "red_eliminated", "red": "transit_complete|blue_eliminated"},
  "difficulty": 1 }
```
> MVP는 JSON(무의존). yaml은 pyyaml 추가 시 지원.

### 계약 5 — 에이전트 인터페이스 (규칙/RL/LLM 공통)
```python
class Policy:
    def act(self, obs: Obs, rng: random.Random) -> Action: ...
```
- 규칙기반(MVP), RLlib 정책, LLM 지휘관이 모두 이 시그니처를 구현 → 교체 가능.

### 계약 6 — 평가 메트릭 + 리플레이
```python
# 리플레이: _workspace 산출 JSONL, step마다 한 줄
{ "step": int, "entities": [Entity 직렬화...], "events": [{"type":"fire|hit|kill","src":mmsi,"dst":mmsi,"hit":bool}] }
# 메트릭: {"winner": "blue|red|draw", "steps": int,
#          "blue_survivors": int, "red_survivors": int,
#          "blue_hp_total": float, "red_hp_total": float, "shots": int, "hits": int}
```

## MVP 마일스톤 (각 마일스톤 "완료 정의")
1. **상태 모델 + 트윈 저장소** — Entity dataclass + SQLite 적재/저장. *완료: roundtrip 테스트 통과.*
2. **환경 골격** — reset/step 시그니처, 시간·기동(위치 갱신). *완료: reset→step N회 무오류 스모크.*
3. **탐지·교전** — 부분관측 contacts, fire→hit 판정(거리기반 확률), 피해·격침. *완료: 1발 발사→피해 반영.*
4. **규칙기반 블루/레드 정책** — 추격/요격/회피/사격. *완료: act()가 유효 Action 반환.*
5. **1판 실행 + 리플레이/메트릭** — runner가 끝까지 돌리고 JSONL+메트릭 출력. *완료: winner 판정.*

## 검증 (qa-verifier)
각 마일스톤 직후 경계면 교차검증: 계약1↔상태저장소, 계약2/3↔환경, 계약5↔정책↔환경, 계약4↔runner. 스모크: import·시드 재현성(같은 seed→같은 winner).
