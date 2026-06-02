/* ============================================================================
 * Ender's Foundry — 시뮬레이션 엔진 (JS 포팅)
 * src/enders_foundry/env/naval_env.py + agents/rule_based.py 의 충실한 1:1 포팅.
 * - 결정적 시드 RNG (mulberry32) 로 동일 시드 → 동일 전개 재현
 * - 부분관측(센서 사거리), 명중확률 모델, 재장전, 종료 판정 동일
 * 브라우저/Node 양쪽에서 import 가능 (ESM).
 * ========================================================================== */

export const NM_PER_DEG_LAT = 60.0;

/* ---- 결정적 RNG (Python random.Random 대체) ------------------------------ */
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ---- 기하 (naval_env.py) -------------------------------------------------- */
export function bearingRange(a, b) {
  const northNm = (b.lat - a.lat) * NM_PER_DEG_LAT;
  const eastNm = (b.lon - a.lon) * NM_PER_DEG_LAT * Math.cos((a.lat * Math.PI) / 180);
  const rng = Math.hypot(northNm, eastNm);
  let brg = (Math.atan2(eastNm, northNm) * 180) / Math.PI;
  brg = ((brg % 360) + 360) % 360;
  return { bearing: brg, range: rng };
}

export function advance(e, dtSeconds) {
  const distNm = e.speed * (dtSeconds / 3600.0);
  const rad = (e.heading * Math.PI) / 180;
  e.lat += (distNm * Math.cos(rad)) / NM_PER_DEG_LAT;
  const coslat = Math.max(Math.cos((e.lat * Math.PI) / 180), 1e-6);
  e.lon += (distNm * Math.sin(rad)) / (NM_PER_DEG_LAT * coslat);
}

export function turnToward(current, target, maxTurn = 20.0) {
  let diff = (((target - current + 180) % 360) + 360) % 360 - 180;
  diff = Math.max(-maxTurn, Math.min(maxTurn, diff));
  return (((current + diff) % 360) + 360) % 360;
}

/* ---- 엔티티 (state_store.Entity) ----------------------------------------- */
export function makeEntity(spec, side, idx) {
  return {
    id: `${side}_${idx}`,
    mmsi: spec.mmsi,
    name: spec.name,
    side,
    etype: spec.etype,
    lat: spec.lat,
    lon: spec.lon,
    heading: spec.heading,
    speed: spec.speed,
    hp: spec.hp ?? 100,
    maxHp: spec.hp ?? 100,
    sensor_nm: spec.sensor_nm ?? 40,
    weapon_nm: spec.weapon_nm ?? 18,
    reload: 0,
    max_speed: spec.max_speed ?? 32,
    trail: [],
  };
}
const alive = (e) => e.hp > 0;

/* ---- 환경 (NavalWargameEnv) ---------------------------------------------- */
export class NavalEnv {
  constructor() {
    this.entities = {};
    this.step_count = 0;
    this.dt_seconds = 30.0;
    this.max_steps = 400;
    this.objectives = { blue: 'intercept', red: 'transit' };
    this.roe = 'weapons_free';
    this._rng = mulberry32(0);
    this.events = [];
    this.transit_heading = 90.0;
  }

  reset(seed, scenario) {
    this._rng = mulberry32(seed);
    this.step_count = 0;
    this.dt_seconds = Number(scenario.dt_seconds ?? 30);
    this.max_steps = Number(scenario.max_steps ?? 400);
    this.objectives = scenario.objectives ?? { blue: 'intercept', red: 'transit' };
    this.roe = scenario.roe ?? 'weapons_free';
    this.transit_heading = Number(scenario.transit_heading ?? 90.0);
    this.entities = {};
    for (const side of ['blue', 'red']) {
      (scenario[side] ?? []).forEach((spec, i) => {
        this.entities[`${side}_${i}`] = makeEntity(spec, side, i);
      });
    }
    this.events = [];
    return this.observations();
  }

  get agents() {
    return Object.entries(this.entities).filter(([, e]) => alive(e)).map(([id]) => id);
  }

  observations() {
    const obs = {};
    for (const [aid, e] of Object.entries(this.entities)) {
      if (!alive(e)) continue;
      const contacts = [];
      for (const [oid, o] of Object.entries(this.entities)) {
        if (oid === aid || !alive(o)) continue;
        const { bearing, range } = bearingRange(e, o);
        if (range <= e.sensor_nm) {
          contacts.push({ mmsi: o.mmsi, side: o.side, etype: o.etype,
            bearing_deg: +bearing.toFixed(1), range_nm: +range.toFixed(2) });
        }
      }
      obs[aid] = {
        self: { mmsi: e.mmsi, side: e.side, lat: e.lat, lon: e.lon, heading: e.heading,
          speed: e.speed, hp: e.hp, reload: e.reload, weapon_nm: e.weapon_nm, max_speed: e.max_speed },
        contacts, step: this.step_count, objective: this.objectives[e.side] ?? '',
      };
    }
    return obs;
  }

