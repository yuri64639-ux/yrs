import streamlit as st

st.set_page_config(
    page_title="Portal dos Mundos - EM Pato Donald",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔗 LINKS DOS APLICATIVOS SEPARADOS NA NUVEM (STREAMLIT CLOUD)
# Cole aqui os links reais de cada mundo conforme você for publicando no Streamlit
LINK_ESCOLA  = "https://streamlit.app"
LINK_REPRESA = "https://streamlit.app"
LINK_OCEANO  = "https://streamlit.app"
LINK_ESPACO  = "https://streamlit.app"

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
        
        /* Botões grandes dos mundos */
        div[data-testid="stLinkButton"] > a {
            width: 100% !important;
            height: 145px !important;
            border-radius: 25px !important;
            border: 4px solid white !important;
            font-size: clamp(20px, 4vw, 26px) !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            box-shadow: 0 8px 18px rgba(0,0,0,0.2) !important;
            transition: transform 0.2s !important;
            background-color: #1E90FF !important;
            color: white !important;
        }
        div[data-testid="stLinkButton"] > a:hover {
            transform: scale(1.04) !important;
            background-color: #005BB5 !important;
        }
    </style>

    <div class="cabecalho">
        <h1>🌍 Portal dos Mundos Mágicos</h1>
        <p>🏫 EM Pato Donald - São José do Rio Preto</p>
        <p style="font-size: 15px; margin-top: 6px; color: #333;">Toque em um portal abaixo para entrar no mundo!</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.link_button("🦆\nMundo da Escola", LINK_ESCOLA, use_container_width=True)
    st.write("")
    st.link_button("🐳\nMundo do Oceano", LINK_OCEANO, use_container_width=True)

with col2:
    st.link_button("🦫\nMundo da Represa", LINK_REPRESA, use_container_width=True)
    st.write("")
    st.link_button("🚀\nMundo do Espaço", LINK_ESPACO, use_container_width=True)
