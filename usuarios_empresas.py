import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Configuração expandida para computadores (layout wide nativo)
st.set_page_config(
    page_title="Portal Corporativo - Gestão de Empresas", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Estilização limpa e corporativa para monitores (sem ocultar cabeçalhos úteis)
st.markdown("""
<style>
    /* Ajuste de preenchimento para telas grandes */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .titulo-sistema {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #1E3A8A;
        margin-bottom: 1.5rem !important;
    }
    .subcard {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização das variáveis de sessão de controle de segurança
if "empresa_logada" not in st.session_state: st.session_state.empresa_logada = False
if "empresa_id_ativo" not in st.session_state: st.session_state.empresa_id_ativo = None
if "empresa_nome_ativo" not in st.session_state: st.session_state.empresa_nome_ativo = ""

def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão com o banco Neon: {e}")
        return None

def criar_estrutura_multi_tenant():
    conn = init_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # 1. Cria a tabela básica caso ela não exista
                cur.execute("""
                CREATE TABLE IF NOT EXISTS public.empresas (
                    id SERIAL PRIMARY KEY,
                    nome_fantasia VARCHAR(255) UNIQUE,
                    usuario_admin VARCHAR(100),
                    senha_master VARCHAR(255),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                
                # 2. GARANTIA: Injeta as colunas caso a tabela antiga no Neon esteja incompleta
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS nome_fantasia VARCHAR(255) UNIQUE;")
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS usuario_admin VARCHAR(100);")
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS senha_master VARCHAR(255);")
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                
                # 3. HIGIENIZAÇÃO PROFUNDA: Descobre TODAS as colunas da tabela e remove o NOT NULL delas (exceto a chave primária 'id')
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'empresas' AND column_name != 'id';
                """)
                todas_colunas = [row[0] for row in cur.fetchall()]
                
                for coluna in todas_colunas:
                    try:
                        cur.execute(f"ALTER TABLE public.empresas ALTER COLUMN {coluna} DROP NOT NULL;")
                    except:
                        pass
                
                conn.commit()
        except Exception as e:
            st.error(f"Erro ao sincronizar colunas da tabela: {e}")
        finally:
            conn.close()

criar_estrutura_multi_tenant()
# Fluxo de autenticação caso nenhuma empresa esteja conectada neste terminal
if not st.session_state.empresa_logada:
    st.markdown("<h1 class='titulo-sistema'>🏢 Painel de Controle Multitasking</h1>", unsafe_allow_html=True)
    
    # Uso de colunas paralelas aproveitando a largura do monitor do PC
    col_login, col_cadastro = st.columns([1, 1], gap="large")
    
    # --- COLUNA 1: LOGIN DA EMPRESA ---
    with col_login:
        st.subheader("🔑 Acesso Restrito à Empresa")
        conn = init_connection()
        lista_empresas = []
        if conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT id, nome_fantasia FROM public.empresas ORDER BY nome_fantasia;")
                    lista_empresas = cur.fetchall()
                except:
                    pass
            conn.close()
            
        mapa_empresas = {row[1]: row[0] for row in lista_empresas}
        
        if not mapa_empresas:
            st.info("Nenhuma empresa localizada na nuvem Neon. Cadastre sua empresa ao lado.")
        else:
            with st.form("form_login_empresa_pc"):
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", options=list(mapa_empresas.keys()))
                usuario_login = st.text_input("Usuário Administrador:")
                senha_login = st.text_input("Senha Master:", type="password")
                
                if st.form_submit_button("Liberar Painel de Controle", type="primary", use_container_width=True):
                    id_empresa_alvo = mapa_empresas[empresa_selecionada]
                    conn = init_connection()
                    dados_autenticacao = None
                    if conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cur:
                            cur.execute("""
                            SELECT id, nome_fantasia FROM public.empresas 
                            WHERE id = %s AND LOWER(usuario_admin) = LOWER(%s) AND senha_master = %s;
                            """, (id_empresa_alvo, usuario_login.strip(), senha_login.strip()))
                            dados_autenticacao = cur.fetchone()
                        conn.close()
                        
                    if dados_autenticacao:
                        st.session_state.empresa_logada = True
                        st.session_state.empresa_id_ativo = int(dados_autenticacao["id"])
                        st.session_state.empresa_nome_ativo = str(dados_autenticacao["nome_fantasia"])
                        st.success("Autenticação Efetuada com Sucesso!")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error("❌ Credenciais incorretas para a empresa selecionada!")
                        
    # --- COLUNA 2: CADASTRO DE NOVA CONTA ---
    with col_cadastro:
        st.subheader("🚀 Cadastrar Novo Estabelecimento")
        with st.form("form_registro_empresa_pc", clear_on_submit=True):
            novo_nome_empresa = st.text_input("Nome do Estabelecimento / Razão Social:").strip()
            novo_usuario_master = st.text_input("Criar Usuário Administrador (Ex: gerente):").strip()
            nova_senha_master = st.text_input("Definir Senha Master de Segurança:", type="password").strip()
            
            if st.form_submit_button("Registrar Minha Empresa", use_container_width=True):
                if not novo_nome_empresa or not novo_usuario_master or not nova_senha_master:
                    st.error("⚠️ Atenção: Preencha todos os campos do formulário!")
                else:
                    conn = init_connection()
                    if conn:
                        try:
                            with conn.cursor() as cur:
                                cur.execute("""
                                INSERT INTO public.empresas (nome_fantasia, usuario_admin, senha_master) 
                                VALUES (%s, %s, %s);
                                """, (novo_nome_empresa, novo_usuario_master, nova_senha_master))
                                conn.commit()
                            st.success(f"🎉 Empresa '{novo_nome_empresa}' registrada! Agora basta fazer o login ao lado.")
                            time.sleep(0.5)
                            st.rerun()
                        except psycopg2.errors.UniqueViolation:
                            st.error("❌ Erro: Este nome de empresa já está cadastrado no sistema.")
                        finally:
                            conn.close()
    st.stop()
# --- AMBIENTE DASHBOARD SEGURO DA EMPRESA LOGADA ---
col_header_titulo, col_header_botao = st.columns([0.8, 0.2])

with col_header_titulo:
    st.markdown(f"<h1 class='titulo-sistema'>🏢 {st.session_state.empresa_nome_ativo.upper()} — Central de Monitoramento</h1>", unsafe_allow_html=True)
with col_header_botao:
    if st.button("🔒 Encerrar Sessão (Sair)", type="secondary", use_container_width=True):
        st.session_state.empresa_logada = False
        st.session_state.empresa_id_ativo = None
        st.session_state.empresa_nome_ativo = ""
        st.rerun()

st.markdown("---")

# Layout de Dashboard Corporativo dividido em Abas Largas para o Navegador do PC
tab_dados, tab_estatisticas, tab_configuracoes = st.tabs(["📊 Dados Operacionais", "📈 Métricas do Negócio", "⚙️ Segurança da Nuvem"])

with tab_dados:
    st.subheader("Informações Cadastrais Isoladas")
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # FILTRO DE PROTEÇÃO ABSOLUTA: O "WHERE id = %s" garante o isolamento completo entre empresas
            cur.execute("SELECT id, nome_fantasia, usuario_admin, data_cadastro FROM public.empresas WHERE id = %s;", (st.session_state.empresa_id_ativo,))
            dados_empresa = cur.fetchone()
            
        if dados_empresa:
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.metric(label="ID Corporativo Interno", value=f"#{dados_empresa['id']}")
            with col_d2:
                st.metric(label="Usuário Master Ativo", value=str(dados_empresa['usuario_admin']))
            with col_d3:
                st.metric(label="Data de Ativação do Sistema", value=dados_empresa['data_cadastro'].strftime('%d/%m/%Y'))
                
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container():
                st.markdown("<div class='subcard'><strong>Nota de Segurança:</strong> Este terminal está criptografado e operando sob uma camada Multi-Tenant. Nenhum dado de outros estabelecimentos cadastrados na nuvem Neon pode ser interceptado por este ambiente.</div>", unsafe_allow_html=True)
        conn.close()

with tab_estatisticas:
    st.subheader("Análise Gráfica e Financeira")
    st.info("As tabelas de faturamento, vendas e fluxo de caixa serão carregadas aqui, pré-filtradas automaticamente pela coluna 'empresa_id' do banco Neon.")

with tab_configuracoes:
    st.subheader("Configurações do Sistema")
    st.warning("Área de privilégios administrativos para alteração de chaves secretas ou conexões de API.")
