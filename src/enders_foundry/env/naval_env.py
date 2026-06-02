"""L1 — 환경 코어 (계약 2/3). PettingZoo ParallelEnv 형태의 standalone 해군 교전 환경.

실 PettingZoo 의존 없이 동일한 reset/step 인터페이스를 제공 → 추후 pettingzoo.ParallelEnv로 교체 가능.
모든 난수는 시드 기반(random.Random)으로 캡슐화하여 결정적 재현성을 보장한다.
"""
from __future__ import annotations

import math
import random

from ..twin.state_store import Entity

NM_PER_DEG_LAT = 60.0


def bearing_range(a: Entity, b: Entity) -> tuple[float, float]:
    """a→b 의 (방위 deg 0=N, 거리 nm). 소면적 equirectangular 근사."""
    north_nm = (b.lat - a.lat) * NM_PER_DEG_LAT
    east_nm = (b.lon - a.lon) * NM_PER_DEG_LAT * math.cos(math.radians(a.lat))
    rng = math.hypot(north_nm, east_nm)
    brg = math.degrees(math.atan2(east_nm, north_nm)) % 360.0
    return brg, rng


def advance(e: Entity, dt_seconds: float) -> None:
    """현재 침로·속력으로 dt초 동안 위치를 전진(제자리 갱신)."""
    dist_nm = e.speed * (dt_seconds / 3600.0)
    rad = math.radians(e.heading)
    e.lat += dist_nm * math.cos(rad) / NM_PER_DEG_LAT
    coslat = max(math.cos(math.radians(e.lat)), 1e-6)
    e.lon += dist_nm * math.sin(rad) / (NM_PER_DEG_LAT * coslat)


def _turn_toward(current: float, target: float, max_turn: float = 20.0) -> float:
    """침로를 목표 방위로 최대 max_turn deg/step 만큼 회전."""
    diff = (target - current + 180.0) % 360.0 - 180.0
    diff = max(-max_turn, min(max_turn, diff))
    return (current + diff) % 360.0


class NavalWargameEnv:
    """블루/레드 부분관측 멀티에이전트 해군 교전 환경."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}   # agent_id("blue_0") -> Entity
        self.step_count = 0
        self.dt_seconds = 30.0
        self.max_steps = 400
        self.objectives = {"blue": "intercept", "red": "transit"}
        self.roe = "weapons_free"
        self._rng = random.Random(0)
        self.events: list[dict] = []   # 직전 step 이벤트 (리플레이용)

    @property
    def agents(self) -> list[str]:
        return [aid for aid, e in self.entities.items() if e.alive]

    # ---- 계약 2 ----
    def reset(self, seed: int, scenario: dict) -> dict:
        self._rng = random.Random(seed)
        self.step_count = 0
        self.dt_seconds = float(scenario.get("dt_seconds", 30))
        self.max_steps = int(scenario.get("max_steps", 400))
        self.objectives = scenario.get("objectives", {"blue": "intercept", "red": "transit"})
        self.roe = scenario.get("roe", "weapons_free")
        self.entities = {}
        for side in ("blue", "red"):
            for i, spec in enumerate(scenario.get(side, [])):
                spec = {**spec, "side": side}
                self.entities[f"{side}_{i}"] = Entity.from_dict(spec)
        self.events = []
        return self._observations()

    # ---- 계약 3 ----
    def _observations(self) -> dict:
        obs: dict[str, dict] = {}
        for aid, e in self.entities.items():
            if not e.alive:
                continue
            contacts = []
            for oid, o in self.entities.items():
                if oid == aid or not o.alive:
                    continue
                brg, rng = bearing_range(e, o)
                if rng <= e.sensor_nm:   # 부분관측: 센서 사거리 이내만
                    contacts.append({"mmsi": o.mmsi, "side": o.side, "etype": o.etype,
                                     "bearing_deg": round(brg, 1), "range_nm": round(rng, 2)})
            obs[aid] = {
                "self": {"mmsi": e.mmsi, "side": e.side, "lat": e.lat, "lon": e.lon,
                         "heading": e.heading, "speed": e.speed, "hp": e.hp,
                         "reload": e.reload, "weapon_nm": e.weapon_nm, "max_speed": e.max_speed},
                "contacts": contacts,
                "step": self.step_count,
                "objective": self.objectives.get(e.side, ""),
            }
        return obs

    # ---- 계약 2 (전이) ----
    def step(self, actions: dict) -> tuple[dict, dict, dict, dict, dict]:
        self.events = []
        rewards = {aid: 0.0 for aid in self.entities}

        # 1) 기동 (침로/속력 명령 적용 후 전진)
        for aid, e in self.entities.items():
            if not e.alive:
                continue
            act = actions.get(aid, {})
            if "heading_cmd" in act and act["heading_cmd"] is not None:
                e.heading = _turn_toward(e.heading, float(act["heading_cmd"]))
            if "speed_cmd" in act and act["speed_cmd"] is not None:
                e.speed = max(0.0, min(e.max_speed, float(act["speed_cmd"])))
            if e.reload > 0:
                e.reload -= 1
            advance(e, self.dt_seconds)

        # 2) 교전 (사격 → 명중 판정 → 피해)
        mmsi_index = {e.mmsi: (aid, e) for aid, e in self.entities.items()}
        for aid, e in self.entities.items():
            if not e.alive:
                continue
            act = actions.get(aid, {})
            tgt_mmsi = act.get("fire_target")
            if tgt_mmsi is None or e.reload > 0:
                continue
            if self.roe == "weapons_tight":
                continue
            if tgt_mmsi not in mmsi_index:
                continue
            taid, tgt = mmsi_index[tgt_mmsi]
            if not tgt.alive:
                continue
            _, rng = bearing_range(e, tgt)
            if rng > e.weapon_nm:
                continue
            # 명중 확률: 근거리일수록↑ (합성 모델), 0.15~0.9
            p_hit = max(0.15, min(0.9, 1.0 - rng / e.weapon_nm))
            hit = self._rng.random() < p_hit
            e.reload = 3
            ev = {"type": "fire", "src": e.mmsi, "dst": tgt.mmsi, "hit": hit,
                  "range_nm": round(rng, 2), "p_hit": round(p_hit, 2)}
            self.events.append(ev)
            if hit:
                dmg = 34.0
                tgt.hp = max(0.0, tgt.hp - dmg)
                rewards[aid] += dmg / 100.0
                rewards[taid] -= dmg / 100.0
                self.events.append({"type": "hit", "src": e.mmsi, "dst": tgt.mmsi, "dmg": dmg})
                if not tgt.alive:
                    rewards[aid] += 1.0
                    self.events.append({"type": "kill", "src": e.mmsi, "dst": tgt.mmsi})

        self.step_count += 1

        # 3) 종료 판정
        blue_alive = [e for e in self.entities.values() if e.side == "blue" and e.alive]
        red_alive = [e for e in self.entities.values() if e.side == "red" and e.alive]
        done = (not blue_alive) or (not red_alive) or (self.step_count >= self.max_steps)
        terminations = {aid: (not self.entities[aid].alive) or done for aid in self.entities}
        truncations = {aid: (self.step_count >= self.max_steps) for aid in self.entities}
        infos = {aid: {} for aid in self.entities}
        return self._observations(), rewards, terminations, truncations, infos

    def is_done(self) -> bool:
        blue_alive = any(e.side == "blue" and e.alive for e in self.entities.values())
        red_alive = any(e.side == "red" and e.alive for e in self.entities.values())
        return (not blue_alive) or (not red_alive) or (self.step_count >= self.max_steps)
