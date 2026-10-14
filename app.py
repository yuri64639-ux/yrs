"""
APP.PY - Ponto de Entrada Principal e Roteador Multi-Tenant
Gerencia o estado da sessão, estilização de segurança e controle de acessos.
"""

import os
import sys

# Garante o alinhamento de caminhos do projeto para importações relativas
raiz_projeto = os.path.dirname(os.path.abspath(__file__))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

import pandas as pd
import streamlit as st
from core.database import inicializar_banco, ob_cx
from views.garcom import renderizar_terminal_garcom, renderizar_fechamento_caixa
from views.gerencia import renderizar_painel_gerencial

# Configuração da página e inicialização de banco
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")
inicializar_banco()

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO (SESSION STATE) ---
estados_obrigatorios = {
    "logado": False,
    "garcom_logado": False,
    "empresa_id_atual": None,
    "senha_master_empresa": "",
    "carrinho": []
}

for chave, valor_padrao in estados_obrigatorios.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor_padrao

# --- SEGURANÇA VISUAL (INJEÇÃO CSS PARA OCULTAÇÃO DE MENUS NATIVOS) ---
st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; } 
    header [data-testid='stToolbar'] { display: none !important; } 
    [data-testid='collapsedControl'] { display: none !important; } 
    header { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- FLUXO DE AUTENTICAÇÃO DO ESTABELECIMENTO ---
if not st.session_state.logado:
    aba_acesso = st.radio(
        "Selecione uma opção:", 
        ["Fazer Login", "Cadastrar Nova Empresa (Criar Conta)"], 
        horizontal=True
    )
    
    if aba_acesso == "Cadastrar Nova Empresa (Criar Conta)":
        with st.form("cadastro_empresa_form"):
            st.subheader("🏢 Cadastrar Empresa no Sistema")
            nova_empresa = st.text_input("Nome do seu Estabelecimento / Empresa:").strip()
            adm_usuario = st.text_input("Usuário Administrador (ex: admin):").strip()
            adm_senha = st.text_input("Defina a Senha do Administrador:", type="password").strip()
            
            if st.form_submit_button("Criar My Conta", type="primary"):
                if not (nova_empresa and adm_usuario and adm_senha):
                    st.error("Todos os campos do formulário são obrigatórios.")
                else:
                    try:
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("INSERT INTO empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                            id_da_empresa = cur.fetchone()[0]
                            cur.execute("INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                            c.commit()
                        st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                    except Exception as error: 
                        st.error(f"Erro crítico durante o processo de cadastro: {error}")
                        
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            with ob_cx() as conn:
                if conn is not None:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("SELECT id, nome_empresa FROM empresas ORDER BY nome_empresa;")
                            dados_empresas = cur.fetchall()
                        
                        dict_empresas = {row[1]: row[0] for row in dados_empresas} if dados_empresas else {}
                        
                        if dict_empresas:
                            empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                            user_input = st.text_input("Usuário Master da Empresa:")
                            senha_input = st.text_input("Senha Master:", type="password")
                            
                            if st.form_submit_button("Liberar Terminal", type="primary"):
                                id_empresa_login = dict_empresas[empresa_selecionada]
                                
                                with ob_cx() as c, c.cursor() as cur:
                                    cur.execute("SET search_path TO public;")
                                    cur.execute(
                                        "SELECT empresa_id, senha FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s;", 
                                        (id_empresa_login, user_input.strip(), senha_input.strip())
                                    )
                                    resultado = cur.fetchone()
                                    
                                if resultado:
                                    st.session_state.logado = True
                                    # CORRIGIDO: Extração do índice [0] e [1] de elementos puros da tupla
                                    st.session_state.empresa_id_atual = int(resultado[0])
                                    st.session_state.senha_master_empresa = str(resultado[1])
                                    st.rerun()
                                else: 
                                    st.error("Credenciais da empresa incorretas ou inexistentes.")
                        else: 
                            st.info("Nenhuma empresa cadastrada no sistema até o momento.")
                    except Exception as error:
                        st.error(f"Falha de conexão ao ler registros: {error}")
    st.stop()

# --- CONTROLE DINÂMICO DE VISUALIZAÇÃO MASTER APÓS LOGIN ---
with ob_cx() as conn_global:
    aba_gerencia, aba_lancamentos, aba_caixa = st.tabs([
        "⚙️ Painel de Controle Gerencial", 
        "🚀 Terminal do Garçom (Lançar)", 
        "🧾 Fechamento de Conta (Caixa)"
    ])
    
    with aba_gerencia:
        if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", width='stretch', key="lock_terminal_global"):
            st.session_state.logado = False
            st.session_state.empresa_id_atual = None
            st.session_state.senha_master_empresa = ""
            st.session_state.garcom_logado = False
            st.session_state.carrinho = []
            st.rerun()
            
        renderizar_painel_gerencial(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
        
    with aba_lancamentos:
        renderizar_terminal_garcom(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
        
    with aba_caixa:
        renderizar_fechamento_caixa(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
