from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sistema Mobile", layout="centered")

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if not st.session_state["logado"]:
    st.subheader("🔑 Acesso ao Sistema")
    if st.text_input("Senha:", type="password") == "orla123" and st.button("Entrar", type="primary", use_container_width=True):
        st.session_state["logado"] = True
        st.rerun()
    st.stop()

# --- BANCO DE DADOS ---
conn = sqlite3.connect("sistema_restaurante.db", check_same_thread=False, timeout=20)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("CREATE TABLE IF NOT EXISTS estoque (id INTEGER PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);")
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL, insumo_id INTEGER, qtd_insumo REAL);")
cursor.execute("CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1);")
conn.commit()

st.fragment(run_every=5)
CATS = ["Bebidas", "Drinks", "Porções", "Pratos Principais", "Sobremesas"]

st.title("📱 Gestão Bar & Restaurante")
ab_g, ab_c, ab_b, ab_co, ab_r, ab_e, ab_m = st.tabs(["🏃 Lanz", "🍳 Coz", "🍹 Bar", "🎟️ Contas", "📊 Relat", "📦 Estq", "⚙️ Card"])

# --- LANÇAR PEDIDO ---
with ab_g:
    st.subheader("📋 Novo Pedido")
    cursor.execute("SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos ORDER BY nome")
    prods = cursor.fetchall()
    
    if not prods: st.warning("Cadastre os produtos na aba 'Cardápio' primeiro.")
    else:
        with st.form("f_ped", clear_on_submit=True):
            m = st.text_input("Mesa / Comanda:")
            dict_p = {f"{p[1]} (R$ {p[3]:.2f})": p for p in prods}
            p_sel = st.selectbox("Item:", list(dict_p.keys()))
            q = st.number_input("Qtd:", min_value=1, value=1)
            
            if st.form_submit_button("🔥 Enviar", type="primary", use_container_width=True) and m.strip():
                p_id, _, _, ins_id, q_ins = dict_p[p_sel]
                ok = True
                if ins_id:
                    cursor.execute("SELECT item, quantidade FROM estoque WHERE id = ?", (ins_id,))
                    n_i, q_a = cursor.fetchone()
                    if q_a < (q_ins * q):
                        st.error(f"❌ Estoque insuficiente de '{n_i}' ({q_a} disponíveis).")
                        ok = False
                if ok:
                    cursor.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)", (m.strip(), p_id, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    if ins_id: cursor.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?", (q_ins * q, ins_id))
                    conn.commit(); st.success("Pedido enviado!"); st.rerun()

# --- TELAS DE PREPARO ---
def render_prep(cats_alvo, tit):
    st.subheader(tit)
    cursor.execute(f"SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({','.join('?'*len(cats_alvo))}) ORDER BY p.id DESC", cats_alvo)
    for pid, mesa, nome, qtd, status in cursor.fetchall():
        with st.container(border=True):
            st.markdown(f"**{mesa}** -> ### {qtd}x {nome}")
            if st.button("👨‍🍳 Preparar" if status == "Pendente" else "🚚 Prontificar", key=f"b_{pid}_{tit}", use_container_width=True):
                cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", ("Preparando" if status == "Pendente" else "Entregue", pid))
                conn.commit(); st.rerun()

with ab_c: render_prep(["Porções", "Pratos Principais", "Sobremesas"], "🍳 Cozinha")
with ab_b: render_prep(["Bebidas", "Drinks"], "🍹 Bar")

# --- CONTAS ABERTAS ---
with ab_co:
    st.subheader("🎟️ Contas Abertas")
    df = pd.read_sql_query("SELECT p.mesa, pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'", conn)
    if df.empty: st.info("Nenhuma comanda ativa.")
    else:
        for mesa, dados in df.groupby("mesa"):
            with st.container(border=True):
                sub = dados['Total'].sum()
                st.markdown(f"### 🎫 {mesa}")
                tx = sub * 0.10 if st.checkbox("Taxa de serviço (10%)", value=True, key=f"tx_{mesa}") else 0.0
                st.markdown(f"Subtotal: R$ {sub:.2f} | Taxa: R$ {tx:.2f} \n #### Total Geral: **R$ {sub + tx:.2f}**")
                st.dataframe(dados[["Produto", "Qtd", "Total"]], hide_index=True, use_container_width=True)
                if st.button(f"💵 Fechar {mesa}", use_container_width=True):
                    cursor.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = ? WHERE mesa = ?", (1 if tx > 0 else 0, mesa))
                    conn.commit(); st.rerun()

