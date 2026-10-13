# ==============================================================================
# VIEWS/GERENCIA.PY - PARTE 1: ESTRUTURA PRINCIPAL E ESTOQUE
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx

def f_estoque(emp_id, df_est):
    st.subheader("📦 Estoque")
    df_v = df_est.copy()
    if not df_v.empty: df_v.columns = ["ID", "Insumo", "Qtd Atual"]
    st.dataframe(df_v, use_container_width=True, hide_index=True)
    
    with st.form("f_ins", clear_on_submit=True):
        n_i = st.text_input("Insumo:")
        q_i = st.number_input("Quantidade:", min_value=0.0, value=1.0)
        if st.form_submit_button("Salvar Insumo") and n_i.strip():
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public; INSERT INTO estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (emp_id, n_i.strip(), q_i))
                c.commit()
            st.rerun()

def renderizar_painel_gerencial(emp_id, senha_master):
    st.markdown("---")
    st.subheader("🔑 Autenticação Gerencial")
    senha_dig = st.text_input("Senha Master:", type="password", key="senha_p_gerencial")
    
    if senha_dig != senha_master:
        st.warning("🔒 Conteúdo restrito.")
        return
        
    if st.button("❌ Bloquear Painel", use_container_width=True):
        st.session_state["senha_p_gerencial"] = ""
        st.rerun()

    conn = ob_cx()
    if conn is None: return

    df_est = pd.read_sql("SELECT id, item, quantidade FROM estoque WHERE empresa_id = %s ORDER BY item", conn, params=[emp_id])
    df_prods = pd.read_sql("SELECT id, nome FROM produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
    
    t1, t2, t3, t4, t5, t6 = st.tabs(["📦 Estoque", "❌ Cancelar", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatório", "🗑️ Excluir"])
    
    with t1: f_estoque(emp_id, df_est)
    with t2: f_cancelar(emp_id, conn)
    with t3: f_cadastro(emp_id)
    with t4: f_receitas(emp_id, df_prods, df_est)
    with t5: f_relatorio(emp_id, conn)
    with t6: f_excluir(emp_id, df_prods, df_est)
    conn.close()
# ==============================================================================
# VIEWS/GERENCIA.PY - PARTE 2: CANCELAMENTOS, CADASTRO E RECEITAS
# ==============================================================================

def f_cancelar(emp_id, conn):
    st.subheader("❌ Cancelamentos")
    p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn, params=[emp_id])
    if p_ab.empty:
        st.info("Nenhuma comanda aberta.")
        return
    m_sel = st.selectbox("Mesa:", sorted(list(set(p_ab['mesa'].tolist()))))
    for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
        col1, col2 = st.columns(2); col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
        if col2.button("Deletar", key=f"cn_{it['id']}"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(it['produto_id'])])
                for _, r in rc.iterrows(): 
                    cur.execute("UPDATE estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])), emp_id, int(r['insumo_id'])))
                cur.execute("DELETE FROM pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                c.commit()
            st.rerun()

def f_cadastro(emp_id):
    st.subheader("🍔 Cadastro Rápido (Nome, Categoria, Preço)")
    with st.form("f_prod_massa", clear_on_submit=True):
        txt = st.text_area("Produtos:", placeholder="Caipirinha, Drinks, 15.0\nHeineken, Cervejas, 12.0")
        if st.form_submit_button("🔥 Gravar") and txt.strip():
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for l in txt.strip().split("\n"):
                    if "," in l:
                        pt = l.split(",")
                        if len(pt) == 3:
                            try: cur.execute("INSERT INTO produtos (empresa_id, nome, categoria, preco) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco", (emp_id, pt[0].strip(), pt[1].strip(), float(pt[2])))
                            except: pass
                c.commit()
            st.rerun()

def f_receitas(emp_id, df_prods, df_est):
    st.subheader("🔬 Ficha Técnica (Até 4 Itens)")
    if df_prods.empty or df_est.empty:
        st.info("Cadastre produtos e insumos primeiro.")
        return
    d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
    d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
    l_i = ["---"] + list(d_i.keys())
    
    with st.form("f_rec", clear_on_submit=True):
        p_sel = d_p[st.selectbox("Produto:", list(d_p.keys()))]
        col1, col2 = st.columns(2); i1 = col1.selectbox("Item 1:", l_i, key="ri1"); q1 = col2.number_input("Qtd 1 (g/ml):", min_value=0.0, key="rq1")
        col3, col4 = st.columns(2); i2 = col3.selectbox("Item 2:", l_i, key="ri2"); q2 = col4.number_input("Qtd 2 (g/ml):", min_value=0.0, key="rq2")
        col5, col6 = st.columns(2); i3 = col5.selectbox("Item 3:", l_i, key="ri3"); q3 = col6.number_input("Qtd 3 (g/ml):", min_value=0.0, key="rq3")
        col7, col8 = st.columns(2); i4 = col7.selectbox("Item 4:", l_i, key="ri4"); q4 = col8.number_input("Qtd 4 (g/ml):", min_value=0.0, key="rq4")
        
        if st.form_submit_button("Gravar Receita"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for i, q in [(i1, q1), (i2, q2), (i3, q3), (i4, q4)]:
                    if i != "---" and q > 0:
                        cur.execute("INSERT INTO receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, int(p_sel), int(d_i[i]), float(q)))
                c.commit()
            st.rerun()

