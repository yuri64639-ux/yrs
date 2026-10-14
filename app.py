# ==============================================================================
# APP.PY - ARQUIVO PRINCIPAL (ROTEADOR E ENTRADA DO SISTEMA)
# ==============================================================================
import sys
import os

# Garante de forma absoluta que as subpastas consigam se enxergar no servidor
raiz_projeto = os.path.dirname(os.path.abspath(__file__))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

import streamlit as st
import pandas as pd
from core.database import ob_cx, inicializar_banco
from views.gerencia import renderizar_painel_gerencial
from views.garcom import renderizar_terminal_garcom

st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

# Inicializa estados de sessão essenciais
if "logado" not in st.session_state:
    st.session_state.logado = False
if "garcom_logado" not in st.session_state:
    st.session_state.garcom_logado = False
if "empresa_id_atual" not in st.session_state:
    st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state:
    st.session_state.senha_master_empresa = ""

# Ocultação estrutural de menus nativos do Streamlit para o celular
st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; } 
    header [data-testid='stToolbar'] { display: none !important; } 
    [data-testid='collapsedControl'] { display: none !important; } 
    header { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# Inicializa as tabelas do banco automaticamente antes de carregar o app
inicializar_banco()

conn = ob_cx()

# --- FLUXO DE LOGIN / CADASTRO DE ESTABELECIMENTO ---
if not st.session_state.logado:
    aba_acesso = st.radio("Selecione uma opção:", ["Fazer Login", "Cadastrar Nova Empresa (Criar Conta)"], horizontal=True)
    
    if aba_acesso == "Cadastrar Nova Empresa (Criar Conta)":
        with st.form("cadastro_empresa_form"):
            st.subheader("🏢 Cadastrar Empresa no Sistema")
            nova_empresa = st.text_input("Nome do seu Estabelecimento / Empresa:").strip()
            adm_usuario = st.text_input("Usuário Administrador (ex: admin):").strip()
            adm_senha = st.text_input("Defina a Senha do Administrador:", type="password").strip()
            
            if st.form_submit_button("Criar Minha Conta", type="primary") and nova_empresa and adm_usuario and adm_senha:
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; INSERT INTO empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as e: 
                    st.error(f"Erro no cadastro: {e}")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            if conn is not None:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id, nome_empresa FROM empresas ORDER BY nome_empresa")
                        dados_empresas = cur.fetchall()
                    
                    dict_empresas = {row[1]: row[0] for row in dados_empresas} if dados_empresas else {}
                    
                    if dict_empresas:
                        empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                        user_input = st.text_input("Usuário Master da Empresa:")
                        senha_input = st.text_input("Senha Master:", type="password")
                        
                        if st.form_submit_button("Liberar Terminal", type="primary"):
                            id_empresa_login = dict_empresas[empresa_selecionada]
                            with ob_cx() as c, c.cursor() as cur:
                                cur.execute("SET search_path TO public; SELECT empresa_id, senha FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (id_empresa_login, user_input.strip(), senha_input.strip()))
                                resultado = cur.fetchone()
                            if resultado:
                                st.session_state.logado = True
                                st.session_state.empresa_id_atual = int(resultado[0])
                                st.session_state.senha_master_empresa = str(resultado[1])
                                st.rerun()
                            else: 
                                st.error("Credenciais da empresa incorretas!")
                    else: 
                        st.info("Nenhuma empresa cadastrada ainda.")
                except Exception as e:
                    st.error(f"Erro ao ler empresas: {e}")
                    
    if conn: 
        conn.close()
    st.stop()

# --- CONTROLE DINÂMICO DE VISUALIZAÇÃO APÓS LOGIN ---
if st.session_state.garcom_logado:
    st.markdown("### 📱 Ambiente do Funcionário")
    renderizar_terminal_garcom(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn)
else:
    aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])
    
    with aba_master_sistema:
        if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True):
            st.session_state.logado = False
            st.session_state.empresa_id_atual = None
            st.session_state.senha_master_empresa = ""
            st.session_state.garcom_logado = False
            st.session_state.carrinho = []
            st.rerun()
        renderizar_painel_gerencial(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn)
        
    with aba_master_operador:
        renderizar_terminal_garcom(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn)

if conn: 
    conn.close()
