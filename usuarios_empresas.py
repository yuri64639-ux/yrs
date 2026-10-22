import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Configuração de tela otimizada para dispositivos móveis
st.set_page_config(page_title="Acesso Corporativo", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* Oculta os elementos nativos do Streamlit */
header, [data-testid="stHeader"] { display: none !important; visibility: hidden !important; height: 0px !important; }
footer { display: none !important; visibility: hidden !important; }
#MainMenu { display: none !important; visibility: hidden !important; }
.stDeployButton { display: none !important; visibility: hidden !important; }

/* Ajustes de preenchimento para telas touch */
.block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; padding-left: 0.7rem !important; padding-right: 0.7rem !important; }
h2 { font-size: 1.4rem !important; font-weight: bold !important; text-align: center; margin-bottom: 1rem; }
div.stButton > button { margin-top: 10px !important; font-size: 1rem !important; padding: 0.6rem !important; }
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
                # 1. Cria a tabela básica se ela não existir
                cur.execute("""
                CREATE TABLE IF NOT EXISTS public.empresas (
                    id SERIAL PRIMARY KEY,
                    nome_fantasia VARCHAR(255) UNIQUE NOT NULL,
                    usuario_admin VARCHAR(100) NOT NULL,
                    senha_master VARCHAR(255) NOT NULL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                
                # 2. GARANTIA: Adiciona cada coluna caso a tabela antiga não as possua
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS nome_fantasia VARCHAR(255) UNIQUE;")
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS usuario_admin VARCHAR(100);")
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS senha_master VARCHAR(255);")
                cur.execute("ALTER TABLE public.empresas ADD COLUMN IF NOT EXISTS data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                
                conn.commit()
        except Exception as e:
            st.error(f"Erro ao sincronizar colunas da tabela: {e}")
        finally:
            conn.close()

criar_estrutura_multi_tenant()
# Fluxo de autenticação caso nenhuma empresa esteja conectada neste terminal
if not st.session_state.empresa_logada:
    opcao_acesso = st.radio("Selecione a ação comercial:", ["🔑 Fazer Login", "🏢 Cadastrar Minha Empresa"], horizontal=True)
    st.markdown("---")
    
    # --- FLUXO 1: CRIAR NOVA CONTA DE EMPRESA ---
    if opcao_acesso == "🏢 Cadastrar Minha Empresa":
        st.markdown("<h2>Cadastrar Empresa no Ecossistema</h2>", unsafe_allow_html=True)
        with st.form("form_registro_empresa", clear_on_submit=True):
            novo_nome_empresa = st.text_input("Nome do Estabelecimento / Razão Social:").strip()
            novo_usuario_master = st.text_input("Criar Usuário Administrador (Ex: admin):").strip()
            nova_senha_master = st.text_input("Definir Senha Master de Gerência:", type="password").strip()
            
            if st.form_submit_button("Criar Minha Conta Comercial", type="primary"):
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
                            st.success(f"🎉 Empresa '{novo_nome_empresa}' registrada! Alterne para a aba de Login para acessar.")
                        except psycopg2.errors.UniqueViolation:
                            st.error("❌ Erro: Este nome de empresa já está cadastrado no sistema.")
                        finally:
                            conn.close()
                            
    # --- FLUXO 2: LOGIN INDIVIDUAL E PROTEGIDO POR EMPRESA ---
    else:
        st.markdown("<h2>Acesso Restrito da Empresa</h2>", unsafe_allow_html=True)
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
            st.info("Nenhuma empresa localizada na nuvem Neon.")
        else:
            with st.form("form_login_empresa"):
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", options=list(mapa_empresas.keys()))
                usuario_login = st.text_input("Usuário Administrador:")
                senha_login = st.text_input("Senha Master:", type="password")
                
                if st.form_submit_button("Liberar Terminal", type="primary"):
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
                        st.success("Autenticação Efetuada!")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error("❌ Credenciais incorretas para a empresa selecionada!")
    st.stop()
# --- AMBIENTE SEGURO DA EMPRESA LOGADA ---
st.markdown(f"### 🏢 {st.session_state.empresa_nome_ativo.upper()} — Painel de Controle")

# Botão de Logoff seguro para limpar o terminal mobile
if st.button("🔒 Desconectar Empresa (Sair)", type="secondary", use_container_width=True):
    st.session_state.empresa_logada = False
    st.session_state.empresa_id_ativo = None
    st.session_state.empresa_nome_ativo = ""
    st.rerun()

st.markdown("---")
st.info(f"🛡️ Todas as consultas realizadas neste ecossistema estão filtradas sob o ID de proteção: `{st.session_state.empresa_id_ativo}`.")

# Exemplo prático de como você vai renderizar dados específicos desta empresa nas sub-abas:
opcao_visualizacao = st.selectbox("Consultar Informações Isoladas:", ["Dados Cadastrais", "Estatísticas da Empresa"])

if opcao_visualizacao == "Dados Cadastrais":
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # FILTRO DE ISOLAMENTO CRÍTICO: "WHERE id = %s" garante que nenhuma outra empresa intercepte os dados
            cur.execute("SELECT id, nome_fantasia, usuario_admin, data_cadastro FROM public.empresas WHERE id = %s;", (st.session_state.empresa_id_ativo,))
            dados_empresa = cur.fetchone()
            
        if dados_empresa:
            st.write(f"• **ID Corporativo Interno:** {dados_empresa['id']}")
            st.write(f"• **Nome do Estabelecimento:** {dados_empresa['nome_fantasia']}")
            st.write(f"• **Operador Master Cadastrado:** {dados_empresa['usuario_admin']}")
            st.write(f"• **Data de Ativação do Sistema:** {dados_empresa['data_cadastro']}")
        conn.close()
        
elif opcao_visualizacao == "Estatísticas da Empresa":
    st.success("Esta área carregará os relatórios e faturamentos filtrados unicamente pela coluna empresa_id.")
