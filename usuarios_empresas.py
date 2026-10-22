import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

st.set_page_config(page_title="Portal Corporativo", layout="wide", initial_sidebar_state="expanded")

# --- CONEXÃO NEON ---
def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão com o banco Neon: {e}")
        return None

# --- CRIAÇÃO E ATUALIZAÇÃO DE TABELAS ---
def criar_estrutura_multi_tenant():
    conn = init_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS public.empresas (
                    id SERIAL PRIMARY KEY,
                    nome_fantasia VARCHAR(255) UNIQUE,
                    usuario_admin VARCHAR(100),
                    senha_master VARCHAR(255),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS public.cadastros_garcons (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    codigo_operacional VARCHAR(100) NOT NULL,
                    empresa_id INT
                );
                """)
                # Força a existência da coluna empresa_id em todas as tabelas críticas do ecossistema
                cur.execute("ALTER TABLE IF EXISTS public.cadastros_garcons ADD COLUMN IF NOT EXISTS empresa_id INT;")
                cur.execute("ALTER TABLE IF EXISTS public.pedidos_realizados ADD COLUMN IF NOT EXISTS empresa_id INT;")
                cur.execute("ALTER TABLE IF EXISTS public.insumos ADD COLUMN IF NOT EXISTS empresa_id INT;")
                cur.execute("ALTER TABLE IF EXISTS public.produtos ADD COLUMN IF NOT EXISTS empresa_id INT;")
                conn.commit()
        except:
            pass
        finally:
            conn.close()

criar_estrutura_multi_tenant()

if "empresa_logada" not in st.session_state: st.session_state.empresa_logada = False
if "empresa_id_ativo" not in st.session_state: st.session_state.empresa_id_ativo = None
if "empresa_nome_ativo" not in st.session_state: st.session_state.empresa_nome_ativo = ""

# --- TELA DE LOGIN / CADASTRO DA EMPRESA ---
if not st.session_state.empresa_logada:
    st.markdown("<h1>🏢 Sistema de Gestão Empresarial</h1>", unsafe_allow_html=True)
    col_login, col_cadastro = st.columns(2, gap="large")
    
    with col_login:
        st.subheader("🔑 Login da Empresa")
        conn = init_connection()
        lista_empresas = []
        if conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT id, nome_fantasia FROM public.empresas ORDER BY nome_fantasia;")
                    lista_empresas = cur.fetchall()
                except: pass
            conn.close()
        
        mapa_empresas = {row[1]: row[0] for row in lista_empresas}
        if not mapa_empresas:
            st.info("Nenhuma empresa localizada no banco.")
        else:
            with st.form("form_login_empresa"):
                emp_sel = st.selectbox("Selecione sua Empresa:", options=list(mapa_empresas.keys()))
                user_login = st.text_input("Usuário Admin:")
                senha_login = st.text_input("Senha Master:", type="password")
                if st.form_submit_button("Acessar Painel", type="primary", use_container_width=True):
                    id_alvo = mapa_empresas[emp_sel]
                    conn = init_connection()
                    if conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cur:
                            cur.execute("SELECT id, nome_fantasia FROM public.empresas WHERE id = %s AND LOWER(usuario_admin) = LOWER(%s) AND senha_master = %s;", (id_alvo, user_login.strip(), senha_login.strip()))
                            dados = cur.fetchone()
                        conn.close()
                        if dados:
                            st.session_state.empresa_logada = True
                            st.session_state.empresa_id_ativo = int(dados["id"])
                            st.session_state.empresa_nome_ativo = str(dados["nome_fantasia"])
                            st.rerun()
                        else:
                            st.error("Credenciais incorretas!")
                            
    with col_cadastro:
        st.subheader("🚀 Cadastrar Nova Empresa")
        with st.form("form_cadastro_emp"):
            nome_emp = st.text_input("Nome da Empresa / Razão Social:")
            user_emp = st.text_input("Usuário Administrador:")
            senha_emp = st.text_input("Senha Master de Gerência:", type="password")
            if st.form_submit_button("Registrar Estabelecimento", use_container_width=True):
                if nome_emp and user_emp and senha_emp:
                    conn = init_connection()
                    if conn:
                        try:
                            with conn.cursor() as cur:
                                cur.execute("INSERT INTO public.empresas (nome_fantasia, usuario_admin, senha_master) VALUES (%s, %s, %s);", (nome_emp.strip(), user_emp.strip(), senha_emp.strip()))
                                conn.commit()
                            st.success("Empresa cadastrada! Faça o login ao lado.")
                        except: st.error("Nome de empresa já existente.")
                        finally: conn.close()
                else: st.error("Preencha todos os campos!")
    st.stop()

# --- INTERFACE PROTEGIDA DA EMPRESA (PÓS-LOGIN) ---
st.markdown(f"<h2>🏢 Painel de Controle — {st.session_state.empresa_nome_ativo.upper()}</h2>", unsafe_allow_html=True)
if st.button("🔒 Encerrar Sessão", type="secondary"):
    st.session_state.empresa_logada = False
    st.rerun()

tab_garcons, tab_lancador, tab_estoque = st.tabs(["👤 Cadastrar Garçom", "🛍️ Lançar Pedidos", "📦 Estoque"])

with tab_garcons:
    st.subheader("Gerenciar Equipe do Estabelecimento")
    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        conn = init_connection()
        if conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, nome, codigo_operacional FROM public.cadastros_garcons WHERE empresa_id = %s ORDER BY nome;", (st.session_state.empresa_id_ativo,))
                st.dataframe(cur.fetchall(), use_container_width=True, hide_index=True)
            conn.close()
    with c2:
        with st.form("add_garcom", clear_on_submit=True):
            n_garcom = st.text_input("Nome do Garçom:")
            c_garcom = st.text_input("Código / Código Operacional (Senha celular):")
            if st.form_submit_button("Cadastrar Funcionário", type="primary", use_container_width=True):
                if n_garcom and c_garcom:
                    conn = init_connection()
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO public.cadastros_garcons (nome, codigo_operacional, empresa_id) VALUES (%s, %s, %s);", (n_garcom.strip(), c_garcom.strip(), st.session_state.empresa_id_ativo))
                            conn.commit()
                        conn.close()
                        st.success(f"{n_garcom} cadastrado!")
                        time.sleep(0.5)
                        st.rerun()

with tab_lancador:
    st.subheader("Lançador Balcão / Caixa Central")
    st.info("Pedidos lançados aqui no PC entrarão automaticamente associados a esta empresa.")

with tab_estoque:
    st.subheader("Controle de Estoque da Empresa")
    # Exemplo simples de visualização filtrada
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT nome, quantidade_atual FROM public.insumos WHERE empresa_id = %s ORDER BY nome;", (st.session_state.empresa_id_ativo,))
            st.dataframe(cur.fetchall(), use_container_width=True, hide_index=True)
        conn.close()
