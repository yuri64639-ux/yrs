# ==============================================================================
# VIEWS/GERENCIA.PY - PARTE 1 DE 3: PROTÓTIPO E ESTOQUE
# ==============================================================================
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from core.database import ob_cx

try:
    from views.gerencia_parte2 import f_cancelar, f_cadastro, f_receitas
    from views.gerencia_parte3 import f_relatorio, f_excluir
except ImportError:
    pass

def f_estoque(emp_id, df_est):
    st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
    df_v = df_est.copy()
    if not df_v.empty: df_v.columns = ["ID", "Insumo", "Quantidade Atual"]
    st.dataframe(df_v, use_container_width=True, hide_index=True)
    
    with st.expander("➕ Alimentar Estoque (Individual)"):
        with st.form("f_ins", clear_on_submit=True):
            n_i = st.text_input("Insumo:")
            q_i = st.number_input("Qtd Inteira:", min_value=0.0, value=1.0, step=1.0)
            if st.form_submit_button("Salvar") and n_i.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; INSERT INTO estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (emp_id, n_i.strip(), q_i))
                    c.commit()
                st.rerun()

    with st.expander("🍔 Alimentar Estoque em Massa (Copiar e Colar)"):
        with st.form("f_ins_massa", clear_on_submit=True):
            tx_ins = st.text_area("Insumo, Quantidade (Ex: Vodka, 10.0):")
            if st.form_submit_button("🔥 Gravar Insumos") and tx_ins.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    for l in tx_ins.strip().split("\n"):
                        if "," in l:
                            p = l.split(",")
                            if len(p) == 2:
                                try: cur.execute("INSERT INTO estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (emp_id, p[0].strip(), float(p[1])))
                                except: pass
                c.commit(); st.rerun()

def renderizar_painel_gerencial(emp_id, senha_master):
    st.markdown("---")
    st.subheader("🔑 Autenticação Gerencial Requerida")
    senha_dig = st.text_input("Senha Master:", type="password", key="senha_p_gerencial_input")
    
    if senha_dig != senha_master:
        st.warning("🔒 Conteúdo restrito. Insira a senha correta.")
        return
        
    if st.button("❌ Bloquear Aba Gerencial", type="secondary", use_container_width=True):
        st.session_state["senha_p_gerencial_input"] = ""; st.rerun()

    conn = ob_cx()
    if conn is None: return

    df_est = pd.read_sql("SELECT id, item, quantidade FROM estoque WHERE empresa_id = %s ORDER BY item", conn, params=[emp_id])
    df_prods = pd.read_sql("SELECT id, nome FROM produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
    
    subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])
    
    with subtabs[0]: f_estoque(emp_id, df_est)
    with subtabs[1]: f_cancelar(emp_id, conn)
    with subtabs[2]: f_cadastro(emp_id)
    with subtabs[3]: f_receitas(emp_id, df_prods, df_est)
    with subtabs[4]: f_relatorio(emp_id, conn)
    with subtabs[5]: f_excluir(emp_id, df_prods, df_est)
    conn.close()
# ==============================================================================
# VIEWS/GERENCIA_PARTE2.PY - PARTE 2 DE 3: CANCELAMENTOS, CADASTRO E RECEITAS
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx

