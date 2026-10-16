# ==============================================================================
# CONFIGURAÇÕES, IMPORTS SEGUROS, TRATAMENTO DE ROTAS E AUTENTICAÇÃO DE EMPRESA
# ==============================================================================
import os
import sys
from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

# Configuração de Identidade Visual na Aba do Navegador
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

# Injeção forçada de caminhos para os módulos locais
raiz_projeto = os.path.dirname(os.path.abspath(__file__))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)
caminho_cloud = "/mount/src/yrs"
if caminho_cloud not in sys.path:
    sys.path.insert(0, caminho_cloud)

# --- IMPORTS DOS MÓDULOS FILHOS QUE ESTÃO OK ---
try:
    from core.database import inicializar_banco, ob_cx                      
    from views.caixa import renderizar_fechamento_caixa                     
    from views.gerencia import renderizar_painel_gerencial                  
except ModuleNotFoundError as e:
    st.error(f"🚨 Erro ao carregar dependências: {e}")
    st.stop()

# --- FUNÇÃO DE LOGIN DO GARÇOM INTEGRADA (CONTORNO DO ERRO DO GITHUB) ---
def renderizar_terminal_garcom():
    """
    Interface de identificação e login do garçom integrada para evitar o erro de importação.
    """
    st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🍽️ Terminal do Garçom</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Insira suas credenciais para acessar os pedidos</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("form_login_garcom"):
            codigo_garcom = st.text_input("Código de Identificação", placeholder="Ex: 1234")
            senha_garcom = st.text_input("Senha", type="password", placeholder="••••")
            botao_entrar = st.form_submit_button("Acessar Terminal")
            
            if botao_entrar:
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            SELECT usuario FROM public.usuarios 
                            WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s
                        """, (st.session_state.empresa_id_atual, codigo_garcom.strip().lower(), senha_garcom.strip()))
                        res_garcom = cur.fetchone()
                        
                    if res_garcom:
                        st.session_state.garcom_logado = True
                        st.session_state.usuario_atual = str(res_garcom[0])
                        st.success(f"Bem-vindo, {st.session_state.usuario_atual.upper()}!")
                        st.rerun()
                    else:
                        st.error("❌ Credenciais do garçom incorretas para esta empresa!")
                except Exception as erro_db:
                    st.error(f"Erro ao conectar com a base de dados: {erro_db}")

# --- INICIALIZAÇÃO DE TODAS AS VARIÁVEIS DE SESSÃO DO ECOSSISTEMA ---
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# Ocultação estética profissional do menu nativo do Streamlit via CSS
st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
    header [data-testid="stToolbar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# Inicialização estrutural do banco
try:
    conn = ob_cx()
    if conn is not None:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO public;")
            inicializar_banco(cur)
        conn.commit()
        conn.close()
except Exception:
    pass

# ==============================================================================
# LOGÍSTICA DE ACESSO DO ESTABELECIMENTO (AUTENTICAÇÃO DE EMPRESA)
# ==============================================================================
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
                        cur.execute("INSERT INTO public.empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Acesse a aba Fazer Login.")
                except Exception as e:
                    st.error(f"Erro no cadastro da empresa: {e}")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            try:
                with ob_cx() as c:
                    df_lista_empresas = pd.read_sql("SELECT id, nome_empresa FROM public.empresas ORDER BY nome_empresa", c)
                dict_empresas = {row["nome_empresa"]: row["id"] for _, row in df_lista_empresas.iterrows()} if not df_lista_empresas.empty else {}
            except Exception:
                dict_empresas = {}
                
            if dict_empresas:
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                user_input = st.text_input("Usuário Master da Empresa:")
                senha_input = st.text_input("Senha Master:", type="password")
                
                if st.form_submit_button("Liberar Terminal", type="primary"):
                    id_empresa_login = dict_empresas[empresa_selecionada]
                    try:
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("""
                                SELECT empresa_id, senha FROM public.usuarios 
                                WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s
                            """, (id_empresa_login, user_input.strip(), senha_input.strip()))
                            resultado = cur.fetchone()
                            
                        if resultado:
                            st.session_state.logado = True
                            st.session_state.empresa_id_atual = int(resultado[0])
                            st.session_state.senha_master_empresa = str(resultado[1])
                            st.rerun()
                        else:
                            st.error("Credenciais da empresa incorretas!")
                    except Exception as e:
                        st.error(f"Erro ao autenticar: {e}")
            else:
                st.info("Nenhuma empresa cadastrada ainda no ecossistema cloud.")
                
    st.stop()

# ==============================================================================
# RENDERIZAÇÃO DAS TELAS OPERACIONAIS ATIVAS (AMBIENTE LOGADO)
# ==============================================================================
if st.session_state.garcom_logado:
    st.markdown(f"### 📱 Ambiente de Trabalho — Operador Ativo: {st.session_state.usuario_atual.upper()}")
    
    if st.button("🔒 Sair do Terminal / Trocar Garçom", key="g_logout_btn"):
        st.session_state.garcom_logado = False
        st.session_state.usuario_atual = ""
        st.session_state.carrinho = []
        st.rerun()
        
    aba_operacao_garcom = st.radio("Selecione a Ação Ativa:", ["➕ Lançar Pedido", "🧾 Fechar Mesas / Gerenciar Contas"], horizontal=True)
    
    if aba_operacao_garcom == "➕ Lançar Pedido":
        st.info("Utilize o lançador de pedidos integrado do garçom configurado em seu painel.")
    else:
        renderizar_fechamento_caixa()

else:
    aba_master_gerencia, aba_master_atendimento = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal de Identificação do Garçom"])
    
    with aba_master_gerencia:
        if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", key="master_lock_emp_btn"):
            st.session_state.logado = False
            st.session_state.empresa_id_atual = None
            st.session_state.senha_master_empresa = ""
            st.session_state.garcom_logado = False
            st.session_state.carrinho = []
            st.rerun()
            
        st.markdown("---")
        st.subheader("🔑 Autenticação Gerencial Requerida")
        senha_gerencial_digitada = st.text_input("Digite a Senha Master da Empresa para liberar as ferramentas:", type="password", key="senha_painel_gerencial_input")
        
        if senha_gerencial_digitada != st.session_state.senha_master_empresa:
            st.warning("🔒 Conteúdo restrito. Insira a senha master válida do estabelecimento.")
        else:
            renderizar_painel_gerencial()
            
    with aba_master_atendimento:
        # Executa a função clonada localmente para ignorar o arquivo com problema do GitHub
        renderizar_terminal_garcom()
