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

# Monitor em tempo real fixado no topo (atualiza o estoque de insumos a cada 1 segundo)
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
st.caption("Aplicativo independente conectado ao Banco de Dados Neon central")

# Renderiza o monitor de estoque
render_estoque_tempo_real()
st.markdown("---")

st.subheader("🔍 Localizar Produto")
busca_termo = st.text_input("🔍 Buscar Produto no Cardápio (Lupa):", placeholder="Ex: Batata Frita", key="busca_lupa_caixa")

# Busca os produtos do cardápio em tempo real filtrando pela lupa
conn = init_connection()
produtos_filtrados = []
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if busca_termo:
            cur.execute("SELECT id, nome, preco FROM produtos WHERE nome ILIKE %s ORDER BY nome;", (f"%{busca_termo}%",))
        else:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
        produtos_filtrados = cur.fetchall()
    conn.close()if not produtos_filtrados:
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
        
        # Tela interativa de confirmação antes de disparar a baixa no estoque
        if st.session_state.get(f"caixa_conf_{prod['id']}", False):
            with st.status(f"⚠️ Confirmar pedido de {qtd_p}x {prod['nome']}?", expanded=True):
                st.write(f"• Valor total: R$ {v_final:.2f} " + ("(Com 10%)" if p_taxa else "(Sem taxa)"))
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Confirmar", key=f"caixa_ok_{prod['id']}", type="primary"):
                        conn = init_connection()
                        if conn:
                            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                # Busca a Ficha Técnica vinculada a este prato
                                cur.execute("SELECT f.insumo_id, f.quantidade, i.nome FROM ficha_tecnica f JOIN insumos i ON f.insumo_id = i.id WHERE f.produto_id = %s;", (prod['id'],))
                                ficha = cur.fetchall()
                                
                                # Processa o débito (g/ml convertido para Kg/L dividindo por 1000)
                                for item in ficha:
                                    consumo = (float(item['quantidade']) / 1000.0) * qtd_p
                                    cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual - %s WHERE id = %s;", (consumo, item['insumo_id']))
                                    
                                # Registra a venda no histórico
                                cur.execute("INSERT INTO pedidos_realizados (produto_nome, quantity_pedida, valor_total, taxa_inclusa) VALUES (%s, %s, %s, %s);".replace("quantity_pedida", "quantidade_pedida"), (prod['nome'], qtd_p, v_final, p_taxa))
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
        if filtro == "Com 10%":
            cur.execute("SELECT produto_nome, quantidade_pedida, valor_total, taxa_inclusa, data_hora FROM pedidos_realizados WHERE taxa_inclusa = TRUE ORDER BY data_hora DESC LIMIT 10;")
        elif filtro == "Sem Taxa":
            cur.execute("SELECT produto_nome, quantidade_pedida, valor_total, taxa_inclusa, data_hora FROM pedidos_realizados WHERE taxa_inclusa = FALSE ORDER BY data_hora DESC LIMIT 10;")
        else:
            cur.execute("SELECT produto_nome, quantidade_pedida, valor_total, taxa_inclusa, data_hora FROM pedidos_realizados ORDER BY data_hora DESC LIMIT 10;")
        historico = cur.fetchall()
    conn.close()
    
    if historico:
        for p in historico:
            txt_t = "🟢 (Com 10%)" if p['taxa_inclusa'] else "⚪ (Sem taxa)"
            st.text(f"• {p['data_hora'].strftime('%H:%M:%S')} - {p['quantidade_pedida']}x {p['produto_nome']} | Total: R$ {float(p['valor_total']):.2f} {txt_t}")
    else:
        st.info("Nenhum pedido lançado recentemente com este filtro.")

