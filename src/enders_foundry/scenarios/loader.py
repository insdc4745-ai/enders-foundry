"""시나리오 로더/검증 (계약 4). MVP는 JSON(무의존). pyyaml 설치 시 .yaml 도 지원."""
from __future__ import annotations

import json
import os

_REQUIRED = ("name", "blue", "red")


def validate_scenario(sc: dict) -> list[str]:
    """검증 결과(문제 목록) 반환. 빈 리스트면 정상."""
    problems: list[str] = []
    for k in _REQUIRED:
        if k not in sc:
            problems.append(f"필수 필드 누락: {k}")
    for side in ("blue", "red"):
        for i, u in enumerate(sc.get(side, [])):
            for f in ("mmsi", "name", "lat", "lon", "heading", "speed"):
                if f not in u:
                    problems.append(f"{side}[{i}] 필드 누락: {f}")
    if not sc.get("blue"):
        problems.append("blue 유닛이 없습니다")
    if not sc.get("red"):
        problems.append("red 유닛이 없습니다")
    return problems


def load_scenario(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as f:
        if ext in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
            except ImportError as e:
                raise RuntimeError("yaml 시나리오는 pyyaml 설치가 필요합니다. JSON을 쓰세요.") from e
            sc = yaml.safe_load(f)
        else:
            sc = json.load(f)
    problems = validate_scenario(sc)
    if problems:
        raise ValueError("시나리오 검증 실패:\n  - " + "\n  - ".join(problems))
    return sc
