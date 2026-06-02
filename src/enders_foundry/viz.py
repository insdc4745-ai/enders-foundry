"""HTML 실행 레이아웃 뷰어 생성.

리플레이 데이터를 자체 포함(self-contained) HTML로 굽는다. 인터넷/타일 서버 없이
브라우저에서 바로 열어 블루/레드 전술 상황도를 재생할 수 있다(HTML5 canvas 전술 플롯).
디지털 트윈 워게임 "실행 레이아웃": 좌측 전술상황도 + 우측 패널(시나리오/메트릭/이벤트로그/난이도).
"""
from __future__ import annotations

import json


def write_html(path: str, scenario: dict, replay: list[dict], summary: dict) -> None:
    data = {"scenario": scenario, "replay": replay, "summary": summary}
    payload = json.dumps(data, ensure_ascii=False)
    html = _TEMPLATE.replace("/*__DATA__*/", payload)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<title>Ender's Foundry — 디지털 트윈 해군 워게임 실행 레이아웃</title>
<style>
  :root{--blue:#3b9dff;--red:#ff5a5a;--bg:#0a0e16;--panel:#121826;--line:#1f2a3d;--txt:#cfe0f5;--mut:#7c8aa5;}
  *{box-sizing:border-box;font-family:'Segoe UI',system-ui,sans-serif;}
  body{margin:0;background:var(--bg);color:var(--txt);}
  header{padding:10px 16px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;}
  header h1{font-size:16px;margin:0;letter-spacing:.5px;}
  header .tag{font-size:11px;color:var(--mut);border:1px solid var(--line);padding:2px 8px;border-radius:10px;}
  .wrap{display:grid;grid-template-columns:1fr 340px;gap:0;height:calc(100vh - 49px);}
  .stage{position:relative;background:radial-gradient(circle at 30% 30%,#0e1726,#070a11);}
  canvas{display:block;width:100%;height:100%;}
  .panel{border-left:1px solid var(--line);background:var(--panel);overflow-y:auto;padding:14px;}
  .card{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:12px;}
  .card h2{font-size:12px;margin:0 0 8px;color:var(--mut);text-transform:uppercase;letter-spacing:1px;}
  .kv{display:flex;justify-content:space-between;font-size:13px;padding:2px 0;}
  .kv b{font-weight:600;}
  .blue{color:var(--blue);} .red{color:var(--red);}
  .bar{height:6px;border-radius:3px;background:#223;overflow:hidden;margin-top:3px;}
  .bar>i{display:block;height:100%;}
  .log{font-size:12px;line-height:1.5;max-height:220px;overflow-y:auto;}
  .log div{padding:1px 0;border-bottom:1px dashed #1a2333;}
  .controls{display:flex;align-items:center;gap:10px;padding:8px 16px;border-top:1px solid var(--line);background:var(--panel);}
  .controls button{background:#1b2638;color:var(--txt);border:1px solid var(--line);border-radius:6px;padding:6px 14px;cursor:pointer;}
  .controls button:hover{background:#26344c;}
  input[type=range]{flex:1;}
  .winner{font-size:14px;font-weight:700;}
  .diff{display:flex;gap:4px;margin-top:4px;}
  .diff span{flex:1;height:6px;border-radius:3px;background:#223;}
  .diff span.on{background:#f5b942;}
</style>
</head>
<body>
<header>
  <h1>⚓ Ender's Foundry</h1>
  <span class="tag">디지털 트윈 해군 워게임</span>
  <span class="tag">비공식 연구·교육용 합성 시뮬</span>
  <span class="tag" id="scnName"></span>
</header>
<div class="wrap">
  <div class="stage"><canvas id="cv"></canvas></div>
  <div class="panel">
    <div class="card"><h2>전투 결과</h2><div id="result"></div></div>
    <div class="card"><h2>전력 (잔존 HP)</h2><div id="forces"></div></div>
    <div class="card"><h2>메트릭</h2><div id="metrics"></div></div>
    <div class="card"><h2>난이도 커리큘럼</h2>
      <div class="kv"><span>등급</span><b id="diffLv"></b></div>
      <div class="diff" id="diffBar"></div>
    </div>
    <div class="card"><h2>교전 이벤트 로그</h2><div class="log" id="log"></div></div>
  </div>
</div>
<div class="controls">
  <button id="play">▶ 재생</button>
  <button id="reset">⟲ 처음</button>
  <input type="range" id="seek" min="0" value="0"/>
  <span id="stepLbl" style="font-variant-numeric:tabular-nums;color:var(--mut);"></span>
</div>
<script>
const D = /*__DATA__*/;
const scn = D.scenario, replay = D.replay, sum = D.summary;
document.getElementById('scnName').textContent = scn.name;

// 좌표 경계 계산 (모든 프레임의 모든 엔티티)
let lats=[],lons=[];
replay.forEach(f=>f.entities.forEach(e=>{lats.push(e.lat);lons.push(e.lon);}));
const pad=0.05;
const minLat=Math.min(...lats)-pad,maxLat=Math.max(...lats)+pad;
const minLon=Math.min(...lons)-pad,maxLon=Math.max(...lons)+pad;

const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
function resize(){cv.width=cv.clientWidth;cv.height=cv.clientHeight;draw(cur);}
function X(lon){return (lon-minLon)/(maxLon-minLon)*cv.width;}
function Y(lat){return (1-(lat-minLat)/(maxLat-minLat))*cv.height;}

let cur=0,playing=false;
const seek=document.getElementById('seek');seek.max=replay.length-1;

function drawGrid(){
  ctx.fillStyle='#070a11';ctx.fillRect(0,0,cv.width,cv.height);
  ctx.strokeStyle='#13202f';ctx.lineWidth=1;
  for(let i=0;i<=8;i++){let x=cv.width*i/8;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,cv.height);ctx.stroke();
    let y=cv.height*i/8;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(cv.width,y);ctx.stroke();}
  ctx.fillStyle='#2a3a52';ctx.font='10px monospace';
  ctx.fillText(minLat.toFixed(2)+'N '+minLon.toFixed(2)+'E',6,cv.height-6);
  ctx.fillText(maxLat.toFixed(2)+'N '+maxLon.toFixed(2)+'E',cv.width-130,14);
}
function unit(e){
  const x=X(e.lon),y=Y(e.lat),col=e.side==='blue'?'#3b9dff':'#ff5a5a';
  // 센서 링
  const sensorPx=(e.sensor_nm/60)/(maxLat-minLat)*cv.height;
  ctx.beginPath();ctx.arc(x,y,sensorPx,0,7);ctx.strokeStyle=col+'22';ctx.stroke();
  // 무장 링
  const wpx=(e.weapon_nm/60)/(maxLat-minLat)*cv.height;
  ctx.beginPath();ctx.arc(x,y,wpx,0,7);ctx.strokeStyle=col+'44';ctx.setLineDash([3,3]);ctx.stroke();ctx.setLineDash([]);
  // 함정 삼각형 (침로 방향)
  if(e.hp>0){
    const a=(e.heading-90)*Math.PI/180;
    ctx.save();ctx.translate(x,y);ctx.rotate(a);
    ctx.beginPath();ctx.moveTo(9,0);ctx.lineTo(-6,-6);ctx.lineTo(-6,6);ctx.closePath();
    ctx.fillStyle=col;ctx.fill();ctx.restore();
    ctx.fillStyle='#cfe0f5';ctx.font='10px monospace';ctx.fillText(e.name,x+10,y-8);
    // HP 바
    ctx.fillStyle='#223';ctx.fillRect(x-12,y+10,24,3);
    ctx.fillStyle=col;ctx.fillRect(x-12,y+10,24*e.hp/100,3);
  }else{
    ctx.strokeStyle='#555';ctx.beginPath();ctx.moveTo(x-6,y-6);ctx.lineTo(x+6,y+6);
    ctx.moveTo(x+6,y-6);ctx.lineTo(x-6,y+6);ctx.stroke();
  }
}
function draw(i){
  if(!replay.length)return;
  const f=replay[i];drawGrid();
  // 교전선
  const byId={};f.entities.forEach(e=>byId[e.mmsi]=e);
  (f.events||[]).forEach(ev=>{
    if(ev.type==='fire'){const s=byId[ev.src],t=byId[ev.dst];if(s&&t){
      ctx.beginPath();ctx.moveTo(X(s.lon),Y(s.lat));ctx.lineTo(X(t.lon),Y(t.lat));
      ctx.strokeStyle=ev.hit?'#ffd24a':'#ffffff33';ctx.lineWidth=ev.hit?2:1;ctx.stroke();ctx.lineWidth=1;}}
  });
  f.entities.forEach(unit);
  document.getElementById('stepLbl').textContent='STEP '+f.step+' / '+(replay.length-1)+'  (T+'+Math.round(f.step*(scn.dt_seconds||30)/60)+'min)';
  seek.value=i;
  renderForces(f);renderLog(i);
}
function renderForces(f){
  let h='';['blue','red'].forEach(side=>{
    f.entities.filter(e=>e.side===side).forEach(e=>{
      const col=side==='blue'?'blue':'red';
      h+=`<div class="kv"><span class="${col}">${e.name}</span><b>${e.hp.toFixed(0)} HP</b></div>`;
      h+=`<div class="bar"><i style="width:${e.hp}%;background:var(--${col})"></i></div>`;
    });
  });
  document.getElementById('forces').innerHTML=h;
}
function renderLog(i){
  let h='';for(let k=0;k<=i;k++){(replay[k].events||[]).forEach(ev=>{
    if(ev.type==='fire')h+=`<div>[${replay[k].step}] 🔥 ${ev.src} → ${ev.dst} (${ev.range_nm}nm, p=${ev.p_hit}) ${ev.hit?'<span style="color:#ffd24a">명중</span>':'빗나감'}</div>`;
    if(ev.type==='kill')h+=`<div>[${replay[k].step}] 💥 <b>${ev.dst} 격침</b> (by ${ev.src})</div>`;
  });}
  const el=document.getElementById('log');el.innerHTML=h;el.scrollTop=el.scrollHeight;
}
// 결과/메트릭/난이도 패널
(function(){
  const m=sum.last_match, wc={blue:'blue',red:'red',draw:''}[m.winner]||'';
  document.getElementById('result').innerHTML=
    `<div class="winner ${wc}">승자: ${m.winner.toUpperCase()}</div>`+
    `<div class="kv"><span>진행 step</span><b>${m.steps}</b></div>`+
    `<div class="kv"><span>blue 승률(${sum.runs}판)</span><b>${(sum.blue_winrate*100).toFixed(0)}%</b></div>`;
  document.getElementById('metrics').innerHTML=
    `<div class="kv"><span>생존 (blue/red)</span><b>${m.blue_survivors} / ${m.red_survivors}</b></div>`+
    `<div class="kv"><span>잔존 HP (blue/red)</span><b>${m.blue_hp_total} / ${m.red_hp_total}</b></div>`+
    `<div class="kv"><span>사격 / 명중</span><b>${m.shots} / ${m.hits}</b></div>`+
    `<div class="kv"><span>명중률</span><b>${(m.hit_rate*100).toFixed(0)}%</b></div>`;
  const lv=scn.difficulty||1;document.getElementById('diffLv').textContent='Lv '+lv+' / 5';
  let db='';for(let i=1;i<=5;i++)db+=`<span class="${i<=lv?'on':''}"></span>`;
  document.getElementById('diffBar').innerHTML=db;
})();
// 컨트롤
document.getElementById('play').onclick=function(){playing=!playing;this.textContent=playing?'⏸ 일시정지':'▶ 재생';tick();};
document.getElementById('reset').onclick=()=>{cur=0;playing=false;document.getElementById('play').textContent='▶ 재생';draw(0);};
seek.oninput=()=>{cur=+seek.value;draw(cur);};
function tick(){if(!playing)return;cur++;if(cur>=replay.length){cur=replay.length-1;playing=false;document.getElementById('play').textContent='▶ 재생';return;}draw(cur);setTimeout(tick,180);}
window.addEventListener('resize',resize);resize();draw(0);
</script>
</body>
</html>
"""
