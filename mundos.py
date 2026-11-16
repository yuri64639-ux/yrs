import streamlit as st
import psycopg2
from cenario_escola import render_escola
from cenario_represa import render_represa
from cenario_outros import render_outros

st.set_page_config(
    page_title="Portal dos Mundos - EM Pato Donald",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def registrar_visita_neon(mundo_nome):
    try:
        if "DATABASE_URL" in st.secrets:
            conn = psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS public.visitas_mundos (
                            id SERIAL PRIMARY KEY,
                            mundo TEXT NOT NULL,
                            data_hora TIMESTAMP DEFAULT NOW()
                        );
                    """)
                    cur.execute("INSERT INTO public.visitas_mundos (mundo) VALUES (%s);", (mundo_nome,))
            conn.close()
    except Exception:
        pass

if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = "portal"

def abrir_mundo(nome):
    st.session_state.tela_atual = nome
    registrar_visita_neon(nome)
if st.session_state.tela_atual == "portal":
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            .stApp {
                background: linear-gradient(135deg, #4FC3F7 0%, #E1F5FE 50%, #FFE082 100%);
                font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
            }
            .cabecalho {
                background: linear-gradient(to bottom, #FFD700, #FFC107);
                color: #003366;
                border: 4px solid #003366;
                border-radius: 28px;
                padding: 22px;
                text-align: center;
                margin-bottom: 24px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.22);
            }
            .cabecalho h1 { margin: 0 0 6px 0; font-size: clamp(24px, 5vw, 36px); }
            .cabecalho p { margin: 0; font-size: clamp(15px, 3vw, 19px); font-weight: bold; }
            div.stButton > button {
                width: 100%;
                height: 132px;
                border-radius: 26px !important;
                border: 4px solid white !important;
                font-size: clamp(18px, 3.8vw, 24px) !important;
                font-weight: bold !important;
                background: linear-gradient(to bottom, #2196F3, #0D47A1) !important;
                color: white !important;
                box-shadow: 0 8px 20px rgba(0,0,0,0.25) !important;
                transition: transform 0.2s !important;
            }
            div.stButton > button:hover {
                transform: scale(1.04) !important;
                background: linear-gradient(to bottom, #00B0FF, #1976D2) !important;
            }
        </style>
        <div class="cabecalho">
            <h1>🌍 Portal dos Mundos Mágicos</h1>
            <p>🏫 EM Pato Donald - São José do Rio Preto</p>
            <p style="font-size: 15px; margin-top: 6px; color: #222;">Escolha um mundo vivo para explorar e brincar!</p>
        </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏫\nMundo da Escola", key="btn_escola", use_container_width=True):
            abrir_mundo("escola")
            st.rerun()
        st.write("")
        if st.button("🐳\nMundo do Oceano", key="btn_oceano", use_container_width=True):
            abrir_mundo("oceano")
            st.rerun()
        st.write("")
        if st.button("✈️\nMundo do Aeroporto", key="btn_aeroporto", use_container_width=True):
            abrir_mundo("aeroporto")
            st.rerun()
    with col2:
        if st.button("🐾\nMundo da Represa", key="btn_represa", use_container_width=True):
            abrir_mundo("represa")
            st.rerun()
        st.write("")
        if st.button("🚀\nMundo do Espaço", key="btn_espaco", use_container_width=True):
            abrir_mundo("espaco")
            st.rerun()
else:
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            .block-container { padding: 5px 10px 0 10px !important; max-width: 100% !important; }
            div.stButton > button {
                background-color: #FF5252 !important;
                color: white !important;
                border-radius: 15px !important;
                font-weight: bold !important;
                border: 2px solid white !important;
                height: 44px !important;
                font-size: 16px !important;
            }
            iframe { width: 100% !important; height: 88vh !important; border: none !important; display: block !important; }
        </style>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Voltar ao Portal dos Mundos"):
        st.session_state.tela_atual = "portal"
        st.rerun()

    tela = st.session_state.tela_atual
    if tela == "escola":
        render_escola()
    elif tela == "represa":
        render_represa()
    else:
        render_outros(tela)
import streamlit.components.v1 as components

def render_escola():
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
            body, html { margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Comic Sans MS', sans-serif; overflow: hidden; user-select: none; touch-action: none; }
            #cenario { width: 100%; height: 100%; background: linear-gradient(to bottom, #64B5F6 0%, #B3E5FC 50%, #E6B88A 50%, #689F38 62%, #33691E 100%); border-radius: 20px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 12px; position: relative; transition: background 0.8s; }
            #noite { position: absolute; inset: 0; border-radius: 20px; background: linear-gradient(to bottom, rgba(7,13,38,0.86) 0%, rgba(15,25,65,0.6) 60%, rgba(5,10,25,0.5) 100%); opacity: 0; pointer-events: none; z-index: 2; transition: opacity 0.8s; }
            #cenario.noite #noite { opacity: 1; }
            #cenario.noite .janela { fill: #FFF176; filter: drop-shadow(0 0 8px #FFEE58); }
            .estrela { position: absolute; background: #FFFDE7; border-radius: 50%; box-shadow: 0 0 8px #FFF; animation: piscar 1.5s infinite alternate; }
            .vagalume { position: absolute; width: 6px; height: 6px; background: #C6FF00; border-radius: 50%; box-shadow: 0 0 10px #AEEA00; animation: voarVL 3s infinite alternate; }
            @keyframes piscar { 0% { opacity: 0.2; } 100% { opacity: 1; } }
            @keyframes voarVL { 0% { transform: translate(0,0); } 100% { transform: translate(25px,-20px); } }
            .ceu { position: absolute; top: 8%; left: 0; width: 100%; display: flex; justify-content: space-around; z-index: 5; pointer-events: none; }
            .item-ceu { font-size: clamp(38px, 7vw, 58px); cursor: pointer; pointer-events: auto; }
            .escola-box { position: absolute; top: 24%; left: 3%; width: clamp(185px, 32vw, 270px); cursor: pointer; z-index: 5; filter: drop-shadow(0 6px 8px rgba(0,0,0,0.28)); }
            .aviso-sala { position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%); background: #FFD700; color: #003366; border: 2px solid #003366; border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: bold; white-space: nowrap; }
            .piscina { position: absolute; bottom: 13%; right: 4%; width: clamp(175px, 35vw, 280px); height: clamp(85px, 16vw, 130px); background: #ECEFF1; border: 5px solid #90A4AE; border-radius: 20px; padding: 5px; z-index: 3; pointer-events: none; box-shadow: 0 6px 14px rgba(0,0,0,0.25); }
            .agua-piscina { width: 100%; height: 100%; background: linear-gradient(to bottom, #4FC3F7, #0288D1); border-radius: 14px; display: flex; align-items: flex-end; justify-content: space-between; padding: 4px 10px; color: white; font-weight: bold; font-size: 13px; }
            .arvores { position: absolute; top: 38%; left: 0; width: 100%; display: flex; justify-content: space-around; z-index: 4; pointer-events: none; }
            .arvore { font-size: clamp(46px, 9vw, 74px); cursor: pointer; pointer-events: auto; }
            .placa { background: #FFD700; color: #003366; border: 3px solid #003366; padding: 6px 16px; border-radius: 14px; font-size: clamp(13px, 3vw, 18px); font-weight: bold; z-index: 15; }
            .ator { position: absolute; font-size: 48px; cursor: grab; z-index: 20; touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3)); }
            .ator.brinquedo { z-index: 18; }
            .ator:active { cursor: grabbing; z-index: 30; }
            .corpo { display: inline-block; pointer-events: none; position: relative; }
            .nadando::after { content: ''; position: absolute; bottom: 0; left: -4px; right: -4px; height: 42%; background: linear-gradient(to bottom, rgba(129,212,250,0.55), rgba(2,136,209,0.75)); border-top: 2px solid #FFF; border-radius: 0 0 14px 14px; pointer-events: none; }
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
    <body>
    <div id="cenario">
        <div id="noite"></div>
        <div class="ceu">
            <span class="item-ceu" onclick="diaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="nuvem(this, '💧')">☁️</span>
            <span class="item-ceu" onclick="nuvem(this, '🕊️')">☁️</span>
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
            <span class="arvore" onclick="particulas(this,'🍂');som(520,880,0.2)">🌲</span>
            <span class="arvore" onclick="particulas(this,'🍃');som(520,880,0.2)">🌳</span>
        </div>
        <div id="sala" style="display:none; position:absolute; inset:0; background:linear-gradient(to bottom, #FFF8E1 0%, #FFE082 78%, #8D6E63 78%, #5D4037 100%); z-index:50; flex-direction:column; justify-content:space-between; align-items:center; padding:10px; border-radius:20px;">
            <div style="width:100%; display:flex; justify-content:space-between; align-items:center;">
                <button onclick="document.getElementById('sala').style.display='none'" style="background:#FF5252; color:white; border:2px solid white; border-radius:14px; padding:6px 12px; font-weight:bold; cursor:pointer;">⬅️ Pátio</button>
                <div style="background:#FFD700; color:#003366; border:3px solid #003366; border-radius:14px; padding:4px 12px; font-weight:bold;">👩‍🏫 Sala - EM Pato Donald</div>
                <button onclick="limparLousa()" style="background:#1565C0; color:white; border:2px solid white; border-radius:14px; padding:6px 12px; font-weight:bold; cursor:pointer;">🧽 Apagar</button>
            </div>
            <div style="position:relative; width:94%; height:64%; background:#1B5E20; border:10px solid #6D4C41; border-radius:16px; overflow:hidden;">
                <canvas id="lousa" style="width:100%; height:100%; display:block; cursor:crosshair; touch-action:none;"></canvas>
                <div onclick="particulas(this,'⭐');som(540,860,0.2)" style="position:absolute; bottom:4px; left:8px; font-size:64px; cursor:pointer;">👩‍🏫</div>
                <div onclick="particulas(this,'✨');som(440,880,0.25)" style="position:absolute; bottom:8px; right:12px; font-size:48px; cursor:pointer;">🌍</div>
            </div>
            <div style="background:white; padding:8px 14px; border-radius:20px; display:flex; gap:10px; align-items:center;">
                <button onclick="corGiz='#FFF'" style="width:28px;height:28px;border-radius:50%;background:#FFF;border:2px solid #333;"></button>
                <button onclick="corGiz='#FFEB3B'" style="width:28px;height:28px;border-radius:50%;background:#FFEB3B;border:2px solid #333;"></button>
                <button onclick="corGiz='#FF5252'" style="width:28px;height:28px;border-radius:50%;background:#FF5252;border:2px solid #333;"></button>
                <button onclick="corGiz='#40C4FF'" style="width:28px;height:28px;border-radius:50%;background:#40C4FF;border:2px solid #333;"></button>
                <button onclick="carimbo('⭐')" class="btn">⭐</button>
                <button onclick="carimbo('🦆')" class="btn">🦆</button>
            </div>
        </div>
        <div class="placa">🏫 EM Pato Donald - Clique na Escola para entrar na Sala!</div>
        <div id="palco"></div>
        <div id="barra">
            <button class="btn" onclick="spawn('👧')">👧</button>
            <button class="btn" onclick="spawn('👦')">👦</button>
            <button class="btn" onclick="spawn('🦆')">🦆</button>
            <button class="btn" onclick="spawn('🐶')">🐶</button>
            <button class="btn" onclick="spawn('ESCORREGADOR')">🛝</button>
            <button class="btn" onclick="spawn('BALANCO')">⛓️</button>
            <button class="btn" onclick="spawn('GANGORRA')">⚖️</button>
            <button class="btn" onclick="spawn('⚽')">⚽</button>
            <button class="btn-cmd" style="background:#4CAF50;color:white;" onclick="resetar()">🔄 Organizar</button>
            <button class="btn-cmd" style="background:#FF5252;color:white;" onclick="document.getElementById('palco').innerHTML=''">🗑️</button>
        </div>
    </div>
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
                for (let i = 0; i < 10; i++) {
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
        function checarInteracoes(el) {
            const r = el.getBoundingClientRect(), cx = r.left + r.width/2, cy = r.top + r.height/2;
            const pisc = document.getElementById('piscina').getBoundingClientRect();
            const naPiscina = cx >= pisc.left && cx <= pisc.right && cy >= pisc.top && cy <= pisc.bottom;
            el.classList.toggle('nadando', naPiscina);
            if (naPiscina) { som(280, 560, 0.22); particulas(el, '💦'); return; }
            document.querySelectorAll('.brinquedo').forEach(b => {
                const rb = b.getBoundingClientRect();
                if (cx >= rb.left-10 && cx <= rb.right+10 && cy >= rb.top-15 && cy <= rb.bottom+10) {
                    const tb = b.dataset.tipo;
                    if (tb === 'ESCORREGADOR') {
                        el.style.left = (rb.left + rb.width*0.2) + 'px'; el.style.top = (rb.top + 5) + 'px';
                        som(760, 260, 0.6);
                        setTimeout(() => { el.style.transition = 'all 0.7s ease-in'; el.style.left = (rb.left + rb.width*0.8) + 'px'; el.style.top = (rb.top + rb.height*0.6) + 'px'; }, 30);
                        setTimeout(() => { el.style.transition = 'none'; particulas(el, '🎉'); }, 750);
                    } else if (tb === 'BALANCO') {
                        el.classList.add('balancando'); el.style.left = (rb.left + rb.width*0.35) + 'px'; el.style.top = (rb.top + rb.height*0.35) + 'px'; som(380, 560, 0.25);
                    } else if (tb === 'GANGORRA') {
                        el.classList.add('gangorra'); el.style.left = (rb.left + rb.width*0.15) + 'px'; el.style.top = (rb.top + rb.height*0.25) + 'px'; som(320, 480, 0.25);
                    }
                }
            });
        }
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
            el.onpointerdown = e => { drag = true; moveu = false; el.classList.remove('balancando','gangorra'); const r = el.getBoundingClientRect(); ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId); };
            el.onpointermove = e => { if (!drag) return; moveu = true; el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 75)) + 'px'; el.style.top = Math.max(40, Math.min(e.clientY - oy, window.innerHeight - 115)) + 'px'; };
            el.onpointerup = e => {
                drag = false; el.releasePointerCapture(e.pointerId);
                if (!moveu && tipo === '⚽') { el.classList.remove('quicar'); void el.offsetWidth; el.classList.add('quicar'); som(240, 520, 0.25); particulas(el, '⭐'); return; }
                const escala = 0.8 + (parseFloat(el.style.top) / window.innerHeight) * 0.32;
                el.style.transform = `scale(${escala})`;
                if (!el.classList.contains('brinquedo')) checarInteracoes(el);
            };
            palco.appendChild(el);
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
    components.html(html, height=700, scrolling=False)
import streamlit.components.v1 as components

def render_represa():
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
            body, html { margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Comic Sans MS', sans-serif; overflow: hidden; user-select: none; touch-action: none; }
            #cenario { width: 100%; height: 100%; background: linear-gradient(to bottom, #4FC3F7 0%, #E1F5FE 34%, #0288D1 34%, #01579B 67%, #78909C 67%, #546E7A 74%, #388E3C 74%, #1B5E20 100%); border-radius: 20px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 12px; position: relative; transition: background 0.8s; }
            #noite { position: absolute; inset: 0; border-radius: 20px; background: linear-gradient(to bottom, rgba(7,13,38,0.86) 0%, rgba(15,25,65,0.6) 60%, rgba(5,10,25,0.5) 100%); opacity: 0; pointer-events: none; z-index: 2; transition: opacity 0.8s; }
            #cenario.noite #noite { opacity: 1; }
            .estrela { position: absolute; background: #FFFDE7; border-radius: 50%; box-shadow: 0 0 8px #FFF; animation: piscar 1.5s infinite alternate; }
            .vagalume { position: absolute; width: 6px; height: 6px; background: #C6FF00; border-radius: 50%; box-shadow: 0 0 10px #AEEA00; animation: voarVL 3s infinite alternate; }
            @keyframes piscar { 0% { opacity: 0.2; } 100% { opacity: 1; } }
            @keyframes voarVL { 0% { transform: translate(0,0); } 100% { transform: translate(25px,-20px); } }
            .ceu { position: absolute; top: 8%; left: 0; width: 100%; display: flex; justify-content: space-around; z-index: 5; pointer-events: none; }
            .item-ceu { font-size: clamp(38px, 7vw, 58px); cursor: pointer; pointer-events: auto; }
            .pista { position: absolute; top: 67%; left: 0; width: 100%; height: 7%; pointer-events: none; z-index: 2; }
            .ciclovia { width: 100%; height: 32%; background: rgba(214,40,40,0.75); border-bottom: 2px dashed #FFF; }
            .ninho { position: absolute; bottom: 13%; right: 4%; width: clamp(145px, 26vw, 205px); height: clamp(74px, 13vw, 105px); z-index: 4; pointer-events: none; }
            .placa-ninho { position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%); background: #FFF8DC; color: #4E342E; border: 2px solid #6D4C41; border-radius: 10px; padding: 1px 8px; font-size: 11px; font-weight: bold; white-space: nowrap; }
            .arvores { position: absolute; top: 52%; left: 0; width: 100%; display: flex; justify-content: space-around; z-index: 4; pointer-events: none; }
            .arvore { font-size: clamp(46px, 9vw, 74px); cursor: pointer; pointer-events: auto; }
            .placa { background: #00CED1; color: #003366; border: 3px solid #003366; padding: 6px 16px; border-radius: 14px; font-size: clamp(13px, 3vw, 18px); font-weight: bold; z-index: 15; }
            .ator { position: absolute; cursor: grab; z-index: 20; touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3)); }
            .ator:active { cursor: grabbing; z-index: 30; }
            .corpo { display: inline-block; pointer-events: none; position: relative; }
            .submerso::after { content: ''; position: absolute; bottom: 0; left: -4px; right: -4px; height: 42%; background: linear-gradient(to bottom, rgba(129,212,250,0.55), rgba(2,136,209,0.78)); border-top: 2px solid #FFF; border-radius: 0 0 14px 14px; pointer-events: none; }
            .submerso .corpo { animation: boiar 1.1s infinite alternate ease-in-out; }
            .salto .corpo { animation: saltar 0.75s ease-out; }
            @keyframes boiar { 0% { transform: translateY(-3px) rotate(-4deg); } 100% { transform: translateY(4px) rotate(4deg); } }
            @keyframes saltar { 0%, 100% { transform: translateY(0); } 45% { transform: translateY(-48px) rotate(-30deg) scale(1.12); } }
            .particula { position: absolute; font-size: 22px; pointer-events: none; z-index: 35; animation: subirP 1.4s ease-out forwards; }
            @keyframes subirP { 0% { opacity: 1; } 100% { transform: translateY(-55px) scale(0.7); opacity: 0; } }
            #barra { background: rgba(255,255,255,0.95); padding: 8px 12px; border-radius: 22px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 25; display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
            .btn { font-size: 22px; border: 2px solid #FFD700; background: #FFF8DC; border-radius: 14px; padding: 4px 8px; cursor: pointer; }
            .btn-cmd { font-size: 14px; font-weight: bold; border: none; border-radius: 14px; padding: 8px 11px; cursor: pointer; }
        </style>
    </head>
    <body>
    <div id="cenario">
        <div id="noite"></div>
        <div class="ceu">
            <span class="item-ceu" onclick="diaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="particulas(this,'💧');som(300,180,0.25)">☁️</span>
            <span class="item-ceu" onclick="particulas(this,'🕊️');som(760,1150,0.22)">☁️</span>
            <span class="item-ceu" onclick="particulas(this,'⭐');som(520,960,0.25)">🎈</span>
        </div>
        <svg viewBox="0 0 1000 320" preserveAspectRatio="none" style="position:absolute; top:14%; left:0; width:100%; height:44%; pointer-events:none; z-index:2;">
            <path d="M0,190 Q250,175 500,190 T1000,190 L1000,210 L0,210 Z" fill="#1B5E20"/>
            <path d="M 270 198 Q 500 130 730 198" fill="none" stroke="#D32F2F" stroke-width="11" stroke-linecap="round"/>
            <rect x="240" y="196" width="520" height="13" rx="4" fill="#E53935"/>
        </svg>
        <div class="pista"><div class="ciclovia"></div></div>
        <div id="ninho" class="ninho">
            <svg viewBox="0 0 180 95" width="100%" height="100%">
                <ellipse cx="90" cy="68" rx="84" ry="24" fill="#795548" stroke="#3E2723" stroke-width="3"/><ellipse cx="90" cy="66" rx="68" ry="16" fill="#D7CCC8"/>
            </svg>
            <div class="placa-ninho">🐾 Ninho das Capivaras</div>
        </div>
        <div class="arvores">
            <span class="arvore" onclick="particulas(this,'🍃');som(520,880,0.2)">🌳</span>
            <span class="arvore" onclick="particulas(this,'🍂');som(520,880,0.2)">🌴</span>
            <span class="arvore" onclick="particulas(this,'🍃');som(520,880,0.2)">🌳</span>
            <span class="arvore" onclick="particulas(this,'🍂');som(520,880,0.2)">🌴</span>
        </div>
        <div class="placa">🌊 Represa Municipal - Coloque os animais na água ou no ninho!</div>
        <div id="palco"></div>
        <div id="barra">
            <button class="btn" onclick="spawn('CAPIVARA')">🦫</button>
            <button class="btn" onclick="spawn('BEBE_CAPIVARA')">👶🦫</button>
            <button class="btn" onclick="spawn('DOURADO')">🐟</button>
            <button class="btn" onclick="spawn('TILAPIA')">🐠</button>
            <button class="btn" onclick="spawn('🦢')">🦢</button>
            <button class="btn" onclick="spawn('🍼')">🍼</button>
            <button class="btn" onclick="spawn('🧷')">🧷</button>
            <button class="btn" onclick="spawn('🧼')">🧼</button>
            <button class="btn" onclick="spawn('🌽')">🌽</button>
            <button class="btn-cmd" style="background:#4CAF50;color:white;" onclick="resetar()">🔄 Organizar</button>
            <button class="btn-cmd" style="background:#FF5252;color:white;" onclick="document.getElementById('palco').innerHTML=''">🗑️</button>
        </div>
    </div>
    <script>
        const audio = new (window.AudioContext || window.webkitAudioContext)();
        let noite = false;
        const nadadores = ['CAPIVARA', 'BEBE_CAPIVARA', 'DOURADO', 'TILAPIA', '🦢'];
        const peixes = ['DOURADO', 'TILAPIA'];
        const pista = ['CICLISTA', 'CAMINHANTE'];
        const svgs = {
            'CAPIVARA': '<svg viewBox="0 0 84 60" width="76" height="54"><ellipse cx="40" cy="54" rx="26" ry="4.5" fill="rgba(0,0,0,0.28)"/><rect x="20" y="42" width="7" height="12" rx="3" fill="#4E342E"/><rect x="49" y="42" width="7" height="12" rx="3" fill="#4E342E"/><ellipse cx="40" cy="33" rx="25" ry="15" fill="#795548" stroke="#3E2723" stroke-width="1.5"/><rect x="50" y="13" width="24" height="19" rx="8" fill="#8D6E63" stroke="#3E2723" stroke-width="1.5"/><circle cx="62" cy="19" r="2.2" fill="#1A1A1A"/></svg>',
            'BEBE_CAPIVARA': '<svg viewBox="0 0 84 60" width="52" height="38"><ellipse cx="40" cy="35" rx="22" ry="14" fill="#A1887F" stroke="#5D4037" stroke-width="1.5"/><rect x="48" y="16" width="20" height="17" rx="7" fill="#BCAAA4" stroke="#5D4037" stroke-width="1.5"/><circle cx="58" cy="22" r="2.2" fill="#1A1A1A"/></svg>',
            'DOURADO': '<svg viewBox="0 0 92 52" width="76" height="44"><path d="M24 26 L5 11 L12 26 L5 41 Z" fill="#E65100"/><ellipse cx="50" cy="26" rx="28" ry="13" fill="#FFD54F" stroke="#BF360C" stroke-width="1.5"/><circle cx="70" cy="22" r="2.6" fill="#111"/></svg>',
            'TILAPIA': '<svg viewBox="0 0 90 56" width="72" height="46"><path d="M24 28 L6 13 L11 28 L6 43 Z" fill="#455A64"/><ellipse cx="50" cy="28" rx="27" ry="15" fill="#78909C" stroke="#263238" stroke-width="1.5"/><circle cx="69" cy="24" r="2.5" fill="#111"/></svg>',
            'CICLISTA': '<svg viewBox="0 0 80 76" width="62" height="58"><circle cx="20" cy="60" r="11" fill="none" stroke="#212121" stroke-width="3"/><circle cx="60" cy="60" r="11" fill="none" stroke="#212121" stroke-width="3"/><path d="M20 60 L38 60 L50 42 L30 42 Z" fill="none" stroke="#E53935" stroke-width="3"/><circle cx="38" cy="18" r="7" fill="#FFCC80"/><line x1="38" y1="25" x2="36" y2="42" stroke="#1E88E5" stroke-width="6" stroke-linecap="round"/></svg>',
            'CAMINHANTE': '<svg viewBox="0 0 60 80" width="44" height="60"><circle cx="30" cy="16" r="8" fill="#FFCC80"/><rect x="23" y="25" width="14" height="24" rx="5" fill="#43A047"/><line x1="26" y1="49" x2="20" y2="72" stroke="#1565C0" stroke-width="5"/><line x1="34" y1="49" x2="40" y2="72" stroke="#1565C0" stroke-width="5"/></svg>'
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
        function diaNoite(el) {
            noite = !noite;
            const c = document.getElementById('cenario'), n = document.getElementById('noite');
            c.classList.toggle('noite', noite); el.innerText = noite ? '🌙' : '☀️'; n.innerHTML = '';
            if (noite) {
                for (let i = 0; i < 28; i++) {
                    const s = document.createElement('div'); s.className = 'estrela';
                    s.style.width = s.style.height = '3px'; s.style.left = Math.random()*95+'%'; s.style.top = Math.random()*35+'%';
                    n.appendChild(s);
                }
                for (let i = 0; i < 14; i++) {
                    const v = document.createElement('div'); v.className = 'vagalume';
                    v.style.left = (10+Math.random()*80)+'%'; v.style.top = (68+Math.random()*22)+'%';
                    n.appendChild(v);
                }
            }
            som(noite ? 600 : 400, noite ? 320 : 840, 0.35);
        }
        function atualizarAgua(el, tocarSom) {
            if (!nadadores.includes(el.dataset.tipo)) return;
            const r = el.getBoundingClientRect(), cy = r.top + r.height/2, h = window.innerHeight;
            const naAgua = cy >= h * 0.32 && cy <= h * 0.68;
            if (naAgua) {
                if (!el.classList.contains('submerso')) {
                    el.classList.add('submerso'); el.dataset.dir = Math.random() > 0.5 ? '1' : '-1';
                    if (tocarSom) { som(280, 560, 0.25); particulas(el, '💦'); }
                }
            } else {
                el.classList.remove('submerso'); el.style.transform = 'scaleX(1)';
            }
        }
        function verificarCuidados(el) {
            const tipo = el.dataset.tipo, r = el.getBoundingClientRect(), cx = r.left + r.width/2, cy = r.top + r.height/2;
            if (tipo === 'CAPIVARA' || tipo === 'BEBE_CAPIVARA') {
                const rn = document.getElementById('ninho').getBoundingClientRect();
                if (cx >= rn.left && cx <= rn.right && cy >= rn.top && cy <= rn.bottom) {
                    el.classList.remove('submerso'); el.style.top = (rn.top + rn.height*0.25) + 'px';
                    som(580, 860, 0.2); particulas(el, '❤️');
                }
            }
            if (['🍼','🧷','🧼','🌽'].includes(tipo)) {
                document.querySelectorAll('.ator').forEach(outro => {
                    if (outro !== el && nadadores.includes(outro.dataset.tipo)) {
                        const ro = outro.getBoundingClientRect();
                        if (Math.abs(cx - (ro.left + ro.width/2)) < 60 && Math.abs(cy - (ro.top + ro.height/2)) < 60) {
                            som(480, 820, 0.2); particulas(outro, tipo === '🧼' ? '🫧' : '❤️');
                            if (tipo !== '🧼') el.remove();
                        }
                    }
                });
            }
        }
        function loop() {
            const maxW = window.innerWidth - 75;
            document.querySelectorAll('.submerso, .na-pista').forEach(el => {
                if (el.dataset.drag === '1') return;
                let left = parseFloat(el.style.left) || el.offsetLeft;
                let dir = parseFloat(el.dataset.dir || '1');
                const vel = peixes.includes(el.dataset.tipo) ? 1.5 : 1.0;
                left += dir * vel;
                if (left >= maxW) { left = maxW; dir = -1; } else if (left <= 10) { left = 10; dir = 1; }
                el.dataset.dir = dir.toString(); el.style.left = left + 'px';
                const olhaDir = ['CAPIVARA','BEBE_CAPIVARA','DOURADO','TILAPIA','CICLISTA'].includes(el.dataset.tipo);
                const inv = olhaDir ? (dir < 0 ? -1 : 1) : (dir > 0 ? -1 : 1);
                const esc = 0.8 + (parseFloat(el.style.top)/window.innerHeight)*0.3;
                el.style.transform = `scale(${inv * esc}, ${esc})`;
            });
            requestAnimationFrame(loop);
        }
        requestAnimationFrame(loop);
        function criarAtor(tipo, xPct, yPct) {
            const palco = document.getElementById('palco'), el = document.createElement('div');
            el.className = 'ator';
            if (pista.includes(tipo)) { el.classList.add('na-pista'); el.dataset.dir = '1'; }
            el.dataset.tipo = tipo; el.style.fontSize = '46px';
            const corpo = document.createElement('div'); corpo.className = 'corpo';
            if (svgs[tipo]) corpo.innerHTML = svgs[tipo]; else corpo.innerText = tipo;
            el.appendChild(corpo);
            el.style.left = (window.innerWidth * xPct / 100) + 'px';
            el.style.top = (window.innerHeight * yPct / 100) + 'px';
            let drag = false, ox = 0, oy = 0, moveu = false;
            el.onpointerdown = e => { drag = true; moveu = false; el.dataset.drag = '1'; const r = el.getBoundingClientRect(); ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId); };
            el.onpointermove = e => { if (!drag) return; moveu = true; el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 70)) + 'px'; el.style.top = Math.max(40, Math.min(e.clientY - oy, window.innerHeight - 110)) + 'px'; };
            el.onpointerup = e => {
                drag = false; el.dataset.drag = '0'; el.releasePointerCapture(e.pointerId);
                if (!moveu && peixes.includes(tipo) && el.classList.contains('submerso')) { el.classList.remove('salto'); void el.offsetWidth; el.classList.add('salto'); som(320, 760, 0.3); particulas(el, '💦'); return; }
                atualizarAgua(el, true); verificarCuidados(el);
            };
            palco.appendChild(el); atualizarAgua(el, false);
        }
        function spawn(t) { criarAtor(t, 15 + Math.random()*60, peixes.includes(t) ? 42 + Math.random()*16 : 73); }
        function resetar() {
            document.getElementById('palco').innerHTML = '';
            criarAtor('🦢', 14, 42); criarAtor('DOURADO', 32, 48); criarAtor('TILAPIA', 58, 52);
            criarAtor('CICLISTA', 22, 61); criarAtor('CAMINHANTE', 65, 62);
            criarAtor('CAPIVARA', 10, 74); criarAtor('BEBE_CAPIVARA', 26, 75);
            criarAtor('🍼', 44, 75); criarAtor('🧷', 52, 75); criarAtor('🧼', 60, 75); criarAtor('🌽', 68, 75);
        }
        resetar();
    </script>
    </body>
    </html>
    """
    components.html(html, height=700, scrolling=False)
import streamlit.components.v1 as components

def render_outros(mundo):
    configs = {
        "oceano": {
            "titulo": "🐠 Mundo do Oceano Azul",
            "fundo": "linear-gradient(to bottom, #26C6DA 0%, #0277BD 45%, #012A4A 100%)",
            "cor": "#00008B",
            "itens": ["🐳", "🐬", "🐠", "🐢", "🐙", "🦀", "🦈"]
        },
        "aeroporto": {
            "titulo": "✈️ Aeroporto de São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #64B5F6 0%, #BBDEFB 48%, #4CAF50 48%, #2E7D32 62%, #37474F 62%, #263238 88%, #2E7D32 88%)",
            "cor": "#1565C0",
            "itens": ["✈️", "🚁", "🛩️", "🧳", "👨‍✈️", "🚌"]
        },
        "espaco": {
            "titulo": "🚀 Viagem pelo Espaço Sideral",
            "fundo": "radial-gradient(circle, #1B2735 0%, #090A0F 100%)",
            "cor": "#4B0082",
            "itens": ["🚀", "🛸", "👨‍🚀", "👽", "🐶", "🛰️", "🪐"]
        }
    }
    cfg = configs[mundo]
    botoes = "".join([f'<button class="btn" onclick="spawn(\'{i}\')">{i}</button>' for i in cfg["itens"]])
    iniciais = "".join([f"criar('{i}', {15 + idx*11}, {28 + (idx%2)*28});" for idx, i in enumerate(cfg["itens"])])
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
            body, html { margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Comic Sans MS', sans-serif; overflow: hidden; user-select: none; touch-action: none; }
            #cenario { width: 100%; height: 100%; background: __FUNDO__; border-radius: 20px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 12px; position: relative; transition: background 0.8s; }
            #noite { position: absolute; inset: 0; border-radius: 20px; background: rgba(5, 10, 30, 0.72); opacity: 0; pointer-events: none; z-index: 2; transition: opacity 0.8s; }
            #cenario.noite #noite { opacity: 1; }
            .ceu { position: absolute; top: 8%; left: 0; width: 100%; display: flex; justify-content: space-around; z-index: 5; pointer-events: none; }
            .item-ceu { font-size: clamp(38px, 7vw, 56px); cursor: pointer; pointer-events: auto; }
            .placa { background: __COR__; color: white; border: 3px solid #FFD700; padding: 6px 16px; border-radius: 14px; font-size: clamp(14px, 3vw, 18px); font-weight: bold; z-index: 15; }
            .ator { position: absolute; font-size: 52px; cursor: grab; z-index: 20; touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.35)); }
            .ator:active { cursor: grabbing; z-index: 30; }
            .flutuar { animation: flutuar 1.4s infinite alternate ease-in-out; }
            @keyframes flutuar { 0% { transform: translateY(-6px) rotate(-3deg); } 100% { transform: translateY(6px) rotate(3deg); } }
            #barra { background: rgba(255,255,255,0.95); padding: 8px 12px; border-radius: 22px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 25; display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
            .btn { font-size: 24px; border: 2px solid #FFD700; background: #FFF8DC; border-radius: 14px; padding: 4px 8px; cursor: pointer; }
            .btn-cmd { font-size: 14px; font-weight: bold; border: none; border-radius: 14px; padding: 8px 11px; cursor: pointer; }
        </style>
    </head>
    <body>
    <div id="cenario">
        <div id="noite"></div>
        <div class="ceu">
            <span class="item-ceu" onclick="diaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="som(420, 820, 0.25)">☁️</span>
        </div>
        <div class="placa">__TITULO__</div>
        <div id="palco"></div>
        <div id="barra">
            __BOTOES__
            <button class="btn-cmd" style="background:#4CAF50;color:white;" onclick="resetar()">🔄 Organizar</button>
            <button class="btn-cmd" style="background:#FF5252;color:white;" onclick="document.getElementById('palco').innerHTML=''">🗑️</button>
        </div>
    </div>
    <script>
        let noite = false;
        const audio = new (window.AudioContext || window.webkitAudioContext)();
        function som(f1, f2, d) {
            if (audio.state === 'suspended') audio.resume();
            const o = audio.createOscillator(), g = audio.createGain();
            o.frequency.setValueAtTime(f1, audio.currentTime);
            o.frequency.exponentialRampToValueAtTime(f2, audio.currentTime + d);
            g.gain.setValueAtTime(0.15, audio.currentTime);
            g.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + d);
            o.connect(g); g.connect(audio.destination); o.start(); o.stop(audio.currentTime + d);
        }
        function diaNoite(el) {
            noite = !noite;
            document.getElementById('cenario').classList.toggle('noite', noite);
            el.innerText = noite ? '🌙' : '☀️';
            som(noite ? 600 : 350, noite ? 300 : 850, 0.35);
        }
        function criar(item, xPct, yPct) {
            const palco = document.getElementById('palco'), el = document.createElement('div');
            el.className = 'ator flutuar'; el.innerText = item;
            el.style.left = (window.innerWidth * xPct / 100) + 'px';
            el.style.top = (window.innerHeight * yPct / 100) + 'px';
            let drag = false, ox = 0, oy = 0;
            el.onpointerdown = e => {
                drag = true;
                const r = el.getBoundingClientRect();
                ox = e.clientX - r.left; oy = e.clientY - r.top;
                el.setPointerCapture(e.pointerId);
                som(360, 620, 0.15);
            };
            el.onpointermove = e => {
                if (!drag) return;
                el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 75)) + 'px';
                el.style.top = Math.max(40, Math.min(e.clientY - oy, window.innerHeight - 115)) + 'px';
            };
            el.onpointerup = e => { drag = false; el.releasePointerCapture(e.pointerId); };
            palco.appendChild(el);
        }
        function spawn(i) { criar(i, 20 + Math.random() * 55, 25 + Math.random() * 40); }
        function resetar() { document.getElementById('palco').innerHTML = ''; __INICIAIS__ }
        resetar();
    </script>
    </body>
    </html>
    """
    html = (
        html.replace("__FUNDO__", cfg["fundo"])
        .replace("__COR__", cfg["cor"])
        .replace("__TITULO__", cfg["titulo"])
        .replace("__BOTOES__", botoes)
        .replace("__INICIAIS__", iniciais)
    )
    components.html(html, height=700, scrolling=False)
