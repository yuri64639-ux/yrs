import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Configuração da página do Streamlit para o Caixa/Pedidos
st.set_page_config(page_title="Frente de Caixa & Pedidos", layout="wide")

# Conexão segura e direta com o Banco de Dados Neon na nuvem
def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro ao conectar ao banco Neon: {e}")
        return None

# Atualização estrutural para incluir Mesa e Comanda no banco
def upgrade_db_pedidos():
    conn = init_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pedidos_realizados (
                    id SERIAL PRIMARY KEY,
                    produto_nome VARCHAR(255) NOT NULL,
                    quantidade_pedida INT NOT NULL,
                    valor_total NUMERIC(10,2) NOT NULL,
                    taxa_inclusa BOOLEAN NOT NULL DEFAULT TRUE,
                    mesa_numero VARCHAR(50) DEFAULT 'Balcão',
                    comanda_codigo VARCHAR(100) DEFAULT 'Não Informado',
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            try:
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS mesa_numero VARCHAR(50) DEFAULT 'Balcão';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS comanda_codigo VARCHAR(100) DEFAULT 'Não Informado';")
            except:
                pass
            conn.commit()
        conn.close()

upgrade_db_pedidos()

# Monitor em tempo real fixado no topo (atualiza a cada 1 segundo)
@st.fragment(run_every="1s")
def render_estoque_tempo_real():
    st.subheader("🔄 Monitor de Estoque Bruto (Atualiza a cada 1s)")
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT nome, quantidade_atual FROM insumos ORDER BY nome;")
            estoque = cur.fetchall()
        conn.close()
        if estoque:
            cols = st.columns(len(estoque) if len(estoque) < 5 else 5)
            for idx, item in enumerate(estoque):
                with cols[idx % 5]:
                    st.metric(label=item['nome'], value=f"{float(item['quantidade_atual']):.3f}")
        else:
            st.info("Nenhum insumo cadastrado no estoque central.")

st.title("🛒 Frente de Caixa: Lançamento de Vendas")
st.caption("Identificação de clientes por Mesa/Comanda integrada com baixa por Ficha Técnica")

render_estoque_tempo_real()
st.markdown("---")

st.subheader("👤 Identificação do Cliente & Filtro")
col_mesa, col_comanda = st.columns(2)
with col_mesa:
    input_mesa = st.text_input("🪑 Número da Mesa:", value="Balcão", placeholder="Ex: Mesa 04")
with col_comanda:
    input_comanda = st.text_input("📋 Código da Comanda:", value="Não Informado", placeholder="Ex: 1042")

st.markdown("---")
st.subheader("🔍 Localizar Produto")
busca_termo = st.text_input("🔍 Buscar Produto no Cardápio (Lupa):", placeholder="Ex: Batata Frita", key="busca_lupa_caixa")

conn = init_connection()
produtos_filtrados = []
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if busca_termo:
            cur.execute("SELECT id, nome, preco FROM produtos WHERE nome ILIKE %s ORDER BY nome;", (f"%{busca_termo}%",))
        else:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
        produtos_filtrados = cur.fetchall()
    conn.close()

if not produtos_filtrados:
    st.warning("Nenhum produto encontrado no cardápio.")
else:
    for prod in produtos_filtrados:
        col_n, col_p, col_q, col_t, col_b = st.columns([0.3, 0.15, 0.15, 0.2, 0.2])
        p_base = float(prod['preco'])
        
        with col_n:
            st.markdown(f"**{prod['nome']}**")
        with col_p:
            st.markdown(f"R$ {p_base:.2f}")
        with col_q:
            qtd_p = st.number_input("Qtd", min_value=1, value=1, key=f"caixa_qtd_{prod['id']}")
        with col_t:
            p_taxa = st.checkbox("Pagar 10% serviço", value=True, key=f"caixa_taxa_{prod['id']}")
            sub = p_base * qtd_p
            v_final = sub * 1.10 if p_taxa else sub
            st.caption(f"Total: R$ {v_final:.2f}")
        with col_b:
            if st.button("🚀 Lançar", key=f"caixa_btn_{prod['id']}", type="primary"):
                st.session_state[f"caixa_conf_{prod['id']}"] = True
        
        if st.session_state.get(f"caixa_conf_{prod['id']}", False):
            with st.status(f"⚠️ Confirmar lançamento para {input_mesa} / Comanda: {input_comanda}?", expanded=True):
                st.write(f"• **Produto:** {qtd_p}x {prod['nome']}")
                st.write(f"• **Valor total:** R$ {v_final:.2f} " + ("(Com 10%)" if p_taxa else "(Sem taxa)"))
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Confirmar", key=f"caixa_ok_{prod['id']}", type="primary"):
                        conn = init_connection()
                        if conn:
                            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                cur.execute("SELECT f.insumo_id, f.quantidade FROM ficha_tecnica f WHERE f.produto_id = %s;", (prod['id'],))
                                ficha = cur.fetchall()
                                
                                for item in ficha:
                                    consumo = (float(item['quantidade']) / 1000.0) * qtd_p
                                    cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual - %s WHERE id = %s;", (consumo, item['insumo_id']))
                                    
                                cur.execute("""
                                    INSERT INTO pedidos_realizados (produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo) 
                                    VALUES (%s, %s, %s, %s, %s, %s);
                                """, (prod['nome'], qtd_p, v_final, p_taxa, input_mesa.strip(), input_comanda.strip()))
                                conn.commit()
                            conn.close()
                            st.session_state[f"caixa_conf_{prod['id']}"] = False
                            st.success("Pedido finalizado com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                with c_btn2:
                    if st.button("❌ Cancelar", key=f"caixa_cancel_{prod['id']}"):
                        st.session_state[f"caixa_conf_{prod['id']}"] = False
                        st.rerun()

st.markdown("---")
st.subheader("📋 Histórico de Vendas Recentes")
filtro = st.radio("Filtrar histórico por status da taxa:", ["Todos", "Com 10%", "Sem Taxa"], horizontal=True, key="filtro_vendas_radio")

conn = init_connection()
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query_base = "SELECT produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo, data_hora FROM pedidos_realizados "
        if filtro == "Com 10%":
            cur.execute(query_base + "WHERE taxa_inclusa = TRUE ORDER BY data_hora DESC LIMIT 15;")
        elif filtro == "Sem Taxa":
            cur.execute(query_base + "WHERE taxa_inclusa = FALSE ORDER BY data_hora DESC LIMIT 15;")
        else:
            cur.execute(query_base + "ORDER BY data_hora DESC LIMIT 15;")
        historico = cur.fetchall()
    conn.close()
    
    if historico:
        for p in historico:
            txt_t = "🟢 (Com 10%)" if p['taxa_inclusa'] else "⚪ (Sem taxa)"
            st.text(f"⏱️ {p['data_hora'].strftime('%H:%M')} | {p['mesa_numero']} (Comanda: {p['comanda_codigo']}) -> {p['quantidade_pedida']}x {p['produto_nome']} | R$ {float(p['valor_total']):.2f} {txt_t}")
    else:
        st.info("Nenhum pedido lançado recentemente com este filtro.")
