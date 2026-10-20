import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

st.set_page_config(page_title="Frente de Caixa & Pedidos", layout="wide")

st.markdown("""
    <style>
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

if "pedido_confirmar" not in st.session_state:
    st.session_state.pedido_confirmar = None

@st.cache_resource
def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro ao conectar ao banco Neon: {e}")
        return None

def upgrade_db_pedidos():
    conn = init_connection()
    if conn:
        with conn:
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

upgrade_db_pedidos()

@st.fragment(run_every="5s")
def checar_alertas_estoque_oculto():
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT nome, quantidade_atual FROM insumos WHERE quantidade_atual <= 2.000 ORDER BY nome;")
            itens_criticos = cur.fetchall()
            
            if itens_criticos:
                for item in itens_criticos:
                    st.toast(f"⚠️ **ATENÇÃO GARÇOM:** O insumo **{item['nome']}** está acabando! (Restam {float(item['quantidade_atual']):.3f} Kg/L)", icon="🚨")

st.title("🛒 Frente de Caixa & Gerenciamento")
st.caption("Conectado ao Banco de Dados Neon central")

checar_alertas_estoque_oculto()
st.markdown("---")

aba_vendas, aba_mesas_abertas = st.tabs(["🚀 Lançar Pedidos", "📋 Mesas & Comandas Abertas"])

with aba_vendas:
    st.subheader("👤 Identificação do Cliente")
    col_mesa, col_comanda = st.columns(2)
    with col_mesa:
        input_mesa = st.text_input("🪑 Número da Mesa:", value="Balcão", placeholder="Ex: Mesa 04", key="input_mesa_vendas")
    with col_comanda:
        input_comanda = st.text_input("📋 Código da Comanda:", value="Não Informado", placeholder="Ex: 1042", key="input_comanda_vendas")

    st.markdown("---")

    if st.session_state.pedido_confirmar:
        pedido = st.session_state.pedido_confirmar
        with st.status(f"⚠️ Confirmar lançamento para {pedido['mesa']} / Comanda: {pedido['comanda']}?", expanded=True):
            st.write(f"• **Produto:** {pedido['qtd']}x {pedido['nome']}")
            st.write(f"• **Valor total:** R$ {pedido['valor_final']:.2f} " + ("(Com 10%)" if pedido['taxa'] else "(Sem taxa)"))
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("✅ Confirmar Lançamento", type="primary", key="btn_conf_global_ok"):
                    conn = init_connection()
                    if conn:
                        try:
                            with conn: 
                                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                    cur.execute("SELECT insumo_id, quantity FROM ficha_tecnica WHERE produto_id = %s;", (pedido['id'],))
                                    ficha = cur.fetchall() if hasattr(cur, 'fetchall') else []
                                    if not ficha:
                                        try:
                                            cur.execute("SELECT insumo_id, quantidade FROM ficha_tecnica WHERE produto_id = %s;", (pedido['id'],))
                                            ficha = cur.fetchall()
                                        except:
                                            pass
                                    
                                    for item in ficha:
                                        qtd_ficha = item.get('quantidade') or item.get('quantity') or 0
                                        consumo = (float(qtd_ficha) / 1000.0) * pedido['qtd']
                                        cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual - %s WHERE id = %s;", (consumo, item['insumo_id']))
                                    
                                    cur.execute("""
                                        INSERT INTO pedidos_realizados (produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo) 
                                        VALUES (%s, %s, %s, %s, %s, %s);
                                    """, (pedido['nome'], pedido['qtd'], pedido['valor_final'], pedido['taxa'], pedido['mesa'], pedido['comanda']))
                            
                            st.success("Pedido finalizado com sucesso!")
                            st.session_state.pedido_confirmar = None
                            time.sleep(0.8)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao processar no banco: {e}")
            with c_btn2:
                if st.button("❌ Cancelar", key="btn_conf_global_cancel"):
                    st.session_state.pedido_confirmar = None
                    st.rerun()

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
                    st.session_state.pedido_confirmar = {
                        "id": prod['id'],
                        "nome": prod['nome'],
                        "qtd": qtd_p,
                        "valor_final": v_final,
                        "taxa": p_taxa,
                        "mesa": input_mesa.strip(),
                        "comanda": input_comanda.strip()
                    }
                    st.rerun()
with aba_mesas_abertas:
    st.subheader("📋 Consumo por Mesa e Código de Comanda")
    
    conn = init_connection()
    todos_pedidos = []
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, mesa_numero, comanda_codigo, produto_nome, quantidade_pedida, valor_total, data_hora 
                FROM pedidos_realizados 
                ORDER BY mesa_numero, comanda_codigo, data_hora DESC;
            """)
            todos_pedidos = cur.fetchall()
        
    if not todos_pedidos:
        st.info("Nenhum pedido ou mesa com consumo registrado no momento.")
    else:
        # Agrupamento dos dados obtidos do banco por Mesa e Comanda
        mesas_agrupadas = {}
        for ped in todos_pedidos:
            chave = (ped['mesa_numero'], ped['comanda_codigo'])
            if chave not in mesas_agrupadas:
                mesas_agrupadas[chave] = []
            mesas_agrupadas[chave].append(ped)
            
        # Renderização visual estruturada das tabelas de consumo
        for (mesa, comanda), itens in mesas_agrupadas.items():
            total_mesa = sum(float(i['valor_total']) for i in itens)
            
            with st.expander(f"🪑 {mesa} | 📋 Comanda: {comanda} — Total: R$ {total_mesa:.2f}"):
                c_head1, c_head2, c_head3, c_head4 = st.columns([0.4, 0.2, 0.2, 0.2])
                with c_head1: st.caption("**Produto**")
                with c_head2: st.caption("**Quantidade**")
                with c_head3: st.caption("**Valor Total**")
                with c_head4: st.caption("**Horário**")
                
                for i in itens:
                    c_row1, c_row2, c_row3, c_row4 = st.columns([0.4, 0.2, 0.2, 0.2])
                    with c_row1: st.write(i['produto_nome'])
                    with c_row2: st.write(f"{i['quantidade_pedida']}x")
                    with c_row3: st.write(f"R$ {float(i['valor_total']):.2f}")
                    with c_row4: st.write(i['data_hora'].strftime("%H:%M:%S"))
                
                st.markdown("---")
                
                # Ação para remover os registros correspondentes ao encerrar a conta
                if st.button(f"🗑️ Fechar Conta ({mesa} / {comanda})", key=f"fechar_{mesa}_{comanda}", type="secondary"):
                    conn = init_connection()
                    if conn:
                        try:
                            with conn:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        DELETE FROM pedidos_realizados 
                                        WHERE mesa_numero = %s AND comanda_codigo = %s;
                                    """, (mesa, comanda))
                            st.success(f"Conta da {mesa} encerrada e limpa!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao fechar conta: {e}")
