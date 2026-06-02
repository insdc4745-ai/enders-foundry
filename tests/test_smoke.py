"""스모크 + 결정성 테스트 (qa-verifier 기준). 의존성 없이 stdlib만."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from enders_foundry.env.naval_env import NavalWargameEnv, bearing_range
from enders_foundry.eval.runner import run_match
from enders_foundry.scenarios.loader import load_scenario, validate_scenario
from enders_foundry.twin.state_store import Entity, StateStore

SCN = os.path.join(os.path.dirname(__file__), "..", "scenarios", "strait_intercept_01.json")


def test_entity_roundtrip():
    e = Entity(mmsi=1, name="x", side="blue", etype="destroyer",
               lat=34.0, lon=128.0, heading=90, speed=20)
    assert Entity.from_dict(e.to_dict()) == e


def test_state_store_roundtrip():
    s = StateStore(":memory:")
    e = Entity(mmsi=1, name="x", side="blue", etype="destroyer",
               lat=34.0, lon=128.0, heading=90, speed=20)
    s.save_snapshot("r", 0, [e])
    loaded = s.load_snapshot("r", 0)
    assert len(loaded) == 1 and loaded[0].mmsi == 1
    s.close()


def test_bearing_range_east():
    a = Entity(mmsi=1, name="a", side="blue", etype="x", lat=34.0, lon=128.0, heading=0, speed=0)
    b = Entity(mmsi=2, name="b", side="red", etype="x", lat=34.0, lon=128.5, heading=0, speed=0)
    brg, rng = bearing_range(a, b)
    assert 80 < brg < 100      # 동쪽
    assert rng > 0


def test_env_reset_step_smoke():
    sc = load_scenario(SCN)
    env = NavalWargameEnv()
    obs = env.reset(42, sc)
    assert len(obs) == 4
    for _ in range(5):
        actions = {aid: {"heading_cmd": None, "speed_cmd": None, "fire_target": None}
                   for aid in env.agents}
        obs, r, term, trunc, info = env.step(actions)


def test_scenario_validation_catches_missing():
    assert validate_scenario({"name": "x"})  # 문제 목록 비어있지 않음


def test_determinism_same_seed_same_winner():
    sc = load_scenario(SCN)
    r1 = run_match(sc, seed=7)
    r2 = run_match(sc, seed=7)
    assert r1.winner == r2.winner
    assert r1.steps == r2.steps
    assert r1.metrics() == r2.metrics()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("ALL SMOKE TESTS PASSED")