# --- RELATÓRIO ---
with ab_r:
    st.subheader("📊 Relatório do Dia")
    df_v = pd.read_sql_query("SELECT pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total, p.horario, p.taxa_paga FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'", conn)
    if df_v.empty: st.info("Sem vendas.")
    else:
        df_v["Dia"] = pd.to_datetime(df_v["horario"]).dt.strftime("%d/%m/%Y")
        dia_sel = st.selectbox("Escolha o Dia:", sorted(df_v["Dia"].unique(), reverse=True))
        df_f = df_v[df_v["Dia"] == dia_sel]
        sub_d = df_f['Total'].sum()
        tx_d = df_f.apply(lambda r: r["Total"] * 0.10 if r["taxa_paga"] == 1 else 0.0, axis=1).sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Produtos", f"R$ {sub_d:.2f}")
        c2.metric("Caixinha", f"R$ {tx_d:.2f}")
        c3.metric("Faturamento", f"R$ {sub_d + tx_d:.2f}")
        st.dataframe(df_f.groupby("Produto", as_index=False)[["Qtd", "Total"]].sum(), hide_index=True, use_container_width=True)

# --- ESTOQUE ---
with ab_e:
    st.subheader("📦 Estoque")
    with st.form("f_est"):
        ni = st.text_input("Nome do Insumo:")
        qi = st.number_input("Qtd Inicial:", min_value=0.0, step=1.0)
        if st.form_submit_button("💾 Salvar", use_container_width=True) and ni.strip():
            try: cursor.execute("INSERT INTO estoque (item, quantidade) VALUES (?, ?)", (ni.strip(), qi)); conn.commit(); st.rerun()
            except sqlite3.IntegrityError: st.error("Insumo já cadastrado.")
    
    df_est = pd.read_sql_query("SELECT id, item as Insumo, quantidade as 'Qtd' FROM estoque ORDER BY item", conn)
    if not df_est.empty:
        st.dataframe(df_est, hide_index=True, use_container_width=True)
        ins_add = st.selectbox("Reabastecer:", df_est["Insumo"].tolist())
        q_add = st.number_input("Adicionar Qtd:", min_value=0.1, step=1.0)
        if st.button("Confirmar Entrada", use_container_width=True):
            cursor.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE item = ?", (q_add, ins_add))
            conn.commit(); st.rerun()

# --- CARDÁPIO ---
with ab_m:
    st.subheader("⚙️ Cardápio")
    cursor.execute("SELECT id, item FROM estoque ORDER BY item")
    insumos = cursor.fetchall()
    with st.form("f_card"):
        n = st.text_input("Nome do Produto:")
        c = st.selectbox("Categoria:", CATS)
        p = st.number_input("Preço (R$):", min_value=0.0, step=0.5)
        dict_i = {ins[1]: ins[0] for ins in insumos}
        i_sel = st.selectbox("Insumo Gasto (Opcional):", ["Nenhum"] + list(dict_i.keys()))
        qi_gasto = st.number_input("Qtd gasta por unidade:", min_value=0.0, step=1.0, value=0.0)
        if st.form_submit_button("💾 Salvar Produto", use_container_width=True) and n.strip() and p > 0:
            try:
                cursor.execute("INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) VALUES (?, ?, ?, ?, ?)", 
                               (n.strip(), c, p, dict_i[i_sel] if i_sel != "Nenhum" else None, qi_gasto if i_sel != "Nenhum" else None))
                conn.commit(); st.rerun()
            except sqlite3.IntegrityError: st.error("Produto já existe.")
            
    df_p = pd.read_sql_query("SELECT id, nome as Nome, categoria as Categoria, preco as Preço FROM produtos ORDER BY categoria, nome", conn)
    if not df_p.empty:
        st.dataframe(df_p, hide_index=True, use_container_width=True)
        if st.selectbox("Remover:", ["Selecione..."] + df_p["Nome"].tolist(), key="del") != "Selecione..." and st.button("❌ Excluir", use_container_width=True):
            cursor.execute("DELETE FROM produtos WHERE nome = ?", (st.session_state["del"],))
            conn.commit(); st.rerun()
