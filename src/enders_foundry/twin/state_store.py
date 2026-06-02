"""L4 — 디지털 트윈 상태 저장소 (계약 1).

Entity 상태 모델(AIS 호환 mmsi/lat/lon + 합성 교전 필드)과 SQLite 영속화.
mda-gotham vessels.db 스키마(mmsi/lat/lon/sog/cog/heading)와 호환되는 필드 사용.
"""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, field


@dataclass
class Entity:
    mmsi: int
    name: str
    side: str          # "blue" | "red"
    etype: str         # "destroyer" | "corvette" | "submarine" ...
    lat: float
    lon: float
    heading: float     # deg, 0=N, 시계방향
    speed: float       # knots
    hp: float = 100.0
    sensor_nm: float = 40.0   # 탐지 사거리 (합성)
    weapon_nm: float = 18.0   # 교전 사거리 (합성)
    reload: int = 0           # 재장전 잔여 step
    max_speed: float = 32.0

    @property
    def alive(self) -> bool:
        return self.hp > 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Entity":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known})


_SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    run_id TEXT, step INTEGER, mmsi INTEGER, name TEXT, side TEXT, etype TEXT,
    lat REAL, lon REAL, heading REAL, speed REAL, hp REAL,
    sensor_nm REAL, weapon_nm REAL, reload INTEGER, max_speed REAL
);
"""


class StateStore:
    """디지털 트윈 권위 상태의 SQLite 영속화 (Lv2~3: 초기/스냅샷 동기화)."""

    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.executescript(_SCHEMA)

    def save_snapshot(self, run_id: str, step: int, entities: list[Entity]) -> None:
        rows = [
            (run_id, step, e.mmsi, e.name, e.side, e.etype, e.lat, e.lon,
             e.heading, e.speed, e.hp, e.sensor_nm, e.weapon_nm, e.reload, e.max_speed)
            for e in entities
        ]
        self.conn.executemany(
            "INSERT INTO entities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows
        )
        self.conn.commit()

    def load_snapshot(self, run_id: str, step: int) -> list[Entity]:
        cur = self.conn.execute(
            "SELECT mmsi,name,side,etype,lat,lon,heading,speed,hp,sensor_nm,"
            "weapon_nm,reload,max_speed FROM entities WHERE run_id=? AND step=?",
            (run_id, step),
        )
        cols = ["mmsi", "name", "side", "etype", "lat", "lon", "heading", "speed",
                "hp", "sensor_nm", "weapon_nm", "reload", "max_speed"]
        return [Entity.from_dict(dict(zip(cols, r))) for r in cur.fetchall()]

    def close(self) -> None:
        self.conn.close()
