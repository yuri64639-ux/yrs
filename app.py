"""
APP.PY - Ponto de Entrada Principal, Roteador Multi-Tenant e Persistência de Sessão
Mantém o usuário logado e oculta dinamicamente a gerência se houver garçom ativo.
"""

import os
import sys

# Alinhamento estrito de caminhos do projeto para evitar erros de importação na nuvem
raiz_projeto = os.path.dirname(os.path.abspath(__file__))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

import pandas as pd
import streamlit as st
from core.database import inicializar_banco, ob_cx
from views.garcom import renderizar_terminal_garcom, renderizar_fechamento_caixa
from views.gerencia import renderizar_painel_gerencial

# Inicialização global do layout e banco de dados
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")
inicializar_banco()

# --- RECUPERAÇÃO AUTOMÁTICA DE SESSÃO VIA URL (ANTI-RELOAD) ---
params = st.query_params
token_empresa = params.get("empresa_id", None)
token_senha = params.get("auth_token", None)
aba_salva = params.get("aba_ativa", "0")

logado_inicial = True if (token_empresa and token_senha) else False

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO (SESSION STATE) ---
estados_obrigatorios = {
    "logado": logado_inicial,
    "operador_atual": None,
    "empresa_id_atual": int(token_empresa) if token_empresa else None,
    "senha_master_empresa": token_senha if token_senha else "",
    "carrinho": [],
    "indice_aba_atual": int(aba_salva)
}

for chave, valor_padrao in estados_obrigatorios.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor_padrao

# --- INJEÇÃO CSS PARA ELIMINAR MENUS NATIVOS DO STREAMLIT ---
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
                        cur.execute("SET search_path TO public;")
                        cur.execute("INSERT INTO empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as error: 
                    st.error(f"Erro no cadastro: {error}")
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
                                    st.session_state.empresa_id_atual = int(resultado[0])
                                    st.session_state.senha_master_empresa = str(resultado[1])
                                    
                                    st.query_params["empresa_id"] = str(resultado[0])
                                    st.query_params["auth_token"] = str(resultado[1])
                                    st.query_params["aba_ativa"] = "0"
                                    st.rerun()
                                else: 
                                    st.error("Credenciais da empresa incorretas!")
                        else: 
                            st.info("Nenhuma empresa cadastrada no sistema ainda.")
                    except Exception as error:
                        st.error(f"Falha ao ler registros: {error}")
    st.stop()

# --- CONTROLE DINÂMICO DE VISUALIZAÇÃO MASTER DE ABAS ---
with ob_cx() as conn_global:
    if st.session_state.operador_atual is not None:
        lista_abas = ["🚀 Terminal do Garçom (Lançar)", "🧾 Fechamento de Conta (Caixa)"]
        abas_renderizadas = st.tabs(lista_abas)
        
        with abas_renderizadas[0]:
            st.query_params["aba_ativa"] = "1"
            renderizar_terminal_garcom(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
            
        with abas_renderizadas[1]:
            st.query_params["aba_ativa"] = "2"
            renderizar_fechamento_caixa(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
    else:
        lista_abas = ["⚙️ Painel de Controle Gerencial", "🚀 Terminal do Garçom (Lançar)", "🧾 Fechamento de Conta (Caixa)"]
        abas_renderizadas = st.tabs(lista_abas)
        
        with abas_renderizadas[0]:
            if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", width='stretch', key="lock_terminal_global"):
                st.session_state.logado = False
                st.session_state.empresa_id_atual = None
                st.session_state.senha_master_empresa = ""
                st.session_state.operador_atual = None
                st.session_state.carrinho = []
                st.query_params.clear()
                st.rerun()
            st.query_params["aba_ativa"] = "0"
            renderizar_painel_gerencial(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
            
        with abas_renderizadas[1]:
            st.query_params["aba_ativa"] = "1"
            renderizar_terminal_garcom(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
            
        with abas_renderizadas[2]:
            st.query_params["aba_ativa"] = "2"
            renderizar_fechamento_caixa(st.session_state.empresa_id_atual, st.session_state.senha_master_empresa, conn_global)
