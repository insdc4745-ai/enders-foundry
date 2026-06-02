"""CLI 진입점: 시나리오 1판 실행 → 리플레이 JSONL + 메트릭 출력 + HTML 뷰어 생성.

사용:
  python -m enders_foundry.run_match scenarios/strait_intercept_01.json
옵션:
  --seed N         시드 오버라이드
  --runs N         N회 반복 실행하여 승률 통계 (리플레이는 마지막 판만 저장)
  --out DIR        산출 디렉토리 (기본 _workspace)
  --html PATH      HTML 뷰어 생성 경로
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# src 레이아웃 지원: 직접 실행 시 패키지 경로 보정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enders_foundry.eval.runner import run_match
from enders_foundry.scenarios.loader import load_scenario


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ender's Foundry — 워게임 1판 실행")
    p.add_argument("scenario")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--out", default="_workspace")
    p.add_argument("--html", default=None)
    args = p.parse_args(argv)

    sc = load_scenario(args.scenario)
    os.makedirs(args.out, exist_ok=True)

    wins = {"blue": 0, "red": 0, "draw": 0}
    last = None
    base_seed = args.seed if args.seed is not None else sc.get("seed", 42)
    for i in range(args.runs):
        res = run_match(sc, seed=base_seed + i)
        wins[res.winner] += 1
        last = res

    assert last is not None
    # 리플레이 저장 (마지막 판)
    replay_path = os.path.join(args.out, "replay.jsonl")
    with open(replay_path, "w", encoding="utf-8") as f:
        for frame in last.replay:
            f.write(json.dumps(frame, ensure_ascii=False) + "\n")

    summary = {
        "scenario": sc["name"], "runs": args.runs, "wins": wins,
        "blue_winrate": round(wins["blue"] / args.runs, 3),
        "last_match": last.metrics(),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.html:
        from enders_foundry.viz import write_html  # 지연 import
        write_html(args.html, sc, last.replay, summary)
        print(f"HTML 뷰어 생성: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
