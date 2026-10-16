import os
import sys
import streamlit as st

# =====================================================================
# FIX OBRIGATÓRIO PARA O STREAMLIT CLOUD (Insira no topo do arquivo)
# =====================================================================
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
if diretorio_atual not in sys.path:
    sys.path.append(diretorio_atual)

# =====================================================================
# SEUS IMPORTS ORIGINAIS (Agora vão funcionar sem dar ModuleNotFoundError)
# =====================================================================
from views.garcom_login import renderizar_terminal_garcom
from datetime import datetime
import psycopg2
import pandas as pd

# =====================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTADO DA SESSÃO
# =====================================================================
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

if "logado" not in st.session_state: 
    st.session_state.logado = False
if "usuario_atual" not in st.session_state: 
    st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: 
    st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: 
    st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state: 
    st.session_state.garcom_logado = False
if "carrinho" not in st.session_state: 
    st.session_state.carrinho = []

# Ocultação do menu nativo do Streamlit via injeção de CSS
st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
    header [data-testid="stToolbar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# Conexão dinâmica com o Banco de Dados PostgreSQL
def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: 
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

# Execução do banco e fluxo do sistema...
conn = ob_cx()
if conn:
    with conn.cursor() as cur:
        cur.execute("SET search_path TO public;")
        # Suas tabelas e constraints continuam aqui normalmente...
    conn.commit()

# --- LOGÍSTICA DE ACESSO ---
if not st.session_state.logado:
    # Tela de Login / Cadastro da Empresa original
    aba_acesso = st.radio("Selecione uma opção:", ["Fazer Login", "Cadastrar Nova Empresa (Criar Conta)"], horizontal=True)
    # (Restante do seu fluxo de login de empresa...)
    st.stop()

# --- CHAMADA DO TERMINAL DO GARÇOM VINDA DA PASTA VIEWS ---
# Se o estabelecimento estiver logado, renderiza o ambiente
if st.session_state.logado:
    # Aqui o Streamlit chama a função importada que estava dando erro
    renderizar_terminal_garcom()

if conn: 
    conn.close()
