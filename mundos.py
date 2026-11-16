import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="EM Pato Donald - Teste Realista", page_icon="🏫", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        .block-container { padding: 0 !important; max-width: 100% !important; }
        iframe { width: 100% !important; height: 98vh !important; border: none !important; display: block !important; }
    </style>
""", unsafe_allow_html=True)

html_teste = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body, html { margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Segoe UI', sans-serif; overflow: hidden; user-select: none; touch-action: none; }
    #cenario {
        width: 100%; height: 100%; position: relative; overflow: hidden;
        background: linear-gradient(180deg, #29B6F6 0%, #81D4FA 35%, #E1F5FE 46%, #D7CCC8 46%, #BCAAA4 53%, #7CB342 53%, #558B2F 78%, #33691E 100%);
    }
    #noite { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(10,18,48,0.82) 0%, rgba(18,32,75,0.58) 55%, rgba(8,14,32,0.48) 100%); opacity: 0; pointer-events: none; z-index: 2; transition: opacity 0.8s; }
    #cenario.noite #noite { opacity: 1; }
    #cenario.noite .vidro-janela { fill: #FFF59D; filter: drop-shadow(0 0 10px #FFEE58); }
    .sol-btn { position: absolute; top: 4%; right: 6%; width: 64px; height: 64px; cursor: pointer; z-index: 6; filter: drop-shadow(0 0 18px rgba(255,215,0,0.8)); }
    .nuvem-svg { position: absolute; top: 6%; opacity: 0.92; pointer-events: none; z-index: 3; animation: moverNuvem 28s linear infinite; }
    @keyframes moverNuvem { 0% { transform: translateX(-180px); } 100% { transform: translateX(110vw); } }
    .predio { position: absolute; top: 15%; left: 4%; width: clamp(230px, 36vw, 340px); z-index: 4; filter: drop-shadow(0 12px 14px rgba(0,0,0,0.28)); }
    .sino { position: absolute; top: 23%; left: 34%; width: 42px; height: 42px; cursor: pointer; z-index: 6; transform-origin: top center; }
    .tocando { animation: balancarSino 0.45s ease-in-out 3; }
    @keyframes balancarSino { 0%,100% { transform: rotate(0deg); } 25% { transform: rotate(22deg); } 75% { transform: rotate(-22deg); } }
    .piscina {
        position: absolute; bottom: 13%; right: 5%; width: clamp(210px, 38vw, 330px); height: clamp(105px, 19vw, 155px);
        background: linear-gradient(145deg, #ECEFF1, #CFD8DC); border: 6px solid #90A4AE; border-radius: 24px;
        padding: 7px; z-index: 3; box-shadow: 0 10px 20px rgba(0,0,0,0.28);
    }
    .agua { width: 100%; height: 100%; border-radius: 16px; position: relative; overflow: hidden; background: radial-gradient(circle at 30% 30%, #4FC3F7, #0288D1 65%, #01579B 100%); }
    .reflexo-agua { position: absolute; inset: 0; opacity: 0.35; background: repeating-radial-gradient(circle at 50% 50%, transparent 0, transparent 18px, rgba(255,255,255,0.4) 20px, transparent 22px); animation: ondulacao 4s infinite linear; }
    @keyframes ondulacao { 0% { transform: scale(1); } 50% { transform: scale(1.06); } 100% { transform: scale(1); } }
    .crianca { position: absolute; cursor: grab; z-index: 20; touch-action: none; transform-origin: bottom center; }
    .crianca:active { cursor: grabbing; z-index: 35; filter: drop-shadow(0 16px 12px rgba(0,0,0,0.35)); }
    .corpo-svg { display: block; pointer-events: none; animation: respirar 2.4s infinite alternate ease-in-out; transform-origin: bottom center; }
    @keyframes respirar { 0% { transform: scaleY(1); } 100% { transform: scaleY(1.022); } }
    .olho-piscar { animation: piscarOlho 4.2s infinite; transform-origin: center; }
    @keyframes piscarOlho { 0%, 94%, 100% { transform: scaleY(1); } 97% { transform: scaleY(0.1); } }
    .submerso::after { content: ''; position: absolute; bottom: 0; left: -6px; right: -6px; height: 46%; background: linear-gradient(180deg, rgba(129,212,250,0.62) 0%, rgba(2,136,209,0.86) 100%); border-top: 2.5px solid #FFF; border-radius: 4px 4px 16px 16px; pointer-events: none; }
    .submerso .corpo-svg { animation: boiarAgua 1.2s infinite alternate ease-in-out; }
    @keyframes boiarAgua { 0% { transform: translateY(-3px) rotate(-3deg); } 100% { transform: translateY(4px) rotate(3deg); } }
    #barra { position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); background: rgba(255,255,255,0.92); padding: 8px 16px; border-radius: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.28); display: flex; gap: 10px; z-index: 40; }
    .btn { border: 2px solid #FFB300; background: #FFFDE7; color: #003366; font-weight: bold; font-size: 14px; border-radius: 16px; padding: 6px 12px; cursor: pointer; }
    .gota-splash { position: absolute; width: 8px; height: 8px; background: #E1F5FE; border-radius: 50%; pointer-events: none; z-index: 30; animation: splashAnim 0.7s ease-out forwards; }
    @keyframes splashAnim { 0% { opacity: 1; transform: translate(0,0) scale(1); } 100% { opacity: 0; transform: translate(var(--dx), -42px) scale(0.4); } }
</style>
</head>
<body>
<div id="cenario">
    <div id="noite"></div>
    <div class="sol-btn" onclick="alternarDiaNoite(this)">
        <svg viewBox="0 0 64 64" width="64" height="64"><circle cx="32" cy="32" r="18" fill="#FFD54F" stroke="#FFA000" stroke-width="2"/></svg>
    </div>
    <svg class="nuvem-svg" style="top:6%; width:140px;" viewBox="0 0 140 60">
        <path d="M25,48 Q10,48 10,35 Q10,23 24,22 Q30,8 48,10 Q64,4 78,16 Q95,12 106,24 Q125,25 125,38 Q125,48 110,48 Z" fill="#FFFFFF"/>
    </svg>
    <div class="predio">
        <svg viewBox="0 0 380 210" width="100%" height="100%">
            <ellipse cx="190" cy="202" rx="175" ry="7" fill="rgba(0,0,0,0.22)"/>
            <polygon points="8,72 190,14 372,72" fill="#B71C1C" stroke="#7F0000" stroke-width="3"/>
            <rect x="26" y="72" width="328" height="126" fill="#1976D2" stroke="#0D47A1" stroke-width="3"/>
            <rect x="55" y="80" width="270" height="28" rx="6" fill="#FFD54F" stroke="#003366" stroke-width="2.5"/>
            <text x="190" y="99" font-family="Segoe UI, sans-serif" font-size="14" font-weight="bold" fill="#003366" text-anchor="middle">EM PATO DONALD</text>
            <rect x="160" y="124" width="60" height="74" rx="4" fill="#6D4C41" stroke="#3E2723" stroke-width="2.5"/>
            <rect class="vidro-janela" x="56" y="122" width="56" height="44" rx="4" fill="#B3E5FC" stroke="#003366" stroke-width="2.5"/>
            <rect class="vidro-janela" x="268" y="122" width="56" height="44" rx="4" fill="#B3E5FC" stroke="#003366" stroke-width="2.5"/>
        </svg>
    </div>
    <div class="sino" onclick="tocarSino(this)">
        <svg viewBox="0 0 48 48" width="42" height="42"><path d="M24,6 C15,6 10,14 10,24 L6,34 L42,34 L38,24 C38,14 33,6 24,6 Z" fill="#FFB300" stroke="#E65100" stroke-width="2"/><circle cx="24" cy="37" r="4" fill="#E65100"/></svg>
    </div>
    <div id="piscina" class="piscina"><div class="agua"><div class="reflexo-agua"></div></div></div>
    <div id="palco"></div>
    <div id="barra">
        <button class="btn" onclick="criarCrianca('MENINA', 35, 58)">+ Menina</button>
        <button class="btn" onclick="criarCrianca('MENINO', 48, 60)">+ Menino</button>
        <button class="btn" style="background:#E8F5E9; border-color:#4CAF50;" onclick="iniciarCena()">Organizar</button>
    </div>
</div>
"""
html_teste += """
<script>
    const audio = new (window.AudioContext || window.webkitAudioContext)();
    let ehNoite = false;

    const modelos = {
        'MENINA': `<svg class="corpo-svg" viewBox="0 0 90 140" width="76" height="118">
            <ellipse cx="45" cy="133" rx="24" ry="5.5" fill="rgba(0,0,0,0.28)"/>
            <circle cx="21" cy="30" r="11" fill="#3E2723"/><circle cx="69" cy="30" r="11" fill="#3E2723"/>
            <rect x="34" y="96" width="8" height="28" rx="4" fill="#F4B47C"/>
            <rect x="48" y="96" width="8" height="28" rx="4" fill="#F4B47C"/>
            <path d="M30,121 Q38,118 43,124 L43,129 L29,129 Z" fill="#EC407A" stroke="#880E4F" stroke-width="1.2"/>
            <path d="M47,124 Q52,118 60,121 L61,129 L47,129 Z" fill="#EC407A" stroke="#880E4F" stroke-width="1.2"/>
            <rect x="19" y="62" width="8" height="28" rx="4" fill="#FFE0B2" transform="rotate(14 19 62)"/>
            <rect x="63" y="62" width="8" height="28" rx="4" fill="#FFE0B2" transform="rotate(-14 63 62)"/>
            <path d="M29,60 L61,60 L67,100 L23,100 Z" fill="#FF4081" stroke="#880E4F" stroke-width="1.5"/>
            <circle cx="45" cy="34" r="21" fill="#FFE0B2" stroke="#D79B60" stroke-width="1.5"/>
            <path d="M24,31 Q45,14 66,31 Q62,11 45,11 Q28,11 24,31 Z" fill="#3E2723"/>
            <g class="olho-piscar">
                <ellipse cx="38" cy="33" rx="2.8" ry="3.2" fill="#212121"/><circle cx="39" cy="32" r="1" fill="#FFF"/>
                <ellipse cx="52" cy="33" rx="2.8" ry="3.2" fill="#212121"/><circle cx="53" cy="32" r="1" fill="#FFF"/>
            </g>
            <path d="M39,43 Q45,49 51,43" stroke="#B71C1C" stroke-width="2.4" fill="none" stroke-linecap="round"/>
        </svg>`,

        'MENINO': `<svg class="corpo-svg" viewBox="0 0 90 140" width="76" height="118">
            <ellipse cx="45" cy="133" rx="24" ry="5.5" fill="rgba(0,0,0,0.28)"/>
            <rect x="34" y="96" width="8" height="28" rx="4" fill="#E09F67"/>
            <rect x="48" y="96" width="8" height="28" rx="4" fill="#E09F67"/>
            <path d="M30,121 Q38,118 43,124 L43,129 L29,129 Z" fill="#1565C0" stroke="#0D47A1" stroke-width="1.2"/>
            <path d="M47,124 Q52,118 60,121 L61,129 L47,129 Z" fill="#1565C0" stroke="#0D47A1" stroke-width="1.2"/>
            <rect x="28" y="83" width="15" height="18" rx="4" fill="#283593"/>
            <rect x="47" y="83" width="15" height="18" rx="4" fill="#283593"/>
            <rect x="19" y="62" width="8" height="28" rx="4" fill="#FFCC80" transform="rotate(14 19 62)"/>
            <rect x="63" y="62" width="8" height="28" rx="4" fill="#FFCC80" transform="rotate(-14 63 62)"/>
            <rect x="27" y="58" width="36" height="28" rx="8" fill="#00ACC1" stroke="#006064" stroke-width="1.5"/>
            <rect x="27" y="68" width="36" height="5" fill="#FFD54F"/>
            <circle cx="45" cy="34" r="21" fill="#FFCC80" stroke="#C68642" stroke-width="1.5"/>
            <path d="M23,30 Q26,10 45,10 Q64,10 67,30 Q56,21 45,23 Q34,21 23,30 Z" fill="#263238"/>
            <g class="olho-piscar">
                <ellipse cx="38" cy="33" rx="2.8" ry="3.2" fill="#212121"/><circle cx="39" cy="32" r="1" fill="#FFF"/>
                <ellipse cx="52" cy="33" rx="2.8" ry="3.2" fill="#212121"/><circle cx="53" cy="32" r="1" fill="#FFF"/>
            </g>
            <path d="M39,43 Q45,49 51,43" stroke="#B71C1C" stroke-width="2.4" fill="none" stroke-linecap="round"/>
        </svg>`
    };

    function som(f1, f2, d) {
        if (audio.state === 'suspended') audio.resume();
        const o = audio.createOscillator(), g = audio.createGain();
        o.frequency.setValueAtTime(f1, audio.currentTime);
        o.frequency.exponentialRampToValueAtTime(f2, audio.currentTime + d);
        g.gain.setValueAtTime(0.14, audio.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + d);
        o.connect(g); g.connect(audio.destination); o.start(); o.stop(audio.currentTime + d);
    }

    function splashAgua(el) {
        const c = document.getElementById('cenario'), r = el.getBoundingClientRect();
        for (let i = 0; i < 8; i++) {
            const g = document.createElement('div');
            g.className = 'gota-splash';
            g.style.left = (r.left + r.width/2) + 'px';
            g.style.top = (r.top + r.height*0.6) + 'px';
            g.style.setProperty('--dx', ((Math.random() - 0.5) * 90) + 'px');
            c.appendChild(g);
            setTimeout(() => g.remove(), 700);
        }
    }

    function tocarSino(el) {
        el.classList.remove('tocando'); void el.offsetWidth; el.classList.add('tocando');
        som(880, 1180, 0.25); setTimeout(() => som(880, 1180, 0.35), 240);
    }

    function alternarDiaNoite(el) {
        ehNoite = !ehNoite;
        document.getElementById('cenario').classList.toggle('noite', ehNoite);
        el.innerHTML = ehNoite
            ? '<svg viewBox="0 0 64 64" width="60" height="60"><path d="M40,12 A22,22 0 1,0 54,44 A18,18 0 1,1 40,12 Z" fill="#FFF59D"/></svg>'
            : '<svg viewBox="0 0 64 64" width="64" height="64"><circle cx="32" cy="32" r="18" fill="#FFD54F" stroke="#FFA000" stroke-width="2"/></svg>';
        som(ehNoite ? 580 : 380, ehNoite ? 300 : 860, 0.35);
    }

    function atualizarProfundidade(el) {
        const top = parseFloat(el.style.top) || el.offsetTop;
        const esc = 0.72 + Math.max(0.35, Math.min(1, top / window.innerHeight)) * 0.36;
        const dir = el.dataset.dir === '-1' ? -1 : 1;
        el.style.transform = `scale(${dir * esc}, ${esc})`;
    }

    function checarPiscina(el, tocarSom) {
        const r = el.getBoundingClientRect(), p = document.getElementById('piscina').getBoundingClientRect();
        const cx = r.left + r.width/2, cy = r.top + r.height*0.75;
        const dentro = cx >= p.left && cx <= p.right && cy >= p.top && cy <= p.bottom;
        if (dentro && !el.classList.contains('submerso')) {
            el.classList.add('submerso'); el.dataset.dir = '1';
            if (tocarSom) { som(260, 560, 0.25); splashAgua(el); }
        } else if (!dentro) {
            el.classList.remove('submerso'); el.dataset.dir = '1';
            atualizarProfundidade(el);
        }
    }

    function loopNado() {
        const p = document.getElementById('piscina').getBoundingClientRect();
        document.querySelectorAll('.submerso').forEach(el => {
            if (el.dataset.drag === '1') return;
            let left = parseFloat(el.style.left) || el.offsetLeft;
            let dir = parseFloat(el.dataset.dir || '1');
            left += dir * 0.85;
            if (left >= p.right - 68) { left = p.right - 68; dir = -1; }
            if (left <= p.left + 8) { left = p.left + 8; dir = 1; }
            el.dataset.dir = dir.toString();
            el.style.left = left + 'px';
            atualizarProfundidade(el);
        });
        requestAnimationFrame(loopNado);
    }
    requestAnimationFrame(loopNado);

    function criarCrianca(tipo, xPct, yPct) {
        const palco = document.getElementById('palco');
        const el = document.createElement('div');
        el.className = 'crianca';
        el.innerHTML = modelos[tipo];
        el.style.left = (window.innerWidth * xPct / 100) + 'px';
        el.style.top = (window.innerHeight * yPct / 100) + 'px';

        let drag = false, ox = 0, oy = 0;
        el.onpointerdown = e => {
            drag = true; el.dataset.drag = '1';
            const r = el.getBoundingClientRect();
            ox = e.clientX - r.left; oy = e.clientY - r.top;
            el.setPointerCapture(e.pointerId);
            som(420, 620, 0.12);
        };
        el.onpointermove = e => {
            if (!drag) return;
            el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 80)) + 'px';
            el.style.top = Math.max(80, Math.min(e.clientY - oy, window.innerHeight - 135)) + 'px';
            atualizarProfundidade(el);
        };
        el.onpointerup = e => {
            drag = false; el.dataset.drag = '0';
            el.releasePointerCapture(e.pointerId);
            checarPiscina(el, true);
            atualizarProfundidade(el);
        };
        palco.appendChild(el);
        atualizarProfundidade(el);
    }

    function iniciarCena() {
        document.getElementById('palco').innerHTML = '';
        criarCrianca('MENINA', 34, 52);
        criarCrianca('MENINO', 46, 56);
    }
    iniciarCena();
</script>
</body>
</html>
"""

components.html(html_teste, height=740, scrolling=False)
