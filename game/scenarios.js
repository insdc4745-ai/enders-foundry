/* 시나리오 데이터 (scenarios/*.json 임베드 — file:// 에서도 CORS 없이 동작) */
export const SCENARIOS = {
  strait_intercept_01: {
    name: 'strait_intercept_01',
    description: '난이도 1 — 해협 통과를 시도하는 적 코르벳 2척을, 아군 구축함 2척이 요격. (합성 파라미터, 비공식 연구·교육용)',
    seed: 42, dt_seconds: 30, max_steps: 400, difficulty: 1, roe: 'weapons_free', transit_heading: 90.0,
    objectives: { blue: 'intercept', red: 'transit' },
    blue: [
      { mmsi: 440100001, name: 'ROKS-Eastern', etype: 'destroyer', lat: 34.30, lon: 128.30, heading: 270, speed: 28, hp: 100, sensor_nm: 45, weapon_nm: 20, max_speed: 30 },
      { mmsi: 440100002, name: 'ROKS-Southern', etype: 'destroyer', lat: 34.12, lon: 128.36, heading: 270, speed: 28, hp: 100, sensor_nm: 45, weapon_nm: 20, max_speed: 30 },
    ],
    red: [
      { mmsi: 412900001, name: 'OPFOR-Alpha', etype: 'corvette', lat: 34.26, lon: 127.80, heading: 90, speed: 30, hp: 80, sensor_nm: 35, weapon_nm: 16, max_speed: 32 },
      { mmsi: 412900002, name: 'OPFOR-Bravo', etype: 'corvette', lat: 34.08, lon: 127.86, heading: 90, speed: 30, hp: 80, sensor_nm: 35, weapon_nm: 16, max_speed: 32 },
    ],
  },
  strait_intercept_02: {
    name: 'strait_intercept_02',
    description: '난이도 2 — 적 코르벳 3척(고속)이 분산 통과 시도, 아군 구축함 2척이 요격(수적 열세). 합성 파라미터.',
    seed: 42, dt_seconds: 30, max_steps: 400, difficulty: 2, roe: 'weapons_free', transit_heading: 90.0,
    objectives: { blue: 'intercept', red: 'transit' },
    blue: [
      { mmsi: 440100001, name: 'ROKS-Eastern', etype: 'destroyer', lat: 34.30, lon: 128.30, heading: 270, speed: 28, hp: 100, sensor_nm: 45, weapon_nm: 20, max_speed: 30 },
      { mmsi: 440100002, name: 'ROKS-Southern', etype: 'destroyer', lat: 34.10, lon: 128.36, heading: 270, speed: 28, hp: 100, sensor_nm: 45, weapon_nm: 20, max_speed: 30 },
    ],
    red: [
      { mmsi: 412900001, name: 'OPFOR-Alpha', etype: 'corvette', lat: 34.30, lon: 127.78, heading: 90, speed: 34, hp: 80, sensor_nm: 35, weapon_nm: 16, max_speed: 36 },
      { mmsi: 412900002, name: 'OPFOR-Bravo', etype: 'corvette', lat: 34.18, lon: 127.82, heading: 90, speed: 34, hp: 80, sensor_nm: 35, weapon_nm: 16, max_speed: 36 },
      { mmsi: 412900003, name: 'OPFOR-Charlie', etype: 'corvette', lat: 34.04, lon: 127.80, heading: 90, speed: 34, hp: 80, sensor_nm: 35, weapon_nm: 16, max_speed: 36 },
    ],
  },
};
