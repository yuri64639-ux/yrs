import streamlit as st
import psycopg2

st.set_page_config(
    page_title="Portal dos Mundos - EM Pato Donald",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def conectar_neon():
    return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")

def buscar_mundos():
    conn = conectar_neon()
    with conn.cursor() as cur:
        cur.execute("SELECT chave, titulo, icone, url_app FROM public.portal_mundos WHERE chave != 'portal' ORDER BY titulo;")
        rows = cur.fetchall()
    conn.close()
    return rows

def salvar_url_neon(chave, nova_url):
    conn = conectar_neon()
    with conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE public.portal_mundos SET url_app = %s WHERE chave = %s;", (nova_url, chave))
    conn.close()

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
        div[data-testid="stLinkButton"] > a {
            width: 100% !important;
            height: 145px !important;
            border-radius: 25px !important;
            border: 4px solid white !important;
            font-size: 24px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: linear-gradient(to bottom, #1E90FF, #005BB5) !important;
            color: white !important;
            box-shadow: 0 8px 18px rgba(0,0,0,0.2) !important;
        }
    </style>
    <div class="cabecalho">
        <h1>🌍 Portal dos Mundos Mágicos</h1>
        <p style="font-size: 18px; font-weight: bold; margin: 0;">🏫 EM Pato Donald - São José do Rio Preto</p>
    </div>
""", unsafe_allow_html=True)

try:
    mundos = buscar_mundos()
    col1, col2 = st.columns(2)
    for i, (chave, titulo, icone, url_app) in enumerate(mundos):
        with (col1 if i % 2 == 0 else col2):
            st.link_button(f"{icone}\n{titulo}", url_app, use_container_width=True)
            st.write("")
except Exception as e:
    st.error("Erro ao conectar com o Neon. Verifique o DATABASE_URL nos Secrets do Streamlit.")

# Painel administrativo para colar novos links direto no Neon
with st.expander("⚙️ Gerenciar Links na Nuvem (Neon)"):
    conn = conectar_neon()
    with conn.cursor() as cur:
        cur.execute("SELECT chave, titulo, url_app FROM public.portal_mundos;")
        todos = cur.fetchall()
    conn.close()
    for chave, titulo, url_atual in todos:
        novo_valor = st.text_input(f"Link de {titulo}:", value=url_atual, key=f"txt_{chave}")
        if st.button(f"Salvar {titulo}", key=f"btn_{chave}"):
            salvar_url_neon(chave, novo_valor)
            st.success(f"{titulo} atualizado no Neon!")
            st.rerun()
