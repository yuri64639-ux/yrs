import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

st.set_page_config(page_title="Frente de Caixa & Pedidos", layout="wide")

def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro ao conectar ao banco Neon: {e}")
        return None

def upgrade_db_silencioso():
    conn = init_connection()
    if conn:
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
                    forma_pagamento VARCHAR(50) DEFAULT 'Dinheiro',
                    garcao_nome VARCHAR(255) DEFAULT 'Sistema',
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            try:
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS total NUMERIC(10, 2) NOT NULL DEFAULT 0.00;")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS metodo_pagamento VARCHAR(50) NOT NULL DEFAULT 'Não Informado';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS mesa_numero VARCHAR(50) DEFAULT 'Balcão';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS comanda_codigo VARCHAR(100) DEFAULT 'Não Informado';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS forma_pagamento VARCHAR(50) DEFAULT 'Dinheiro';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS garcao_nome VARCHAR(255) DEFAULT 'Sistema';")
            except:
                pass
            conn.commit()
        conn.close()

upgrade_db_silencioso()

# Inicialização de memória de alto desempenho
if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}
if "produtos_cache" not in st.session_state:
    st.session_state.produtos_cache = []
if "ultimo_carregamento_produtos" not in st.session_state:
    st.session_state.ultimo_carregamento_produtos = 0.0

if "garcao" in st.query_params:
    st.session_state.usuario_autenticado = True
    st.session_state.garcao_atual = st.query_params["garcao"]
else:
    if "usuario_autenticado" not in st.session_state:
        st.session_state.usuario_autenticado = False
    if "garcao_atual" not in st.session_state:
        st.session_state.garcao_atual = ""

if not st.session_state.usuario_autenticado:
    st.container()
    col_l1, col_l2, col_l3 = st.columns([0.1, 0.8, 0.1])
    with col_l2:
        st.markdown("<h2 style='text-align: center;'>🔐 Login Operador</h2>", unsafe_allow_html=True)
        nome_input = st.selectbox("Usuário:", ["Garçom 01", "Garçom 02", "Garçom 03", "Gerente"])
        senha_input = st.text_input("Senha:", type="password")
        if st.button("Entrar no Sistema", type="primary", use_container_width=True):
            if (nome_input in ["Garçom 01", "Garçom 02", "Garçom 03"] and senha_input == "1234") or (nome_input == "Gerente" and senha_input == "admin"):
                st.session_state.usuario_autenticado = True
                st.session_state.garcao_atual = nome_input
                st.query_params["garcao"] = nome_input
                st.success(f"Bem-vindo, {nome_input}!")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("Credenciais Inválidas!")
    st.stop()

# CARREGAMENTO INTELIGENTE (Puxa do banco uma vez e guarda na memória local do app)
tempo_atual = time.time()
if not st.session_state.produtos_cache or (tempo_atual - st.session_state.ultimo_carregamento_produtos > 30):
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
            st.session_state.produtos_cache = cur.fetchall()
        conn.close()
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
        st.query_params.clear()
        st.rerun()

