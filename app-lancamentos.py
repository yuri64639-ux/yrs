import streamlit as st
from banco import inicializar_tabelas
from acesso import renderizar_tela_acesso
from gerencia import renderizar_painel_gerencial
from garcom import renderizar_terminal_garcom, lancar_novo_pedido
from contas import gerenciar_contas_ativas

# Configuração global da página do ecossistema multi-tenant
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

# Inicialização e manutenção estrita de todas as variáveis de sessão originais
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# Ocultação do menu nativo do Streamlit via injeção de CSS
st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
    header [data-testid="stToolbar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# Inicializa as tabelas relacionais em lote de forma protegida
inicializar_tabelas()

# Controle de fluxo de acesso da empresa
if not st.session_state.logado:
    renderizar_tela_acesso()

# Layout Geral Demandado: Abas Masters de Nível Superior Logo Após o Login da Empresa
aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])

with aba_master_sistema:
    emp_id = st.session_state.empresa_id_atual
    if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True, key="master_lock_empresa"):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.garcom_logado = False
        st.session_state.carrinho = []
        st.rerun()
    renderizar_painel_gerencial()

with aba_master_operador:
    emp_id = st.session_state.empresa_id_atual
    garcom_ativo = renderizar_terminal_garcom()
    if garcom_ativo:
        aba_operacao = st.radio("Selecione a Ação:", ["➕ Lançar Pedido (Abrir/Adicionar Itens)", "🧾 Gerenciar Contas / Fechar Mesas"], horizontal=True)
        if aba_operacao == "➕ Lançar Pedido (Abrir/Adicionar Itens)": lancar_novo_pedido(emp_id)
        elif aba_operacao == "🧾 Gerenciar Contas / Fechar Mesas": gerenciar_contas_ativas(emp_id)
