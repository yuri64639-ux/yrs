import streamlit as st

st.set_page_config(
    page_title="Portal dos Mundos - EM Pato Donald",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def tela_hub():
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            .stApp {
                background: linear-gradient(135deg, #87CEFA 0%, #E0F7FA 50%, #FFD54F 100%);
                font-family: 'Comic Sans MS', sans-serif;
            }
            .titulo-hub {
                text-align: center;
                color: #003366;
                background: #FFD700;
                border: 4px solid #003366;
                border-radius: 25px;
                padding: 15px;
                margin-bottom: 25px;
                box-shadow: 0 6px 15px rgba(0,0,0,0.2);
            }
            div.stButton > button {
                width: 100%;
                height: 140px;
                border-radius: 25px !important;
                font-size: 24px !important;
                font-weight: bold !important;
                border: 4px solid white !important;
                box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
                transition: transform 0.2s !important;
            }
            div.stButton > button:hover {
                transform: scale(1.04) !important;
            }
        </style>
        <div class="titulo-hub">
            <h1>🌍 Portal dos Mundos Mágicos</h1>
            <p style="font-size: 18px; margin: 0;">🏫 EM Pato Donald - São José do Rio Preto | Escolha um mundo para entrar!</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🦆\nMundo da Escola", key="btn_escola", use_container_width=True):
            st.switch_page("mundos/escola.py")
        st.write("")
        if st.button("🐠\nMundo do Oceano", key="btn_oceano", use_container_width=True):
            st.switch_page("mundos/oceano.py")

    with col2:
        if st.button("🦫\nMundo da Represa", key="btn_represa", use_container_width=True):
            st.switch_page("mundos/represa.py")
        st.write("")
        if st.button("🚀\nMundo do Espaço", key="btn_espaco", use_container_width=True):
            st.switch_page("mundos/espaco.py")

# Vincula todos os apps na nuvem do Streamlit
pg = st.navigation([
    st.Page(tela_hub, title="Portal Principal", icon="🌍", default=True),
    st.Page("mundos/escola.py", title="EM Pato Donald", icon="🦆"),
    st.Page("mundos/represa.py", title="Represa Municipal", icon="🦫"),
    st.Page("mundos/oceano.py", title="Fundo do Mar", icon="🐠"),
    st.Page("mundos/espaco.py", title="Espaço Sideral", icon="🚀"),
], position="hidden")

pg.run()
