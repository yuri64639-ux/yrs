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
                height: 130px;
                border-radius: 25px !important;
                border: 4px solid white !important;
                font-size: clamp(18px, 3.8vw, 24px) !important;
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
            "titulo": "🏫 EM Pato Donald - Clique na Escola para entrar na Sala!",
            "fundo": "linear-gradient(to bottom, #64B5F6 0%, #B3E5FC 48%, #E6B88A 48%, #558B2F 60%, #33691E 100%)",
            "placa_bg": "#FFD700", "placa_cor": "#003366",
            "itens": ["MENINA", "MENINO", "🦆", "ESCORREGADOR", "BALANCO", "GANGORRA"],
            "espalhados": [
                ("MENINA", 28, 52), ("MENINO", 40, 52), ("MENINA", 68, 72), ("🦆", 10, 74),
                ("ESCORREGADOR", 52, 48), ("BALANCO", 76, 48), ("GANGORRA", 36, 70)
            ],
            "clima_extra": "chuva_arcoiris"
        },
        "represa": {
            "titulo": "🌊 Represa Municipal - Clique no Ninho para cuidar dos bebês!",
            "fundo": "linear-gradient(to bottom, #4FC3F7 0%, #E1F5FE 35%, #0288D1 35%, #01579B 64%, #78909C 64%, #607D8B 72%, #388E3C 72%, #1B5E20 100%)",
            "placa_bg": "#00CED1", "placa_cor": "#003366",
            "itens": ["CAPIVARA", "PEIXE_DOURADO", "CICLISTA", "CAMINHANTE", "🧼", "🌽"],
            "espalhados": [
                ("🦢", 12, 42), ("PEIXE_DOURADO", 28, 48), ("PEIXE_TILAPIA", 56, 52),
                ("CICLISTA", 18, 61), ("CAMINHANTE", 52, 62), ("CICLISTA", 76, 61),
                ("CAPIVARA", 10, 74), ("CAPIVARA", 26, 75), ("🧼", 44, 75), ("🌽", 54, 75)
            ],
            "clima_extra": "chuva_arcoiris"
        },
        "oceano": {
            "titulo": "🐠 Mundo do Oceano Azul",
            "fundo": "linear-gradient(to bottom, #26C6DA 0%, #0277BD 45%, #012A4A 100%)",
            "placa_bg": "#00008B", "placa_cor": "#FFFFFF",
            "itens": ["🐳", "🐬", "PEIXE_DOURADO", "🐢", "🐙", "🦀"],
            "espalhados": [
                ("🐳", 14, 28), ("🐬", 48, 28), ("PEIXE_DOURADO", 78, 30),
                ("🐢", 22, 48), ("🐙", 54, 48), ("PEIXE_TILAPIA", 80, 48),
                ("🦈", 16, 68), ("🦀", 48, 70), ("🦞", 76, 70)
            ],
            "clima_extra": "bolhas"
        },
        "espaco": {
            "titulo": "🚀 Viagem pelo Espaço Sideral",
            "fundo": "radial-gradient(circle, #1B2735 0%, #090A0F 100%)",
            "placa_bg": "#4B0082", "placa_cor": "#FFFFFF",
            "itens": ["🚀", "🛸", "👨‍🚀", "👽", "🐶", "🛰️"],
            "espalhados": [
                ("🚀", 16, 26), ("🛰️", 48, 24), ("🛸", 74, 28),
                ("👨‍🚀", 26, 54), ("👽", 66, 54), ("🐶", 46, 71)
            ],
            "clima_extra": "estrelas"
        },
        "aeroporto": {
            "titulo": "✈️ Aeroporto de São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #64B5F6 0%, #BBDEFB 48%, #4CAF50 48%, #2E7D32 62%, #37474F 62%, #263238 88%, #2E7D32 88%)",
            "placa_bg": "#1565C0", "placa_cor": "#FFFFFF",
            "itens": ["✈️", "🚁", "🛩️", "🧳", "👨‍✈️", "🚌"],
            "espalhados": [
                ("✈️", 14, 22), ("🚁", 68, 20), ("🛩️", 40, 32),
                ("✈️", 20, 64), ("🧳", 46, 75), ("👨‍✈️", 66, 73), ("🚌", 82, 65)
            ],
            "clima_extra": "chuva_arcoiris"
        }
    }
    cfg = mundos[st.session_state.tela_atual]
    icones_btn = {
        "CAPIVARA": "🐾 Capivara",
        "PEIXE_DOURADO": "🐟 Peixe",
        "CICLISTA": "🚴 Ciclista",
        "CAMINHANTE": "🚶 Pessoa",
        "MENINA": "👧 Menina",
        "MENINO": "👦 Menino",
        "ESCORREGADOR": "🛝 Escorrega",
        "BALANCO": "⛓️ Balanço",
        "GANGORRA": "⚖️ Gangorra"
    }
    botoes_itens = "".join([f'<button class="btn-item" onclick="criar(\'{i}\')">{icones_btn.get(i, i)}</button>' for i in cfg["itens"]])
    espalhados_js = "".join([f"criarNaPosicao('{emoji}', {x}, {y});" for emoji, x, y in cfg["espalhados"]])

    ceu_interativo = """
        <div class="camada-ceu" style="top: 7%;">
            <span class="item-ceu sol-lua-btn" onclick="alternarDiaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="interagirNuvem(this, 'chuva')">☁️</span>
            <span class="item-ceu" onclick="interagirPassaro(this)">🐦</span>
            <span class="item-ceu" onclick="interagirNuvem(this, 'passaro')">☁️</span>
            <span class="item-ceu" onclick="interagirPassaro(this)">🕊️</span>
        </div>
    """

    decoracao_cenario = ""
    if st.session_state.tela_atual == "represa":
        decoracao_cenario = ceu_interativo + """
        <svg viewBox="0 0 1000 320" preserveAspectRatio="none" style="position:absolute; top:14%; left:0; width:100%; height:44%; pointer-events:none; z-index:2;">
            <path d="M0,190 Q250,175 500,190 T1000,190 L1000,210 L0,210 Z" fill="#1B5E20"/>
            <path d="M 270 198 Q 500 130 730 198" fill="none" stroke="#D32F2F" stroke-width="11" stroke-linecap="round"/>
            <rect x="240" y="196" width="520" height="13" rx="4" fill="#E53935"/>
        </svg>
        <div class="pista-riopreto"><div class="faixa-ciclovia"></div><div class="faixa-pedestre"></div></div>
        <div id="ninho-capivaras" class="ninho-capivaras" onclick="abrirNinhoCapivaras()" title="Toque para cuidar dos bebês capivaras!">
            <svg viewBox="0 0 180 95" width="100%" height="100%">
                <ellipse cx="90" cy="68" rx="84" ry="24" fill="#795548" stroke="#3E2723" stroke-width="3"/><ellipse cx="90" cy="66" rx="68" ry="16" fill="#D7CCC8"/>
            </svg>
            <div class="placa-ninho">🍼 Ninho dos Bebês (Clique!)</div>
        </div>
        <div class="elementos-fundo" style="top: 50%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌲</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
        </div>
        """
    elif st.session_state.tela_atual == "escola":
        decoracao_cenario = ceu_interativo + """
        <div class="predio-escola-clicavel" onclick="abrirSalaAula()" title="Toque para entrar na sala de aula!">
            <svg viewBox="0 0 360 195" width="100%" height="100%">
                <polygon points="10,65 180,15 350,65" fill="#D62828" stroke="#8D0801" stroke-width="3"/>
                <rect x="25" y="65" width="310" height="105" fill="#1E88E5" stroke="#0D47A1" stroke-width="3"/>
                <rect x="45" y="72" width="270" height="24" rx="4" fill="#FFD700" stroke="#003366" stroke-width="2"/>
                <text x="180" y="88" font-family="Comic Sans MS, sans-serif" font-size="13" font-weight="bold" fill="#003366" text-anchor="middle">EM PATO DONALD</text>
                <rect x="155" y="115" width="50" height="55" rx="3" fill="#FFD700" stroke="#003366" stroke-width="2"/>
            </svg>
            <div class="aviso-entrar-sala">🚪 Entrar na Sala</div>
        </div>
        <div id="piscina-escola" class="piscina-escola">
            <div class="agua-piscina"></div>
            <div class="placa-piscina">🏊 Piscina</div>
        </div>
        <div class="elementos-fundo" style="top: 35%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌲</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
        </div>
        """
    elif st.session_state.tela_atual == "aeroporto":
        decoracao_cenario = ceu_interativo + """
        <svg viewBox="0 0 800 200" preserveAspectRatio="none" style="position:absolute; top:24%; left:0; width:100%; height:28%; pointer-events:none; z-index:2;">
            <rect x="60" y="90" width="240" height="80" rx="6" fill="#ECEFF1" stroke="#546E7A" stroke-width="3"/>
            <path d="M 55 90 Q 180 40 305 90 Z" fill="#1565C0"/>
            <rect x="330" y="45" width="36" height="125" fill="#CFD8DC" stroke="#455A64" stroke-width="3"/>
            <polygon points="315,45 381,45 370,15 326,15" fill="#263238"/>
        </svg>
        <div style="position:absolute; top:74%; left:0; width:100%; height:4px; background:repeating-linear-gradient(90deg, #FFFFFF, #FFFFFF 45px, transparent 45px, transparent 85px); pointer-events:none; z-index:2;"></div>
        <div class="elementos-fundo" style="top: 38%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌲</span>
        </div>
        """
    elif st.session_state.tela_atual == "oceano":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 8%;">
            <span class="item-ceu sol-lua-btn" onclick="alternarDiaNoite(this)">☀️</span>
            <span class="item-agua" onclick="interagirAgua(this)">⛵</span>
            <span class="item-ceu" onclick="interagirPassaro(this)">🕊️</span>
        </div>
        <div class="elementos-fundo" style="top: 68%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🪸</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🌿</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🐚</span>
        </div>
        """
    elif st.session_state.tela_atual == "espaco":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 9%;">
            <span class="item-ceu" onclick="interagirCeu(this, 'estrela')">🌠</span>
            <span class="item-ceu sol-lua-btn" onclick="alternarDiaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'estrela')">🌠</span>
        </div>
        <div class="elementos-fundo" style="top: 18%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">🪐</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">🌕</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">☄️</span>
        </div>
        """
    modais_extras_html = ""
    if st.session_state.tela_atual == "escola":
        modais_extras_html = """
        <div id="modal-sala" style="display:none; position:absolute; inset:0; background:linear-gradient(to bottom, #FFF8E1 0%, #FFE082 78%, #8D6E63 78%, #5D4037 100%); z-index:30; flex-direction:column; justify-content:space-between; align-items:center; padding:10px; border-radius:20px;">
            <div style="width:100%; display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <button onclick="fecharSalaAula()" style="background:#FF6B6B; color:white; border:2px solid white; border-radius:14px; padding:6px 12px; font-weight:bold; font-size:15px; cursor:pointer;">⬅️ Sair para o Pátio</button>
                <div style="background:#FFD700; color:#003366; border:3px solid #003366; border-radius:14px; padding:4px 12px; font-weight:bold; font-size:clamp(13px,3vw,17px);">👩‍🏫 Sala de Aula - EM Pato Donald</div>
                <button onclick="limparLousa()" style="background:#1565C0; color:white; border:2px solid white; border-radius:14px; padding:6px 12px; font-weight:bold; font-size:15px; cursor:pointer;">🧽 Apagar</button>
            </div>
            <div style="position:relative; width:94%; height:64%; background:#1B5E20; border:10px solid #6D4C41; border-radius:16px; box-shadow:0 8px 20px rgba(0,0,0,0.35); overflow:hidden;">
                <canvas id="lousa-canvas" style="width:100%; height:100%; display:block; cursor:crosshair; touch-action:none;"></canvas>
                <div onclick="interagirProfessora(this)" style="position:absolute; bottom:4px; left:8px; display:flex; align-items:flex-end; gap:6px; cursor:pointer; z-index:5;">
                    <span style="font-size:clamp(54px, 11vw, 84px); line-height:1;">👩‍🏫</span>
                    <div id="fala-professora" style="background:white; color:#003366; border:2px solid #003366; border-radius:14px; padding:5px 10px; font-size:clamp(12px, 2.5vw, 15px); font-weight:bold; margin-bottom:24px;">Desenhe na lousa! ✏️</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.95); padding:8px 14px; border-radius:20px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:center;">
                <span style="font-weight:bold; color:#333; font-size:14px;">Giz:</span>
                <button onclick="mudarCorGiz('#FFFFFF')" style="width:30px; height:30px; border-radius:50%; background:#FFFFFF; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="mudarCorGiz('#FFEB3B')" style="width:30px; height:30px; border-radius:50%; background:#FFEB3B; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="mudarCorGiz('#FF5252')" style="width:30px; height:30px; border-radius:50%; background:#FF5252; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="mudarCorGiz('#40C4FF')" style="width:30px; height:30px; border-radius:50%; background:#40C4FF; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="carimbarLousa('⭐')" style="font-size:20px; border:2px solid #FFD700; background:#FFF8DC; border-radius:10px; padding:2px 8px; cursor:pointer;">⭐</button>
                <button onclick="carimbarLousa('🦆')" style="font-size:20px; border:2px solid #FFD700; background:#FFF8DC; border-radius:10px; padding:2px 8px; cursor:pointer;">🦆</button>
            </div>
        </div>
        """
    elif st.session_state.tela_atual == "represa":
        modais_extras_html = """
        <div id="modal-ninho" style="display:none; position:absolute; inset:0; background:radial-gradient(circle, #D7CCC8 0%, #8D6E63 55%, #3E2723 100%); z-index:30; flex-direction:column; justify-content:space-between; align-items:center; padding:12px; border-radius:20px;">
            <div style="width:100%; display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <button onclick="fecharNinhoCapivaras()" style="background:#FF6B6B; color:white; border:2px solid white; border-radius:14px; padding:6px 12px; font-weight:bold; font-size:15px; cursor:pointer;">⬅️ Sair do Ninho</button>
                <div style="background:#FFD700; color:#3E2723; border:3px solid #3E2723; border-radius:14px; padding:4px 12px; font-weight:bold; font-size:clamp(13px,3vw,17px);">🐾 Berçário das Capivaras</div>
                <div style="width:70px;"></div>
            </div>
            <div style="position:relative; width:92%; height:64%; background:radial-gradient(ellipse at center, #FFF8E1 0%, #EFEBE9 65%, #A1887F 100%); border:8px solid #5D4037; border-radius:50%; box-shadow: inset 0 6px 18px rgba(0,0,0,0.35); display:flex; justify-content:space-around; align-items:center; padding:16px;">
                <div class="bebe-capivara" id="bebe-1" onclick="acariciarBebe(this)" style="text-align:center; cursor:pointer;">
                    <svg viewBox="0 0 84 60" width="96" height="68"><ellipse cx="40" cy="34" rx="24" ry="14" fill="#8D6E63" stroke="#3E2723" stroke-width="1.5"/><rect x="50" y="15" width="22" height="17" rx="7" fill="#A1887F" stroke="#3E2723" stroke-width="1.5"/><circle cx="61" cy="21" r="2.2" fill="#1A1A1A"/><path d="M22 30 Q34 26 42 36 L24 44 Z" fill="#FFFFFF" stroke="#90CAF9" stroke-width="1.5"/></svg>
                    <div class="status-bebe" style="background:white; border:2px solid #5D4037; border-radius:10px; padding:2px 8px; font-size:12px; font-weight:bold; color:#3E2723;">🍼 Com fome!</div>
                </div>
                <div class="bebe-capivara" id="bebe-2" onclick="acariciarBebe(this)" style="text-align:center; cursor:pointer;">
                    <svg viewBox="0 0 84 60" width="96" height="68"><ellipse cx="40" cy="34" rx="24" ry="14" fill="#8D6E63" stroke="#3E2723" stroke-width="1.5"/><rect x="50" y="15" width="22" height="17" rx="7" fill="#A1887F" stroke="#3E2723" stroke-width="1.5"/><circle cx="61" cy="21" r="2.2" fill="#1A1A1A"/><path d="M22 30 Q34 26 42 36 L24 44 Z" fill="#FFF59D" stroke="#FBC02D" stroke-width="1.5"/></svg>
                    <div class="status-bebe" style="background:white; border:2px solid #5D4037; border-radius:10px; padding:2px 8px; font-size:12px; font-weight:bold; color:#3E2723;">🧷 Trocar fralda!</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.95); padding:8px 14px; border-radius:20px; display:flex; gap:12px; align-items:center; justify-content:center; box-shadow:0 4px 12px rgba(0,0,0,0.25);">
                <button onclick="cuidarBebes('mamadeira')" style="font-size:16px; font-weight:bold; border:2px solid #1976D2; background:#E3F2FD; color:#0D47A1; border-radius:14px; padding:8px 14px; cursor:pointer;">🍼 Dar Mamadeira</button>
                <button onclick="cuidarBebes('fralda')" style="font-size:16px; font-weight:bold; border:2px solid #388E3C; background:#E8F5E9; color:#1B5E20; border-radius:14px; padding:8px 14px; cursor:pointer;">🧷 Trocar Fralda</button>
            </div>
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
            body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Comic Sans MS', sans-serif; overflow: hidden; user-select: none; touch-action: none; }}
            #cenario {{ width: 100%; height: 100%; background: {cfg['fundo']}; border-radius: 20px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 12px; position: relative; transition: background 0.8s ease; }}
            #camada-noite {{ position: absolute; inset: 0; border-radius: 20px; background: linear-gradient(to bottom, rgba(7, 13, 38, 0.86) 0%, rgba(15, 25, 65, 0.65) 55%, rgba(5, 10, 25, 0.58) 100%); opacity: 0; pointer-events: none; z-index: 2; transition: opacity 0.8s ease; }}
            #cenario.modo-noite #camada-noite {{ opacity: 1; }}
            .estrela-noite {{ position: absolute; background: #FFFDE7; border-radius: 50%; box-shadow: 0 0 8px #FFF59D; animation: piscar 1.6s infinite alternate; }}
            .camada-ceu, .camada-agua {{ position: absolute; left: 0; width: 100%; display: flex; justify-content: space-around; align-items: center; z-index: 5; pointer-events: none; }}
            .item-ceu, .item-agua {{ font-size: clamp(38px, 7.5vw, 58px); cursor: pointer; pointer-events: auto; display: inline-block; }}
            .predio-escola-clicavel {{ position: absolute; top: 24%; left: 3%; width: clamp(175px, 30vw, 260px); cursor: pointer; z-index: 5; transition: transform 0.2s; filter: drop-shadow(0 6px 8px rgba(0,0,0,0.28)); }}
            .predio-escola-clicavel:hover {{ transform: scale(1.04); }}
            .aviso-entrar-sala {{ position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%); background: #FFD700; color: #003366; border: 2px solid #003366; border-radius: 12px; padding: 2px 10px; font-size: 11px; font-weight: bold; white-space: nowrap; }}
            .piscina-escola {{ position: absolute; bottom: 13%; left: 3%; width: clamp(160px, 28vw, 240px); height: clamp(68px, 12vw, 95px); background: #ECEFF1; border: 4px solid #90A4AE; border-radius: 16px; z-index: 4; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.25); }}
            .agua-piscina {{ width: 100%; height: 100%; background: linear-gradient(to bottom, #4FC3F7, #0288D1); opacity: 0.9; }}
            .placa-piscina {{ position: absolute; top: 2px; right: 6px; background: rgba(255,255,255,0.85); color: #01579B; border-radius: 8px; padding: 1px 6px; font-size: 10px; font-weight: bold; }}
            .ninho-capivaras {{ position: absolute; bottom: 13%; right: 4%; width: clamp(145px, 27vw, 210px); height: clamp(72px, 13vw, 105px); z-index: 5; cursor: pointer; transition: transform 0.25s; }}
            .ninho-capivaras:hover {{ transform: scale(1.06); }}
            .placa-ninho {{ position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%); background: #FFD700; color: #3E2723; border: 2px solid #3E2723; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: bold; white-space: nowrap; }}
            .pista-riopreto {{ position: absolute; top: 64%; left: 0; width: 100%; height: 8%; pointer-events: none; z-index: 2; }}
            .faixa-ciclovia {{ width: 100%; height: 32%; background: rgba(214, 40, 40, 0.75); border-bottom: 2px dashed #FFFFFF; }}
            .faixa-pedestre {{ width: 100%; height: 68%; background: repeating-linear-gradient(90deg, transparent, transparent 30px, #FFD166 30px, #FFD166 55px); background-size: 100% 3px; background-repeat: no-repeat; background-position: center; }}
            .elementos-fundo {{ position: absolute; left: 0; width: 100%; display: flex; justify-content: space-around; align-items: flex-end; z-index: 4; pointer-events: none; }}
            .item-fundo-interativo {{ font-size: clamp(44px, 9vw, 72px); cursor: pointer; pointer-events: auto; transform-origin: bottom center; display: inline-block; }}
            .xagualhar {{ animation: balancarItem 0.65s ease-in-out; }}
            @keyframes balancarItem {{ 0%, 100% {{ transform: rotate(0deg); }} 25% {{ transform: rotate(-10deg); }} 50% {{ transform: rotate(9deg); }} 75% {{ transform: rotate(-6deg); }} }}
            .girar-ceu {{ animation: giroNoCeu 0.8s ease-in-out; }}
            @keyframes giroNoCeu {{ 0% {{ transform: scale(1) rotate(0deg); }} 50% {{ transform: scale(1.25) rotate(180deg); }} 100% {{ transform: scale(1) rotate(360deg); }} }}
            .particula-caindo {{ position: absolute; font-size: 22px; pointer-events: none; z-index: 12; animation: animarParticula 1.5s ease-out forwards; }}
            @keyframes animarParticula {{ 0% {{ opacity: 1; }} 100% {{ transform: translate(-12px, -55px) rotate(280deg) scale(0.7); opacity: 0; }} }}
            #efeitos-container {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: hidden; z-index: 3; }}
            .gota {{ position: absolute; width: 2px; height: 20px; background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.85)); animation: cair linear infinite; }}
            @keyframes cair {{ 0% {{ transform: translate(0, -20px) rotate(12deg); }} 100% {{ transform: translate(-35px, 105vh) rotate(12deg); }} }}
            .bolha {{ position: absolute; bottom: -20px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.7); background: rgba(255,255,255,0.2); animation: subir linear infinite; }}
            @keyframes subir {{ 0% {{ transform: translateY(0); opacity: 0.8; }} 100% {{ transform: translateY(-105vh) scale(1.3); opacity: 0; }} }}
            .estrela {{ position: absolute; background: white; border-radius: 50%; box-shadow: 0 0 8px #FFF; animation: piscar 1.5s infinite alternate; }}
            @keyframes piscar {{ 0% {{ opacity: 0.2; }} 100% {{ opacity: 1; transform: scale(1.3); }} }}
            .placa {{ background: {cfg['placa_bg']}; color: {cfg['placa_cor']}; border: 3px solid #003366; padding: 6px 16px; border-radius: 14px; font-size: clamp(13px, 3vw, 18px); font-weight: bold; text-align: center; z-index: 10; }}
            .bicho {{ position: absolute; font-size: 46px; cursor: grab; z-index: 6; touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3)); }}
            .bicho.brinquedo {{ z-index: 5; }}
            .bicho.brincando {{ z-index: 7; }}
            .bicho:active {{ cursor: grabbing; transform: scale(1.18); }}
            .conteudo-bicho {{ display: inline-block; }}
            .nadando .conteudo-bicho {{ animation: boiarNaAgua 1.1s infinite alternate ease-in-out; }}
            @keyframes boiarNaAgua {{ 0% {{ transform: translateY(-3px) rotate(-4deg); }} 100% {{ transform: translateY(4px) rotate(4deg); }} }}
            .salto-peixe .conteudo-bicho {{ animation: saltarForaAgua 0.75s ease-out; }}
            @keyframes saltarForaAgua {{ 0% {{ transform: translateY(0) rotate(0deg); }} 45% {{ transform: translateY(-48px) rotate(-32deg) scale(1.12); }} 100% {{ transform: translateY(0) rotate(0deg); }} }}
            .voando .conteudo-bicho {{ animation: flutuarNoAr 1.4s infinite alternate ease-in-out; }}
            @keyframes flutuarNoAr {{ 0% {{ transform: translateY(-6px) rotate(-3deg); }} 100% {{ transform: translateY(6px) rotate(3deg); }} }}
            .balancando-brinquedo .conteudo-bicho {{ transform-origin: top center; animation: balancarNoBrinquedo 0.85s infinite alternate ease-in-out; }}
            @keyframes balancarNoBrinquedo {{ 0% {{ transform: rotate(-22deg) translateX(-10px); }} 100% {{ transform: rotate(22deg) translateX(10px); }} }}
            .gangorra-brinquedo .conteudo-bicho {{ animation: gangorraSobeDesce 0.9s infinite alternate ease-in-out; }}
            @keyframes gangorraSobeDesce {{ 0% {{ transform: translateY(-14px) rotate(-8deg); }} 100% {{ transform: translateY(10px) rotate(8deg); }} }}
            #barra {{ background: rgba(255, 255, 255, 0.94); padding: 8px 12px; border-radius: 22px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 10; display: flex; justify-content: center; align-items: center; gap: 6px; flex-wrap: wrap; max-width: 96%; }}
            .btn-item {{ font-size: 15px; font-weight: bold; border: 2px solid #FFD700; background: #FFF8DC; color: #003366; border-radius: 14px; padding: 6px 10px; cursor: pointer; }}
            .btn-acao {{ font-size: 14px; font-weight: bold; border: none; border-radius: 14px; padding: 8px 11px; cursor: pointer; }}
        </style>
    </head>
    <body>
    <div id="cenario">
        <div id="camada-noite"></div>
        {decoracao_cenario}
        {modais_extras_html}
        <div id="efeitos-container"></div>
        <div class="placa">{cfg['titulo']}</div>
        <div id="palco"></div>
        <div id="barra">
            {botoes_itens}
            <button class="btn-acao" style="background:#4CAF50; color:white;" onclick="organizar()">🔄 Organizar</button>
            <button class="btn-acao" style="background:#FF6B6B; color:white;" onclick="limpar()">🗑️</button>
        </div>
    </div>
    <script>
        let ehNoite = false;
        let ultimoBanho = 0;
        let ctxLousa = null;
        let desenhandoLousa = false;
        let corGizAtual = '#FFFFFF';
        const mundoAtual = "{st.session_state.tela_atual}";
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        const tiposPeixes = ['PEIXE_DOURADO', 'PEIXE_TILAPIA', '🐠', '🐡', '🦈'];
        const tiposAnimais = ['CAPIVARA', 'PEIXE_DOURADO', 'PEIXE_TILAPIA', '🦆', '🦢', '🐶', '🐳', '🐬', '🐠', '🐢', '🐙', '🦀', '🐡', '🦈', '🦞'];
        const tiposPessoas = ['MENINA', 'MENINO', 'CICLISTA', 'CAMINHANTE', '👨‍🚀', '👨‍✈️', '👽'];
        const tiposBrinquedos = ['ESCORREGADOR', 'BALANCO', 'GANGORRA'];
        const tiposAereos = ['✈️', '🚁', '🛩️', '🚀', '🛸', '🛰️'];
        const tiposPista = ['CICLISTA', 'CAMINHANTE', '🚌'];
        const tiposBanho = ['🧼', '🚿'];
        const tiposComida = ['🌽', '🍎', '🌿'];

        const svgsObjetos = {{
            'CAPIVARA': '<svg viewBox="0 0 84 60" width="74" height="52"><ellipse cx="40" cy="54" rx="26" ry="4.5" fill="rgba(0,0,0,0.28)"/><rect x="20" y="42" width="7" height="12" rx="3" fill="#4E342E"/><rect x="50" y="42" width="7" height="12" rx="3" fill="#4E342E"/><ellipse cx="40" cy="33" rx="25" ry="15" fill="#795548" stroke="#3E2723" stroke-width="1.5"/><rect x="50" y="13" width="24" height="19" rx="8" fill="#8D6E63" stroke="#3E2723" stroke-width="1.5"/><circle cx="62" cy="19" r="2.2" fill="#1A1A1A"/></svg>',
            'PEIXE_DOURADO': '<svg viewBox="0 0 92 52" width="72" height="42"><path d="M24 26 L5 11 L12 26 L5 41 Z" fill="#E65100"/><ellipse cx="50" cy="26" rx="28" ry="13" fill="#FFB300" stroke="#BF360C" stroke-width="1.2"/><circle cx="70" cy="22" r="2.5" fill="#111"/></svg>',
            'PEIXE_TILAPIA': '<svg viewBox="0 0 90 56" width="68" height="44"><path d="M24 28 L6 13 L11 28 L6 43 Z" fill="#455A64"/><ellipse cx="50" cy="28" rx="27" ry="15" fill="#78909C" stroke="#263238" stroke-width="1.2"/><circle cx="69" cy="24" r="2.5" fill="#111"/></svg>',
            'MENINA': '<svg viewBox="0 0 54 88" width="46" height="76"><ellipse cx="27" cy="84" rx="14" ry="3.5" fill="rgba(0,0,0,0.25)"/><rect x="20" y="56" width="5" height="24" rx="2" fill="#FFCCBC"/><rect x="29" y="56" width="5" height="24" rx="2" fill="#FFCCBC"/><path d="M16 58 L21 34 L33 34 L38 58 Z" fill="#E91E63"/><path d="M16 36 L10 50 M38 36 L44 50" stroke="#FFCCBC" stroke-width="4.5" stroke-linecap="round"/><circle cx="27" cy="20" r="11" fill="#FFCCBC"/><path d="M16 18 Q27 6 38 18 L40 28 L35 24 L19 24 L14 28 Z" fill="#4E342E"/><circle cx="23.5" cy="19" r="1.5" fill="#111"/><circle cx="30.5" cy="19" r="1.5" fill="#111"/></svg>',
            'MENINO': '<svg viewBox="0 0 54 88" width="46" height="76"><ellipse cx="27" cy="84" rx="14" ry="3.5" fill="rgba(0,0,0,0.25)"/><rect x="19" y="56" width="6" height="24" rx="2" fill="#1565C0"/><rect x="29" y="56" width="6" height="24" rx="2" fill="#1565C0"/><rect x="18" y="33" width="18" height="24" rx="4" fill="#4CAF50"/><path d="M18 36 L11 50 M36 36 L43 50" stroke="#FFCCBC" stroke-width="4.5" stroke-linecap="round"/><circle cx="27" cy="20" r="11" fill="#FFCCBC"/><path d="M16 17 Q27 7 38 17 Z" fill="#212121"/><circle cx="23.5" cy="19" r="1.5" fill="#111"/><circle cx="30.5" cy="19" r="1.5" fill="#111"/></svg>',
            'CICLISTA': '<svg viewBox="0 0 88 84" width="74" height="70"><circle cx="20" cy="64" r="13" fill="none" stroke="#263238" stroke-width="3"/><circle cx="68" cy="64" r="13" fill="none" stroke="#263238" stroke-width="3"/><path d="M20 64 L42 64 L56 44 L34 44 Z" fill="none" stroke="#E53935" stroke-width="3"/><rect x="33" y="24" width="13" height="20" rx="4" fill="#FF9800"/><circle cx="42" cy="14" r="8" fill="#FFCCBC"/><path d="M34 12 Q42 4 50 12 Z" fill="#1976D2"/></svg>',
            'CAMINHANTE': '<svg viewBox="0 0 54 88" width="46" height="76"><ellipse cx="27" cy="84" rx="14" ry="3.5" fill="rgba(0,0,0,0.25)"/><path d="M23 56 L17 80 M31 56 L37 80" stroke="#37474F" stroke-width="5.5" stroke-linecap="round"/><rect x="18" y="32" width="18" height="25" rx="4" fill="#0288D1"/><circle cx="27" cy="19" r="10.5" fill="#FFCCBC"/><path d="M17 16 Q27 6 37 16 Z" fill="#5D4037"/></svg>',
            'ESCORREGADOR': '<svg viewBox="0 0 110 95" width="94" height="80"><ellipse cx="55" cy="88" rx="44" ry="5" fill="rgba(0,0,0,0.22)"/><path d="M16 86 L28 18 L40 18 L28 86" stroke="#1565C0" stroke-width="5.5" fill="none" stroke-linecap="round"/><path d="M38 20 Q58 64 98 80" stroke="#E53935" stroke-width="10" fill="none" stroke-linecap="round"/></svg>',
            'BALANCO': '<svg viewBox="0 0 105 95" width="90" height="80"><ellipse cx="52" cy="88" rx="40" ry="5" fill="rgba(0,0,0,0.22)"/><path d="M14 86 L28 16 L76 16 L90 86" stroke="#D32F2F" stroke-width="5.5" fill="none" stroke-linecap="round"/><line x1="42" y1="16" x2="42" y2="64" stroke="#546E7A" stroke-width="2.5"/><line x1="62" y1="16" x2="62" y2="64" stroke="#546E7A" stroke-width="2.5"/><rect x="35" y="62" width="34" height="7" rx="3" fill="#FFB300"/></svg>',
            'GANGORRA': '<svg viewBox="0 0 110 74" width="94" height="64"><ellipse cx="55" cy="68" rx="42" ry="4.5" fill="rgba(0,0,0,0.22)"/><polygon points="45,67 55,40 65,67" fill="#1565C0"/><line x1="12" y1="55" x2="98" y2="27" stroke="#FFB300" stroke-width="7.5" stroke-linecap="round"/></svg>'
        }};
        function soltarParticulas(el, simbolo) {{
            const cenario = document.getElementById('cenario');
            const rect = el.getBoundingClientRect();
            const cRect = cenario.getBoundingClientRect();
            for (let i = 0; i < 4; i++) {{
                const p = document.createElement('div');
                p.className = 'particula-caindo';
                p.innerText = simbolo;
                p.style.left = (rect.left - cRect.left + 8 + Math.random() * 40) + 'px';
                p.style.top = (rect.top - cRect.top + 5 + Math.random() * 25) + 'px';
                cenario.appendChild(p);
                setTimeout(() => p.remove(), 1500);
            }}
        }}

        function tocarNota(freqIni, freqFim, duracao, onda) {{
            if (audioCtx.state === 'suspended') audioCtx.resume();
            const agora = audioCtx.currentTime;
            const osc = audioCtx.createOscillator();
            const ganho = audioCtx.createGain();
            osc.type = onda || 'sine';
            osc.frequency.setValueAtTime(freqIni, agora);
            osc.frequency.exponentialRampToValueAtTime(freqFim, agora + duracao);
            ganho.gain.setValueAtTime(0.16, agora);
            ganho.gain.exponentialRampToValueAtTime(0.001, agora + duracao);
            osc.connect(ganho); ganho.connect(audioCtx.destination);
            osc.start(agora); osc.stop(agora + duracao);
        }}

        function alternarDiaNoite(el) {{
            const cenario = document.getElementById('cenario');
            const camadaNoite = document.getElementById('camada-noite');
            ehNoite = !ehNoite;
            el.classList.remove('girar-ceu');
            void el.offsetWidth;
            el.classList.add('girar-ceu');
            if (ehNoite) {{
                cenario.classList.add('modo-noite');
                el.innerText = '🌙';
                camadaNoite.innerHTML = '';
                for (let i = 0; i < 30; i++) {{
                    const st = document.createElement('div');
                    st.className = 'estrela-noite';
                    const tam = (Math.random() * 3.5 + 2) + 'px';
                    st.style.width = tam; st.style.height = tam;
                    st.style.left = Math.random() * 96 + '%';
                    st.style.top = Math.random() * 42 + '%';
                    camadaNoite.appendChild(st);
                }}
                tocarNota(660, 330, 0.45, 'sine');
            }} else {{
                cenario.classList.remove('modo-noite');
                el.innerText = '☀️';
                camadaNoite.innerHTML = '';
                tocarNota(380, 880, 0.45, 'triangle');
            }}
        }}

        function interagirNuvem(el, acao) {{
            el.classList.remove('girar-ceu');
            void el.offsetWidth;
            el.classList.add('girar-ceu');
            if (acao === 'chuva') {{
                const div = document.getElementById('efeitos-container');
                div.innerHTML = '';
                for (let i = 0; i < 35; i++) {{
                    const g = document.createElement('div');
                    g.className = 'gota';
                    g.style.left = Math.random() * 100 + 'vw';
                    g.style.animationDuration = (Math.random() * 0.4 + 0.5) + 's';
                    div.appendChild(g);
                }}
                tocarNota(280, 160, 0.35, 'sine');
                setTimeout(() => {{ div.innerHTML = ''; }}, 4000);
            }} else {{
                tocarNota(680, 1080, 0.22, 'sine');
                soltarParticulas(el, '🐦');
            }}
        }}

        function interagirPassaro(el) {{
            el.classList.remove('girar-ceu');
            void el.offsetWidth;
            el.classList.add('girar-ceu');
            tocarNota(820, 1220, 0.18, 'sine');
            soltarParticulas(el, '🎵');
        }}
        function abrirNinhoCapivaras() {{
            const modal = document.getElementById('modal-ninho');
            if (modal) modal.style.display = 'flex';
            tocarNota(480, 740, 0.22, 'triangle');
        }}

        function fecharNinhoCapivaras() {{
            const modal = document.getElementById('modal-ninho');
            if (modal) modal.style.display = 'none';
            tocarNota(520, 340, 0.2, 'sine');
        }}

        function acariciarBebe(el) {{
            tocarNota(580, 880, 0.2, 'triangle');
            soltarParticulas(el, '❤️');
        }}

        function cuidarBebes(tipo) {{
            if (tipo === 'mamadeira') {{
                const b1 = document.getElementById('bebe-1');
                if (b1) {{
                    b1.querySelector('.status-bebe').innerText = '😋 Barriguinha cheia!';
                    soltarParticulas(b1, '🍼');
                    soltarParticulas(b1, '❤️');
                }}
                tocarNota(420, 760, 0.25, 'triangle');
            }} else {{
                const b2 = document.getElementById('bebe-2');
                if (b2) {{
                    b2.querySelector('.status-bebe').innerText = '✨ Limpinho e cheiroso!';
                    soltarParticulas(b2, '🧷');
                    soltarParticulas(b2, '✨');
                }}
                tocarNota(520, 860, 0.25, 'sine');
            }}
        }}

        function abrirSalaAula() {{
            const modal = document.getElementById('modal-sala');
            if (!modal) return;
            modal.style.display = 'flex';
            tocarNota(520, 780, 0.25, 'triangle');
            const canvas = document.getElementById('lousa-canvas');
            if (canvas && !ctxLousa) {{
                canvas.width = canvas.offsetWidth;
                canvas.height = canvas.offsetHeight;
                ctxLousa = canvas.getContext('2d');
                ctxLousa.lineCap = 'round';
                ctxLousa.lineJoin = 'round';
                ctxLousa.lineWidth = 5;
                canvas.onpointerdown = e => {{
                    desenhandoLousa = true;
                    const r = canvas.getBoundingClientRect();
                    ctxLousa.strokeStyle = corGizAtual;
                    ctxLousa.beginPath();
                    ctxLousa.moveTo(e.clientX - r.left, e.clientY - r.top);
                }};
                canvas.onpointermove = e => {{
                    if (!desenhandoLousa) return;
                    const r = canvas.getBoundingClientRect();
                    ctxLousa.lineTo(e.clientX - r.left, e.clientY - r.top);
                    ctxLousa.stroke();
                }};
                canvas.onpointerup = () => {{ desenhandoLousa = false; }};
            }}
        }}
        function verificarInteracaoElementos(el, soltou) {{
            const tipo = el.dataset.tipo;
            const rEl = el.getBoundingClientRect();
            const cx = rEl.left + rEl.width / 2;
            const cy = rEl.top + rEl.height / 2;

            if (soltou && verificarBrinquedos(el)) return;

            if (tipo === 'CAPIVARA' || tipo === 'BEBE_CAPIVARA') {{
                const ninho = document.getElementById('ninho-capivaras');
                if (ninho) {{
                    const rNinho = ninho.getBoundingClientRect();
                    const dentro = cx >= rNinho.left && cx <= rNinho.right && cy >= rNinho.top && cy <= rNinho.bottom;
                    if (dentro) {{
                        ninho.classList.add('destaque');
                        if (soltou) {{
                            ninho.classList.remove('destaque');
                            el.classList.remove('nadando');
                            el.style.transform = 'scaleX(1)';
                            el.style.top = (rNinho.top + rNinho.height * 0.25) + 'px';
                            tocarNota(580, 860, 0.18, 'triangle');
                            soltarParticulas(el, '❤️');
                        }}
                    }} else {{ ninho.classList.remove('destaque'); }}
                }}
            }}

            if ((tipo === '🍼' || tipo === '🧷') && soltou) {{
                document.querySelectorAll('.bicho').forEach(outro => {{
                    if (outro !== el && (outro.dataset.tipo === 'BEBE_CAPIVARA' || outro.dataset.tipo === 'CAPIVARA')) {{
                        const rOutro = outro.getBoundingClientRect();
                        if (Math.abs(cx - (rOutro.left + rOutro.width/2)) < 65 && Math.abs(cy - (rOutro.top + rOutro.height/2)) < 65) {{
                            tocarNota(480, 780, 0.2, 'triangle');
                            setTimeout(() => tocarNota(620, 920, 0.2, 'triangle'), 160);
                            soltarParticulas(outro, tipo === '🍼' ? '🍼' : '✨');
                            soltarParticulas(outro, '❤️');
                            el.remove();
                        }}
                    }}
                }});
            }}

            if (tiposBanho.includes(tipo)) {{
                const agora = Date.now();
                if (agora - ultimoBanho > 350) {{
                    document.querySelectorAll('.bicho').forEach(outro => {{
                        if (outro !== el && (outro.dataset.tipo === 'CAPIVARA' || outro.dataset.tipo === 'BEBE_CAPIVARA')) {{
                            const rOutro = outro.getBoundingClientRect();
                            if (Math.abs(cx - (rOutro.left + rOutro.width/2)) < 55 && Math.abs(cy - (rOutro.top + rOutro.height/2)) < 55) {{
                                ultimoBanho = agora;
                                tocarNota(420, 820, 0.2, 'sine');
                                soltarParticulas(outro, '🫧');
                                soltarParticulas(outro, '✨');
                            }}
                        }}
                    }});
                }}
            }}

            if (tiposComida.includes(tipo) && soltou && !estaNaAgua(el)) {{
                document.querySelectorAll('.bicho').forEach(outro => {{
                    if (outro !== el && tiposAnimais.includes(outro.dataset.tipo)) {{
                        const rOutro = outro.getBoundingClientRect();
                        if (Math.abs(cx - (rOutro.left + rOutro.width/2)) < 60 && Math.abs(cy - (rOutro.top + rOutro.height/2)) < 60) {{
                            tocarNota(340, 580, 0.15, 'triangle');
                            setTimeout(() => tocarNota(420, 680, 0.15, 'triangle'), 160);
                            soltarParticulas(outro, '❤️');
                            soltarParticulas(outro, '😋');
                            el.remove();
                        }}
                    }}
                }});
            }}
        }}

        function interagirNuvem(el, acao) {{
            el.classList.remove('girar-ceu');
            void el.offsetWidth;
            el.classList.add('girar-ceu');
            if (acao === 'chover') {{
                tocarNota(300, 160, 0.35, 'sine');
                soltarParticulas(el, '💧');
                soltarParticulas(el, '🌧️');
            }} else if (acao === 'passaro') {{
                tocarNota(720, 1180, 0.25, 'sine');
                soltarParticulas(el, '🕊️');
                soltarParticulas(el, '🎵');
            }} else {{
                tocarNota(440, 880, 0.35, 'triangle');
                soltarParticulas(el, '🌈');
                soltarParticulas(el, '✨');
            }}
        }}

        function interagirCeu(el, tipo) {{
            el.classList.remove('girar-ceu');
            void el.offsetWidth;
            el.classList.add('girar-ceu');
            if (tipo === 'passaro') {{ tocarNota(780, 1150, 0.18, 'sine'); soltarParticulas(el, '🎵'); }}
            else {{ tocarNota(520, 960, 0.3, 'sine'); soltarParticulas(el, '⭐'); }}
        }}

        function interagirAgua(el) {{
            el.classList.remove('pular-agua');
            void el.offsetWidth;
            el.classList.add('pular-agua');
            tocarNota(260, 620, 0.28, 'sine');
            soltarParticulas(el, '💦');
        }}

        function chacoalharFundo(el, tipo) {{
            el.classList.remove('xagualhar');
            void el.offsetWidth;
            el.classList.add('xagualhar');
            tocarNota(tipo === 'bolha' ? 320 : 520, tipo === 'bolha' ? 680 : 980, 0.25, 'sine');
            if (tipo === 'folha') soltarParticulas(el, Math.random() > 0.3 ? '🍃' : '🍂');
            else if (tipo === 'bolha') soltarParticulas(el, '🫧');
            else soltarParticulas(el, '✨');
        }}
        function dispararTrovao() {{
            if (estadoClima !== 1 || tipoClima !== 'chuva_arcoiris') return;
            const flash = document.getElementById('relampago');
            flash.style.opacity = '0.85';
            setTimeout(() => {{ flash.style.opacity = '0'; }}, 90);
            setTimeout(() => {{ flash.style.opacity = '0.5'; }}, 160);
            setTimeout(() => {{ flash.style.opacity = '0'; }}, 260);
            tocarNota(120, 45, 0.9, 'sawtooth');
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
                        div.appendChild(g);
                    }}
                    setTimeout(dispararTrovao, 600);
                }} else if (estadoClima === 2) {{ arco.classList.add('ativo'); }}
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
                        div.appendChild(e);
                    }}
                }}
            }}
        }}

        function criarNaPosicao(item, xPct, yPct) {{
            const palco = document.getElementById('palco');
            const el = document.createElement('div');
            el.className = 'bicho';
            if (tiposBrinquedos.includes(item)) el.classList.add('brinquedo');
            if (tiposPista.includes(item)) {{
                el.classList.add('na-pista');
                el.dataset.dirX = Math.random() > 0.5 ? '1' : '-1';
            }}
            el.dataset.tipo = item;
            const miolo = document.createElement('div');
            miolo.className = 'conteudo-bicho';
            if (svgsObjetos[item]) {{ miolo.innerHTML = svgsObjetos[item]; }}
            else {{ miolo.innerText = item; }}
            el.appendChild(miolo);
            el.style.left = (window.innerWidth * xPct / 100) + 'px';
            el.style.top = (window.innerHeight * yPct / 100) + 'px';

            let drag = false, ox = 0, oy = 0, moveu = false;
            el.onpointerdown = e => {{
                drag = true;
                moveu = false;
                el.dataset.arrastando = '1';
                limparEstadosBrinquedo(el);
                const r = el.getBoundingClientRect();
                ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId);
            }};
            el.onpointermove = e => {{
                if (!drag) return;
                moveu = true;
                el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 75)) + 'px';
                el.style.top = Math.max(45, Math.min(e.clientY - oy, window.innerHeight - 120)) + 'px';
                verificarInteracaoElementos(el, false);
            }};
            el.onpointerup = e => {{
                drag = false;
                el.dataset.arrastando = '0';
                el.releasePointerCapture(e.pointerId);
                if (!moveu) {{
                    if (tiposPeixes.includes(item) && el.classList.contains('nadando')) {{
                        el.classList.remove('salto-peixe');
                        void el.offsetWidth;
                        el.classList.add('salto-peixe');
                        tocarNota(300, 740, 0.32, 'sine');
                        soltarParticulas(el, '💦');
                        setTimeout(() => el.classList.remove('salto-peixe'), 780);
                        return;
                    }}
                    if (tiposAereos.includes(item) && !el.classList.contains('voando')) {{
                        el.style.top = (window.innerHeight * 0.22) + 'px';
                        atualizarEstadoVoo(el, true);
                        return;
                    }}
                    if (tiposPista.includes(item)) {{
                        tocarNota(440, 680, 0.18, 'triangle');
                        soltarParticulas(el, '👋');
                        return;
                    }}
                }}
                atualizarEstadoVoo(el, true);
                atualizarEstadoNado(el, true);
                verificarInteracaoElementos(el, true);
            }};
            palco.appendChild(el);
            atualizarEstadoVoo(el, false);
            atualizarEstadoNado(el, false);
        }}

        function criar(item) {{
            let yIni = 52 + Math.random() * 22;
            if (tiposAereos.includes(item)) yIni = 20 + Math.random() * 15;
            else if (tiposPeixes.includes(item) && (mundoAtual === 'represa' || mundoAtual === 'oceano')) yIni = 42 + Math.random() * 16;
            else if (tiposPista.includes(item) && mundoAtual === 'represa') yIni = 61;
            criarNaPosicao(item, 15 + Math.random() * 65, yIni);
        }}
        function limpar() {{ document.getElementById('palco').innerHTML = ''; }}
        function organizar() {{ limpar(); {espalhados_js} }}
        organizar();
    </script>
    </body>
    </html>
    """

    components.html(html_cenario, height=700, scrolling=False)
