import streamlit as st
import streamlit.components.v1 as components
import psycopg2

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
                background: linear-gradient(135deg, #87CEFA 0%, #E0F7FA 50%, #FFD54F 100%);
                font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
            }
            .cabecalho {
                background: #FFD700;
                color: #003366;
                border: 4px solid #003366;
                border-radius: 25px;
                padding: 20px;
                text-align: center;
                margin-bottom: 25px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            }
            .cabecalho h1 { margin: 0 0 8px 0; font-size: clamp(24px, 5vw, 34px); }
            .cabecalho p { margin: 0; font-size: clamp(15px, 3vw, 19px); font-weight: bold; }
            div.stButton > button {
                width: 100%;
                height: 150px;
                border-radius: 25px !important;
                border: 4px solid white !important;
                font-size: clamp(20px, 4vw, 26px) !important;
                font-weight: bold !important;
                background: linear-gradient(to bottom, #1E90FF, #005BB5) !important;
                color: white !important;
                box-shadow: 0 8px 18px rgba(0,0,0,0.25) !important;
                transition: transform 0.2s !important;
            }
            div.stButton > button:hover {
                transform: scale(1.04) !important;
                background: linear-gradient(to bottom, #00BFFF, #1E90FF) !important;
            }
        </style>

        <div class="cabecalho">
            <h1>🌍 Portal dos Mundos Mágicos</h1>
            <p>🏫 EM Pato Donald - São José do Rio Preto</p>
            <p style="font-size: 15px; margin-top: 6px; color: #333;">Toque em um mundo abaixo para entrar!</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🦆\nMundo da Escola", key="btn_escola", use_container_width=True):
            abrir_mundo("escola")
            st.rerun()
        st.write("")
        if st.button("🐳\nMundo do Oceano", key="btn_oceano", use_container_width=True):
            abrir_mundo("oceano")
            st.rerun()

    with col2:
        if st.button("🦫\nMundo da Represa", key="btn_represa", use_container_width=True):
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
                background-color: #FF6B6B !important;
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

    mundos = {
        "escola": {
            "titulo": "🏫 EM Pato Donald - São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #87CEFA 55%, #F4A460 55%, #2E8B57 85%)",
            "placa_bg": "#FFD700", "placa_cor": "#003366",
            "itens": ["🦆", "🛝", "📚", "🎨", "⚽", "🐶"],
            "espalhados": [
                ("🛝", 26, 56), ("📚", 46, 62), ("🦆", 64, 58),
                ("🎨", 78, 65), ("⚽", 20, 70), ("🐶", 55, 72), ("🐱", 82, 54)
            ],
            "clima_extra": "chuva_arcoiris"
        },
        "represa": {
            "titulo": "🌊 Represa Municipal - São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #5BC0EB 0%, #BBE6F8 36%, #1B9AAA 36%, #0D6E8A 66%, #8D99AE 66%, #8D99AE 74%, #38B000 74%, #007200 100%)",
            "placa_bg": "#00CED1", "placa_cor": "#003366",
            "itens": ["🦫", "🦢", "🚲", "🏃", "🛝", "🦆"],
            "espalhados": [
                ("🦢", 16, 48), ("🦆", 62, 52), ("🚲", 18, 64),
                ("🏃", 52, 64), ("🦫", 22, 74), ("🦫", 36, 76),
                ("🦫", 74, 75), ("🛝", 82, 68), ("📚", 10, 73)
            ],
            "clima_extra": "chuva_arcoiris"
        },
        "oceano": {
            "titulo": "🐠 Mundo do Oceano Azul",
            "fundo": "linear-gradient(to bottom, #00CED1 20%, #000080 85%)",
            "placa_bg": "#00008B", "placa_cor": "#FFFFFF",
            "itens": ["🐳", "🐙", "🐠", "🦀", "🐬", "🐢"],
            "espalhados": [
                ("🐳", 12, 32), ("🐬", 45, 28), ("🐠", 76, 36),
                ("🐙", 24, 54), ("🐢", 60, 50), ("🦀", 38, 72),
                ("🐡", 80, 62), ("🦈", 10, 64)
            ],
            "clima_extra": "bolhas"
        },
        "espaco": {
            "titulo": "🚀 Viagem pelo Espaço Sideral",
            "fundo": "radial-gradient(circle, #1B2735 0%, #090A0F 100%)",
            "placa_bg": "#4B0082", "placa_cor": "#FFFFFF",
            "itens": ["👨‍🚀", "🛸", "🚀", "👽", "🐶", "📚"],
            "espalhados": [
                ("🚀", 14, 34), ("👨‍🚀", 36, 48), ("🛸", 68, 32),
                ("👽", 78, 56), ("🐶", 22, 66), ("📚", 54, 68),
                ("🛰️", 48, 30), ("🦆", 82, 70)
            ],
            "clima_extra": "estrelas"
        }
    }

    cfg = mundos[st.session_state.tela_atual]
    botoes_itens = "".join([f'<button class="btn-item" onclick="criar(\'{i}\')">{i}</button>' for i in cfg["itens"]])
    espalhados_js = "".join([f"criarNaPosicao('{emoji}', {x}, {y});" for emoji, x, y in cfg["espalhados"]])
    decoracao_cenario = ""
    if st.session_state.tela_atual == "represa":
        decoracao_cenario = """
        <svg viewBox="0 0 1000 320" preserveAspectRatio="none" style="position:absolute; top:14%; left:0; width:100%; height:42%; pointer-events:none; z-index:2;">
            <g fill="#6C7A89" opacity="0.65">
                <rect x="40" y="95" width="38" height="95" rx="3"/>
                <rect x="85" y="70" width="46" height="120" rx="3"/>
                <rect x="140" y="105" width="35" height="85" rx="3"/>
                <rect x="260" y="80" width="42" height="110" rx="3"/>
                <rect x="310" y="60" width="52" height="130" rx="3"/>
                <rect x="650" y="75" width="48" height="115" rx="3"/>
                <rect x="708" y="90" width="40" height="100" rx="3"/>
                <rect x="820" y="65" width="55" height="125" rx="3"/>
                <rect x="885" y="95" width="42" height="95" rx="3"/>
            </g>
            <path d="M0,190 Q250,175 500,190 T1000,190 L1000,210 L0,210 Z" fill="#2D6A4F"/>
            <polygon points="488,185 500,25 512,185" fill="#FFFFFF" stroke="#CFD8DC" stroke-width="2"/>
            <line x1="500" y1="35" x2="320" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="500" y1="55" x2="365" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="500" y1="75" x2="410" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="500" y1="95" x2="455" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="500" y1="35" x2="680" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="500" y1="55" x2="635" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="500" y1="75" x2="590" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="500" y1="95" x2="545" y2="188" stroke="#FFFFFF" stroke-width="2.5"/>
            <rect x="270" y="186" width="460" height="11" rx="4" fill="#ECEFF1" stroke="#90A4AE" stroke-width="2"/>
        </svg>
        <div class="chafariz-riopreto">
            <div class="jato-central"></div>
            <div class="jato-esq"></div>
            <div class="jato-dir"></div>
            <div class="espuma-lago"></div>
        </div>
        <div class="pista-riopreto">
            <div class="faixa-ciclovia"></div>
            <div class="faixa-pedestre"></div>
        </div>
        <div class="elementos-fundo" style="top: 56%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
        </div>
        """
    elif st.session_state.tela_atual == "escola":
        decoracao_cenario = """
        <svg viewBox="0 0 360 180" style="position:absolute; top:30%; left:4%; width:clamp(190px, 34vw, 290px); pointer-events:none; z-index:3; filter: drop-shadow(0 6px 8px rgba(0,0,0,0.25));">
            <polygon points="10,65 180,15 350,65" fill="#D62828" stroke="#8D0801" stroke-width="3"/>
            <rect x="25" y="65" width="310" height="105" fill="#1E88E5" stroke="#0D47A1" stroke-width="3"/>
            <rect x="45" y="72" width="270" height="24" rx="4" fill="#FFD700" stroke="#003366" stroke-width="2"/>
            <text x="180" y="88" font-family="Comic Sans MS, sans-serif" font-size="13" font-weight="bold" fill="#003366" text-anchor="middle">EM PATO DONALD</text>
            <rect x="155" y="115" width="50" height="55" rx="3" fill="#FFD700" stroke="#003366" stroke-width="2"/>
            <rect x="55" y="110" width="45" height="35" rx="3" fill="#E3F2FD" stroke="#003366" stroke-width="2"/>
            <rect x="260" y="110" width="45" height="35" rx="3" fill="#E3F2FD" stroke="#003366" stroke-width="2"/>
        </svg>
        <div class="balanco-escola" onclick="chacoalharFundo(this, 'folha')">⛓️🪑⛓️</div>
        <div class="elementos-fundo" style="top: 41%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌲</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
        </div>
        """
    elif st.session_state.tela_atual == "oceano":
        decoracao_cenario = """
        <div class="elementos-fundo" style="top: 68%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🪸</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🌿</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🪸</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🐚</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🌿</span>
        </div>
        """
    elif st.session_state.tela_atual == "espaco":
        decoracao_cenario = """
        <div class="elementos-fundo" style="top: 22%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">🪐</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">⭐</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">🌕</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">⭐</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">☄️</span>
        </div>
        """
    html_cenario = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
            body, html {{
                margin: 0; padding: 0; width: 100%; height: 100%;
                font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
                overflow: hidden; user-select: none; touch-action: none;
            }}
            #cenario {{
                width: 100%; height: 100%; background: {cfg['fundo']};
                border-radius: 20px; display: flex; flex-direction: column;
                justify-content: space-between; align-items: center; padding: 12px; position: relative;
            }}
            .balanco-escola {{
                position: absolute; top: 47%; left: 38%; font-size: clamp(32px, 6vw, 48px);
                cursor: pointer; z-index: 5; transform-origin: top center;
                animation: balancarSuave 2s infinite alternate ease-in-out;
                filter: drop-shadow(0 4px 4px rgba(0,0,0,0.3));
            }}
            @keyframes balancarSuave {{
                0% {{ transform: rotate(-10deg); }}
                100% {{ transform: rotate(10deg); }}
            }}
            .chafariz-riopreto {{
                position: absolute; top: 44%; left: 26%; width: 90px; height: 80px;
                pointer-events: none; z-index: 3;
            }}
            .jato-central {{
                position: absolute; bottom: 8px; left: 41px; width: 8px; height: 68px;
                background: linear-gradient(to top, rgba(255,255,255,0.9), rgba(224,247,250,0.2));
                border-radius: 50% 50% 0 0; animation: pulsarJato 1.1s infinite alternate ease-in-out;
            }}
            .jato-esq {{
                position: absolute; bottom: 8px; left: 26px; width: 6px; height: 45px;
                background: linear-gradient(to top, rgba(255,255,255,0.8), transparent);
                transform: rotate(-18deg); transform-origin: bottom center;
                animation: pulsarJato 1.1s infinite alternate ease-in-out;
            }}
            .jato-dir {{
                position: absolute; bottom: 8px; left: 58px; width: 6px; height: 45px;
                background: linear-gradient(to top, rgba(255,255,255,0.8), transparent);
                transform: rotate(18deg); transform-origin: bottom center;
                animation: pulsarJato 1.1s infinite alternate ease-in-out;
            }}
            .espuma-lago {{
                position: absolute; bottom: 4px; left: 15px; width: 60px; height: 10px;
                background: rgba(255,255,255,0.75); border-radius: 50%; filter: blur(2px);
            }}
            @keyframes pulsarJato {{
                0% {{ transform: scaleY(0.85); opacity: 0.85; }}
                100% {{ transform: scaleY(1.12); opacity: 1; }}
            }}
            .pista-riopreto {{
                position: absolute; top: 66%; left: 0; width: 100%; height: 8%;
                pointer-events: none; z-index: 2;
            }}
            .faixa-ciclovia {{
                width: 100%; height: 32%; background: rgba(214, 40, 40, 0.75);
                border-bottom: 2px dashed #FFFFFF;
            }}
            .faixa-pedestre {{
                width: 100%; height: 68%;
                background: repeating-linear-gradient(90deg, transparent, transparent 30px, #FFD166 30px, #FFD166 55px);
                background-size: 100% 3px; background-repeat: no-repeat; background-position: center;
            }}
            .elementos-fundo {{
                position: absolute; left: 0; width: 100%; display: flex;
                justify-content: space-around; align-items: flex-end; z-index: 4;
                pointer-events: none;
            }}
            .item-fundo-interativo {{
                font-size: clamp(52px, 11vw, 84px); cursor: pointer; pointer-events: auto;
                transform-origin: bottom center; display: inline-block;
                filter: drop-shadow(0 4px 4px rgba(0,0,0,0.25));
            }}
            .xagualhar {{
                animation: balancarItem 0.65s ease-in-out;
            }}
            @keyframes balancarItem {{
                0% {{ transform: rotate(0deg) scale(1); }}
                20% {{ transform: rotate(-14deg) scale(1.08); }}
                40% {{ transform: rotate(12deg) scale(1.08); }}
                60% {{ transform: rotate(-9deg) scale(1.04); }}
                80% {{ transform: rotate(6deg) scale(1.02); }}
                100% {{ transform: rotate(0deg) scale(1); }}
            }}
            .particula-caindo {{
                position: absolute; font-size: 22px; pointer-events: none; z-index: 7;
                animation: animarParticula 1.5s ease-out forwards;
            }}
            @keyframes animarParticula {{
                0% {{ transform: translate(0, 0) rotate(0deg) scale(1); opacity: 1; }}
                50% {{ transform: translate(16px, 25px) rotate(140deg) scale(1.1); opacity: 0.9; }}
                100% {{ transform: translate(-12px, 65px) rotate(280deg) scale(0.7); opacity: 0; }}
            }}
            #relampago {{
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(255, 255, 255, 0.85); pointer-events: none;
                opacity: 0; z-index: 5; transition: opacity 0.08s ease-out;
            }}
            #arco-iris {{
                position: absolute; top: 8%; left: 50%; transform: translateX(-50%);
                width: 120vw; max-width: 850px; height: 60vw; max-height: 420px;
                border-radius: 50% 50% 0 0 / 100% 100% 0 0;
                background: radial-gradient(circle at 50% 100%,
                    transparent 48%, rgba(148,0,211,0.35) 52%, rgba(0,119,255,0.4) 56%,
                    rgba(0,200,80,0.4) 60%, rgba(255,230,0,0.45) 64%, rgba(255,20,20,0.4) 68%, transparent 72%);
                filter: blur(6px); pointer-events: none; opacity: 0; transition: opacity 0.8s; z-index: 1;
            }}
            #arco-iris.ativo {{ opacity: 1; }}
            #efeitos-container {{
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                pointer-events: none; overflow: hidden; z-index: 3;
            }}
            .gota {{
                position: absolute; width: 2px; height: 20px;
                background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0.85));
                animation: cair linear infinite;
            }}
            @keyframes cair {{
                0% {{ transform: translate(0, -20px) rotate(12deg); }}
                100% {{ transform: translate(-35px, 105vh) rotate(12deg); }}
            }}
            .bolha {{
                position: absolute; bottom: -20px; border-radius: 50%;
                border: 2px solid rgba(255,255,255,0.7); background: rgba(255,255,255,0.2);
                animation: subir linear infinite;
            }}
            @keyframes subir {{
                0% {{ transform: translateY(0) scale(0.8); opacity: 0.8; }}
                100% {{ transform: translateY(-105vh) scale(1.3); opacity: 0; }}
            }}
            .estrela {{
                position: absolute; background: white; border-radius: 50%;
                box-shadow: 0 0 8px #FFF; animation: piscar 1.5s infinite alternate;
            }}
            @keyframes piscar {{
                0% {{ opacity: 0.2; transform: scale(0.8); }}
                100% {{ opacity: 1; transform: scale(1.3); }}
            }}
            .placa {{
                background: {cfg['placa_bg']}; color: {cfg['placa_cor']}; border: 3px solid #003366;
                padding: 6px 16px; border-radius: 14px; font-size: clamp(13px, 3vw, 18px);
                font-weight: bold; text-align: center; z-index: 10;
            }}
            .bicho {{
                position: absolute; font-size: 52px; cursor: grab; z-index: 6;
                touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3));
            }}
            .bicho:active {{ cursor: grabbing; transform: scale(1.2); }}
            #barra {{
                background: rgba(255, 255, 255, 0.94); padding: 8px 12px; border-radius: 22px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 10;
                display: flex; justify-content: center; align-items: center; gap: 6px;
                flex-wrap: wrap; max-width: 96%;
            }}
            .btn-item {{
                font-size: 24px; border: 2px solid #FFD700; background: #FFF8DC;
                border-radius: 14px; padding: 4px 8px; cursor: pointer;
            }}
            .btn-acao {{
                font-size: 14px; font-weight: bold; border: none; border-radius: 14px;
                padding: 8px 11px; cursor: pointer;
            }}
        </style>
    </head>
    <body>
    <div id="cenario">
        {decoracao_cenario}
        <div id="relampago"></div>
        <div id="arco-iris"></div>
        <div id="efeitos-container"></div>
        <div class="placa">{cfg['titulo']}</div>
        <div id="palco"></div>
        <div id="barra">
            {botoes_itens}
            <button class="btn-acao" style="background:#FFD700; color:#333;" onclick="alternarClima()">🌦️ Clima</button>
            <button class="btn-acao" style="background:#FF6B6B; color:white;" onclick="limpar()">🗑️</button>
        </div>
    </div>
    <script>
        let estadoClima = 0;
        let timerTrovao = null;
        const tipoClima = "{cfg['clima_extra']}";
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        function somToqueFundo(tipo) {{
            if (audioCtx.state === 'suspended') audioCtx.resume();
            const agora = audioCtx.currentTime;
            if (tipo === 'folha') {{
                const bufferSize = audioCtx.sampleRate * 0.45;
                const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
                const data = buffer.getChannelData(0);
                for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
                const noise = audioCtx.createBufferSource();
                noise.buffer = buffer;
                const filtro = audioCtx.createBiquadFilter();
                filtro.type = 'bandpass';
                filtro.frequency.setValueAtTime(900, agora);
                const ganho = audioCtx.createGain();
                ganho.gain.setValueAtTime(0.01, agora);
                ganho.gain.linearRampToValueAtTime(0.18, agora + 0.1);
                ganho.gain.exponentialRampToValueAtTime(0.001, agora + 0.45);
                noise.connect(filtro); filtro.connect(ganho); ganho.connect(audioCtx.destination);
                noise.start(agora);
            }} else {{
                const osc = audioCtx.createOscillator();
                const ganho = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(tipo === 'bolha' ? 320 : 520, agora);
                osc.frequency.exponentialRampToValueAtTime(tipo === 'bolha' ? 680 : 980, agora + 0.25);
                ganho.gain.setValueAtTime(0.15, agora);
                ganho.gain.exponentialRampToValueAtTime(0.001, agora + 0.25);
                osc.connect(ganho); ganho.connect(audioCtx.destination);
                osc.start(agora); osc.stop(agora + 0.25);
            }}
        }}

        function chacoalharFundo(el, tipo) {{
            el.classList.remove('xagualhar');
            void el.offsetWidth;
            el.classList.add('xagualhar');
            somToqueFundo(tipo);

            const cenario = document.getElementById('cenario');
            const rect = el.getBoundingClientRect();
            const cRect = cenario.getBoundingClientRect();

            for (let i = 0; i < 4; i++) {{
                const p = document.createElement('div');
                p.className = 'particula-caindo';
                if (tipo === 'folha') p.innerText = Math.random() > 0.3 ? '🍃' : '🍂';
                else if (tipo === 'bolha') p.innerText = '🫧';
                else p.innerText = '✨';
                p.style.left = (rect.left - cRect.left + 15 + Math.random() * 40) + 'px';
                p.style.top = (rect.top - cRect.top + 10 + Math.random() * 25) + 'px';
                cenario.appendChild(p);
                setTimeout(() => p.remove(), 1500);
            }}
        }}

        function dispararTrovao() {{
            if (estadoClima !== 1 || tipoClima !== 'chuva_arcoiris') return;
            const flash = document.getElementById('relampago');
            flash.style.opacity = '0.85';
            setTimeout(() => {{ flash.style.opacity = '0'; }}, 90);
            setTimeout(() => {{ flash.style.opacity = '0.5'; }}, 160);
            setTimeout(() => {{ flash.style.opacity = '0'; }}, 260);

            if (audioCtx.state === 'suspended') audioCtx.resume();
            const agora = audioCtx.currentTime;
            const bufferSize = audioCtx.sampleRate * 1.6;
            const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
            const data = buffer.getChannelData(0);
            for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;

            const noise = audioCtx.createBufferSource();
            noise.buffer = buffer;

            const filtro = audioCtx.createBiquadFilter();
            filtro.type = 'lowpass';
            filtro.frequency.setValueAtTime(160, agora);
            filtro.frequency.exponentialRampToValueAtTime(45, agora + 1.5);

            const ganho = audioCtx.createGain();
            ganho.gain.setValueAtTime(0.01, agora);
            ganho.gain.linearRampToValueAtTime(0.5, agora + 0.15);
            ganho.gain.exponentialRampToValueAtTime(0.001, agora + 1.6);

            noise.connect(filtro);
            filtro.connect(ganho);
            ganho.connect(audioCtx.destination);
            noise.start(agora);

            timerTrovao = setTimeout(dispararTrovao, 3500 + Math.random() * 4500);
        }}

        function alternarClima() {{
            const div = document.getElementById('efeitos-container');
            const arco = document.getElementById('arco-iris');
            div.innerHTML = '';
            arco.classList.remove('ativo');
            clearTimeout(timerTrovao);

            if (tipoClima === 'chuva_arcoiris') {{
                estadoClima = (estadoClima + 1) % 3;
                if (estadoClima === 1) {{
                    for (let i = 0; i < 50; i++) {{
                        const g = document.createElement('div');
                        g.className = 'gota';
                        g.style.left = Math.random() * 100 + 'vw';
                        g.style.animationDuration = (Math.random() * 0.4 + 0.5) + 's';
                        g.style.animationDelay = Math.random() + 's';
                        div.appendChild(g);
                    }}
                    setTimeout(dispararTrovao, 600);
                }} else if (estadoClima === 2) {{
                    arco.classList.add('ativo');
                }}
            }} else if (tipoClima === 'bolhas') {{
                estadoClima = (estadoClima + 1) % 2;
                if (estadoClima === 1) {{
                    for (let i = 0; i < 35; i++) {{
                        const b = document.createElement('div');
                        b.className = 'bolha';
                        const tam = (Math.random() * 14 + 6) + 'px';
                        b.style.width = tam; b.style.height = tam;
                        b.style.left = Math.random() * 100 + 'vw';
                        b.style.animationDuration = (Math.random() * 2 + 2) + 's';
                        b.style.animationDelay = (Math.random() * 2) + 's';
                        div.appendChild(b);
                    }}
                }}
            }} else if (tipoClima === 'estrelas') {{
                estadoClima = (estadoClima + 1) % 2;
                if (estadoClima === 1) {{
                    for (let i = 0; i < 45; i++) {{
                        const e = document.createElement('div');
                        e.className = 'estrela';
                        const tam = (Math.random() * 4 + 2) + 'px';
                        e.style.width = tam; e.style.height = tam;
                        e.style.left = Math.random() * 100 + 'vw';
                        e.style.top = Math.random() * 85 + 'vh';
                        e.style.animationDelay = (Math.random() * 2) + 's';
                        div.appendChild(e);
                    }}
                }}
            }}
        }}

        function criarNaPosicao(emoji, xPct, yPct) {{
            const palco = document.getElementById('palco');
            const el = document.createElement('div');
            el.className = 'bicho'; el.innerText = emoji;
            el.style.left = xPct + 'vw';
            el.style.top = yPct + 'vh';
            let drag = false, ox = 0, oy = 0;
            el.onpointerdown = e => {{
                drag = true; const r = el.getBoundingClientRect();
                ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId);
            }};
            el.onpointermove = e => {{
                if (!drag) return;
                el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 60)) + 'px';
                el.style.top = Math.max(45, Math.min(e.clientY - oy, window.innerHeight - 120)) + 'px';
            }};
            el.onpointerup = e => {{ drag = false; el.releasePointerCapture(e.pointerId); }};
            palco.appendChild(el);
        }}

        function criar(emoji) {{
            criarNaPosicao(emoji, 15 + Math.random() * 65, 50 + Math.random() * 25);
        }}

        function limpar() {{ document.getElementById('palco').innerHTML = ''; }}
        {espalhados_js}
    </script>
    </body>
    </html>
    """

    components.html(html_cenario, height=700, scrolling=False)
