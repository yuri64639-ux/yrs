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
            "titulo": "🏫 EM Pato Donald - São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #64B5F6 0%, #B3E5FC 54%, #E6B88A 54%, #558B2F 64%, #33691E 100%)",
            "placa_bg": "#FFD700", "placa_cor": "#003366",
            "itens": ["PATO", "ESCORREGADOR", "BALANCO", "GANGORRA", "BOLA", "CACHORRO"],
            "espalhados": [
                ("PATO", 10, 58), ("ESCORREGADOR", 28, 54), ("BALANCO", 50, 54),
                ("GANGORRA", 72, 58), ("BOLA", 20, 74), ("CACHORRO", 44, 72), ("📚", 68, 74)
            ],
            "clima_extra": "chuva_arcoiris"
        },
        "represa": {
            "titulo": "🌊 Represa Municipal - São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #4FC3F7 0%, #E1F5FE 36%, #0288D1 36%, #01579B 66%, #78909C 66%, #607D8B 74%, #388E3C 74%, #1B5E20 100%)",
            "placa_bg": "#00CED1", "placa_cor": "#003366",
            "itens": ["CAPIVARA", "CISNE", "ESCORREGADOR", "BOLA", "🧼", "🌽"],
            "espalhados": [
                ("CISNE", 14, 46), ("PATO", 62, 48), ("BICICLETA", 22, 62),
                ("CAPIVARA", 10, 74), ("CAPIVARA", 26, 75), ("ESCORREGADOR", 44, 71),
                ("BOLA", 62, 76), ("🧼", 70, 75), ("🌽", 78, 75)
            ],
            "clima_extra": "chuva_arcoiris"
        },
        "oceano": {
            "titulo": "🐠 Mundo do Oceano Azul",
            "fundo": "linear-gradient(to bottom, #26C6DA 0%, #0277BD 45%, #012A4A 100%)",
            "placa_bg": "#00008B", "placa_cor": "#FFFFFF",
            "itens": ["BALEIA", "GOLFINHO", "TARTARUGA", "🐙", "🐠", "🦀"],
            "espalhados": [
                ("BALEIA", 14, 28), ("GOLFINHO", 48, 28), ("🐠", 78, 30),
                ("TARTARUGA", 22, 48), ("🐙", 54, 48), ("🐡", 80, 48),
                ("🦈", 16, 68), ("🦀", 48, 70), ("🦞", 76, 70)
            ],
            "clima_extra": "bolhas"
        },
        "espaco": {
            "titulo": "🚀 Viagem pelo Espaço Sideral",
            "fundo": "radial-gradient(circle, #1B2735 0%, #090A0F 100%)",
            "placa_bg": "#4B0082", "placa_cor": "#FFFFFF",
            "itens": ["FOGUETE", "DISCO", "👨‍🚀", "👽", "CACHORRO", "📚"],
            "espalhados": [
                ("FOGUETE", 16, 34), ("🛰️", 48, 34), ("DISCO", 74, 34),
                ("👨‍🚀", 26, 54), ("👽", 66, 54), ("CACHORRO", 18, 71),
                ("📚", 48, 71), ("PATO", 76, 71)
            ],
            "clima_extra": "estrelas"
        },
        "aeroporto": {
            "titulo": "✈️ Aeroporto de São José do Rio Preto",
            "fundo": "linear-gradient(to bottom, #64B5F6 0%, #BBDEFB 48%, #4CAF50 48%, #2E7D32 62%, #37474F 62%, #263238 88%, #2E7D32 88%)",
            "placa_bg": "#1565C0", "placa_cor": "#FFFFFF",
            "itens": ["AVIAO", "HELICOPTERO", "🛩️", "🧳", "👨‍✈️", "🚌"],
            "espalhados": [
                ("AVIAO", 14, 28), ("HELICOPTERO", 70, 26), ("AVIAO", 22, 64),
                ("🛩️", 54, 65), ("🧳", 38, 76), ("👨‍✈️", 74, 74), ("🚌", 84, 65)
            ],
            "clima_extra": "chuva_arcoiris"
        }
    }
    cfg = mundos[st.session_state.tela_atual]
    icones_btn = {
        "CAPIVARA": '<svg viewBox="0 0 80 56" width="32" height="24" style="vertical-align:middle;"><ellipse cx="38" cy="31" rx="24" ry="15" fill="#795548"/><rect x="48" y="12" width="22" height="17" rx="7" fill="#8D6E63"/><circle cx="60" cy="18" r="2.2" fill="#1A1A1A"/></svg>',
        "PATO": '<svg viewBox="0 0 64 60" width="28" height="24" style="vertical-align:middle;"><ellipse cx="28" cy="38" rx="18" ry="13" fill="#FAFAFA"/><circle cx="42" cy="20" r="10" fill="#2E7D32"/><path d="M50 20 L62 23 L50 26 Z" fill="#FFB300"/></svg>',
        "CISNE": '<svg viewBox="0 0 64 60" width="28" height="24" style="vertical-align:middle;"><ellipse cx="26" cy="40" rx="18" ry="11" fill="#FFFFFF"/><path d="M38 38 C44 26 36 12 46 12 C52 12 52 18 48 20" stroke="#FFFFFF" stroke-width="5" fill="none"/><path d="M51 15 L60 18 L51 20 Z" fill="#FF6F00"/></svg>',
        "CACHORRO": '<svg viewBox="0 0 70 56" width="30" height="24" style="vertical-align:middle;"><ellipse cx="32" cy="34" rx="18" ry="12" fill="#D79E5B"/><circle cx="48" cy="20" r="11" fill="#E0AC69"/><ellipse cx="42" cy="22" rx="4" ry="8" fill="#6D4C41"/></svg>',
        "BALEIA": '<svg viewBox="0 0 90 54" width="34" height="22" style="vertical-align:middle;"><path d="M15 32 Q35 10 68 24 Q82 30 78 40 Q45 48 15 32 Z" fill="#1976D2"/><path d="M15 32 L4 20 L8 32 L4 44 Z" fill="#1565C0"/></svg>',
        "GOLFINHO": '<svg viewBox="0 0 84 50" width="34" height="22" style="vertical-align:middle;"><path d="M14 30 Q40 10 68 26 L78 29 L66 33 Q40 38 14 30 Z" fill="#4FC3F7"/></svg>',
        "TARTARUGA": '<svg viewBox="0 0 76 50" width="32" height="22" style="vertical-align:middle;"><path d="M16 32 A22 18 0 0 1 60 32 Z" fill="#2E7D32"/><circle cx="64" cy="28" r="6" fill="#66BB6A"/></svg>',
        "ESCORREGADOR": '<svg viewBox="0 0 80 70" width="30" height="24" style="vertical-align:middle;"><path d="M14 62 L24 16 L32 16 L22 62" stroke="#1565C0" stroke-width="4" fill="none"/><path d="M30 18 Q44 48 72 58" stroke="#E53935" stroke-width="6" fill="none" stroke-linecap="round"/></svg>',
        "BALANCO": '<svg viewBox="0 0 80 70" width="30" height="24" style="vertical-align:middle;"><path d="M12 62 L24 14 L56 14 L68 62" stroke="#D32F2F" stroke-width="4" fill="none"/><rect x="30" y="47" width="20" height="5" rx="2" fill="#FFB300"/></svg>',
        "GANGORRA": '<svg viewBox="0 0 84 60" width="32" height="24" style="vertical-align:middle;"><polygon points="34,52 42,34 50,52" fill="#1565C0"/><line x1="12" y1="44" x2="72" y2="24" stroke="#FFB300" stroke-width="6" stroke-linecap="round"/></svg>',
        "BOLA": '<svg viewBox="0 0 50 50" width="26" height="24" style="vertical-align:middle;"><circle cx="25" cy="25" r="20" fill="#FFFFFF" stroke="#212121" stroke-width="2"/><polygon points="25,15 33,21 30,30 20,30 17,21" fill="#212121"/></svg>',
        "AVIAO": '<svg viewBox="0 0 90 50" width="34" height="22" style="vertical-align:middle;"><path d="M14 30 L74 30 Q84 30 82 24 L24 22 L12 10 L6 10 L14 30 Z" fill="#ECEFF1" stroke="#1565C0" stroke-width="2"/><path d="M38 26 L56 26 L44 40 L34 40 Z" fill="#1565C0"/></svg>',
        "HELICOPTERO": '<svg viewBox="0 0 90 54" width="34" height="22" style="vertical-align:middle;"><line x1="26" y1="12" x2="82" y2="12" stroke="#263238" stroke-width="3"/><ellipse cx="56" cy="28" rx="22" ry="12" fill="#E53935"/></svg>',
        "FOGUETE": '<svg viewBox="0 0 60 84" width="28" height="24" style="vertical-align:middle;"><path d="M30 6 Q46 28 44 60 L16 60 Q14 28 30 6 Z" fill="#ECEFF1" stroke="#D32F2F" stroke-width="2"/><circle cx="30" cy="40" r="7" fill="#29B6F6"/></svg>',
        "DISCO": '<svg viewBox="0 0 84 52" width="34" height="22" style="vertical-align:middle;"><path d="M26 24 A16 14 0 0 1 58 24 Z" fill="#81D4FA"/><ellipse cx="42" cy="28" rx="34" ry="9" fill="#7E57C2"/></svg>'
    }
    botoes_itens = "".join([f'<button class="btn-item" onclick="criar(\'{i}\')">{icones_btn.get(i, i)}</button>' for i in cfg["itens"]])
    espalhados_js = "".join([f"criarNaPosicao('{emoji}', {x}, {y});" for emoji, x, y in cfg["espalhados"]])
    arvore_frondosa_svg = '<svg viewBox="0 0 120 150" class="arvore-realista-svg"><defs><radialGradient id="copaVerde1" cx="35%" cy="30%" r="70%"><stop offset="0%" stop-color="#81C784"/><stop offset="55%" stop-color="#388E3C"/><stop offset="100%" stop-color="#1B5E20"/></radialGradient><linearGradient id="troncoGrad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#4E342E"/><stop offset="50%" stop-color="#6D4C41"/><stop offset="100%" stop-color="#3E2723"/></linearGradient></defs><ellipse cx="60" cy="142" rx="34" ry="7" fill="rgba(0,0,0,0.28)"/><path d="M51 142 L53 86 L67 86 L69 142 Q60 146 51 142 Z" fill="url(#troncoGrad)"/><path d="M55 96 L40 76 M65 92 L80 74" stroke="#5D4037" stroke-width="5" stroke-linecap="round"/><circle cx="38" cy="70" r="26" fill="url(#copaVerde1)"/><circle cx="82" cy="70" r="26" fill="url(#copaVerde1)"/><circle cx="60" cy="46" r="32" fill="url(#copaVerde1)"/><circle cx="46" cy="58" r="24" fill="#43A047" opacity="0.85"/><circle cx="74" cy="58" r="24" fill="#2E7D32" opacity="0.85"/></svg>'

    palmeira_realista_svg = '<svg viewBox="0 0 120 150" class="arvore-realista-svg"><ellipse cx="56" cy="143" rx="28" ry="6" fill="rgba(0,0,0,0.25)"/><path d="M52 143 Q46 95 58 52 L65 53 Q55 95 60 143 Z" fill="#6D4C41"/><path d="M61 52 Q28 38 14 62 Q34 52 58 56 Z" fill="#2E7D32"/><path d="M61 52 Q94 38 108 62 Q88 52 64 56 Z" fill="#388E3C"/><path d="M61 52 Q30 22 18 36 Q38 36 59 53 Z" fill="#43A047"/><path d="M61 52 Q92 22 104 36 Q84 36 63 53 Z" fill="#66BB6A"/><path d="M61 52 Q60 18 46 22 Q56 34 61 52 Z" fill="#81C784"/><circle cx="57" cy="57" r="4.5" fill="#4E342E"/><circle cx="65" cy="57" r="4.5" fill="#3E2723"/></svg>'

    decoracao_cenario = ""
    if st.session_state.tela_atual == "represa":
        decoracao_cenario = f"""
        <div class="camada-ceu" style="top: 8%;">
            <span class="item-ceu" onclick="interagirCeu(this, 'sol')">☀️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'passaro')">🐦</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'balao')">🎈</span>
        </div>
        <svg viewBox="0 0 1000 320" preserveAspectRatio="none" style="position:absolute; top:14%; left:0; width:100%; height:44%; pointer-events:none; z-index:2;">
            <g fill="#546E7A" opacity="0.6">
                <rect x="40" y="95" width="38" height="95" rx="3"/><rect x="85" y="70" width="46" height="120" rx="3"/>
                <rect x="260" y="80" width="42" height="110" rx="3"/><rect x="310" y="60" width="52" height="130" rx="3"/>
                <rect x="650" y="75" width="48" height="115" rx="3"/><rect x="820" y="65" width="55" height="125" rx="3"/>
            </g>
            <path d="M0,190 Q250,175 500,190 T1000,190 L1000,210 L0,210 Z" fill="#1B5E20"/>
            <path d="M 270 198 Q 500 130 730 198" fill="none" stroke="#D32F2F" stroke-width="11" stroke-linecap="round"/>
            <path d="M 285 198 Q 500 144 715 198" fill="none" stroke="#B71C1C" stroke-width="5"/>
            <line x1="340" y1="176" x2="340" y2="198" stroke="#D32F2F" stroke-width="5"/><line x1="420" y1="160" x2="420" y2="198" stroke="#D32F2F" stroke-width="5"/>
            <line x1="500" y1="154" x2="500" y2="198" stroke="#D32F2F" stroke-width="5"/><line x1="580" y1="160" x2="580" y2="198" stroke="#D32F2F" stroke-width="5"/>
            <line x1="660" y1="176" x2="660" y2="198" stroke="#D32F2F" stroke-width="5"/>
            <rect x="240" y="196" width="520" height="13" rx="4" fill="#E53935" stroke="#8E0000" stroke-width="2"/>
            <rect x="330" y="209" width="14" height="32" fill="#8E0000"/><rect x="493" y="209" width="14" height="32" fill="#8E0000"/><rect x="656" y="209" width="14" height="32" fill="#8E0000"/>
        </svg>
        <div class="camada-agua" style="top: 42%;">
            <span class="item-agua" onclick="interagirAgua(this)">🐟</span>
            <span class="item-agua" onclick="interagirAgua(this)">⛵</span>
            <span class="item-agua" onclick="interagirAgua(this)">🐠</span>
        </div>
        <div class="chafariz-riopreto"><div class="jato-central"></div><div class="jato-esq"></div><div class="jato-dir"></div><div class="espuma-lago"></div></div>
        <div class="pista-riopreto"><div class="faixa-ciclovia"></div><div class="faixa-pedestre"></div></div>
        <div id="ninho-capivaras" class="ninho-capivaras">
            <svg viewBox="0 0 180 95" width="100%" height="100%">
                <ellipse cx="90" cy="68" rx="84" ry="24" fill="#795548" stroke="#3E2723" stroke-width="3"/><ellipse cx="90" cy="66" rx="68" ry="16" fill="#D7CCC8"/>
                <path d="M 15 68 Q 35 45 65 55 Q 90 42 115 55 Q 145 45 165 68" fill="none" stroke="#A1887F" stroke-width="6" stroke-linecap="round"/>
            </svg>
            <div class="placa-ninho">🐾 Ninho das Capivaras</div>
        </div>
        <div class="elementos-fundo" style="top: 52%;">
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{arvore_frondosa_svg}</div>
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{palmeira_realista_svg}</div>
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{arvore_frondosa_svg}</div>
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{palmeira_realista_svg}</div>
        </div>
        """
    elif st.session_state.tela_atual == "escola":
        decoracao_cenario = f"""
        <div class="camada-ceu" style="top: 9%;">
            <span class="item-ceu" onclick="interagirCeu(this, 'sol')">☀️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'aviao')">✈️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'passaro')">🐦</span>
        </div>
        <svg viewBox="0 0 360 180" style="position:absolute; top:29%; left:4%; width:clamp(190px, 34vw, 290px); pointer-events:none; z-index:3; filter: drop-shadow(0 6px 8px rgba(0,0,0,0.28));">
            <polygon points="10,65 180,15 350,65" fill="#D62828" stroke="#8D0801" stroke-width="3"/>
            <rect x="25" y="65" width="310" height="105" fill="#1E88E5" stroke="#0D47A1" stroke-width="3"/>
            <rect x="45" y="72" width="270" height="24" rx="4" fill="#FFD700" stroke="#003366" stroke-width="2"/>
            <text x="180" y="88" font-family="Comic Sans MS, sans-serif" font-size="13" font-weight="bold" fill="#003366" text-anchor="middle">EM PATO DONALD</text>
            <rect x="155" y="115" width="50" height="55" rx="3" fill="#FFD700" stroke="#003366" stroke-width="2"/>
        </svg>
        <div class="elementos-fundo" style="top: 37%;">
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{arvore_frondosa_svg}</div>
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{palmeira_realista_svg}</div>
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{arvore_frondosa_svg}</div>
        </div>
        """
    elif st.session_state.tela_atual == "oceano":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 8%;">
            <span class="item-ceu" onclick="interagirCeu(this, 'sol')">☀️</span>
            <span class="item-agua" onclick="interagirAgua(this)">⛵</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'passaro')">🕊️</span>
        </div>
        <div class="elementos-fundo" style="top: 68%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🪸</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🌿</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🪸</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'bolha')">🐚</span>
        </div>
        """
    elif st.session_state.tela_atual == "espaco":
        decoracao_cenario = """
        <div class="camada-ceu" style="top: 9%;">
            <span class="item-ceu" onclick="interagirCeu(this, 'estrela')">🌠</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'sol')">🌞</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'estrela')">🌠</span>
        </div>
        <div class="elementos-fundo" style="top: 18%;">
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">🪐</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">🌕</span>
            <span class="item-fundo-interativo" onclick="chacoalharFundo(this, 'estrela')">☄️</span>
        </div>
        """
    elif st.session_state.tela_atual == "aeroporto":
        decoracao_cenario = f"""
        <div class="camada-ceu" style="top: 9%;">
            <span class="item-ceu" onclick="interagirCeu(this, 'sol')">☀️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'nuvem')">☁️</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'aviao')">🛫</span>
            <span class="item-ceu" onclick="interagirCeu(this, 'balao')">🎈</span>
        </div>
        <svg viewBox="0 0 800 200" preserveAspectRatio="none" style="position:absolute; top:24%; left:0; width:100%; height:28%; pointer-events:none; z-index:2;">
            <rect x="60" y="90" width="240" height="80" rx="6" fill="#ECEFF1" stroke="#546E7A" stroke-width="3"/>
            <path d="M 55 90 Q 180 40 305 90 Z" fill="#1565C0"/>
            <rect x="330" y="45" width="36" height="125" fill="#CFD8DC" stroke="#455A64" stroke-width="3"/>
            <polygon points="315,45 381,45 370,15 326,15" fill="#263238" stroke="#FFD700" stroke-width="2"/>
            <path d="M 450 170 A 110 75 0 0 1 670 170 Z" fill="#B0BEC5" stroke="#37474F" stroke-width="3"/>
        </svg>
        <div style="position:absolute; top:74%; left:0; width:100%; height:4px; background:repeating-linear-gradient(90deg, #FFFFFF, #FFFFFF 45px, transparent 45px, transparent 85px); pointer-events:none; z-index:2;"></div>
        <div class="elementos-fundo" style="top: 38%;">
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{palmeira_realista_svg}</div>
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{arvore_frondosa_svg}</div>
            <div class="item-fundo-interativo" onclick="chacoalharFundo(this, 'folha')">{palmeira_realista_svg}</div>
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
            #cenario {{ width: 100%; height: 100%; background: {cfg['fundo']}; border-radius: 20px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 12px; position: relative; }}
            .arvore-realista-svg {{ width: clamp(72px, 14vw, 118px); height: auto; display: block; filter: drop-shadow(0 6px 6px rgba(0,0,0,0.28)); }}
            .camada-ceu, .camada-agua {{ position: absolute; left: 0; width: 100%; display: flex; justify-content: space-around; align-items: center; z-index: 4; pointer-events: none; }}
            .item-ceu, .item-agua {{ font-size: clamp(36px, 7vw, 56px); cursor: pointer; pointer-events: auto; display: inline-block; filter: drop-shadow(0 3px 4px rgba(0,0,0,0.2)); }}
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
            .particula-caindo {{ position: absolute; font-size: 22px; pointer-events: none; z-index: 8; animation: animarParticula 1.5s ease-out forwards; }}
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
            .bicho {{ position: absolute; font-size: 50px; cursor: grab; z-index: 6; touch-action: none; filter: drop-shadow(0 6px 6px rgba(0,0,0,0.35)); }}
            .bicho:active {{ cursor: grabbing; transform: scale(1.18); }}
            .conteudo-bicho {{ display: inline-block; }}
            .nadando .conteudo-bicho {{ animation: boiarNaAgua 1.1s infinite alternate ease-in-out; }}
            @keyframes boiarNaAgua {{ 0% {{ transform: translateY(-3px) rotate(-5deg); }} 100% {{ transform: translateY(4px) rotate(5deg); }} }}
            #barra {{ background: rgba(255, 255, 255, 0.94); padding: 8px 12px; border-radius: 22px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); z-index: 10; display: flex; justify-content: center; align-items: center; gap: 6px; flex-wrap: wrap; max-width: 96%; }}
            .btn-item {{ font-size: 24px; border: 2px solid #FFD700; background: #FFF8DC; border-radius: 14px; padding: 4px 8px; cursor: pointer; }}
            .btn-acao {{ font-size: 14px; font-weight: bold; border: none; border-radius: 14px; padding: 8px 11px; cursor: pointer; }}
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
            <button class="btn-acao" style="background:#4CAF50; color:white;" onclick="organizar()">🔄 Organizar</button>
            <button class="btn-acao" style="background:#FF6B6B; color:white;" onclick="limpar()">🗑️</button>
        </div>
    </div>
    <script>
        let estadoClima = 0;
        let timerTrovao = null;
        let ultimoBanho = 0;
        const mundoAtual = "{st.session_state.tela_atual}";
        const tipoClima = "{cfg['clima_extra']}";
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const tiposAnimais = ['CAPIVARA', 'PATO', 'CISNE', 'CACHORRO', 'BALEIA', 'GOLFINHO', 'TARTARUGA', '🦆', '🦢', '🐶', '🐱', '🐳', '🐬', '🐠', '🐢', '🐙', '🦀', '🐡', '🦈', '🦞'];
        const tiposBanho = ['🧼', '🚿'];
        const tiposComida = ['🌽', '🍎', '🌿'];

        const svgsObjetos = {{
            'CAPIVARA': '<svg viewBox="0 0 84 60" width="76" height="54"><ellipse cx="40" cy="54" rx="26" ry="4.5" fill="rgba(0,0,0,0.28)"/><rect x="20" y="42" width="7" height="12" rx="3" fill="#4E342E"/><rect x="30" y="43" width="7" height="11" rx="3" fill="#5D4037"/><rect x="49" y="42" width="7" height="12" rx="3" fill="#4E342E"/><rect x="58" y="43" width="7" height="11" rx="3" fill="#5D4037"/><ellipse cx="40" cy="33" rx="25" ry="15" fill="#795548" stroke="#3E2723" stroke-width="1.5"/><rect x="50" y="13" width="24" height="19" rx="8" fill="#8D6E63" stroke="#3E2723" stroke-width="1.5"/><ellipse cx="53" cy="12" rx="3" ry="4.5" fill="#4E342E"/><circle cx="62" cy="19" r="2.2" fill="#1A1A1A"/><ellipse cx="71" cy="22" rx="2.5" ry="2" fill="#2E1B16"/><path d="M65 27 Q69 29 73 27" stroke="#3E2723" stroke-width="1.5" fill="none"/></svg>',
            'PATO': '<svg viewBox="0 0 70 64" width="64" height="58"><ellipse cx="32" cy="58" rx="20" ry="4" fill="rgba(0,0,0,0.22)"/><path d="M26 48 L24 57 M36 48 L38 57" stroke="#FF8F00" stroke-width="3" stroke-linecap="round"/><ellipse cx="30" cy="40" rx="20" ry="13" fill="#FAFAFA" stroke="#9E9E9E" stroke-width="1.2"/><circle cx="45" cy="21" r="11" fill="#1B5E20"/><path d="M54 20 L67 23 L54 27 Z" fill="#FFB300"/><circle cx="48" cy="19" r="2" fill="#111111"/></svg>',
            'CISNE': '<svg viewBox="0 0 74 66" width="68" height="60"><ellipse cx="30" cy="58" rx="22" ry="4" fill="rgba(0,0,0,0.2)"/><ellipse cx="30" cy="44" rx="22" ry="12" fill="#FFFFFF" stroke="#CFD8DC" stroke-width="1.5"/><path d="M44 42 C52 28 40 12 52 12 C59 12 59 19 54 21" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" fill="none"/><path d="M56 16 L68 19 L56 22 Z" fill="#FF6F00"/><circle cx="53" cy="16" r="1.8" fill="#111111"/></svg>',
            'CACHORRO': '<svg viewBox="0 0 76 62" width="68" height="56"><ellipse cx="36" cy="56" rx="22" ry="4" fill="rgba(0,0,0,0.25)"/><rect x="20" y="42" width="6" height="13" rx="3" fill="#B87D3E"/><rect x="44" y="42" width="6" height="13" rx="3" fill="#B87D3E"/><ellipse cx="35" cy="36" rx="19" ry="12" fill="#D79E5B" stroke="#8D5524" stroke-width="1.5"/><circle cx="52" cy="21" r="12" fill="#E0AC69" stroke="#8D5524" stroke-width="1.5"/><ellipse cx="45" cy="23" rx="4.5" ry="9" fill="#6D4C41"/><circle cx="56" cy="19" r="2.2" fill="#111111"/><circle cx="63" cy="22" r="2.8" fill="#212121"/></svg>',
            'BALEIA': '<svg viewBox="0 0 96 60" width="84" height="52"><path d="M18 35 Q38 10 74 26 Q88 32 82 43 Q46 52 18 35 Z" fill="#1976D2" stroke="#0D47A1" stroke-width="1.5"/><path d="M18 35 L4 21 L9 35 L4 48 Z" fill="#1565C0"/><circle cx="71" cy="31" r="2.2" fill="#111111"/></svg>',
            'GOLFINHO': '<svg viewBox="0 0 90 54" width="80" height="48"><path d="M14 32 Q42 10 72 28 L84 31 L70 35 Q42 42 14 32 Z" fill="#29B6F6" stroke="#0277BD" stroke-width="1.5"/><path d="M42 18 L36 7 L49 17 Z" fill="#0288D1"/><path d="M14 32 L4 23 L8 32 L4 41 Z" fill="#0288D1"/><circle cx="67" cy="28" r="2" fill="#111111"/></svg>',
            'TARTARUGA': '<svg viewBox="0 0 82 54" width="74" height="48"><ellipse cx="26" cy="40" rx="9" ry="4" fill="#66BB6A"/><ellipse cx="52" cy="40" rx="9" ry="4" fill="#66BB6A"/><path d="M18 34 A22 19 0 0 1 62 34 Z" fill="#2E7D32" stroke="#1B5E20" stroke-width="2"/><circle cx="68" cy="30" r="6.5" fill="#66BB6A"/></svg>',
            'ESCORREGADOR': '<svg viewBox="0 0 100 90" width="88" height="78"><ellipse cx="52" cy="83" rx="40" ry="5" fill="rgba(0,0,0,0.22)"/><path d="M16 82 L28 20 L38 20 L26 82" stroke="#1565C0" stroke-width="5" fill="none" stroke-linecap="round"/><line x1="21" y1="36" x2="33" y2="36" stroke="#FFB300" stroke-width="4"/><line x1="19" y1="52" x2="31" y2="52" stroke="#FFB300" stroke-width="4"/><line x1="17" y1="68" x2="29" y2="68" stroke="#FFB300" stroke-width="4"/><path d="M36 22 Q54 62 90 76" stroke="#E53935" stroke-width="9" fill="none" stroke-linecap="round"/></svg>',
            'BALANCO': '<svg viewBox="0 0 100 90" width="88" height="78"><ellipse cx="50" cy="83" rx="38" ry="5" fill="rgba(0,0,0,0.22)"/><path d="M14 82 L28 16 L72 16 L86 82" stroke="#D32F2F" stroke-width="5" fill="none" stroke-linecap="round"/><line x1="40" y1="16" x2="40" y2="62" stroke="#546E7A" stroke-width="2.5"/><line x1="60" y1="16" x2="60" y2="62" stroke="#546E7A" stroke-width="2.5"/><rect x="34" y="60" width="32" height="7" rx="3" fill="#FFB300"/></svg>',
            'GANGORRA': '<svg viewBox="0 0 104 70" width="90" height="62"><ellipse cx="52" cy="64" rx="40" ry="4.5" fill="rgba(0,0,0,0.22)"/><polygon points="42,63 52,38 62,63" fill="#1565C0"/><line x1="12" y1="52" x2="92" y2="26" stroke="#FFB300" stroke-width="7" stroke-linecap="round"/></svg>',
            'BOLA': '<svg viewBox="0 0 56 56" width="46" height="46"><ellipse cx="28" cy="51" rx="16" ry="3.5" fill="rgba(0,0,0,0.25)"/><circle cx="28" cy="26" r="21" fill="#FFFFFF" stroke="#263238" stroke-width="2"/><polygon points="28,15 37,22 33,32 23,32 19,22" fill="#263238"/></svg>',
            'BICICLETA': '<svg viewBox="0 0 96 64" width="82" height="54"><circle cx="22" cy="44" r="14" fill="none" stroke="#263238" stroke-width="3.5"/><circle cx="74" cy="44" r="14" fill="none" stroke="#263238" stroke-width="3.5"/><path d="M22 44 L44 44 L62 24 L36 24 Z" fill="none" stroke="#E53935" stroke-width="3.5"/><line x1="62" y1="24" x2="74" y2="44" stroke="#E53935" stroke-width="3.5"/></svg>',
            'AVIAO': '<svg viewBox="0 0 110 60" width="96" height="52"><path d="M16 36 L88 36 Q102 36 98 28 L30 26 L14 10 L6 10 L16 36 Z" fill="#ECEFF1" stroke="#1565C0" stroke-width="2"/><path d="M44 30 L68 30 L52 48 L40 48 Z" fill="#1565C0"/></svg>',
            'HELICOPTERO': '<svg viewBox="0 0 104 64" width="90" height="54"><line x1="28" y1="12" x2="94" y2="12" stroke="#263238" stroke-width="3.5"/><line x1="62" y1="12" x2="62" y2="20" stroke="#263238" stroke-width="3"/><ellipse cx="64" cy="33" rx="25" ry="14" fill="#E53935"/><path d="M40 33 L12 28 L9 20 L4 20 L7 36 L40 36 Z" fill="#C62828"/></svg>',
            'FOGUETE': '<svg viewBox="0 0 68 96" width="58" height="82"><path d="M34 6 Q52 32 49 68 L19 68 Q16 32 34 6 Z" fill="#ECEFF1" stroke="#D32F2F" stroke-width="2"/><path d="M34 6 Q43 20 45 28 L23 28 Q25 20 34 6 Z" fill="#D32F2F"/><circle cx="34" cy="44" r="9" fill="#29B6F6"/><path d="M25 68 L34 88 L43 68 Z" fill="#FF9800"/></svg>',
            'DISCO': '<svg viewBox="0 0 96 60" width="84" height="52"><path d="M28 28 A20 16 0 0 1 68 28 Z" fill="#81D4FA"/><ellipse cx="48" cy="32" rx="40" ry="11" fill="#7E57C2"/></svg>'
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
            const naAgua = estaNaAgua(el);
            if (naAgua) {{
                if (!el.classList.contains('nadando')) {{
                    el.classList.add('nadando');
                    el.dataset.dirX = Math.random() > 0.5 ? '1' : '-1';
                    if (tocandoSom) {{
                        tocarNota(280, 560, 0.25, 'sine');
                        soltarParticulas(el, '💦');
                    }}
                }}
            }} else {{
                el.classList.remove('nadando');
                el.style.transform = 'scaleX(1)';
            }}
        }}

        function loopNado() {{
            const animaisOlhandoDireita = ['CAPIVARA', 'PATO', 'CISNE', 'CACHORRO', 'BALEIA', 'GOLFINHO', 'TARTARUGA'];
            document.querySelectorAll('.bicho.nadando').forEach(el => {{
                if (el.dataset.arrastando === '1') return;
                let left = parseFloat(el.style.left);
                if (isNaN(left)) left = el.offsetLeft;
                let dir = parseFloat(el.dataset.dirX || '1');
                const maxW = window.innerWidth - 75;
                left += dir * 1.1;
                if (left >= maxW) {{ left = maxW; dir = -1; }}
                else if (left <= 10) {{ left = 10; dir = 1; }}
                el.dataset.dirX = dir.toString();
                el.style.left = left + 'px';
                const olhaDir = animaisOlhandoDireita.includes(el.dataset.tipo);
                const inverte = olhaDir ? (dir < 0 ? -1 : 1) : (dir > 0 ? -1 : 1);
                el.style.transform = `scaleX(${{inverte}})`;
            }});
            requestAnimationFrame(loopNado);
        }}
        requestAnimationFrame(loopNado);

        function verificarInteracaoElementos(el, soltou) {{
            const tipo = el.dataset.tipo;
            const rEl = el.getBoundingClientRect();
            const cx = rEl.left + rEl.width / 2;
            const cy = rEl.top + rEl.height / 2;

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

            if (tiposComida.includes(tipo) && soltou) {{
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
            if (tipo === 'sol') {{ tocarNota(440, 880, 0.35, 'triangle'); soltarParticulas(el, '✨'); }}
            else if (tipo === 'nuvem') {{ tocarNota(300, 180, 0.3, 'sine'); soltarParticulas(el, '💧'); }}
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
            el.dataset.tipo = item;
            const miolo = document.createElement('div');
            miolo.className = 'conteudo-bicho';
            if (svgsObjetos[item]) {{ miolo.innerHTML = svgsObjetos[item]; }}
            else {{ miolo.innerText = item; }}
            el.appendChild(miolo);
            el.style.left = (window.innerWidth * xPct / 100) + 'px';
            el.style.top = (window.innerHeight * yPct / 100) + 'px';

            let drag = false, ox = 0, oy = 0;
            el.onpointerdown = e => {{
                drag = true;
                el.dataset.arrastando = '1';
                const r = el.getBoundingClientRect();
                ox = e.clientX - r.left; oy = e.clientY - r.top; el.setPointerCapture(e.pointerId);
            }};
            el.onpointermove = e => {{
                if (!drag) return;
                el.style.left = Math.max(5, Math.min(e.clientX - ox, window.innerWidth - 75)) + 'px';
                el.style.top = Math.max(45, Math.min(e.clientY - oy, window.innerHeight - 120)) + 'px';
                verificarInteracaoElementos(el, false);
            }};
            el.onpointerup = e => {{
                drag = false;
                el.dataset.arrastando = '0';
                el.releasePointerCapture(e.pointerId);
                atualizarEstadoNado(el, true);
                verificarInteracaoElementos(el, true);
            }};
            palco.appendChild(el);
            atualizarEstadoNado(el, false);
        }}

        function criar(item) {{ criarNaPosicao(item, 15 + Math.random() * 65, 50 + Math.random() * 25); }}
        function limpar() {{ document.getElementById('palco').innerHTML = ''; }}
        function organizar() {{ limpar(); {espalhados_js} }}
        organizar();
    </script>
    </body>
    </html>
    """

    components.html(html_cenario, height=700, scrolling=False)
