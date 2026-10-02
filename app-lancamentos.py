from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sistema", layout="centered")
PASS, ADMIN = "orla123", "admin123"

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if not st.session_state["logado"]:
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar", type="primary", use_container_width=True) and senha == PASS:
        st.session_state["logado"] = True; st.rerun()
    st.stop()

# --- BANCO ---
conn = sqlite3.connect("restaurante.db", check_same_thread=False, timeout=20)
cur = conn.cursor()
cur.execute("PRAGMA journal_mode=WAL;")
cur.execute("CREATE TABLE IF NOT EXISTS estoque (id INTEGER PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);")
cur.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL, insumo_id INTEGER, qtd_insumo REAL);")
cur.execute("CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1);")
conn.commit()

for col, t, tab in [("insumo_id", "INTEGER", "produtos"), ("qtd_insumo", "REAL", "produtos"), ("taxa_paga", "INTEGER DEFAULT 1", "pedidos")]:
    try: cur.execute(f"ALTER TABLE {tab} ADD COLUMN {col} {t};"); conn.commit()
    except: pass

# --- ALERTA ESTOQUE ---
@st.fragment(run_every=5)
def alerta_estoque():
    c_frag = sqlite3.connect("restaurante.db").cursor()
    if crit := c_frag.execute("SELECT item, quantidade FROM estoque WHERE quantidade <= 4").fetchall():
        with st.expander("Alerta Estoque Baixo", expanded=True):
            for i, q in crit: st.warning(f"{i}: {q} restante(s)")
alerta_estoque()

st.title("Gestão")
CATS = ["Bebidas", "Drinks", "Porções", "Pratos Principais", "Sobremesas"]
ab_g, ab_c, ab_b, ab_co, ab_can, ab_r, ab_e, ab_m = st.tabs(["Lançar", "Cozinha", "Bar", "Contas", "Cancelar", "Relatório", "Estoque", "Cardápio"])

def verificar_admin(chave):
    if f"ok_{chave}" not in st.session_state: st.session_state[f"ok_{chave}"] = False
    if not st.session_state[f"ok_{chave}"]:
        with st.form(f"f_adm_{chave}"):
            if st.form_submit_button("🔓 Liberar Aba") and st.text_input("Senha Gerência:", type="password", key=f"s_{chave}") == ADMIN:
                st.session_state[f"ok_{chave}"] = True; st.rerun()
        return False
    return True

# --- LANÇAR ---
with ab_g:
    cur.execute("SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos ORDER BY nome")
    if prods := cur.fetchall():
        with st.form("f_ped", clear_on_submit=True):
            m = st.text_input("Mesa:")
            dp = {f"{p[1]} (R$ {p[2]:.2f})": p for p in prods}
            ps = st.selectbox("Item:", list(dp.keys()))
            q = st.number_input("Qtd:", min_value=1, value=1)
            if st.form_submit_button("Enviar", type="primary") and m.strip():
                pid, _, _, iid, qins = dp[ps]
                if iid and (res := cur.execute("SELECT quantidade FROM estoque WHERE id = ?", (iid,)).fetchone()) and res[0] < (qins * q):
                    st.error("Estoque insuficiente.")
                else:
                    cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    if iid: cur.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?", (qins * q, iid))
                    conn.commit(); st.rerun()
    else: st.warning("Cadastre produtos.")

# --- PREPARO (COZINHA / BAR) ---
def prep(cats, title):
    cur.execute(f"SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({','.join('?'*len(cats))}) ORDER BY p.id DESC", cats)
    for pid, mesa, nome, qtd, status in cur.fetchall():
        with st.container(border=True):
            st.write(f"**{mesa}** -> {qtd}x {nome}")
            if st.button("Preparar" if status == "Pendente" else "Prontificar", key=f"b_{pid}_{title}"):
                cur.execute("UPDATE pedidos SET status = ? WHERE id = ?", ("Preparando" if status == "Pendente" else "Entregue", pid))
                conn.commit(); st.rerun()

with ab_c: prep(["Porções", "Pratos Principais", "Sobremesas"], "Cozinha")
with ab_b: prep(["Bebidas", "Drinks"], "Bar")

