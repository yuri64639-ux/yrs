<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; user-select: none; font-family: sans-serif; }
  body { margin: 0; background: #0b0f19; color: #fff; display: flex; justify-content: center; }
  #box { position: relative; width: 880px; height: 580px; border: 3px solid #1e293b; border-radius: 12px; overflow: hidden; background: #000; }
  canvas { display: block; width: 100%; height: 100%; }
  #garagem, #fim { position: absolute; inset: 0; background: rgba(11,15,25,0.95); display: flex; flex-direction: column; justify-content: space-between; padding: 20px; }
  #fim { display: none; justify-content: center; align-items: center; text-align: center; }
  h1 { text-align: center; color: #facc15; margin: 0; font-size: 30px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; flex: 1; margin: 12px 0; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; }
  .card h3 { margin: 0 0 8px; color: #38bdf8; font-size: 15px; }
  .ops { display: flex; gap: 6px; margin-bottom: 8px; }
  button { flex: 1; padding: 8px; background: #0f172a; color: #fff; border: 1px solid #475569; border-radius: 6px; cursor: pointer; font-weight: bold; }
  button.ativo { background: #0284c7; border-color: #7dd3fc; }
  .cor { width: 28px; height: 28px; border-radius: 50%; border: 2px solid #fff; cursor: pointer; }
  .cor.ativo { transform: scale(1.2); box-shadow: 0 0 8px #fff; }
  .bar { height: 8px; background: #0f172a; border-radius: 4px; overflow: hidden; margin: 4px 0 8px; }
  .fill { height: 100%; background: linear-gradient(90deg, #22c55e, #facc15); }
  #btn-play, .btn-re { flex: none; width: 100%; padding: 14px; background: #16a34a; font-size: 18px; border: none; }
  .btn-re { width: auto; padding: 12px 24px; background: #0284c7; }
</style>
</head>
<body>
<div id="box">
  <canvas id="c" width="880" height="580"></canvas>
  <div id="garagem">
    <h1>TOP GEAR: HORIZONTE TURBO</h1>
    <div class="grid">
      <div class="card">
        <h3>SEU SUPERCARRO</h3>
        <canvas id="prev" width="380" height="160" style="background:#0f172a;border-radius:8px;width:100%;height:160px"></canvas>
        <div>
          <small>VELOCIDADE: <b id="tv">285 KM/H</b></small><div class="bar"><div class="fill" id="bv" style="width:65%"></div></div>
          <small>ACELERAÇÃO: <b id="ta">70%</b></small><div class="bar"><div class="fill" id="ba" style="width:70%"></div></div>
          <small>FREIOS & GRIP: <b id="tf">65%</b></small><div class="bar"><div class="fill" id="bf" style="width:65%"></div></div>
        </div>
      </div>
      <div class="card">
        <h3>OFICINA DE PEÇAS</h3>
        <div>
          <small>MOTOR</small>
          <div class="ops">
            <button class="ativo" onclick="setOp('m',0,this)">V6</button>
            <button onclick="setOp('m',1,this)">V8 Turbo</button>
            <button onclick="setOp('m',2,this)">V12 Híbrido</button>
          </div>
          <small>FREIOS</small>
          <div class="ops">
            <button class="ativo" onclick="setOp('f',0,this)">Ventilado</button>
            <button onclick="setOp('f',1,this)">Cerâmica</button>
            <button onclick="setOp('f',2,this)">Carbono</button>
          </div>
          <small>RODAS</small>
          <div class="ops">
            <button class="ativo" onclick="setOp('r',0,this)">Prata</button>
            <button onclick="setOp('r',1,this)">Dourada</button>
            <button onclick="setOp('r',2,this)">Carbono</button>
          </div>
          <small>PINTURA</small>
          <div class="ops" style="gap:10px;margin-top:4px">
            <div class="cor ativo" style="background:#dc2626" onclick="setCor('#dc2626','#991b1b',this)"></div>
            <div class="cor" style="background:#2563eb" onclick="setCor('#2563eb','#1e40af',this)"></div>
            <div class="cor" style="background:#eab308" onclick="setCor('#eab308','#a16207',this)"></div>
            <div class="cor" style="background:#16a34a" onclick="setCor('#16a34a','#166534',this)"></div>
            <div class="cor" style="background:#9333ea" onclick="setCor('#9333ea','#581c87',this)"></div>
            <div class="cor" style="background:#f8fafc" onclick="setCor('#f8fafc','#94a3b8',this)"></div>
          </div>
        </div>
        <small style="color:#94a3b8">Setas/WASD: Dirigir | ESPAÇO: Nitro</small>
      </div>
    </div>
    <button id="btn-play" onclick="iniciar()">🏁 CORRER CONTRA 25 RIVAIS!</button>
  </div>
  <div id="fim">
    <h1 id="ftit" style="font-size:38px">FIM!</h1>
    <p id="fdesc" style="font-size:18px"></p>
    <button class="btn-re" onclick="voltar()">🔧 VOLTAR À OFICINA</button>
  </div>
</div>
<script>
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const pv = document.getElementById('prev'), pctx = pv.getContext('2d');
const ac = new (window.AudioContext || window.webkitAudioContext)();

function som(f, t, d, v = 0.1) {
  if (ac.state === 'suspended') ac.resume();
  const o = ac.createOscillator(), g = ac.createGain();
  o.type = t; o.frequency.setValueAtTime(f, ac.currentTime);
  g.gain.setValueAtTime(v, ac.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + d);
  o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + d);
}

const MOT = [{ v: 285, a: 0.75, c: 0.85 }, { v: 315, a: 0.95, c: 1.05 }, { v: 345, a: 1.15, c: 1.25 }];
const FRE = [{ f: 1.0, g: 0.95 }, { f: 1.4, g: 1.1 }, { f: 1.8, g: 1.25 }];
const ROD = [{ aro: '#cbd5e1', g: 1.0 }, { aro: '#facc15', g: 1.15 }, { aro: '#334155', g: 1.3 }];
let cfg = { m: 0, f: 0, r: 0, c1: '#dc2626', c2: '#991b1b' };

function setOp(k, i, b) {
  cfg[k] = i;
  [...b.parentElement.children].forEach(x => x.classList.remove('ativo'));
  b.classList.add('ativo'); som(440, 'triangle', 0.08); desenharPrev();
}

function setCor(c1, c2, el) {
  cfg.c1 = c1; cfg.c2 = c2;
  document.querySelectorAll('.cor').forEach(x => x.classList.remove('ativo'));
  el.classList.add('ativo'); som(520, 'sine', 0.08); desenharPrev();
}
function carro(g, cx, cy, esc, c1, c2, aro, inc, nitro, freio) {
  g.save(); g.translate(cx, cy); g.scale(esc, esc); const t = inc * 10;
  g.fillStyle = 'rgba(0,0,0,0.55)'; g.beginPath(); g.ellipse(0, 32, 80, 15, 0, 0, Math.PI * 2); g.fill();
  [-74, 50].forEach((rx, idx) => {
    g.fillStyle = '#111'; g.fillRect(rx + t * 0.4, 4, 24, 32);
    g.fillStyle = aro; g.fillRect(rx + t * 0.4 + (idx === 0 ? 2 : 18), 8, 4, 24);
  });
  if (nitro) {
    const l = 25 + Math.random() * 25;
    [-35, 35].forEach(ex => {
      g.fillStyle = '#38bdf8'; g.beginPath(); g.moveTo(ex - 8 + t * 0.5, 26); g.lineTo(ex + 8 + t * 0.5, 26); g.lineTo(ex + t * 0.5, 26 + l); g.fill();
    });
  }
  const gr = g.createLinearGradient(0, -15, 0, 25); gr.addColorStop(0, c1); gr.addColorStop(1, c2);
  g.fillStyle = gr; g.beginPath(); g.moveTo(-66 + t, -6); g.lineTo(66 + t, -6); g.lineTo(72 + t * 0.5, 22); g.lineTo(-72 + t * 0.5, 22); g.fill();
  g.fillStyle = '#1e293b'; g.beginPath(); g.moveTo(-42 + t * 1.3, -32); g.lineTo(42 + t * 1.3, -32); g.lineTo(54 + t, -6); g.lineTo(-54 + t, -6); g.fill();
  g.fillStyle = '#0f172a'; g.fillRect(-70 + t, -18, 140, 6);
  g.fillStyle = freio ? '#ff2a2a' : '#b91c1c'; g.fillRect(-60 + t * 0.7, 0, 36, 8); g.fillRect(24 + t * 0.7, 0, 36, 8);
  g.fillStyle = '#fff'; g.fillRect(-14 + t * 0.6, 5, 28, 10); g.restore();
}

function desenharPrev() {
  pctx.clearRect(0, 0, 380, 160); pctx.fillStyle = '#1e293b'; pctx.fillRect(0, 105, 380, 55);
  [70, 310].forEach(rx => {
    pctx.fillStyle = '#090d16'; pctx.beginPath(); pctx.arc(rx, 80, 26, 0, Math.PI * 2); pctx.fill();
    pctx.fillStyle = ROD[cfg.r].aro; pctx.beginPath(); pctx.arc(rx, 80, 17, 0, Math.PI * 2); pctx.fill();
  });
  carro(pctx, 190, 85, 1.3, cfg.c1, cfg.c2, ROD[cfg.r].aro, 0, false, false);
  const m = MOT[cfg.m], f = FRE[cfg.f], r = ROD[cfg.r];
  document.getElementById('tv').innerText = m.v + ' KM/H'; document.getElementById('bv').style.width = ((m.v - 220) / 140 * 100) + '%';
  const ap = Math.min(100, Math.round(m.a * 82)); document.getElementById('ta').innerText = ap + '%'; document.getElementById('ba').style.width = ap + '%';
  const fp = Math.min(100, Math.round((f.f + r.g) / 3.1 * 100)); document.getElementById('tf').innerText = fp + '%'; document.getElementById('bf').style.width = fp + '%';
}
let run = false, pos = 0, px = 0, vel = 0, comb = 100, nit = 3, tnit = 0, tempo = 0, trem = 0, segs = [], rivais = [], galoes = [], keys = {}, ult = 0;
const COMP = 4200;
window.onkeydown = e => { keys[e.code] = true; if (e.code === 'Space' && run && nit > 0 && tnit <= 0) { nit--; tnit = 2.5; som(200, 'sawtooth', 0.35); } };
window.onkeyup = e => { keys[e.code] = false; };

function iniciar() {
  document.getElementById('garagem').style.display = 'none'; document.getElementById('fim').style.display = 'none';
  pos = 0; px = 0; vel = 0; comb = 100; nit = 3; tnit = 0; tempo = 0; trem = 0; segs = []; rivais = []; galoes = [];
  let cur = 0;
  for (let i = 0; i < COMP; i++) {
    if (i % 120 === 0 && i > 100 && i < COMP - 200) cur = [-2.2, -1.4, 0, 1.4, 2.2][Math.floor(Math.random() * 5)];
    else if (i >= COMP - 200) cur = 0;
    segs.push({ c: cur, arv: i % 7 === 0 ? (Math.random() > 0.5 ? 1 : -1) : 0 });
  }
  const cols = [['#eab308', '#a16207'], ['#2563eb', '#1e40af'], ['#16a34a', '#166534'], ['#9333ea', '#581c87'], ['#f97316', '#9a3412'], ['#06b6d4', '#155e75']];
  for (let i = 1; i <= 25; i++) {
    const pc = cols[i % cols.length];
    rivais.push({ z: i * 155 + Math.random() * 35, x: Math.random() * 1.4 - 0.7, v: 160 + Math.random() * 85, c1: pc[0], c2: pc[1] });
  }
  for (let z = 650; z < COMP - 300; z += 650) galoes.push({ z, x: Math.random() * 1.2 - 0.6, ok: false });
  run = true; som(520, 'square', 0.2); ult = performance.now(); requestAnimationFrame(loop);
}

function voltar() { document.getElementById('fim').style.display = 'none'; document.getElementById('garagem').style.display = 'flex'; desenharPrev(); }
function fimJogo(win, p) {
  run = false; document.getElementById('ftit').innerText = win ? '🏆 BANDEIRADA FINAL!' : '⛽ PANE SECA!';
  document.getElementById('fdesc').innerText = win ? `Você chegou em ${p}º lugar de 26 carros (${tempo.toFixed(1)}s)!` : 'Acabou o combustível! Pegue os galões vermelhos na pista.';
  som(win ? 660 : 140, 'square', 0.35); document.getElementById('fim').style.display = 'flex';
}

function loop(now) {
  if (!run) return; const dt = Math.min(0.05, (now - ult) / 1000); ult = now;
  tempo += dt; const m = MOT[cfg.m], f = FRE[cfg.f], r = ROD[cfg.r];
  if (tnit > 0) tnit -= dt; const na = tnit > 0;
  const acel = keys['ArrowUp'] || keys['KeyW'], fre = keys['ArrowDown'] || keys['KeyS'];
  const esq = keys['ArrowLeft'] || keys['KeyA'], dir = keys['ArrowRight'] || keys['KeyD'];
  const vmax = m.v * (na ? 1.25 : 1);
  if (comb > 0) { vel += (acel || na) ? 115 * m.a * (na ? 1.6 : 1) * dt : -45 * dt; } else vel -= 70 * dt;
  if (fre) vel -= 185 * f.f * dt;
  if (Math.abs(px) > 1.05) { vel -= 110 * dt; if (vel > 50) trem = 3; }
  vel = Math.max(0, Math.min(vmax, vel));
  const seg = segs[Math.floor(pos) % segs.length];
  pos += (vel / 60) * dt * 28;
  px += (((esq ? -1 : 0) + (dir ? 1 : 0)) * 1.6 * f.g * r.g * Math.min(1, vel / 65) * dt) - (seg.c * (vel / 270) * 0.55 * dt);
  px = Math.max(-1.85, Math.min(1.85, px));
  if (vel > 5) comb = Math.max(0, comb - (0.75 + vel / 210) * m.c * (na ? 1.4 : 1) * dt);
  if (comb <= 0 && vel <= 2) return fimJogo(false, 26);
  for (let rv of rivais) {
    rv.z += (rv.v / 60) * dt * 28;
    if (rv.z - pos > 0 && rv.z - pos < 2.3 && Math.abs(rv.x - px) < 0.34) { vel *= 0.52; rv.z += 4.5; trem = 10; som(120, 'sawtooth', 0.2); }
  }
  for (let g of galoes) {
    if (!g.ok && g.z - pos > -1.5 && g.z - pos < 2.5 && Math.abs(g.x - px) < 0.36) { g.ok = true; comb = Math.min(100, comb + 35); som(680, 'sine', 0.2); }
  }
  if (trem > 0) trem--;
  if (pos >= COMP - 50) return fimJogo(true, rivais.filter(x => x.z > pos).length + 1);
  desenhar(); requestAnimationFrame(loop);
}
function desenhar() {
  const ox = trem > 0 ? (Math.random() - 0.5) * trem * 2 : 0, oy = trem > 0 ? (Math.random() - 0.5) * trem * 2 : 0, hor = 260 + oy;
  const gc = ctx.createLinearGradient(0, 0, 0, hor); gc.addColorStop(0, '#0f172a'); gc.addColorStop(0.6, '#1d4ed8'); gc.addColorStop(1, '#f97316');
  ctx.fillStyle = gc; ctx.fillRect(0, 0, 880, hor);
  ctx.fillStyle = '#fde047'; ctx.beginPath(); ctx.arc(440 + ox * 0.3, hor - 20, 42, 0, Math.PI * 2); ctx.fill();
  const lv = 580 - hor; let ca = 0, dc = 0, objs = [];
  for (let y = 579; y > hor; y--) {
    const dt = y - hor, z = (lv / dt) * 12, si = Math.floor(pos + z), s = segs[si % segs.length];
    ca += s.c * 0.0045; dc += ca; const esc = dt / lv, cen = 440 - (px * 330 * esc) + dc + ox, lp = 36 + 430 * esc, lz = lp * 0.11;
    const alt = Math.floor(si / 3) % 2 === 0, cheg = si >= COMP - 55 && si <= COMP - 48;
    ctx.fillStyle = alt ? '#15803d' : '#166534'; ctx.fillRect(0, y, 880, 1);
    ctx.fillStyle = alt ? '#ef4444' : '#f8fafc'; ctx.fillRect(cen - lp - lz, y, (lp + lz) * 2, 1);
    ctx.fillStyle = cheg ? (si % 2 === 0 ? '#fff' : '#111') : (alt ? '#334155' : '#1e293b'); ctx.fillRect(cen - lp, y, lp * 2, 1);
    if (alt) { ctx.fillStyle = '#f8fafc'; const fw = Math.max(1, 4 * esc); ctx.fillRect(cen - lp * 0.33 - fw, y, fw * 2, 1); ctx.fillRect(cen + lp * 0.33 - fw, y, fw * 2, 1); }
    if (s.arv !== 0) objs.push({ t: 'a', x: cen + s.arv * (lp + lz + 48 * esc), y, esc });
  }
  for (let rv of rivais) { const dz = rv.z - pos; if (dz > 1 && dz < 145) { const esc = Math.min(1.15, 12 / dz), ry = hor + lv * esc; if (ry > hor && ry < 580) objs.push({ t: 'r', x: 440 + (rv.x - px) * 330 * esc + ox, y: ry, esc, c1: rv.c1, c2: rv.c2 }); } }
  for (let g of galoes) { if (!g.ok) { const dz = g.z - pos; if (dz > 1 && dz < 145) { const esc = Math.min(1.15, 12 / dz), gy = hor + lv * esc; if (gy > hor && gy < 580) objs.push({ t: 'g', x: 440 + (g.x - px) * 330 * esc + ox, y: gy, esc }); } } }
  objs.sort((a, b) => a.y - b.y);
  for (let o of objs) {
    if (o.t === 'a') { const th = 85 * o.esc, tw = Math.max(2, 12 * o.esc); ctx.fillStyle = '#78350f'; ctx.fillRect(o.x - tw / 2, o.y - th / 2, tw, th / 2); ctx.fillStyle = '#14532d'; ctx.beginPath(); ctx.arc(o.x, o.y - th / 2, Math.max(4, 30 * o.esc), 0, Math.PI * 2); ctx.fill(); }
    else if (o.t === 'r') carro(ctx, o.x, o.y - 24 * o.esc, o.esc * 0.9, o.c1, o.c2, '#cbd5e1', 0, false, false);
    else { const gw = Math.max(6, 30 * o.esc), gh = Math.max(8, 40 * o.esc); ctx.fillStyle = '#ef4444'; ctx.fillRect(o.x - gw / 2, o.y - gh, gw, gh); ctx.fillStyle = '#facc15'; ctx.fillRect(o.x - gw / 4, o.y - gh - 4 * o.esc, gw / 2, 4 * o.esc); }
  }
  const dv = ((keys['ArrowLeft'] || keys['KeyA']) ? -1 : 0) + ((keys['ArrowRight'] || keys['KeyD']) ? 1 : 0);
  carro(ctx, 440 + ox, 500 + oy, 1.05, cfg.c1, cfg.c2, ROD[cfg.r].aro, dv, tnit > 0, keys['ArrowDown'] || keys['KeyS']);
  ctx.fillStyle = 'rgba(15,23,42,0.85)'; ctx.fillRect(0, 0, 880, 44);
  ctx.fillStyle = '#facc15'; ctx.font = 'bold 19px monospace'; ctx.fillText(`POS: ${rivais.filter(x => x.z > pos).length + 1}º/26`, 20, 28);
  ctx.fillStyle = '#fff'; ctx.fillText(`TEMPO: ${tempo.toFixed(1)}s`, 180, 28);
  ctx.fillStyle = '#38bdf8'; ctx.fillText(`PISTA: ${Math.min(100, Math.floor(pos / (COMP - 50) * 100))}%`, 370, 28);
  ctx.fillText('NITRO:', 550, 28); for (let i = 0; i < 3; i++) { ctx.fillStyle = i < nit ? '#38bdf8' : '#334155'; ctx.fillRect(625 + i * 30, 11, 22, 20); }
  ctx.fillStyle = 'rgba(15,23,42,0.85)'; ctx.fillRect(15, 525, 200, 40);
  ctx.fillStyle = '#334155'; ctx.fillRect(25, 545, 180, 12);
  ctx.fillStyle = comb > 35 ? '#22c55e' : (comb > 15 ? '#eab308' : '#ef4444'); ctx.fillRect(25, 545, 180 * (comb / 100), 12);
  ctx.fillStyle = '#fff'; ctx.font = 'bold 12px sans-serif'; ctx.fillText('COMBUSTÍVEL', 25, 539);
  ctx.fillStyle = 'rgba(15,23,42,0.85)'; ctx.fillRect(700, 525, 165, 40);
  ctx.fillStyle = '#facc15'; ctx.font = 'bold 22px monospace'; ctx.fillText(`${Math.floor(vel)} KM/H`, 715, 552);
}
desenharPrev();
</script>
</body>
</html>
