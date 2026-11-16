import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="EM Pato Donald - Mundo da Escola",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        .block-container { padding: 0 !important; max-width: 100% !important; }
        iframe { width: 100% !important; height: 98vh !important; border: none !important; display: block !important; }
    </style>
""", unsafe_allow_html=True)

html_escola = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Comic Sans MS', sans-serif; overflow: hidden; user-select: none; touch-action: none; }
        #cenario { width: 100%; height: 100%; background: linear-gradient(to bottom, #4FC3F7 0%, #B3E5FC 48%, #E6B88A 48%, #689F38 60%, #33691E 100%); display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 12px; position: relative; transition: background 0.8s; }
        #noite { position: absolute; inset: 0; background: linear-gradient(to bottom, rgba(7,13,38,0.86) 0%, rgba(15,25,65,0.62) 60%, rgba(5,10,25,0.52) 100%); opacity: 0; pointer-events: none; z-index: 2; transition: opacity 0.8s; }
        #cenario.noite #noite { opacity: 1; }
        #cenario.noite .janela { fill: #FFF176; filter: drop-shadow(0 0 10px #FFEE58); }
        .estrela { position: absolute; background: #FFFDE7; border-radius: 50%; box-shadow: 0 0 8px #FFF; animation: piscar 1.5s infinite alternate; }
        .vagalume { position: absolute; width: 6px; height: 6px; background: #C6FF00; border-radius: 50%; box-shadow: 0 0 12px #AEEA00; animation: voarVL 3.2s infinite alternate ease-in-out; }
        @keyframes piscar { 0% { opacity: 0.2; } 100% { opacity: 1; } }
        @keyframes voarVL { 0% { transform: translate(0,0) scale(0.8); } 100% { transform: translate(28px,-22px) scale(1.3); } }
        .ceu { position: absolute; top: 8%; left: 0; width: 100%; display: flex; justify-content: space-around; z-index: 5; pointer-events: none; }
        .item-ceu { font-size: clamp(40px, 7.5vw, 60px); cursor: pointer; pointer-events: auto; display: inline-block; }
        .nuvem { animation: flutuarNuvem 4.5s infinite alternate ease-in-out; }
        @keyframes flutuarNuvem { 0% { transform: translateX(-12px); } 100% { transform: translateX(12px); } }
        .escola-box { position: absolute; top: 22%; left: 3%; width: clamp(190px, 32vw, 280px); cursor: pointer; z-index: 5; transition: transform 0.2s; filter: drop-shadow(0 6px 10px rgba(0,0,0,0.3)); }
        .escola-box:hover { transform: scale(1.04); }
        .aviso-sala { position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%); background: #FFD700; color: #003366; border: 2px solid #003366; border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: bold; white-space: nowrap; }
        .piscina { position: absolute; bottom: 13%; right: 4%; width: clamp(180px, 36vw, 290px); height: clamp(88px, 17vw, 135px); background: #ECEFF1; border: 5px solid #90A4AE; border-radius: 22px; padding: 5px; z-index: 3; pointer-events: none; box-shadow: 0 6px 14px rgba(0,0,0,0.25); }
        .agua-piscina { width: 100%; height: 100%; background: linear-gradient(to bottom, #4FC3F7, #0288D1); border-radius: 14px; display: flex; align-items: flex-end; justify-content: space-between; padding: 4px 10px; color: white; font-weight: bold; font-size: 13px; }
        .arvores { position: absolute; top: 37%; left: 0; width: 100%; display: flex; justify-content: space-around; z-index: 4; pointer-events: none; }
        .arvore { font-size: clamp(46px, 9vw, 74px); cursor: pointer; pointer-events: auto; }
        .placa { background: #FFD700; color: #003366; border: 3px solid #003366; padding: 6px 16px; border-radius: 14px; font-size: clamp(13px, 3vw, 18px); font-weight: bold; z-index: 15; }
        .ator { position: absolute; font-size: 48px; cursor: grab; z-index: 20; touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3)); }
        .ator.brinquedo { z-index: 18; }
        .ator:active { cursor: grabbing; z-index: 30; }
        .corpo { display: inline-block; pointer-events: none; position: relative; }
        .balao { position: absolute; top: -30px; left: 50%; transform: translateX(-50%); background: white; border: 2px solid #003366; border-radius: 12px; padding: 1px 6px; font-size: 15px; box-shadow: 0 3px 6px rgba(0,0,0,0.25); pointer-events: none; animation: pulsar 1s infinite alternate; }
        @keyframes pulsar { 0% { transform: translateX(-50%) scale(0.95); } 100% { transform: translateX(-50%) scale(1.1); } }
        .nadando::after { content: ''; position: absolute; bottom: 0; left: -4px; right: -4px; height: 42%; background: linear-gradient(to bottom, rgba(129,212,250,0.55), rgba(2,136,209,0.78)); border-top: 2px solid #FFF; border-radius: 0 0 14px 14px; pointer-events: none; }
        .nadando .corpo { animation: boiar 1s infinite alternate ease-in-out; }
        .balancando .corpo { transform-origin: top center; animation: balancar 0.8s infinite alternate ease-in-out; }
        .gangorra .corpo { animation: gangorrar 0.85s infinite alternate ease-in-out; }
        .quicar .corpo { animation: quicarBola 0.6s ease-out; }
        @keyframes boiar { 0% { transform: translateY(-3px) rotate(-4deg); } 100% { transform: translateY(4px) rotate(4deg); } }
        @keyframes balancar { 0% { transform: rotate(-22deg) translateX(-10px); } 100% { transform: rotate(22deg) translateX(10px); } }
        @keyframes gangorrar { 0% { transform: translateY(-14px) rotate(-8deg); } 100% { transform: translateY(10px) rotate(8deg); } }
        @keyframes quicarBola { 0%, 100% { transform: translateY(0); } 45% { transform: translateY(-42px) rotate(180deg); } }
        .particula { position: absolute; font-size: 22px; pointer-events: none; z-index: 35; animation: subirP 1.4s ease-out forwards; }
        @keyframes subirP { 0% { opacity: 1; } 100% { transform: translateY(-55px) scale(0.7); opacity: 0; } }
        #barra { background: rgba(255,255,255,0.95); padding: 8px 12px; border-radius: 22px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 25; display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
        .btn { font-size: 24px; border: 2px solid #FFD700; background: #FFF8DC; border-radius: 14px; padding: 4px 8px; cursor: pointer; }
        .btn-cmd { font-size: 14px; font-weight: bold; border: none; border-radius: 14px; padding: 8px 11px; cursor: pointer; }
    </style>
</head>
"""
html_escola += """
<body>
<div id="cenario">
    <div id="noite"></div>
    <div class="ceu">
        <span class="item-ceu" onclick="diaNoite(this)">☀️</span>
        <span class="item-ceu nuvem" onclick="nuvem(this, '💧')">☁️</span>
        <span class="item-ceu nuvem" style="animation-delay:1.5s;" onclick="nuvem(this, '🕊️')">☁️</span>
    </div>
    <div class="escola-box" onclick="abrirSala()">
        <svg viewBox="0 0 360 195" width="100%" height="100%">
            <polygon points="10,65 180,15 350,65" fill="#D62828" stroke="#8D0801" stroke-width="3"/>
            <rect x="25" y="65" width="310" height="105" fill="#1E88E5" stroke="#0D47A1" stroke-width="3"/>
            <rect x="45" y="72" width="270" height="24" rx="4" fill="#FFD700" stroke="#003366" stroke-width="2"/>
            <text x="180" y="88" font-family="Comic Sans MS" font-size="13" font-weight="bold" fill="#003366" text-anchor="middle">EM PATO DONALD</text>
            <rect x="155" y="115" width="50" height="55" rx="3" fill="#FFD700" stroke="#003366" stroke-width="2"/>
            <rect class="janela" x="55" y="110" width="45" height="35" rx="3" fill="#E3F2FD" stroke="#003366" stroke-width="2"/>
            <rect class="janela" x="260" y="110" width="45" height="35" rx="3" fill="#E3F2FD" stroke="#003366" stroke-width="2"/>
        </svg>
        <div class="aviso-sala">🚪 Entrar na Sala</div>
    </div>
    <div id="piscina" class="piscina"><div class="agua-piscina"><span>🛟</span><span>🏊 Piscina</span></div></div>
    <div class="arvores">
        <span class="arvore" onclick="particulas(this,'🍃');som(520,880,0.2)">🌳</span>
        <span class="arvore" onclick="particulas(this,'🍎');som(520,880,0.2)">🌲</span>
        <span class="arvore" onclick="particulas(this,'🍃');som(520,880,0.2)">🌳</span>
    </div>
    <div id="sala" style="display:none; position:absolute; inset:0; background:linear-gradient(to bottom, #FFF8E1 0%, #FFE082 78%, #8D6E63 78%, #5D4037 100%); z-index:50; flex-direction:column; justify-content:space-between; align-items:center; padding:10px;">
        <div style="width:100%; display:flex; justify-content:space-between; align-items:center;">
            <button onclick="document.getElementById('sala').style.display='none'" style="background:#FF5252; color:white; border:2px solid white; border-radius:14px; padding:6px 12px; font-weight:bold; cursor:pointer;">⬅️ Pátio</button>
            <div style="background:#FFD700; color:#003366; border:3px solid #003366; border-radius:14px; padding:4px 12px; font-weight:bold;">👩‍🏫 Sala - EM Pato Donald</div>
            <button onclick="limparLousa()" style="background:#1565C0; color:white; border:2px solid white; border-radius:14px; padding:6px 12px; font-weight:bold; cursor:pointer;">🧽 Apagar</button>
        </div>
        <div style="position:relative; width:94%; height:64%; background:#1B5E20; border:10px solid #6D4C41; border-radius:16px; overflow:hidden;">
            <canvas id="lousa" style="width:100%; height:100%; display:block; cursor:crosshair; touch-action:none;"></canvas>
            <div onclick="falarProf(this)" style="position:absolute; bottom:4px; left:8px; display:flex; align-items:flex-end; gap:6px; cursor:pointer;">
                <span style="font-size:64px; line-height:1;">👩‍🏫</span>
                <div id="fala-prof" style="background:white; color:#003366; border:2px solid #003366; border-radius:14px; padding:5px 10px; font-weight:bold; margin-bottom:20px;">Desenhe na lousa! ✏️</div>
            </div>
            <div onclick="particulas(this,'✨');som(440,880,0.25)" style="position:absolute; bottom:8px; right:12px; font-size:48px; cursor:pointer;">🌍</div>
        </div>
        <div style="background:white; padding:8px 14px; border-radius:20px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:center;">
            <button onclick="corGiz='#FFF'" style="width:28px;height:28px;border-radius:50%;background:#FFF;border:2px solid #333;"></button>
            <button onclick="corGiz='#FFEB3B'" style="width:28px;height:28px;border-radius:50%;background:#FFEB3B;border:2px solid #333;"></button>
            <button onclick="corGiz='#FF5252'" style="width:28px;height:28px;border-radius:50%;background:#FF5252;border:2px solid #333;"></button>
            <button onclick="corGiz='#40C4FF'" style="width:28px;height:28px;border-radius:50%;background:#40C4FF;border:2px solid #333;"></button>
            <button onclick="carimbo('⭐')" class="btn">⭐</button>
            <button onclick="carimbo('🦆')" class="btn">🦆</button>
            <button onclick="carimbo('❤️')" class="btn">❤️</button>
        </div>
    </div>
    <div class="placa">🏫 EM Pato Donald - Clique na Escola para entrar na Sala!</div>
    <div id="palco"></div>
    <div id="barra">
        <button class="btn" onclick="spawn('👧')">👧</button>
        <button class="btn" onclick="spawn('👦')">👦</button>
        <button class="btn" onclick="spawn('🦆')">🦆</button>
        <button class="btn" onclick="spawn('🐶')">🐶</button>
        <button class="btn" onclick="spawn('🍎')">🍎</button>
        <button class="btn" onclick="spawn('⚽')">⚽</button>
        <button class="btn-cmd" style="background:#4CAF50;color:white;" onclick="resetar()">🔄 Organizar</button>
        <button class="btn-cmd" style="background:#FF5252;color:white;" onclick="document.getElementById('palco').innerHTML=''">🗑️</button>
    </div>
</div>
"""
html_escola += """
<script>
    const audio = new (window.AudioContext || window.webkitAudioContext)();
    let noite = false, corGiz = '#FFF', ctx = null, desenhando = false;
    const svgs = {
        'ESCORREGADOR': '<svg viewBox="0 0 110 95" width="96" height="82"><path d="M16 86 L28 18 L40 18 L28 86" stroke="#1565C0" stroke-width="5.5" fill="none"/><path d="M38 20 Q58 64 98 80" stroke="#E53935" stroke-width="10" fill="none" stroke-linecap="round"/></svg>',
        'BALANCO': '<svg viewBox="0 0 105 95" width="92" height="82"><path d="M14 86 L28 16 L76 16 L90 86" stroke="#D32F2F" stroke-width="5.5" fill="none"/><line x1="42" y1="16" x2="42" y2="64" stroke="#546E7A" stroke-width="2.5"/><line x1="62" y1="16" x2="62" y2="64" stroke="#546E7A" stroke-width="2.5"/><rect x="35" y="62" width="34" height="7" rx="3" fill="#FFB300"/></svg>',
        'GANGORRA': '<svg viewBox="0 0 110 74" width="96" height="64"><polygon points="45,67 55,40 65,67" fill="#1565C0"/><line x1="12" y1="55" x2="98" y2="27" stroke="#FFB300" stroke-width="7.5" stroke-linecap="round"/></svg>'
    };
    function som(f1, f2, d) {
        if (audio.state === 'suspended') audio.resume();
        const o = audio.createOscillator(), g = audio.createGain();
        o.frequency.setValueAtTime(f1, audio.currentTime);
        o.frequency.exponentialRampToValueAtTime(f2, audio.currentTime + d);
        g.gain.setValueAtTime(0.15, audio.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + d);
        o.connect(g); g.connect(audio.destination); o.start(); o.stop(audio.currentTime + d);
    }
    function particulas(el, s) {
        const c = document.getElementById('cenario'), r = el.getBoundingClientRect(), cr = c.getBoundingClientRect();
        for (let i = 0; i < 4; i++) {
            const p = document.createElement('div'); p.className = 'particula'; p.innerText = s;
            p.style.left = (r.left - cr.left + 10 + Math.random()*35) + 'px';
            p.style.top = (r.top - cr.top + 10) + 'px';
            c.appendChild(p); setTimeout(() => p.remove(), 1400);
        }
    }
    function darDesejo(el) {
        if (!['👧','👦','🦆','🐶'].includes(el.dataset.tipo)) return;
        const ant = el.querySelector('.balao'); if (ant) ant.remove();
        const opcoes = ['🏊', '🛝', '🍎', '⚽'];
        const d = opcoes[Math.floor(Math.random()*opcoes.length)];
        el.dataset.desejo = d;
        const b = document.createElement('div'); b.className = 'balao'; b.innerText = d;
        el.appendChild(b);
    }
    function cumprirDesejo(el, pedido) {
        if (el.dataset.desejo === pedido) {
            delete el.dataset.desejo;
            const b = el.querySelector('.balao'); if (b) b.remove();
            som(520, 980, 0.25); particulas(el, '🌟');
            setTimeout(() => darDesejo(el), 5000);
        }
    }
    function diaNoite(el) {
        noite = !noite;
        const c = document.getElementById('cenario'), n = document.getElementById('noite');
        c.classList.toggle('noite', noite); el.innerText = noite ? '🌙' : '☀️'; n.innerHTML = '';
        if (noite) {
            for (let i = 0; i < 28; i++) {
                const s = document.createElement('div'); s.className = 'estrela';
                s.style.width = s.style.height = '3px'; s.style.left = Math.random()*95+'%'; s.style.top = Math.random()*40+'%';
                n.appendChild(s);
            }
            for (let i = 0; i < 12; i++) {
                const v = document.createElement('div'); v.className = 'vagalume';
                v.style.left = (10+Math.random()*80)+'%'; v.style.top = (55+Math.random()*30)+'%';
                n.appendChild(v);
            }
        }
        som(noite ? 600 : 400, noite ? 320 : 840, 0.35);
    }
    function nuvem(el, s) { particulas(el, s); som(340, 200, 0.25); }
    function abrirSala() {
        document.getElementById('sala').style.display = 'flex'; som(520, 780, 0.2);
        const cv = document.getElementById('lousa');
        if (!ctx) {
            cv.width = cv.offsetWidth; cv.height = cv.offsetHeight; ctx = cv.getContext('2d');
            ctx.lineCap = 'round'; ctx.lineWidth = 5;
            cv.onpointerdown = e => { desenhando = true; const r = cv.getBoundingClientRect(); ctx.strokeStyle = corGiz; ctx.beginPath(); ctx.moveTo(e.clientX-r.left, e.clientY-r.top); };
            cv.onpointermove = e => { if (!desenhando) return; const r = cv.getBoundingClientRect(); ctx.lineTo(e.clientX-r.left, e.clientY-r.top); ctx.stroke(); };
            cv.onpointerup = () => desenhando = false;
        }
    }
    function limparLousa() { const cv = document.getElementById('lousa'); if (ctx) ctx.clearRect(0,0,cv.width,cv.height); }
    function carimbo(e) { const cv = document.getElementById('lousa'); if (ctx) { ctx.font = '36px sans-serif'; ctx.fillText(e, 60+Math.random()*(cv.width-120), 60+Math.random()*(cv.height-120)); } }
    function falarProf(el) {
        const f = ['Muito bem! 🌟', 'Que lindo desenho! 🎨', 'Parabéns, turma! 👏'];
        document.getElementById('fala-prof').innerText = f[Math.floor(Math.random()*f.length)];
        som(540, 860, 0.2); particulas(el, '⭐');
    }
"""
html_escola += """
    function aplicarEscala(el) {
        const top = parseFloat(el.style.top) || el.offsetTop;
        const esc = 0.8 + Math.max(0.25, Math.min(1, top / window.innerHeight)) * 0.32;
        const inv = el.dataset.inv === '-1' ? -1 : 1;
        el.style.transform = `scale(${inv * esc}, ${esc})`;
    }
    function checarInteracoes(el) {
        const tipo = el.dataset.tipo, r = el.getBoundingClientRect(), cx = r.left + r.width/2, cy = r.top + r.height/2;
        if (tipo === '🍎') {
            document.querySelectorAll('.ator').forEach(o => {
                if (o !== el && ['👧','👦','🦆','🐶'].includes(o.dataset.tipo)) {
                    const ro = o.getBoundingClientRect();
                    if (Math.abs(cx-(ro.left+ro.width/2)) < 55 && Math.abs(cy-(ro.top+ro.height/2)) < 55) {
                        cumprirDesejo(o, '🍎'); som(450, 780, 0.2); particulas(o, '❤️'); el.remove();
                    }
                }
            });
            return;
        }
        const pisc = document.getElementById('piscina').getBoundingClientRect();
        const naPiscina = cx >= pisc.left && cx <= pisc.right && cy >= pisc.top && cy <= pisc.bottom;
        el.classList.toggle('nadando', naPiscina);
        if (naPiscina) { el.dataset.dir = '1'; cumprirDesejo(el, '🏊'); som(280, 560, 0.22); particulas(el, '💦'); return; }
        document.querySelectorAll('.brinquedo').forEach(b => {
            const rb = b.getBoundingClientRect();
            if (cx >= rb.left-10 && cx <= rb.right+10 && cy >= rb.top-15 && cy <= rb.bottom+10) {
                const tb = b.dataset.tipo;
                if (tb === 'ESCORREGADOR') {
                    cumprirDesejo(el, '🛝');
                    el.style.left = (rb.left + rb.width*0.2) + 'px'; el.style.top = (rb.top + 5) + 'px';
                    som(760, 260, 0.6);
                    setTimeout(() => { el.style.transition = 'all 0.7s ease-in'; el.style.left = (rb.left + rb.width*0.8) + 'px'; el.style.top = (rb.top + rb.height*0.6) + 'px'; }, 30);
                    setTimeout(() => { el.style.transition = 'none'; particulas(el, '🎉'); aplicarEscala(el); }, 750);
                } else if (tb === 'BALANCO') {
                    el.classList.add('balancando'); el.style.left = (rb.left + rb.width*0.35) + 'px'; el.style.top = (rb.top + rb.height*0.35) + 'px'; som(380, 560, 0.25);
                } else if (tb === 'GANGORRA') {
                    el.classList.add('gangorra'); el.style.left = (rb.left + rb.width*0.15) + 'px'; el.style.top = (rb.top + rb.height*0.25) + 'px'; som(320, 480, 0.25);
                }
            }
        });
    }
    function loop() {
        const pisc = document.getElementById('piscina').getBoundingClientRect();
        document.querySelectorAll('.nadando').forEach(el => {
            if (el.dataset.drag === '1') return;
            let left = parseFloat(el.style.left) || el.offsetLeft, dir = parseFloat(el.dataset.dir || '1');
            left += dir * 0.9;
            if (left >= pisc.right - 48) { left = pisc.right - 48; dir = -1; }
            if (left <= pisc.left + 8) { left = pisc.left + 8; dir = 1; }
            el.dataset.dir = dir; el.style.left = left + 'px'; el.dataset.inv = dir > 0 ? '-1' : '1'; aplicarEscala(el);
        });
        requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
    function criarAtor(tipo, xPct, yPct) {
        const palco = document.getElementById('palco'), el = document.createElement('div');
        el.className = 'ator';
        if (['ESCORREGADOR','BALANCO','GANGORRA'].includes(tipo)) el.classList.add('brinquedo');
        el.dataset.tipo = tipo;
        const corpo = document.createElement('div'); corpo.className = 'corpo';
        if (svgs[tipo]) corpo.innerHTML = svgs[tipo]; else corpo.innerText = tipo;
        el.appendChild(corpo);
        el.style.left = (window.innerWidth * xPct / 100) + 'px';
        el.style.top = (window.innerHeight * yPct / 100) + 'px';
        let drag = false, ox = 0, oy = 0, moveu = false;
        el.onpointerdown = e => { drag = true; moveu = false; el.dataset.drag = '1'; el.classList.remove('balancando','gangorra'); const r = el.getBoundingClientRect(); ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId); };
        el.onpointermove = e => { if (!drag) return; moveu = true; el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 75)) + 'px'; el.style.top = Math.max(40, Math.min(e.clientY - oy, window.innerHeight - 115)) + 'px'; aplicarEscala(el); };
        el.onpointerup = e => {
            drag = false; el.dataset.drag = '0'; el.releasePointerCapture(e.pointerId);
            if (!moveu && tipo === '⚽') {
                el.classList.remove('quicar'); void el.offsetWidth; el.classList.add('quicar');
                document.querySelectorAll('.ator').forEach(o => cumprirDesejo(o, '⚽'));
                som(240, 520, 0.25); particulas(el, '⭐'); return;
            }
            aplicarEscala(el);
            if (!el.classList.contains('brinquedo')) checarInteracoes(el);
        };
        palco.appendChild(el); aplicarEscala(el);
        setTimeout(() => darDesejo(el), 1500 + Math.random()*2000);
    }
    function spawn(t) { criarAtor(t, 20 + Math.random()*55, 55 + Math.random()*18); }
    function resetar() {
        document.getElementById('palco').innerHTML = '';
        criarAtor('👧', 34, 55); criarAtor('👦', 46, 56); criarAtor('🦆', 12, 74); criarAtor('🐶', 22, 74);
        criarAtor('ESCORREGADOR', 56, 52); criarAtor('BALANCO', 77, 52); criarAtor('GANGORRA', 34, 72); criarAtor('⚽', 48, 75);
    }
    resetar();
</script>
</body>
</html>
"""

components.html(html_escola, height=740, scrolling=False)
