# ⚓ Ender's Foundry (엔더스파운드리)

> 디지털 트윈 해군 워게임 AI 시뮬레이션 — 실제 해역/함대 데이터를 디지털 트윈으로 복제하고,
> 그 위에서 블루/레드 AI가 전술 의사결정을 실험·단련하는 **비공식 연구·교육용 합성 시뮬레이션**.

[![play](https://img.shields.io/badge/▶_Play-GitHub_Pages-3b9dff)](https://insdc4745-ai.github.io/enders-foundry/)

브라우저에서 바로 구동되는 **인터랙티브 해군 워게임**입니다. 플레이어가 블루 함대를 직접 지휘하고,
레드는 규칙기반 AI가 해협 통과를 시도합니다. 시뮬레이션 엔진은 결정적 시드 RNG로 동일 조건에서 동일 전개를 재현합니다.

---

## 🎮 플레이 방법

**온라인:** GitHub Pages 링크(위 배지)로 접속 — 설치 불필요.

**로컬:** ES 모듈을 쓰므로 `file://` 더블클릭이 아닌 로컬 서버가 필요합니다.

```bash
# 저장소 루트에서
python -m http.server 8753
# 브라우저에서 http://127.0.0.1:8753/index.html 열기
```

### 조작
| 동작 | 결과 |
|------|------|
| 🟦 블루 함정 클릭 | 함정 선택 |
| 바다 클릭 | 선택 함정의 침로를 클릭 지점으로 지정(최대속력) |
| 🟥 적 접촉 클릭 | 선택 함정의 사격 목표 지정 |
| 우클릭 | 명령 취소 |
| ▶ 재생 / ⏭ 1스텝 | 시뮬레이션 진행 |
| 시뮬속도 슬라이더 | 1×~20× 배속 |
| 블루: 수동/AI | 블루를 규칙기반 AI에게 위임(관전 모드) |
| 자동사격 ON/OFF | 사거리 내 적 자동 교전 |

---

## 🧠 시뮬레이션 엔진

`game/engine.js` 는 Python 레퍼런스 구현(`src/enders_foundry/`)의 충실한 1:1 포팅입니다.

- **부분관측(POMDP):** 각 함정은 자신의 센서 사거리 내 접촉만 인지
- **기동:** 침로 회전 제한(20°/step), 등속 전진(equirectangular 근사)
- **교전:** 사거리 모델 + 근거리 가중 명중확률(`p = clamp(1 − range/weapon_nm, 0.15, 0.9)`), 재장전(3 step)
- **결정성:** `mulberry32` 시드 RNG → 동일 시나리오·시드 → 동일 결과
- **종료:** 일방 전멸 또는 `max_steps` 도달

레드 전술은 `RuleBasedPolicy`(추격·요격 / 통과·응사). RLlib 정책이나 LLM 지휘 계층도
동일한 `act(obs)` 시그니처로 교체 가능합니다.

### 시나리오
- `strait_intercept_01` — 난이도 1, 코르벳 2척 vs 구축함 2척
- `strait_intercept_02` — 난이도 2, 고속 코르벳 3척(수적 열세)

---

## 📁 구조

```
index.html              # 인터랙티브 게임 (브라우저)
game/engine.js          # 시뮬레이션 엔진 (ESM, Node/브라우저 공용)
game/scenarios.js       # 시나리오 데이터
src/enders_foundry/     # Python 레퍼런스 구현 (환경·정책·평가 러너)
scenarios/*.json        # 원본 시나리오 정의
tests/test_engine.mjs   # 엔진 포팅 검증(AI vs AI 30판 승률 회귀)
_workspace/             # 리서치·아키텍처·운영 로그 + 리플레이 뷰어
```

### Python 레퍼런스 실행
```bash
python -m enders_foundry.run_match --scenario scenarios/strait_intercept_01.json
```

### 엔진 회귀 테스트 (Node 필요)
```bash
node tests/test_engine.mjs
```

---

## ⚠️ 도메인 안전 고지

본 프로젝트는 **공개/합성 데이터를 전제로 한 비공식 연구·교육용** 시뮬레이션입니다.
실제 무기체계 성능을 모델링하지 않으며, 모든 파라미터는 합성값입니다. LLM 지휘 계층을
도입할 경우 HITL 가드레일과 행동 검증 게이트 뒤에 두어 에스컬레이션 위험을 차단합니다.

## 라이선스
[MIT](LICENSE)