st.markdown("---")
tabs = st.tabs(["🛍️ Lançar Pedidos (Carrinho)", "🗂️ Mesas Abertas & Consumo"])
# ABA 1: OPERAÇÃO DE LANÇAMENTO (INSTANTÂNEA)
with tabs[0]:
    st.subheader("👤 Identificação do Atendimento")
    col_mesa, col_comanda = st.columns(2)
    with col_mesa:
        input_mesa = st.text_input("🪑 Número da Mesa:", placeholder="Ex: Mesa 04")
    with col_comanda:
        input_comanda = st.text_input("📋 Código da Comanda:", placeholder="Ex: 1042")

    st.markdown("---")
    st.subheader("🔍 Encontrar Itens do Cardápio")
    busca_termo = st.text_input("🔍 Buscar Produto (Lupa):", placeholder="Ex: Batata Frita")

    # Filtra os produtos direto na memória do celular, sem fazer requisição ao banco de dados
    if busca_termo:
        produtos_filtrados = [p for p in st.session_state.produtos_cache if busca_termo.lower() in p['nome'].lower()]
    else:
        produtos_filtrados = st.session_state.produtos_cache

    if not produtos_filtrados:
        st.warning("Nenhum produto encontrado no cardápio.")
    else:
        for prod in produtos_filtrados:
            col_n, col_p, col_q, col_b = st.columns([0.4, 0.2, 0.2, 0.2])
            p_base = float(prod['preco'])
            with col_n:
                st.markdown(f"**{prod['nome']}**")
            with col_p:
                st.markdown(f"R\$ {p_base:.2f}")
            with col_q:
                qtd_p = st.number_input("Quantidade", min_value=1, value=1, key=f"caixa_qtd_{prod['id']}")
            with col_b:
                if st.button("➕ Adicionar", key=f"add_cart_{prod['id']}", use_container_width=True):
                    p_id = str(prod['id'])
                    if p_id in st.session_state.carrinho:
                        st.session_state.carrinho[p_id]["qtd"] += qtd_p
                    else:
                        st.session_state.carrinho[p_id] = {"nome": prod['nome'], "preco": p_base, "qtd": qtd_p, "id_real": prod['id']}
                    st.toast(f"Adicionado: {qtd_p}x {prod['nome']}")

    st.markdown("---")
    st.subheader("📋 Conferir Seleção (Carrinho)")

    if not st.session_state.carrinho:
        st.info("Nenhum item selecionado.")
    else:
        st.markdown(f"**Destino:** {input_mesa.strip()} | **Comanda:** {input_comanda.strip()}")
        total_geral_carrinho = 0.0
        itens_remover = []
        
        for k, item in st.session_state.carrinho.items():
            c_item_nome, c_item_qtd, c_item_sub, c_item_del = st.columns([0.4, 0.2, 0.2, 0.2])
            sub_total_item = item["preco"] * item["qtd"]
            total_geral_carrinho += sub_total_item
            with c_item_nome:
                st.write(f"• **{item['nome']}** (R\$ {item['preco']:.2f})")
            with c_item_qtd:
                st.write(f"{item['qtd']} un")
            with c_item_sub:
                st.write(f"R\$ {sub_total_item:.2f}")
            with c_item_del:
                if st.button("Tirar", key=f"del_item_cart_{k}", use_container_width=True):
                    itens_remover.append(k)
                    
        for k in itens_remover:
            del st.session_state.carrinho[k]
            st.rerun()
            
        st.markdown(f"### Total: R\$ {total_geral_carrinho:.2f}")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("✅ Confirmar e Enviar Pedido", type="primary", use_container_width=True):
                if not input_mesa.strip() or input_mesa.strip().lower() in ["balcão", ""]:
                    st.error("🚨 Informe uma Mesa válida.")
                elif not input_comanda.strip() or input_comanda.strip().lower() in ["não informado", ""]:
                    st.error("🚨 O código da Comanda é obrigatório.")
                else:
                    conn = init_connection()
                    if conn:
                        try:
                            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                erro_estoque_geral = False
                                for k, item in st.session_state.carrinho.items():
                                    cur.execute("SELECT f.insumo_id, f.quantidade, i.nome, i.quantidade_atual FROM ficha_tecnica f JOIN insumos i ON f.insumo_id = i.id WHERE f.produto_id = %s;", (item['id_real'],))
                                    ficha = cur.fetchall()
                                    for f_item in ficha:
                                        consumo_necessario = (float(f_item['quantidade']) / 1000.0) * item['qtd']
                                        if float(f_item['quantidade_atual']) < consumo_necessario:
                                            st.error(f"Estoque Insuficiente de '{f_item['nome']}'!")
                                            erro_estoque_geral = True
                                
                                if not erro_estoque_geral:
                                    for k, item in st.session_state.carrinho.items():
                                        cur.execute("SELECT f.insumo_id, f.quantidade FROM ficha_tecnica f WHERE f.produto_id = %s;", (item['id_real'],))
                                        ficha = cur.fetchall()
                                        for f_item in ficha:
                                            consumo = (float(f_item['quantidade']) / 1000.0) * item['qtd']
                                            cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual - %s WHERE id = %s;", (consumo, f_item['insumo_id']))
                                        
                                        valor_venda_item = item["preco"] * item["qtd"]
                                        cur.execute("""
                                            INSERT INTO pedidos_realizados (produto_nome, quantidade_pedida, valor_total, total, forma_pagamento, metodo_pagamento, taxa_inclusa, mesa_numero, comanda_codigo, garcao_nome) 
                                            VALUES (%s, %s, %s, %s, 'Não Informado', 'Não Informado', FALSE, %s, %s, %s);
                                        """, (item['nome'], item['qtd'], valor_venda_item, valor_venda_item, input_mesa.strip(), input_comanda.strip(), st.session_state.garcao_atual))
                                    
                                    conn.commit()
                                    st.session_state.carrinho = {}
                                    st.success("Pedido enviado!")
                                    time.sleep(0.4)
                                    st.rerun()
                        except Exception as err:
                            st.error(f"Erro no banco: {err}")
                        finally:
                            conn.close()
        with col_c2:
            if st.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.carrinho = {}
                st.rerun()

# ABA 2: CONSULTA DE CONSUMO EM TEMPO REAL DAS MESAS ATIVAS (CARREGA SOB DEMANDA)
with tabs[1]:
    st.subheader("🗂️ Painel Operacional de Consumo das Mesas")
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT DISTINCT mesa_numero FROM pedidos_realizados ORDER BY mesa_numero;")
            mesas_abertas = cur.fetchall()
            
            if not mesas_abertas:
                st.info("Nenhum lançamento registrado no momento.")
            else:
                for m in mesas_abertas:
                    cur.execute("""
                        SELECT produto_nome, comanda_codigo, garcao_nome, SUM(quantidade_pedida) as total_qtd, SUM(valor_total) as total_financeiro
                        FROM pedidos_realizados WHERE mesa_numero = %s GROUP BY produto_nome, comanda_codigo, garcao_nome ORDER BY produto_nome;
                    """, (m['mesa_numero'],))
                    itens_mesa = cur.fetchall()
                    if itens_mesa:
                        subtotal_mesa = sum(float(it['total_financeiro']) for it in itens_mesa)
                        comanda_ref = itens_mesa[0]['comanda_codigo']
                        garcao_ref = itens_mesa[0]['garcao_nome']
                        with st.expander(f"🪑 {m['mesa_numero']} (Comanda: {comanda_ref}) — R\$ {subtotal_mesa:.2f}"):
                            st.markdown(f"**Último Atendente:** `{garcao_ref}`")
                            for it in itens_mesa:
                                st.markdown(f"- **{it['total_qtd']}x** {it['produto_nome']} — R\$ {float(it['total_financeiro']):.2f}")
        conn.close()