def f_cancelar(emp_id, conn):
    st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
    p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn, params=[emp_id])
    if p_ab.empty:
        st.info("Nenhuma comanda aberta para cancelamento.")
        return
    m_sel = st.selectbox("Selecione a Mesa para auditar:", sorted(list(set(p_ab['mesa'].tolist()))))
    for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
        col1, col2 = st.columns(2); col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
        if col2.button("Deletar Item", key=f"cn_{it['id']}"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(it['produto_id'])])
                for _, r in rc.iterrows(): 
                    cur.execute("UPDATE estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])), emp_id, int(r['insumo_id'])))
                cur.execute("DELETE FROM pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                c.commit()
            st.rerun()

def f_cadastro(emp_id):
    cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
    st.subheader("🍔 Cadastro Rápido (Copiar e Colar)")
    with st.form("f_prod_massa", clear_on_submit=True):
        txt = st.text_area("Formato: Nome, Categoria, Preço", placeholder="Caipirinha, Drinks, 15.0")
        if st.form_submit_button("🔥 Gravar Todos"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for l in txt.strip().split("\n"):
                    if "," in l:
                        pt = l.split(",")
                        if len(pt) == 3:
                            n_p, c_p, p_p = pt[0].strip(), pt[1].strip(), pt[2].strip()
                            cat_valida = [c for c in cats if c.lower() == c_p.lower()]
                            if n_p and cat_valida:
                                try: cur.execute("INSERT INTO produtos (empresa_id, nome, categoria, preco) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco", (emp_id, n_p, str(cat_valida[0]), float(p_p)))
                                except: pass
                c.commit(); st.rerun()

def f_receitas(emp_id, df_prods, df_est):
    st.subheader("🔬 Ficha Técnica (Até 4 Ingredientes)")
    if df_prods.empty or df_est.empty: return st.info("Cadastre dados primeiro.")
    d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
    d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
    l_i = ["---"] + list(d_i.keys())
    
    with st.form("f_vinc_multi", clear_on_submit=True):
        p_sel = d_p[st.selectbox("Produto Final:", list(d_p.keys()))]
        col1, col2 = st.columns(2); i1 = col1.selectbox("Item 1:", l_i, key="rec_i1"); q1 = col2.number_input("Qtd 1:", min_value=0.0, key="rec_q1")
        col3, col4 = st.columns(2); i2 = col3.selectbox("Item 2:", l_i, key="rec_i2"); q2 = col4.number_input("Qtd 2:", min_value=0.0, key="rec_q2")
        col5, col6 = st.columns(2); i3 = col5.selectbox("Item 3:", l_i, key="rec_i3"); q3 = col6.number_input("Qtd 3:", min_value=0.0, key="rec_q3")
        col7, col8 = st.columns(2); i4 = col7.selectbox("Item 4:", l_i, key="rec_i4"); q4 = col8.number_input("Qtd 4:", min_value=0.0, key="rec_q4")
        
        if st.form_submit_button("🔥 Gravar Ficha Completa"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for i, q in [(i1, q1), (i2, q2), (i3, q3), (i4, q4)]:
                    if i != "---" and q > 0:
                        cur.execute("INSERT INTO receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, int(p_sel), int(d_i[i]), float(q)))
                c.commit(); st.rerun()
# ==============================================================================
# VIEWS/GERENCIA_PARTE3.PY - PARTE 3 DE 3: RELATÓRIOS E EXCLUSÃO DEFINITIVA
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx

def f_relatorio(emp_id, conn):
    st.subheader("📊 Resumo Financeiro Detalhado")
    v_df = pd.read_sql("SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario, p.modo_pagamento FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC", conn, params=[emp_id])
    if v_df.empty: return st.info("Nenhuma comanda histórica.")
    
    v_df['data_somente'] = v_df['horario'].apply(lambda x: str(x).split(" ")[0] if " " in str(x) else "Sem Data")
    d_sel = st.selectbox("📅 Selecione a Data:", sorted(list(set(v_df['data_somente'].tolist())), reverse=True))
    df_f = v_df[v_df['data_somente'] == d_sel]
    
    emp_t, gar_t, pen_t = 0.0, 0.0, 0.0
    for _, g in df_f.groupby('mesa'):
        sub_m = float(g['subtotal'].sum())
        if g['status'].iloc[0] == 'Finalizado (Pago)':
            emp_t += sub_m
            if int(g['taxa_paga'].iloc[0]) == 1: gar_t += (sub_m * 0.10)
        else: pen_t += sub_m
        
    c1, c2, c3 = st.columns(3); c1.metric("💰 Líquido", f"R$ {emp_t:.2f}"); c2.metric("🍹 Caixinha", f"R$ {gar_t:.2f}"); c3.metric("⚠️ Perdas", f"R$ {pen_t:.2f}")
    
    st.markdown("#### 💳 Meios de Recebimento")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    for c, m in zip([col_p1, col_p2, col_p3, col_p4], ['Pix', 'Cartão de Crédito', 'Cartão de Débito', 'Dinheiro']):
        v_m = df_f[(df_f['status']=='Finalizado (Pago)') & (df_f['modo_pagamento'] == m)]['subtotal'].sum()
        c.metric(m, f"R$ {v_m:.2f}")
    st.dataframe(df_f.drop(columns=['data_somente']), use_container_width=True, hide_index=True)

def f_excluir(emp_id, df_prods, df_est):
    st.subheader("🗑️ Remover Registros")
    col1, col2, col3 = st.columns(3)
    with col1:
        if not df_prods.empty:
            p_del = st.selectbox("Remover Produto:", [r['nome'] for _, r in df_prods.iterrows()])
            if st.button("❌ Produto", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; DELETE FROM receitas WHERE empresa_id = %s AND produto_id = (SELECT id FROM produtos WHERE empresa_id = %s AND nome = %s); DELETE FROM produtos WHERE empresa_id = %s AND nome = %s", (emp_id, emp_id, p_del, emp_id, p_del))
                    c.commit(); st.rerun()
    with col2:
        if not df_est.empty:
            i_del = st.selectbox("Remover Insumo:", [r['item'] for _, r in df_est.iterrows()], key="del_i")
            if st.button("❌ Insumo", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; DELETE FROM receitas WHERE empresa_id = %s AND insumo_id = (SELECT id FROM estoque WHERE empresa_id = %s AND item = %s); DELETE FROM estoque WHERE empresa_id = %s AND item = %s", (emp_id, emp_id, i_del, emp_id, i_del))
                    c.commit(); st.rerun()
    with col3:
        conn = ob_cx()
        df_g = pd.read_sql("SELECT id, usuario FROM usuarios WHERE empresa_id = %s ORDER BY usuario", conn, params=[emp_id])
        conn.close()
        if not df_g.empty:
            g_del = st.selectbox("Remover Garçom:", [r['usuario'] for _, r in df_g.iterrows()])
            if st.button("❌ Garçom", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; DELETE FROM usuarios WHERE empresa_id = %s AND usuario = %s", (emp_id, g_del))
                    c.commit(); st.rerun()
