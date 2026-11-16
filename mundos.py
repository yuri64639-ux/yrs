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
            "titulo": "🏫 EM Pato Donald (Toque na escola para entrar na sala!)",
            "fundo": "linear-gradient(to bottom, #64B5F6 0%, #B3E5FC 54%, #E6B88A 54%, #558B2F 64%, #33691E 100%)",
            "placa_bg": "#FFD700", "placa_cor": "#003366",
            "itens": ["👧", "👦", "🦆", "🐶", "ESCORREGADOR", "BALANCO", "GANGORRA"],
            "espalhados": [
                ("👧", 32, 58), ("👦", 44, 58), ("👧", 58, 72), ("👦", 74, 72),
                ("🦆", 12, 74), ("ESCORREGADOR", 56, 53), ("BALANCO", 77, 53), ("GANGORRA", 30, 72)
            ],
            "clima_extra": "chuva_arcoiris"
        },
        "represa": {
            "titulo": "🌊 Represa Municipal - São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #4FC3F7 0%, #E1F5FE 36%, #0288D1 36%, #01579B 66%, #78909C 66%, #607D8B 74%, #388E3C 74%, #1B5E20 100%)",
            "placa_bg": "#00CED1", "placa_cor": "#003366",
            "itens": ["CAPIVARA", "PEIXE_DOURADO", "PEIXE_TILAPIA", "🦢", "🧼", "🌽"],
            "espalhados": [
                ("🦢", 12, 43), ("PEIXE_DOURADO", 26, 50), ("PEIXE_TILAPIA", 52, 54),
                ("PEIXE_LAMBARI", 72, 48), ("PEIXE_DOURADO", 40, 44),
                ("CAPIVARA", 10, 74), ("CAPIVARA", 26, 75), ("ESCORREGADOR", 46, 71),
                ("🧼", 66, 75), ("🌽", 76, 75)
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
        "CAPIVARA": '<svg viewBox="0 0 80 56" width="32" height="24" style="vertical-align:middle;"><ellipse cx="38" cy="31" rx="24" ry="15" fill="#795548"/><rect x="48" y="12" width="22" height="17" rx="7" fill="#8D6E63"/><circle cx="60" cy="18" r="2.2" fill="#1A1A1A"/></svg>',
        "PEIXE_DOURADO": '<svg viewBox="0 0 84 48" width="34" height="22" style="vertical-align:middle;"><ellipse cx="44" cy="24" rx="24" ry="12" fill="#FFA000"/><polygon points="22,24 6,11 11,24 6,37" fill="#D84315"/><circle cx="58" cy="21" r="2.2" fill="#111"/></svg>',
        "PEIXE_TILAPIA": '<svg viewBox="0 0 84 52" width="34" height="22" style="vertical-align:middle;"><ellipse cx="44" cy="26" rx="23" ry="14" fill="#607D8B"/><polygon points="22,26 6,13 11,26 6,39" fill="#455A64"/><circle cx="58" cy="23" r="2.2" fill="#111"/></svg>',
        "ESCORREGADOR": '<svg viewBox="0 0 80 70" width="30" height="24" style="vertical-align:middle;"><path d="M14 62 L24 16 L32 16 L22 62" stroke="#1565C0" stroke-width="4" fill="none"/><path d="M30 18 Q44 48 72 58" stroke="#E53935" stroke-width="6" fill="none" stroke-linecap="round"/></svg>',
        "BALANCO": '<svg viewBox="0 0 80 70" width="30" height="24" style="vertical-align:middle;"><path d="M12 62 L24 14 L56 14 L68 62" stroke="#D32F2F" stroke-width="4" fill="none"/><rect x="30" y="47" width="20" height="5" rx="2" fill="#FFB300"/></svg>',
        "GANGORRA": '<svg viewBox="0 0 84 60" width="32" height="24" style="vertical-align:middle;"><polygon points="34,52 42,34 50,52" fill="#1565C0"/><line x1="12" y1="44" x2="72" y2="24" stroke="#FFB300" stroke-width="6" stroke-linecap="round"/></svg>'
    }
    botoes_itens = "".join([f'<button class="btn-item" onclick="criar(\'{i}\')">{icones_btn.get(i, i)}</button>' for i in cfg["itens"]])
    espalhados_js = "".join([f"criarNaPosicao('{emoji}', {x}, {y});" for emoji, x, y in cfg["espalhados"]])
    decoracao_cenario = ""
    if st.session_state.tela_atual == "represa":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 8%;">
            <span class="item-ceu sol-lua-btn" onclick="alternarDiaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'passaro')">🐦</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'balao')">🎈</span>
        </div>
        <svg viewBox="0 0 1000 320" preserveAspectRatio="none" style="position:absolute; top:14%; left:0; width:100%; height:44%; pointer-events:none; z-index:2;">
            <path d="M0,190 Q250,175 500,190 T1000,190 L1000,210 L0,210 Z" fill="#1B5E20"/>
            <path d="M 270 198 Q 500 130 730 198" fill="none" stroke="#D32F2F" stroke-width="11" stroke-linecap="round"/>
            <path d="M 285 198 Q 500 144 715 198" fill="none" stroke="#B71C1C" stroke-width="5"/>
            <rect x="240" y="196" width="520" height="13" rx="4" fill="#E53935"/>
        </svg>
        <div class="ondulacoes-agua"></div>
        <div class="chafariz-riopreto"><div class="jato-central"></div><div class="jato-esq"></div><div class="jato-dir"></div><div class="espuma-lago"></div></div>
        <div class="pista-riopreto"><div class="faixa-ciclovia"></div><div class="faixa-pedestre"></div></div>
        <div id="ninho-capivaras" class="ninho-capivaras">
            <svg viewBox="0 0 180 95" width="100%" height="100%">
                <ellipse cx="90" cy="68" rx="84" ry="24" fill="#795548" stroke="#3E2723" stroke-width="3"/><ellipse cx="90" cy="66" rx="68" ry="16" fill="#D7CCC8"/>
            </svg>
            <div class="placa-ninho">🐾 Ninho das Capivaras</div>
        </div>
        <div class="elementos-fundo" style="top: 52%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
        </div>
        """
    elif st.session_state.tela_atual == "escola":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 9%;">
            <span class="item-ceu sol-lua-btn" onclick="alternarDiaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'passaro')">🐦</span>
        </div>
        <div class="predio-escola-clicavel" onclick="abrirSalaAula()" title="Toque para entrar na sala de aula!">
            <svg viewBox="0 0 360 195" width="100%" height="100%">
                <polygon points="10,65 180,15 350,65" fill="#D62828" stroke="#8D0801" stroke-width="3"/>
                <rect x="25" y="65" width="310" height="105" fill="#1E88E5" stroke="#0D47A1" stroke-width="3"/>
                <rect x="45" y="72" width="270" height="24" rx="4" fill="#FFD700" stroke="#003366" stroke-width="2"/>
                <text x="180" y="88" font-family="Comic Sans MS, sans-serif" font-size="13" font-weight="bold" fill="#003366" text-anchor="middle">EM PATO DONALD</text>
                <rect x="155" y="115" width="50" height="55" rx="3" fill="#FFD700" stroke="#003366" stroke-width="2"/>
                <circle cx="195" cy="144" r="3.5" fill="#003366"/>
                <rect x="55" y="110" width="45" height="35" rx="3" fill="#E3F2FD" stroke="#003366" stroke-width="2"/>
                <rect x="260" y="110" width="45" height="35" rx="3" fill="#E3F2FD" stroke="#003366" stroke-width="2"/>
            </svg>
            <div class="aviso-entrar-sala">🚪 Entrar na Sala</div>
        </div>
        <div class="elementos-fundo" style="top: 38%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌲</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
        </div>
        """
    elif st.session_state.tela_atual == "aeroporto":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 9%;">
            <span class="item-ceu sol-lua-btn" onclick="alternarDiaNoite(this)">☀️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
        </div>
        <svg viewBox="0 0 800 200" preserveAspectRatio="none" style="position:absolute; top:24%; left:0; width:100%; height:28%; pointer-events:none; z-index:2;">
            <rect x="60" y="90" width="240" height="80" rx="6" fill="#ECEFF1" stroke="#546E7A" stroke-width="3"/>
            <path d="M 55 90 Q 180 40 305 90 Z" fill="#1565C0"/>
            <rect x="330" y="45" width="36" height="125" fill="#CFD8DC" stroke="#455A64" stroke-width="3"/>
            <polygon points="315,45 381,45 370,15 326,15" fill="#263238"/>
        </svg>
        <div style="position:absolute; top:74%; left:0; width:100%; height:4px; background:repeating-linear-gradient(90deg, #FFFFFF, #FFFFFF 45px, transparent 45px, transparent 85px); pointer-events:none; z-index:2;"></div>
        <div class="elementos-fundo" style="top: 40%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌳</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">🌴</span>
        </div>
        """
    elif st.session_state.tela_atual == "oceano":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 8%;">
            <span class="item-ceu sol-lua-btn" onclick="alternarDiaNoite(this)">☀️</span>
            <span class="item-agua" onclick="interagirAgua(this)">⛵</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'passaro')">🕊️</span>
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
    sala_aula_html = ""
    if st.session_state.tela_atual == "escola":
        sala_aula_html = """
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
                    <div id="fala-professora" style="background:white; color:#003366; border:2px solid #003366; border-radius:14px; padding:5px 10px; font-size:clamp(12px, 2.5vw, 15px); font-weight:bold; margin-bottom:24px; box-shadow:0 3px 8px rgba(0,0,0,0.2);">Desenhe na lousa! ✏️</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.95); padding:8px 14px; border-radius:20px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:center; box-shadow:0 4px 12px rgba(0,0,0,0.25);">
                <span style="font-weight:bold; color:#333; font-size:14px;">Giz:</span>
                <button onclick="mudarCorGiz('#FFFFFF')" style="width:30px; height:30px; border-radius:50%; background:#FFFFFF; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="mudarCorGiz('#FFEB3B')" style="width:30px; height:30px; border-radius:50%; background:#FFEB3B; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="mudarCorGiz('#FF5252')" style="width:30px; height:30px; border-radius:50%; background:#FF5252; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="mudarCorGiz('#40C4FF')" style="width:30px; height:30px; border-radius:50%; background:#40C4FF; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="mudarCorGiz('#69F0AE')" style="width:30px; height:30px; border-radius:50%; background:#69F0AE; border:3px solid #333; cursor:pointer;"></button>
                <button onclick="carimbarLousa('⭐')" style="font-size:20px; border:2px solid #FFD700; background:#FFF8DC; border-radius:10px; padding:2px 8px; cursor:pointer;">⭐</button>
                <button onclick="carimbarLousa('🦆')" style="font-size:20px; border:2px solid #FFD700; background:#FFF8DC; border-radius:10px; padding:2px 8px; cursor:pointer;">🦆</button>
                <button onclick="carimbarLousa('❤️')" style="font-size:20px; border:2px solid #FFD700; background:#FFF8DC; border-radius:10px; padding:2px 8px; cursor:pointer;">❤️</button>
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
            #camada-noite {{
                position: absolute; inset: 0; border-radius: 20px;
                background: linear-gradient(to bottom, rgba(7, 13, 38, 0.86) 0%, rgba(15, 25, 65, 0.65) 55%, rgba(5, 10, 25, 0.58) 100%);
                opacity: 0; pointer-events: none; z-index: 2; transition: opacity 0.8s ease;
            }}
            #cenario.modo-noite #camada-noite {{ opacity: 1; }}
            .estrela-noite {{
                position: absolute; background: #FFFDE7; border-radius: 50%;
                box-shadow: 0 0 8px #FFF59D; animation: piscar 1.6s infinite alternate;
            }}
            .sol-lua-btn {{
                transition: transform 0.5s ease, filter 0.5s ease;
                filter: drop-shadow(0 0 12px rgba(255, 235, 59, 0.8));
            }}
            #cenario.modo-noite .sol-lua-btn {{
                filter: drop-shadow(0 0 16px rgba(255, 255, 255, 0.95));
            }}
            .camada-ceu, .camada-agua {{ position: absolute; left: 0; width: 100%; display: flex; justify-content: space-around; align-items: center; z-index: 5; pointer-events: none; }}
            .item-ceu, .item-agua {{ font-size: clamp(38px, 7.5vw, 60px); cursor: pointer; pointer-events: auto; display: inline-block; }}
            .predio-escola-clicavel {{
                position: absolute; top: 27%; left: 3%; width: clamp(185px, 32vw, 275px);
                cursor: pointer; z-index: 5; transition: transform 0.2s;
                filter: drop-shadow(0 6px 8px rgba(0,0,0,0.28));
            }}
            .predio-escola-clicavel:hover {{ transform: scale(1.04); }}
            .aviso-entrar-sala {{
                position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
                background: #FFD700; color: #003366; border: 2px solid #003366;
                border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: bold; white-space: nowrap;
            }}
            .ondulacoes-agua {{
                position: absolute; top: 36%; left: 0; width: 100%; height: 30%;
                background: repeating-linear-gradient(180deg, rgba(255,255,255,0.12) 0px, rgba(255,255,255,0.12) 2px, transparent 2px, transparent 18px);
                pointer-events: none; z-index: 2;
            }}
            .pular-agua {{ animation: puloNaAgua 0.7s ease-out; }}
            @keyframes puloNaAgua {{ 0% {{ transform: translateY(0); }} 45% {{ transform: translateY(-28px) rotate(-18deg) scale(1.15); }} 100% {{ transform: translateY(0); }} }}
            .girar-ceu {{ animation: giroNoCeu 0.8s ease-in-out; }}
            @keyframes giroNoCeu {{ 0% {{ transform: scale(1) rotate(0deg); }} 50% {{ transform: scale(1.25) rotate(180deg); }} 100% {{ transform: scale(1) rotate(360deg); }} }}
            .ninho-capivaras {{ position: absolute; bottom: 13%; right: 4%; width: clamp(140px, 26vw, 205px); height: clamp(72px, 13vw, 105px); z-index: 4; pointer-events: none; transition: transform 0.25s; }}
            .ninho-capivaras.destaque {{ transform: scale(1.08); filter: drop-shadow(0 0 12px #FFD700); }}
            .placa-ninho {{ position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%); background: #FFF8DC; color: #4E342E; border: 2px solid #6D4C41; border-radius: 10px; padding: 1px 8px; font-size: 11px; font-weight: bold; white-space: nowrap; }}
            .chafariz-riopreto {{ position: absolute; top: 44%; left: 26%; width: 90px; height: 80px; pointer-events: none; z-index: 3; }}
            .jato-central {{ position: absolute; bottom: 8px; left: 41px; width: 8px; height: 68px; background: linear-gradient(to top, rgba(255,255,255,0.9), transparent); border-radius: 50% 50% 0 0; animation: pulsarJato 1.1s infinite alternate; }}
            .jato-esq {{ position: absolute; bottom: 8px; left: 26px; width: 6px; height: 45px; background: linear-gradient(to top, rgba(255,255,255,0.8), transparent); transform: rotate(-18deg); transform-origin: bottom; animation: pulsarJato 1.1s infinite alternate; }}
            .jato-dir {{ position: absolute; bottom: 8px; left: 58px; width: 6px; height: 45px; background: linear-gradient(to top, rgba(255,255,255,0.8), transparent); transform: rotate(18deg); transform-origin: bottom; animation: pulsarJato 1.1s infinite alternate; }}
            .espuma-lago {{ position: absolute; bottom: 4px; left: 15px; width: 60px; height: 10px; background: rgba(255,255,255,0.75); border-radius: 50%; filter: blur(2px); }}
            @keyframes pulsarJato {{ 0% {{ transform: scaleY(0.85); }} 100% {{ transform: scaleY(1.12); }} }}
            .pista-riopreto {{ position: absolute; top: 66%; left: 0; width: 100%; height: 8%; pointer-events: none; z-index: 2; }}
            .faixa-ciclovia {{ width: 100%; height: 32%; background: rgba(214, 40, 40, 0.75); border-bottom: 2px dashed #FFFFFF; }}
            .faixa-pedestre {{ width: 100%; height: 68%; background: repeating-linear-gradient(90deg, transparent, transparent 30px, #FFD166 30px, #FFD166 55px); background-size: 100% 3px; background-repeat: no-repeat; background-position: center; }}
            .elementos-fundo {{ position: absolute; left: 0; width: 100%; display: flex; justify-content: space-around; align-items: flex-end; z-index: 4; pointer-events: none; }}
            .item-fundo-interativo {{ font-size: clamp(46px, 9.5vw, 76px); cursor: pointer; pointer-events: auto; transform-origin: bottom center; display: inline-block; }}
            .xagualhar {{ animation: balancarItem 0.65s ease-in-out; }}
            @keyframes balancarItem {{ 0%, 100% {{ transform: rotate(0deg); }} 25% {{ transform: rotate(-10deg); }} 50% {{ transform: rotate(9deg); }} 75% {{ transform: rotate(-6deg); }} }}
            .particula-caindo {{ position: absolute; font-size: 22px; pointer-events: none; z-index: 9; animation: animarParticula 1.5s ease-out forwards; }}
            @keyframes animarParticula {{ 0% {{ opacity: 1; }} 100% {{ transform: translate(-12px, -55px) rotate(280deg) scale(0.7); opacity: 0; }} }}
            #relampago {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.85); pointer-events: none; opacity: 0; z-index: 5; transition: opacity 0.08s; }}
            #arco-iris {{ position: absolute; top: 8%; left: 50%; transform: translateX(-50%); width: 120vw; max-width: 850px; height: 60vw; max-height: 420px; border-radius: 50% 50% 0 0 / 100% 100% 0 0; background: radial-gradient(circle at 50% 100%, transparent 48%, rgba(148,0,211,0.35) 52%, rgba(0,119,255,0.4) 56%, rgba(0,200,80,0.4) 60%, rgba(255,230,0,0.45) 64%, rgba(255,20,20,0.4) 68%, transparent 72%); filter: blur(6px); pointer-events: none; opacity: 0; transition: opacity 0.8s; z-index: 1; }}
            #arco-iris.ativo {{ opacity: 1; }}
            #efeitos-container {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: hidden; z-index: 3; }}
            .gota {{ position: absolute; width: 2px; height: 20px; background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.85)); animation: cair linear infinite; }}
            @keyframes cair {{ 0% {{ transform: translate(0, -20px) rotate(12deg); }} 100% {{ transform: translate(-35px, 105vh) rotate(12deg); }} }}
            .bolha {{ position: absolute; bottom: -20px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.7); background: rgba(255,255,255,0.2); animation: subir linear infinite; }}
            @keyframes subir {{ 0% {{ transform: translateY(0); opacity: 0.8; }} 100% {{ transform: translateY(-105vh) scale(1.3); opacity: 0; }} }}
            .estrela {{ position: absolute; background: white; border-radius: 50%; box-shadow: 0 0 8px #FFF; animation: piscar 1.5s infinite alternate; }}
            @keyframes piscar {{ 0% {{ opacity: 0.2; }} 100% {{ opacity: 1; transform: scale(1.3); }} }}
            .placa {{ background: {cfg['placa_bg']}; color: {cfg['placa_cor']}; border: 3px solid #003366; padding: 6px 16px; border-radius: 14px; font-size: clamp(13px, 3vw, 18px); font-weight: bold; text-align: center; z-index: 10; }}
            .bicho {{ position: absolute; font-size: 48px; cursor: grab; z-index: 6; touch-action: none; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.3)); }}
            .bicho.brinquedo {{ z-index: 5; }}
            .bicho.brincando {{ z-index: 7; }}
            .bicho:active {{ cursor: grabbing; transform: scale(1.18); }}
            .conteudo-bicho {{ display: inline-block; }}
            .nadando .conteudo-bicho {{ animation: boiarNaAgua 1.1s infinite alternate ease-in-out; }}
            @keyframes boiarNaAgua {{ 0% {{ transform: translateY(-3px) rotate(-4deg); }} 100% {{ transform: translateY(4px) rotate(4deg); }} }}
            .peixe-nadando .conteudo-bicho {{ animation: nadarPeixe 0.55s infinite alternate ease-in-out; }}
            @keyframes nadarPeixe {{ 0% {{ transform: translateY(-2px) skewY(-2deg); }} 100% {{ transform: translateY(2px) skewY(2deg); }} }}
            .salto-peixe .conteudo-bicho {{ animation: saltarForaAgua 0.75s ease-out; }}
            @keyframes saltarForaAgua {{ 0% {{ transform: translateY(0) rotate(0deg); }} 45% {{ transform: translateY(-48px) rotate(-32deg) scale(1.12); }} 100% {{ transform: translateY(0) rotate(0deg); }} }}
            .voando .conteudo-bicho {{ animation: flutuarNoAr 1.4s infinite alternate ease-in-out; }}
            @keyframes flutuarNoAr {{ 0% {{ transform: translateY(-6px) rotate(-3deg); }} 100% {{ transform: translateY(6px) rotate(3deg); }} }}
            .balancando-brinquedo .conteudo-bicho {{ transform-origin: top center; animation: balancarNoBrinquedo 0.85s infinite alternate ease-in-out; }}
            @keyframes balancarNoBrinquedo {{ 0% {{ transform: rotate(-22deg) translateX(-10px); }} 100% {{ transform: rotate(22deg) translateX(10px); }} }}
            .gangorra-brinquedo .conteudo-bicho {{ animation: gangorraSobeDesce 0.9s infinite alternate ease-in-out; }}
            @keyframes gangorraSobeDesce {{ 0% {{ transform: translateY(-14px) rotate(-8deg); }} 100% {{ transform: translateY(10px) rotate(8deg); }} }}
            #barra {{ background: rgba(255, 255, 255, 0.94); padding: 8px 12px; border-radius: 22px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 10; display: flex; justify-content: center; align-items: center; gap: 6px; flex-wrap: wrap; max-width: 96%; }}
            .btn-item {{ font-size: 24px; border: 2px solid #FFD700; background: #FFF8DC; border-radius: 14px; padding: 4px 8px; cursor: pointer; }}
            .btn-acao {{ font-size: 14px; font-weight: bold; border: none; border-radius: 14px; padding: 8px 11px; cursor: pointer; }}
        </style>
    </head>
    <body>
    <div id="cenario">
        <div id="camada-noite"></div>
        {decoracao_cenario}
        {sala_aula_html}
        <div id="relampago"></div>
        <div id="arco-iris"></div>
        <div id="efeitos-container"></div>
        <div class="placa">{cfg['titulo']}</div>
        <div id="palco"></div>
        <div id="barra">
            {botoes_itens}
            <button class="btn-acao" style="background:#FFD700; color:#333;" onclick="alternarClima()">🌦️ Clima</button>
            <button class="btn-acao" style="background:#4CAF50; color:white;" onclick="organizar()">🔄 Organizar</button>
            <button class="btn-acao" style="background:#FF6B6B; color:white;" onclick="limpar()">🗑️</button>
        </div>
    </div>
    <script>
        let estadoClima = 0;
        let ehNoite = false;
        let timerTrovao = null;
        let ultimoBanho = 0;
        const mundoAtual = "{st.session_state.tela_atual}";
        const tipoClima = "{cfg['clima_extra']}";
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        const tiposPeixes = ['PEIXE_DOURADO', 'PEIXE_TILAPIA', 'PEIXE_LAMBARI', '🐠', '🐡', '🦈'];
        const tiposAnimais = ['CAPIVARA', 'PEIXE_DOURADO', 'PEIXE_TILAPIA', 'PEIXE_LAMBARI', '🦆', '🦢', '🐶', '🐱', '🐳', '🐬', '🐠', '🐢', '🐙', '🦀', '🐡', '🦈', '🦞'];
        const tiposPessoas = ['👧', '👦', '👨‍🚀', '👨‍✈️', '👽'];
        const tiposBrinquedos = ['ESCORREGADOR', 'BALANCO', 'GANGORRA'];
        const tiposAereos = ['✈️', '🚁', '🛩️', '🚀', '🛸', '🛰️'];
        const tiposBanho = ['🧼', '🚿'];
        const tiposComida = ['🌽', '🍎', '🌿'];

        const svgsObjetos = {{
            'CAPIVARA': '<svg viewBox="0 0 84 60" width="76" height="54"><ellipse cx="40" cy="54" rx="26" ry="4.5" fill="rgba(0,0,0,0.28)"/><rect x="20" y="42" width="7" height="12" rx="3" fill="#4E342E"/><rect x="30" y="43" width="7" height="11" rx="3" fill="#5D4037"/><rect x="49" y="42" width="7" height="12" rx="3" fill="#4E342E"/><rect x="58" y="43" width="7" height="11" rx="3" fill="#5D4037"/><ellipse cx="40" cy="33" rx="25" ry="15" fill="#795548" stroke="#3E2723" stroke-width="1.5"/><rect x="50" y="13" width="24" height="19" rx="8" fill="#8D6E63" stroke="#3E2723" stroke-width="1.5"/><ellipse cx="53" cy="12" rx="3" ry="4.5" fill="#4E342E"/><circle cx="62" cy="19" r="2.2" fill="#1A1A1A"/><ellipse cx="71" cy="22" rx="2.5" ry="2" fill="#2E1B16"/><path d="M65 27 Q69 29 73 27" stroke="#3E2723" stroke-width="1.5" fill="none"/></svg>',
            'PEIXE_DOURADO': '<svg viewBox="0 0 92 52" width="76" height="44"><defs><linearGradient id="douradoGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FF8F00"/><stop offset="45%" stop-color="#FFD54F"/><stop offset="100%" stop-color="#FFF8E1"/></linearGradient></defs><path d="M24 26 L5 11 L12 26 L5 41 Z" fill="#E65100"/><path d="M40 13 Q50 3 60 14 Z" fill="#EF6C00"/><ellipse cx="50" cy="26" rx="28" ry="13" fill="url(#douradoGrad)" stroke="#BF360C" stroke-width="1.2"/><circle cx="70" cy="22" r="2.6" fill="#111111"/><circle cx="70.8" cy="21.2" r="0.9" fill="#FFFFFF"/></svg>',
            'PEIXE_TILAPIA': '<svg viewBox="0 0 90 56" width="72" height="46"><defs><linearGradient id="tilapiaGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#37474F"/><stop offset="50%" stop-color="#78909C"/><stop offset="100%" stop-color="#CFD8DC"/></linearGradient></defs><path d="M24 28 L6 13 L11 28 L6 43 Z" fill="#455A64"/><ellipse cx="50" cy="28" rx="27" ry="15" fill="url(#tilapiaGrad)" stroke="#263238" stroke-width="1.2"/><circle cx="69" cy="24" r="2.5" fill="#111111"/><circle cx="69.7" cy="23.3" r="0.8" fill="#FFFFFF"/></svg>',
            'PEIXE_LAMBARI': '<svg viewBox="0 0 76 42" width="56" height="32"><path d="M20 21 L5 10 L10 21 L5 32 Z" fill="#E53935"/><ellipse cx="42" cy="21" rx="22" ry="9.5" fill="#ECEFF1" stroke="#607D8B" stroke-width="1.2"/><line x1="24" y1="21" x2="60" y2="21" stroke="#0288D1" stroke-width="2.5" opacity="0.7"/><circle cx="57" cy="18.5" r="2" fill="#111111"/></svg>',
            'ESCORREGADOR': '<svg viewBox="0 0 110 95" width="98" height="84"><ellipse cx="55" cy="88" rx="44" ry="5" fill="rgba(0,0,0,0.22)"/><path d="M16 86 L28 18 L40 18 L28 86" stroke="#1565C0" stroke-width="5.5" fill="none" stroke-linecap="round"/><line x1="21" y1="36" x2="34" y2="36" stroke="#FFB300" stroke-width="4"/><line x1="19" y1="53" x2="32" y2="53" stroke="#FFB300" stroke-width="4"/><line x1="17" y1="70" x2="30" y2="70" stroke="#FFB300" stroke-width="4"/><path d="M38 20 Q58 64 98 80" stroke="#E53935" stroke-width="10" fill="none" stroke-linecap="round"/></svg>',
            'BALANCO': '<svg viewBox="0 0 105 95" width="94" height="84"><ellipse cx="52" cy="88" rx="40" ry="5" fill="rgba(0,0,0,0.22)"/><path d="M14 86 L28 16 L76 16 L90 86" stroke="#D32F2F" stroke-width="5.5" fill="none" stroke-linecap="round"/><line x1="42" y1="16" x2="42" y2="64" stroke="#546E7A" stroke-width="2.5"/><line x1="62" y1="16" x2="62" y2="64" stroke="#546E7A" stroke-width="2.5"/><rect x="35" y="62" width="34" height="7" rx="3" fill="#FFB300" stroke="#E65100" stroke-width="1.5"/></svg>',
            'GANGORRA': '<svg viewBox="0 0 110 74" width="98" height="66"><ellipse cx="55" cy="68" rx="42" ry="4.5" fill="rgba(0,0,0,0.22)"/><polygon points="45,67 55,40 65,67" fill="#1565C0"/><line x1="12" y1="55" x2="98" y2="27" stroke="#FFB300" stroke-width="7.5" stroke-linecap="round"/></svg>'
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
                for (let i = 0; i < 32; i++) {{
                    const st = document.createElement('div');
                    st.className = 'estrela-noite';
                    const tam = (Math.random() * 3.5 + 2) + 'px';
                    st.style.width = tam; st.style.height = tam;
                    st.style.left = Math.random() * 96 + '%';
                    st.style.top = Math.random() * 42 + '%';
                    st.style.animationDelay = (Math.random() * 2) + 's';
                    camadaNoite.appendChild(st);
                }}
                tocarNota(660, 330, 0.45, 'sine');
                soltarParticulas(el, '✨');
            }} else {{
                cenario.classList.remove('modo-noite');
                el.innerText = '☀️';
                camadaNoite.innerHTML = '';
                tocarNota(380, 880, 0.45, 'triangle');
                soltarParticulas(el, '☀️');
            }}
        }}
        let desenhandoLousa = false;
        let corGizAtual = '#FFFFFF';
        let ctxLousa = null;

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

                const pegarPos = e => {{
                    const r = canvas.getBoundingClientRect();
                    return {{ x: e.clientX - r.left, y: e.clientY - r.top }};
                }};
                canvas.onpointerdown = e => {{
                    desenhandoLousa = true;
                    const p = pegarPos(e);
                    ctxLousa.strokeStyle = corGizAtual;
                    ctxLousa.beginPath();
                    ctxLousa.moveTo(p.x, p.y);
                }};
                canvas.onpointermove = e => {{
                    if (!desenhandoLousa) return;
                    const p = pegarPos(e);
                    ctxLousa.lineTo(p.x, p.y);
                    ctxLousa.stroke();
                }};
                canvas.onpointerup = () => {{ desenhandoLousa = false; }};
                canvas.onpointerleave = () => {{ desenhandoLousa = false; }};
            }}
        }}

        function fecharSalaAula() {{
            const modal = document.getElementById('modal-sala');
            if (modal) modal.style.display = 'none';
            tocarNota(620, 400, 0.2, 'sine');
        }}

        function mudarCorGiz(cor) {{
            corGizAtual = cor;
            tocarNota(700, 920, 0.12, 'sine');
        }}

        function limparLousa() {{
            const canvas = document.getElementById('lousa-canvas');
            if (canvas && ctxLousa) {{
                ctxLousa.clearRect(0, 0, canvas.width, canvas.height);
                tocarNota(300, 180, 0.25, 'sine');
            }}
        }}

        function carimbarLousa(emoji) {{
            const canvas = document.getElementById('lousa-canvas');
            if (canvas && ctxLousa) {{
                ctxLousa.font = '38px sans-serif';
                ctxLousa.fillText(emoji, 60 + Math.random() * (canvas.width - 140), 50 + Math.random() * (canvas.height - 100));
                tocarNota(580, 880, 0.16, 'triangle');
            }}
        }}

        function interagirProfessora(el) {{
            const frases = ['Muito bem! 🌟', 'Que lindo desenho! 🎨', 'Parabéns, turma! 👏', 'Vamos aprender juntos! 📚'];
            const balao = document.getElementById('fala-professora');
            if (balao) balao.innerText = frases[Math.floor(Math.random() * frases.length)];
            tocarNota(540, 860, 0.22, 'triangle');
            soltarParticulas(el, '⭐');
        }}
        function limparEstadosBrinquedo(el) {{
            el.classList.remove('brincando', 'balancando-brinquedo', 'gangorra-brinquedo');
        }}

        function estaNoAr(el) {{
            const r = el.getBoundingClientRect();
            const cy = r.top + r.height / 2;
            const h = window.innerHeight;
            if (mundoAtual === 'espaco') return true;
            if (mundoAtual === 'aeroporto') return cy < h * 0.56;
            return cy < h * 0.48;
        }}

        function atualizarEstadoVoo(el, tocandoSom) {{
            if (!tiposAereos.includes(el.dataset.tipo)) return;
            if (estaNoAr(el)) {{
                if (!el.classList.contains('voando')) {{
                    el.classList.add('voando');
                    if (!el.dataset.dirX) el.dataset.dirX = '1';
                    if (tocandoSom) {{
                        tocarNota(220, 520, 0.35, 'sawtooth');
                        soltarParticulas(el, '💨');
                    }}
                }}
            }} else {{
                el.classList.remove('voando');
                el.style.transform = 'scaleX(1)';
            }}
        }}

        function estaNaAgua(el) {{
            const r = el.getBoundingClientRect();
            const cy = r.top + r.height / 2;
            const h = window.innerHeight;
            if (mundoAtual === 'represa') return cy >= h * 0.35 && cy <= h * 0.65;
            if (mundoAtual === 'oceano') return cy >= h * 0.20;
            return false;
        }}

        function atualizarEstadoNado(el, tocandoSom) {{
            if (!tiposAnimais.includes(el.dataset.tipo)) return;
            if (el.classList.contains('brincando')) return;
            const naAgua = estaNaAgua(el);
            const ehPeixe = tiposPeixes.includes(el.dataset.tipo);
            if (naAgua) {{
                if (!el.classList.contains('nadando')) {{
                    el.classList.add('nadando');
                    if (ehPeixe) el.classList.add('peixe-nadando');
                    el.dataset.dirX = Math.random() > 0.5 ? '1' : '-1';
                    if (tocandoSom) {{
                        tocarNota(280, 560, 0.25, 'sine');
                        soltarParticulas(el, '💦');
                    }}
                }}
            }} else {{
                el.classList.remove('nadando', 'peixe-nadando');
                el.style.transform = 'scaleX(1)';
            }}
        }}

        function loopMovimentoContinuo() {{
            const animaisOlhandoDireita = ['CAPIVARA', 'PEIXE_DOURADO', 'PEIXE_TILAPIA', 'PEIXE_LAMBARI'];
            const aereosOlhandoDireita = ['✈️', '🛩️'];
            const maxW = window.innerWidth - 80;

            let comidaNaAgua = null;
            document.querySelectorAll('.bicho').forEach(item => {{
                if (tiposComida.includes(item.dataset.tipo) && estaNaAgua(item)) comidaNaAgua = item;
            }});

            document.querySelectorAll('.bicho.nadando').forEach(el => {{
                if (el.dataset.arrastando === '1') return;
                let left = parseFloat(el.style.left);
                if (isNaN(left)) left = el.offsetLeft;
                let top = parseFloat(el.style.top);
                if (isNaN(top)) top = el.offsetTop;

                let dir = parseFloat(el.dataset.dirX || '1');
                const ehPeixe = tiposPeixes.includes(el.dataset.tipo);
                let vel = ehPeixe ? (el.dataset.tipo === 'PEIXE_LAMBARI' ? 1.8 : 1.35) : 1.0;

                if (ehPeixe && comidaNaAgua) {{
                    const rCom = comidaNaAgua.getBoundingClientRect();
                    const rEl = el.getBoundingClientRect();
                    const dx = (rCom.left + rCom.width / 2) - (rEl.left + rEl.width / 2);
                    const dy = (rCom.top + rCom.height / 2) - (rEl.top + rEl.height / 2);
                    dir = dx >= 0 ? 1 : -1;
                    vel = 2.4;
                    top += Math.sign(dy) * Math.min(Math.abs(dy) * 0.04, 1.4);
                    el.style.top = top + 'px';

                    if (Math.abs(dx) < 28 && Math.abs(dy) < 28) {{
                        tocarNota(380, 720, 0.16, 'triangle');
                        soltarParticulas(el, '❤️');
                        soltarParticulas(el, '🫧');
                        comidaNaAgua.remove();
                        comidaNaAgua = null;
                    }}
                }}

                left += dir * vel;
                if (left >= maxW) {{ left = maxW; dir = -1; }}
                else if (left <= 10) {{ left = 10; dir = 1; }}
                el.dataset.dirX = dir.toString();
                el.style.left = left + 'px';
                const olhaDir = animaisOlhandoDireita.includes(el.dataset.tipo);
                const inverte = olhaDir ? (dir < 0 ? -1 : 1) : (dir > 0 ? -1 : 1);
                el.style.transform = `scaleX(${{inverte}})`;
            }});

            document.querySelectorAll('.bicho.voando').forEach(el => {{
                if (el.dataset.arrastando === '1') return;
                let left = parseFloat(el.style.left);
                if (isNaN(left)) left = el.offsetLeft;
                let dir = parseFloat(el.dataset.dirX || '1');
                const vel = el.dataset.tipo === '🚁' ? 1.5 : 2.3;
                left += dir * vel;
                if (left >= maxW) {{ left = maxW; dir = -1; }}
                else if (left <= 10) {{ left = 10; dir = 1; }}
                el.dataset.dirX = dir.toString();
                el.style.left = left + 'px';
                const olhaDir = aereosOlhandoDireita.includes(el.dataset.tipo);
                const inverte = olhaDir ? (dir < 0 ? -1 : 1) : (dir > 0 ? -1 : 1);
                el.style.transform = `scaleX(${{inverte}})`;
            }});

            requestAnimationFrame(loopMovimentoContinuo);
        }}
        requestAnimationFrame(loopMovimentoContinuo);
        function animarEscorregador(personagem, escorregador) {{
            limparEstadosBrinquedo(personagem);
            personagem.classList.remove('nadando', 'peixe-nadando');
            personagem.classList.add('brincando');
            personagem.style.transform = 'scaleX(1)';

            const rEsc = escorregador.getBoundingClientRect();
            const rPer = personagem.getBoundingClientRect();
            const inicioX = rEsc.left + rEsc.width * 0.25 - rPer.width / 2;
            const inicioY = rEsc.top + rEsc.height * 0.05;
            const fimX = rEsc.left + rEsc.width * 0.85 - rPer.width / 2;
            const fimY = rEsc.top + rEsc.height * 0.62;

            personagem.style.transition = 'none';
            personagem.style.left = inicioX + 'px';
            personagem.style.top = inicioY + 'px';

            tocarNota(780, 260, 0.65, 'triangle');
            soltarParticulas(personagem, '✨');

            requestAnimationFrame(() => {{
                requestAnimationFrame(() => {{
                    personagem.style.transition = 'left 0.75s ease-in, top 0.75s ease-in';
                    personagem.style.left = fimX + 'px';
                    personagem.style.top = fimY + 'px';
                }});
            }});

            setTimeout(() => {{
                personagem.style.transition = 'none';
                limparEstadosBrinquedo(personagem);
                soltarParticulas(personagem, '🎉');
            }}, 800);
        }}

        function verificarBrinquedos(el) {{
            const tipo = el.dataset.tipo;
            if (!tiposAnimais.includes(tipo) && !tiposPessoas.includes(tipo)) return false;

            const rEl = el.getBoundingClientRect();
            const cx = rEl.left + rEl.width / 2;
            const cy = rEl.top + rEl.height / 2;

            let interagiu = false;
            document.querySelectorAll('.bicho.brinquedo').forEach(brinq => {{
                if (interagiu) return;
                const rB = brinq.getBoundingClientRect();
                const perto = cx >= rB.left - 15 && cx <= rB.right + 15 && cy >= rB.top - 25 && cy <= rB.bottom + 15;
                if (!perto) return;

                const tBrinq = brinq.dataset.tipo;
                if (tBrinq === 'ESCORREGADOR') {{
                    interagiu = true;
                    animarEscorregador(el, brinq);
                }} else if (tBrinq === 'BALANCO') {{
                    interagiu = true;
                    limparEstadosBrinquedo(el);
                    el.classList.remove('nadando', 'peixe-nadando');
                    el.classList.add('brincando', 'balancando-brinquedo');
                    el.style.transform = 'scaleX(1)';
                    el.style.left = (rB.left + rB.width * 0.5 - rEl.width / 2) + 'px';
                    el.style.top = (rB.top + rB.height * 0.35) + 'px';
                    tocarNota(380, 560, 0.25, 'sine');
                    soltarParticulas(el, '🎵');
                }} else if (tBrinq === 'GANGORRA') {{
                    interagiu = true;
                    limparEstadosBrinquedo(el);
                    el.classList.remove('nadando', 'peixe-nadando');
                    el.classList.add('brincando', 'gangorra-brinquedo');
                    el.style.transform = 'scaleX(1)';
                    const ladoEsq = cx < (rB.left + rB.width / 2);
                    el.style.left = (rB.left + rB.width * (ladoEsq ? 0.18 : 0.78) - rEl.width / 2) + 'px';
                    el.style.top = (rB.top + rB.height * (ladoEsq ? 0.32 : 0.12)) + 'px';
                    tocarNota(320, 480, 0.25, 'triangle');
                    soltarParticulas(el, '⭐');
                }}
            }});
            return interagiu;
        }}

        function verificarInteracaoElementos(el, soltou) {{
            const tipo = el.dataset.tipo;
            const rEl = el.getBoundingClientRect();
            const cx = rEl.left + rEl.width / 2;
            const cy = rEl.top + rEl.height / 2;

            if (soltou && verificarBrinquedos(el)) return;

            if (tipo === 'CAPIVARA') {{
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
                            el.style.top = (rNinho.top + rNinho.height * 0.22) + 'px';
                            tocarNota(580, 860, 0.18, 'triangle');
                            soltarParticulas(el, '❤️');
                        }}
                    }} else {{ ninho.classList.remove('destaque'); }}
                }}
            }}

            if (tiposBanho.includes(tipo)) {{
                const agora = Date.now();
                if (agora - ultimoBanho > 350) {{
                    document.querySelectorAll('.bicho').forEach(outro => {{
                        if (outro !== el && outro.dataset.tipo === 'CAPIVARA') {{
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
        function interagirCeu(el, tipo) {{
            el.classList.remove('girar-ceu');
            void el.offsetWidth;
            el.classList.add('girar-ceu');
            if (tipo === 'nuvem') {{ tocarNota(300, 180, 0.3, 'sine'); soltarParticulas(el, '💧'); }}
            else if (tipo === 'passaro') {{ tocarNota(780, 1150, 0.18, 'sine'); soltarParticulas(el, '🎵'); }}
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
