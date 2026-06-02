"""L2 — 규칙기반 전술 정책 (계약 5). act(obs, rng) -> Action.

RLlib 정책이나 LLM 지휘관도 동일한 act() 시그니처를 구현하면 교체 가능하다(MVP는 규칙기반).
objective에 따라 행동이 갈린다:
  - intercept/protect_zone(주로 blue): 최근접 적을 추격·요격, 사거리 내면 사격
  - transit/strike(주로 red): 목표 방위로 항진, 위협 시 응사
"""
from __future__ import annotations

import random


class RuleBasedPolicy:
    def __init__(self, objective: str, transit_heading: float = 90.0):
        self.objective = objective
        self.transit_heading = transit_heading   # transit 시 목표 방위 (기본 동향 E)

    def act(self, obs: dict, rng: random.Random) -> dict:
        me = obs["self"]
        enemies = [c for c in obs["contacts"] if c["side"] != _my_side(obs)]

        # 적 접촉이 없으면: transit은 목표 방위로, 그 외는 탐색 항진
        if not enemies:
            heading = self.transit_heading if self.objective in ("transit", "strike") else me["heading"]
            return {"heading_cmd": heading, "speed_cmd": me["max_speed"], "fire_target": None}

        nearest = min(enemies, key=lambda c: c["range_nm"])
        fire_target = None
        if nearest["range_nm"] <= me["weapon_nm"] and me["reload"] == 0:
            fire_target = nearest["mmsi"]

        if self.objective in ("transit", "strike"):
            # 목표로 항진하되, 위협이 사거리 내면 응사 (회피 약간)
            if nearest["range_nm"] <= me["weapon_nm"]:
                heading = self.transit_heading
            else:
                # 적이 진로를 막으면 살짝 우회
                heading = (self.transit_heading + 15.0) % 360.0
            return {"heading_cmd": heading, "speed_cmd": me["max_speed"], "fire_target": fire_target}

        # intercept/protect_zone: 최근접 적 방위로 추격
        heading = nearest["bearing_deg"]
        # 사거리 안에 들면 속력 약간 줄여 사격 안정 (합성 휴리스틱)
        speed = me["max_speed"] * (0.6 if nearest["range_nm"] <= me["weapon_nm"] else 1.0)
        return {"heading_cmd": heading, "speed_cmd": speed, "fire_target": fire_target}


def _my_side(obs: dict) -> str:
    # contacts에 아군이 섞일 수 있어 self 기준 추론이 어려우므로,
    # objective로 측 추정(transit/strike=red, 그 외=blue)은 부정확할 수 있다.
    # 안전하게: obs에 side 단서가 없으므로 적은 "contacts 중 다른 side"로 처리.
    # 여기서는 self의 side를 모를 때를 대비해 빈 문자열 반환(아래 enemies 필터가 != 로 동작).
    return obs.get("self", {}).get("side", "")


def make_policy(side: str, objective: str, transit_heading: float = 90.0) -> RuleBasedPolicy:
    return RuleBasedPolicy(objective=objective, transit_heading=transit_heading)