# --- CONTAS ---
with ab_co:
    df = pd.read_sql_query("SELECT p.mesa, pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'", conn)
    if df.empty: st.info("Vazio.")
    else:
        for mesa, dados in df.groupby("mesa"):
            with st.container(border=True):
                sub = dados['Total'].sum()
                tx = sub * 0.10 if st.checkbox("Taxa 10%", value=True, key=f"tx_{mesa}") else 0.0
                st.write(f"**Mesa {mesa}** | Total: R$ {sub + tx:.2f}")
                st.dataframe(dados, hide_index=True)
                if st.button(f"Fechar Mesa {mesa}"):
                    cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = ? WHERE mesa = ?", (1 if tx > 0 else 0, mesa))
                    conn.commit(); st.rerun()

# --- CANCELAR ITEM POR ITEM ---
with ab_can:
    if verificar_admin("cancelar"):
        cur.execute("SELECT p.id, p.mesa, pr.nome, p.quantidade FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'")
        if not (itens := cur.fetchall()): st.info("Vazio.")
        else:
            for pid, mesa, nome, qtd in itens:
                col_txt, col_btn = st.columns([3, 1])
                col_txt.write(f"🔹 **Mesa {mesa}**: {qtd}x {nome}")
                if col_btn.button("❌", key=f"del_{pid}"):
                    if v := cur.execute("SELECT pr.insumo_id, (p.quantidade * pr.qtd_insumo) FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.id = ?", (pid,)).fetchone():
                        if v[0]: cur.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE id = ?", (v[1], v[0]))
                    cur.execute("DELETE FROM pedidos WHERE id = ?", (pid,))
                    conn.commit(); st.rerun()

# --- RELATÓRIO ---
with ab_r:
    dfv = pd.read_sql_query("SELECT pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total, p.horario FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'", conn)
    if dfv.empty: st.info("Sem vendas.")
    else:
        dfv["Dia"] = pd.to_datetime(dfv["horario"]).dt.strftime("%d/%m/%Y")
        ds = st.selectbox("Dia:", sorted(dfv["Dia"].unique(), reverse=True))
        dff = dfv[dfv["Dia"] == ds]
        st.metric("Total", f"R$ {dff['Total'].sum():.2f}")
        st.dataframe(dff.groupby("Produto", as_index=False)[["Qtd", "Total"]].sum(), hide_index=True)

# --- ESTOQUE ---
with ab_e:
    if verificar_admin("estoque"):
        with st.form("fe"):
            ni, qi = st.text_input("Insumo:"), st.number_input("Qtd:", min_value=0.0)
            if st.form_submit_button("Salvar") and ni.strip():
                cur.execute("INSERT INTO estoque (item, quantidade) VALUES (?, ?) ON CONFLICT(item) DO UPDATE SET quantidade = quantidade + excluded.quantidade", (ni.strip(), qi))
                conn.commit(); st.rerun()
        st.dataframe(pd.read_sql_query("SELECT id, item, quantidade FROM estoque", conn), hide_index=True)

# --- CARDÁPIO ---
with ab_m:
    if verificar_admin("cardapio"):
        di = {i[1]: i[0] for i in cur.execute("SELECT id, item FROM estoque").fetchall()}
        with st.form("fc"):
            n, c, p = st.text_input("Produto:"), st.selectbox("Cat:", CATS), st.number_input("Preço:", min_value=0.0)
            sel_i, qg = st.selectbox("Insumo:", ["Nenhum"] + list(di.keys())), st.number_input("Gasto qtd:", min_value=0.0)
            if st.form_submit_button("Salvar") and n.strip() and p > 0:
                cur.execute("INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) VALUES (?, ?, ?, ?, ?)", (n.strip(), c, p, di[sel_i] if sel_i != "Nenhum" else None, qg if sel_i != "Nenhum" else None))
                conn.commit(); st.rerun()
        st.dataframe(pd.read_sql_query("SELECT id, nome, categoria, preco FROM produtos", conn), hide_index=True)
