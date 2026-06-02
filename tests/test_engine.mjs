/* 엔진 포팅 검증: AI vs AI 30판 → 블루 승률이 Python 원본(0.867) 대역인지 확인 */
import { NavalEnv, RuleBasedPolicy } from '../game/engine.js';
import { SCENARIOS } from '../game/scenarios.js';

function runMatch(scn, seed) {
  const env = new NavalEnv();
  env.reset(seed, scn);
  const red = new RuleBasedPolicy('transit', scn.transit_heading);
  const blue = new RuleBasedPolicy('intercept', scn.transit_heading);
  let shots = 0, hits = 0;
  while (!env.isDone()) {
    const obs = env.observations();
    const actions = {};
    for (const e of Object.values(env.entities)) {
      if (e.hp <= 0) continue;
      actions[e.id] = (e.side === 'red' ? red : blue).act(obs[e.id]);
    }
    env.step(actions);
    for (const ev of env.events) { if (ev.type === 'fire') shots++; if (ev.type === 'hit') hits++; }
  }
  let res = env.result(); if (res === null) res = 'draw';
  return { res, steps: env.step_count, shots, hits };
}

for (const key of Object.keys(SCENARIOS)) {
  const scn = SCENARIOS[key];
  const w = { blue: 0, red: 0, draw: 0 };
  let totShots = 0, totHits = 0, totSteps = 0;
  for (let i = 0; i < 30; i++) {
    const m = runMatch(scn, scn.seed + i);
    w[m.res]++; totShots += m.shots; totHits += m.hits; totSteps += m.steps;
  }
  const wr = (w.blue / 30 * 100).toFixed(1);
  const hr = totShots ? (totHits / totShots * 100).toFixed(1) : '0';
  console.log(`${key}: blue ${w.blue} / red ${w.red} / draw ${w.draw}  | 블루승률 ${wr}%  명중률 ${hr}%  평균 ${(totSteps/30).toFixed(0)}스텝`);
}