  step(actions) {
    this.events = [];

    // 1) 기동
    for (const e of Object.values(this.entities)) {
      if (!alive(e)) continue;
      const act = actions[e.id] || {};
      if (act.heading_cmd != null) e.heading = turnToward(e.heading, Number(act.heading_cmd));
      if (act.speed_cmd != null) e.speed = Math.max(0, Math.min(e.max_speed, Number(act.speed_cmd)));
      if (e.reload > 0) e.reload -= 1;
      advance(e, this.dt_seconds);
      e.trail.push([e.lat, e.lon]);
      if (e.trail.length > 60) e.trail.shift();
    }

    // 2) 교전
    const mmsiIndex = {};
    for (const e of Object.values(this.entities)) mmsiIndex[e.mmsi] = e;
    for (const e of Object.values(this.entities)) {
      if (!alive(e)) continue;
      const act = actions[e.id] || {};
      const tgtMmsi = act.fire_target;
      if (tgtMmsi == null || e.reload > 0) continue;
      if (this.roe === 'weapons_tight') continue;
      const tgt = mmsiIndex[tgtMmsi];
      if (!tgt || !alive(tgt)) continue;
      const { range } = bearingRange(e, tgt);
      if (range > e.weapon_nm) continue;
      const pHit = Math.max(0.15, Math.min(0.9, 1.0 - range / e.weapon_nm));
      const hit = this._rng() < pHit;
      e.reload = 3;
      this.events.push({ type: 'fire', src: e.mmsi, dst: tgt.mmsi, hit,
        range_nm: +range.toFixed(2), p_hit: +pHit.toFixed(2) });
      if (hit) {
        const dmg = 34.0;
        tgt.hp = Math.max(0, tgt.hp - dmg);
        this.events.push({ type: 'hit', src: e.mmsi, dst: tgt.mmsi, dmg });
        if (!alive(tgt)) this.events.push({ type: 'kill', src: e.mmsi, dst: tgt.mmsi });
      }
    }

    this.step_count += 1;
    return this.observations();
  }

  isDone() {
    const blueAlive = Object.values(this.entities).some((e) => e.side === 'blue' && alive(e));
    const redAlive = Object.values(this.entities).some((e) => e.side === 'red' && alive(e));
    return !blueAlive || !redAlive || this.step_count >= this.max_steps;
  }

  result() {
    const blueAlive = Object.values(this.entities).filter((e) => e.side === 'blue' && alive(e));
    const redAlive = Object.values(this.entities).filter((e) => e.side === 'red' && alive(e));
    if (!redAlive.length && blueAlive.length) return 'blue';
    if (!blueAlive.length && redAlive.length) return 'red';
    if (!blueAlive.length && !redAlive.length) return 'draw';
    return null; // 진행 중 / 시간초과 시 호출부에서 처리
  }
}

/* ---- 규칙기반 정책 (rule_based.py) --------------------------------------- */
export class RuleBasedPolicy {
  constructor(objective, transitHeading = 90.0) {
    this.objective = objective;
    this.transit_heading = transitHeading;
  }
  act(obs) {
    const me = obs.self;
    const mySide = me.side;
    const enemies = obs.contacts.filter((c) => c.side !== mySide);
    if (!enemies.length) {
      const heading = ['transit', 'strike'].includes(this.objective) ? this.transit_heading : me.heading;
      return { heading_cmd: heading, speed_cmd: me.max_speed, fire_target: null };
    }
    const nearest = enemies.reduce((a, b) => (a.range_nm <= b.range_nm ? a : b));
    let fireTarget = null;
    if (nearest.range_nm <= me.weapon_nm && me.reload === 0) fireTarget = nearest.mmsi;

    if (['transit', 'strike'].includes(this.objective)) {
      const heading = nearest.range_nm <= me.weapon_nm
        ? this.transit_heading
        : (this.transit_heading + 15.0) % 360.0;
      return { heading_cmd: heading, speed_cmd: me.max_speed, fire_target: fireTarget };
    }
    const heading = nearest.bearing_deg;
    const speed = me.max_speed * (nearest.range_nm <= me.weapon_nm ? 0.6 : 1.0);
    return { heading_cmd: heading, speed_cmd: speed, fire_target: fireTarget };
  }
}
