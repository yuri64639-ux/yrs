import streamlit as st
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import time

# Configuração de ambiente para dispositivos móveis e maquininhas
st.set_page_config(page_title="Frente de Caixa & Pedidos", layout="wide")

# Ocultar Share, Estrela, Lápis, Menu de 3 pontos e rodapé nativo do Streamlit
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    button[title="View source code"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Inicializa o Pool de Conexões seguro para threads (Suporta múltiplos acessos sem travar)
@st.cache_resource
def get_connection_pool():
    try:
        # Configurado para manter entre 1 e 20 conexões reutilizáveis simultâneas
        return ThreadedConnectionPool(1, 20, st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro ao inicializar pool de conexões: {e}")
        return None

def init_connection():
    pool = get_connection_pool()
    if pool:
        try:
            return pool.getconn()
        except Exception as e:
            st.error(f"Erro ao obter conexão do pool: {e}")
    return None

def release_connection(conn):
    pool = get_connection_pool()
    if pool and conn:
        try:
            pool.putconn(conn)
        except:
            pass

# MANUTENÇÃO OCULTA: Agora com cache para rodar uma única vez no servidor e não travar cliques
@st.cache_resource
def upgrade_db_silencioso():
    pool = get_connection_pool()
    if pool:
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS pedidos_realizados (
                        id SERIAL PRIMARY KEY,
                        produto_nome VARCHAR(255) NOT NULL,
                        quantidade_pedida INT NOT NULL,
                        valor_total NUMERIC(10,2) NOT NULL,
                        taxa_inclusa BOOLEAN NOT NULL DEFAULT FALSE,
                        mesa_numero VARCHAR(50) DEFAULT 'Balcão',
                        comanda_codigo VARCHAR(100) DEFAULT 'Não Informado',
                        forma_pagamento VARCHAR(50) DEFAULT 'Mesa Aberta',
                        garcao_nome VARCHAR(255) DEFAULT 'Sistema',
                        status_conta VARCHAR(50) DEFAULT 'Aberta',
                        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                try:
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS total NUMERIC(10, 2) NOT NULL DEFAULT 0.00;")
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS metodo_pagamento VARCHAR(50) NOT NULL DEFAULT 'Não Informado';")
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS status_conta VARCHAR(50) DEFAULT 'Aberta';")
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS mesa_numero VARCHAR(50) DEFAULT 'Balcão';")
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS comanda_codigo VARCHAR(100) DEFAULT 'Não Informado';")
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS forma_pagamento VARCHAR(50) DEFAULT 'Dinheiro';")
                    cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS garcao_nome VARCHAR(255) DEFAULT 'Sistema';")
                except:
                    pass
                conn.commit()
        finally:
            pool.putconn(conn)

upgrade_db_silencioso()

# Inicialização de memória de alto desempenho (Evita lentidão ao alternar abas)
if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}
if "produtos_cache" not in st.session_state:
    st.session_state.produtos_cache = []
if "ultimo_carregamento_produtos" not in st.session_state:
    st.session_state.ultimo_carregamento_produtos = 0.0
if "gerente_autenticado" not in st.session_state:
    st.session_state.gerente_autenticado = False

# Sistema Anti-F5: Mantém o operador conectado caso a página recarregue
if "garcao" in st.query_params:
    st.session_state.usuario_autenticado = True
    st.session_state.garcao_atual = st.query_params["garcao"]
else:
    if "usuario_autenticado" not in st.session_state:
        st.session_state.usuario_autenticado = False
    if "garcao_atual" not in st.session_state:
        st.session_state.garcao_atual = ""

# --- LOGIN DINÂMICO VIA BANCO DE DADOS NEON ---
if not st.session_state.usuario_autenticado:
    lista_garcons_db = ["Gerente"]
    conn = init_connection()
    if conn:
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT nome FROM cadastros_garcons ORDER BY nome;")
                lista_garcons_db += [row[0] for row in cur.fetchall()]
            except:
                pass
        release_connection(conn)

    st.container()
    col_l1, col_l2, col_l3 = st.columns([0.1, 0.8, 0.1])
    with col_l2:
        st.markdown("<h2 style='text-align: center;'>🔐 Login Operador</h2>", unsafe_allow_html=True)
        nome_input = st.selectbox("Selecione seu Nome:", options=lista_garcons_db)
        senha_input = st.text_input("Sua Senha / Código Operacional:", type="password")
        
        if st.button("Entrar no Sistema", type="primary", use_container_width=True):
            if nome_input == "Gerente" and senha_input == "admin":
                st.session_state.usuario_autenticado = True
                st.session_state.garcao_atual = nome_input
                st.query_params["garcao"] = nome_input
                st.success("Acesso Gerencial Autorizado!")
                time.sleep(0.3)
                st.rerun()
            else:
                conn = init_connection()
                autenticado_db = False
                if conn:
                    with conn.cursor() as cur:
                        try:
                            cur.execute("SELECT nome FROM cadastros_garcons WHERE nome = %s AND codigo_operacional = %s;", (nome_input, senha_input.strip()))
                            if cur.fetchone():
                                autenticado_db = True
                        except:
                            pass
                    release_connection(conn)
                
                if autenticado_db:
                    st.session_state.usuario_autenticado = True
                    st.session_state.garcao_atual = nome_input
                    st.query_params["garcao"] = nome_input
                    st.success(f"Bem-vindo, {nome_input}!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("Senha Incorreta para o garçom selecionado!")
    st.stop()

tempo_atual = time.time()
if not st.session_state.produtos_cache or (tempo_atual - st.session_state.ultimo_carregamento_produtos > 30):
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
            st.session_state.produtos_cache = cur.fetchall()
        release_connection(conn)
        st.session_state.ultimo_carregamento_produtos = tempo_atual

col_titulo, col_logout = st.columns([0.7, 0.3])
with col_titulo:
    st.title("🛒 Caixa & Salão")
with col_logout:
    st.markdown(f"👤 **{st.session_state.garcao_atual}**")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_autenticado = False
        st.session_state.garcao_atual = ""
        st.session_state.carrinho = {}
        st.session_state.gerente_autenticado = False
        st.query_params.clear()
        st.rerun()

st.markdown("---")
tabs = st.tabs(["🛍️ Lançar Pedidos", "🗂️ Mesas Abertas", "🔐 Gerência"])

# ABA 1: OPERAÇÃO DE LANÇAMENTO (ÍNDICE 0)
with tabs[0]:
    st.subheader("👤 Identificação do Atendimento")
    col_mesa, col_comanda = st.columns(2)
    with col_mesa:
        mesa_final = st.text_input("🪑 Número da Mesa:", placeholder="Ex: Mesa 04", value="Balcão")
    with col_comanda:
        comanda_final = st.text_input("📋 Código da Comanda:", placeholder="Ex: 1042", value="Não Informado")

    st.markdown("---")
    st.subheader("🔍 Encontrar Itens")
    # Lupa de busca rápida por produto reativada
    busca_termo = st.text_input("🔍 Buscar Produto (Lupa):", placeholder="Ex: Batata Frita")

    # Filtro em memória de alto desempenho usando o cache
    produtos_filtrados = [p for p in st.session_state.produtos_cache if busca_termo.lower() in p['nome'].lower()] if busca_termo else st.session_state.produtos_cache

    if busca_termo:
        if not produtos_filtrados:
            st.warning("Nenhum produto encontrado com este nome.")
        else:
            for prod in produtos_filtrados:
                col_n, col_p, col_q, col_b = st.columns([0.4, 0.2, 0.2, 0.2])
                p_base = float(prod['preco'])
                with col_n:
                    st.markdown(f"**{prod['nome']}**")
                with col_p:
                    st.markdown(f"R$ {p_base:.2f}")
                with col_q:
                    qtd_p = st.number_input("Quantidade", min_value=1, value=1, key=f"caixa_qtd_{prod['id']}")
                with col_b:
                    if st.button("➕ Selecionar", key=f"add_cart_{prod['id']}", use_container_width=True):
                        pid = prod['id']
                        if pid in st.session_state.carrinho:
                            st.session_state.carrinho[pid]['qtd'] += qtd_p
                        else:
                            st.session_state.carrinho[pid] = {
                                "nome": prod['nome'],
                                "preco": p_base,
                                "qtd": qtd_p
                            }
                        st.toast(f"➕ {prod['nome']} adicionado ao carrinho!")

    if st.session_state.carrinho:
        st.markdown("---")
        st.subheader("🛒 Itens Selecionados no Atendimento")
        total_geral = 0.0
        
        for k, v in list(st.session_state.carrinho.items()):
            c_item, c_sub, c_rem = st.columns([0.5, 0.3, 0.2])
            sub_item = v['preco'] * v['qtd']
            total_geral += sub_item
            with c_item:
                st.write(f"**{v['nome']}** (x{v['qtd']})")
            with c_sub:
                st.write(f"R$ {sub_item:.2f}")
            with c_rem:
                if st.button("🗑️", key=f"rem_cart_{k}"):
                    del st.session_state.carrinho[k]
                    st.rerun()
                    
        st.markdown(f"### **Total do Pedido: R$ {total_geral:.2f}**")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🚀 Confirmar e Enviar para o Banco", type="primary", use_container_width=True):
                conn = init_connection()
                if conn:
                    try:
                        with conn:
                            with conn.cursor() as cur:
                                for k, v in st.session_state.carrinho.items():
                                    sub_val = v['preco'] * v['qtd']
                                    cur.execute("""
                                        INSERT INTO pedidos_realizados 
                                        (produto_nome, quantidade_pedida, valor_total, mesa_numero, comanda_codigo, garcao_nome, status_conta) 
                                        VALUES (%s, %s, %s, %s, %s, %s, 'Aberta');
                                    """, (v['nome'], v['qtd'], sub_val, mesa_final.strip(), comanda_final.strip(), st.session_state.garcao_atual))
                        st.success("Pedido gravado com sucesso no banco Neon!")
                        st.session_state.carrinho = {}
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                    finally:
                        release_connection(conn)
        with col_c2:
            if st.button("❌ Limpar Tudo", use_container_width=True):
                st.session_state.carrinho = {}
                st.rerun()
    else:
        if not busca_termo:
            st.info("Utilize a lupa de pesquisa acima para encontrar e adicionar produtos ao carrinho.")

# ABA 2: VISUALIZAÇÃO DE MESAS EM ABERTO (ÍNDICE 1)
with tabs[1]:
    st.subheader("📋 Painel de Consumo")
    conn = init_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT mesa_numero, comanda_codigo, produto_nome, quantidade_pedida, valor_total 
                    FROM pedidos_realizados WHERE status_conta = 'Aberta' 
                    ORDER BY mesa_numero, comanda_codigo;
                """)
                pedidos_abertos = cur.fetchall()
        finally:
            release_connection(conn)
        
        if not pedidos_abertos:
            st.info("Nenhuma mesa ou comanda aberta no momento.")
        else:
            grupos = {}
            for p in pedidos_abertos:
                chave = (p['mesa_numero'], p['comanda_codigo'])
                if chave not in grupos: grupos[chave] = []
                grupos[chave].append(p)
                
            for (m, c), itens in grupos.items():
                tot_m = sum(float(i['valor_total']) for i in itens)
                with st.expander(f"🪑 {m} | Comanda: {c} — Total: R$ {tot_m:.2f}"):
                    for i in itens:
                        st.write(f"• {i['quantidade_pedida']}x {i['produto_nome']} — R$ {float(i['valor_total']):.2f}")

# ABA 3: CONTEXTO GERENCIAL RESIDUAL (ÍNDICE 2)
with tabs[2]:
    st.subheader("🔐 Área de Segurança e Relatórios")
    st.info("Utilize credenciais administrativas para gerar auditoria de estoque ou faturamento consolidado.")
