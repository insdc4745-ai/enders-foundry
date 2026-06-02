"""L1+평가 — 1판 실행 + 리플레이/메트릭 (계약 6).

같은 (seed, scenario)는 항상 같은 결과를 낸다(결정적 재현성).
리플레이는 step마다 한 줄의 dict(JSONL 직렬화 가능)로 누적된다 → HTML 뷰어가 소비.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..agents.rule_based import make_policy
from ..env.naval_env import NavalWargameEnv
from ..twin.state_store import StateStore


@dataclass
class MatchResult:
    winner: str
    steps: int
    blue_survivors: int
    red_survivors: int
    blue_hp_total: float
    red_hp_total: float
    shots: int
    hits: int
    replay: list = field(default_factory=list)

    def metrics(self) -> dict:
        d = self.__dict__.copy()
        d.pop("replay", None)
        d["hit_rate"] = round(self.hits / self.shots, 3) if self.shots else 0.0
        return d


def _winner(env: NavalWargameEnv) -> str:
    blue = sum(1 for e in env.entities.values() if e.side == "blue" and e.alive)
    red = sum(1 for e in env.entities.values() if e.side == "red" and e.alive)
    if red == 0 and blue > 0:
        return "blue"
    if blue == 0 and red > 0:
        return "red"
    if blue == 0 and red == 0:
        return "draw"
    # 시간 초과: red 목표가 transit이면 통과 성공으로 red 승, 아니면 잔존 전투력으로 판정
    if env.objectives.get("red") in ("transit", "strike"):
        return "red"
    bhp = sum(e.hp for e in env.entities.values() if e.side == "blue")
    rhp = sum(e.hp for e in env.entities.values() if e.side == "red")
    return "blue" if bhp >= rhp else "red"


def run_match(scenario: dict, seed: int | None = None,
              store: StateStore | None = None, run_id: str = "run") -> MatchResult:
    seed = scenario.get("seed", 42) if seed is None else seed
    env = NavalWargameEnv()
    obs = env.reset(seed, scenario)
    rng = random.Random(seed + 1000)

    transit_heading = float(scenario.get("transit_heading", 90.0))
    policies = {}
    for aid in env.entities:
        side = env.entities[aid].side
        obj = env.objectives.get(side, "intercept")
        policies[aid] = make_policy(side, obj, transit_heading)

    shots = hits = 0
    replay: list[dict] = []

    def snapshot(step: int, events: list[dict]) -> None:
        replay.append({
            "step": step,
            "entities": [e.to_dict() for e in env.entities.values()],
            "events": events,
        })
        if store is not None:
            store.save_snapshot(run_id, step, list(env.entities.values()))

    snapshot(0, [])
    while not env.is_done():
        actions = {aid: policies[aid].act(obs[aid], rng) for aid in env.agents}
        obs, rewards, term, trunc, info = env.step(actions)
        for ev in env.events:
            if ev["type"] == "fire":
                shots += 1
                if ev["hit"]:
                    hits += 1
        snapshot(env.step_count, list(env.events))

    blue = [e for e in env.entities.values() if e.side == "blue"]
    red = [e for e in env.entities.values() if e.side == "red"]
    return MatchResult(
        winner=_winner(env),
        steps=env.step_count,
        blue_survivors=sum(1 for e in blue if e.alive),
        red_survivors=sum(1 for e in red if e.alive),
        blue_hp_total=round(sum(e.hp for e in blue), 1),
        red_hp_total=round(sum(e.hp for e in red), 1),
        shots=shots, hits=hits, replay=replay,
    )
