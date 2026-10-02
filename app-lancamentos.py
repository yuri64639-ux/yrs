from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sistema", layout="centered")
PASS, ADMIN = "orla123", "admin123"

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False
if not st.session_state["logado"]:
    st.subheader("Acesso")
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar", type="primary", use_container_width=True) and senha == PASS:
        st.session_state["logado"] = True; st.rerun()
    st.stop()

if "admin_ok" not in st.session_state: st.session_state["admin_ok"] = False

# --- BANCO DE DADOS ---
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

st.fragment(run_every=5)
CATS = ["Bebidas", "Drinks", "Porções", "Pratos Principais", "Sobremesas"]

cur.execute("SELECT item, quantidade FROM estoque WHERE quantidade <= 4")
if crit := cur.fetchall():
    with st.expander("Alerta Estoque Baixo", expanded=True):
        for i, q in crit: st.warning(f"{i}: {q} restante(s)")

st.title("Gestao")
ab_g, ab_c, ab_b, ab_co, ab_can, ab_r, ab_e, ab_m = st.tabs(["Lancar", "Cozinha", "Bar", "Contas", "Cancelar", "Relatorio", "Estoque", "Cardapio"])

# --- FUNÇÃO DE VALIDAÇÃO DE SENHA CORRIGIDA ---
def v_admin(key):
    if not st.session_state["admin_ok"]:
        sc = st.text_input("Senha Gerencia:", type="password", key=key)
        if st.button("🔓 Validar", key=f"b_{key}", use_container_width=True):
            if sc == ADMIN:
                st.session_state["admin_ok"] = True; st.rerun()
            else: st.error("Incorreta.")
        return False
    return True

# --- LANÇAR PEDIDO ---
with ab_g:
    st.subheader("Novo Pedido")
    cur.execute("SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos ORDER BY nome")
    if prods := cur.fetchall():
        with st.form("f_ped", clear_on_submit=True):
            m = st.text_input("Mesa:")
            # CORREÇÃO DEFINITIVA DA TUPLA: p[1] é o nome do produto e p[2] é o preço de venda
            dp = {f"{p} (R$ {p:.2f})": p for p in prods}
            ps = st.selectbox("Item:", list(dp.keys()))
            q = st.number_input("Qtd:", min_value=1, value=1)
            if st.form_submit_button("Enviar", type="primary", use_container_width=True) and m.strip():
                pid, _, _, iid, qins = dp[ps]
                ok = True
                if iid:
                    cur.execute("SELECT quantidade FROM estoque WHERE id = ?", (iid,))
                    res = cur.fetchone()
                    if res and res[0] < (qins * q): st.error("Estoque insuficiente."); ok = False
                if ok:
                    cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    if iid: cur.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?", (qins * q, iid))
                    conn.commit(); st.success("Enviado!"); st.rerun()
    else: st.warning("Cadastre produtos.")

# --- TELAS DE PREPARO ---
def prep(cats, title):
    st.subheader(title)
    cur.execute(f"SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({','.join('?'*len(cats))}) ORDER BY p.id DESC", cats)
    for pid, mesa, nome, qtd, status in cur.fetchall():
        with st.container(border=True):
            st.markdown(f"**{mesa}** -> {qtd}x {nome}")
            if st.button("Preparar" if status == "Pendente" else "Prontificar", key=f"b_{pid}_{title}", use_container_width=True):
                cur.execute("UPDATE pedidos SET status = ? WHERE id = ?", ("Preparando" if status == "Pendente" else "Entregue", pid))
                conn.commit(); st.rerun()

with ab_c: prep(["Porções", "Pratos Principais", "Sobremesas"], "Cozinha")
with ab_b: prep(["Bebidas", "Drinks"], "Bar")

# --- CONTAS ABERTAS ---
with ab_co:
    st.subheader("Contas Abertas")
    df = pd.read_sql_query("SELECT p.mesa, pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'", conn)
    if df.empty: st.info("Vazio.")
    else:
        for mesa, dados in df.groupby("mesa"):
            with st.container(border=True):
                sub = dados['Total'].sum()
                st.markdown(f"Mesa {mesa}")
                tx = sub * 0.10 if st.checkbox("Taxa 10%", value=True, key=f"tx_{mesa}") else 0.0
                st.markdown(f"Total: R$ {sub + tx:.2f}")
                st.dataframe(dados[["Produto", "Qtd", "Total"]], hide_index=True, use_container_width=True)
                if st.button(f"Fechar {mesa}", use_container_width=True):
                    cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = ? WHERE mesa = ?", (1 if tx > 0 else 0, mesa))
                    conn.commit(); st.rerun()

# --- CANCELAR UM POR UM ---
with ab_can:
    st.subheader("Cancelar Unidades")
    if v_admin("p_can"):
        dfa = pd.read_sql_query("SELECT p.id as ID, p.mesa, pr.nome, p.quantidade FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'", conn)
        if dfa.empty: st.info("Sem pedidos.")
        else:
            st.dataframe(dfa, hide_index=True, use_container_width=True)
            opc = {f"ID #{r['ID']} | Mesa {r['mesa']} - {r['nome']} ({r['quantidade']} un)": r['ID'] for _, r in dfa.iterrows()}
            sel = st.selectbox("Item:", ["Selecione..."] + list(opc.keys()))
            if sel != "Selecione..." and st.button("🚨 Remover 1 Unidade", type="primary", use_container_width=True):
                id_p = opc[sel]
                cur.execute("SELECT pr.insumo_id, pr.qtd_insumo, p.quantidade FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.id = ?", (id_p,))
                iid, qins, q_p = cur.fetchone()
                if iid and qins: cur.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE id = ?", (qins, iid))
                if q_p > 1: cur.execute("UPDATE pedidos SET quantidade = quantidade - 1 WHERE id = ?", (id_p,))
                else: cur.execute("DELETE FROM pedidos WHERE id = ?", (id_p,))
                conn.commit(); st.success("Removido!"); st.rerun()

# --- RELATÓRIO ---
with ab_r:
    st.subheader("Relatorio")
    dfv = pd.read_sql_query("SELECT pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total, p.horario, p.taxa_paga FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'", conn)
    if dfv.empty: st.info("Sem vendas.")
    else:
        dfv["Dia"] = pd.to_datetime(dfv["horario"]).dt.strftime("%d/%m/%Y")
        ds = st.selectbox("Dia:", sorted(dfv["Dia"].unique(), reverse=True))
        dff = dfv[dfv["Dia"] == ds]
        st.metric("Total", f"R$ {dff['Total'].sum():.2f}")
        st.dataframe(dff.groupby("Produto", as_index=False)[["Qtd", "Total"]].sum(), hide_index=True)

# --- ESTOQUE ---
with ab_e:
    st.subheader("Estoque")
    if v_admin("p_est"):
        with st.form("fe"):
            ni = st.text_input("Insumo:")
            qi = st.number_input("Qtd:", min_value=0.0)
            if st.form_submit_button("Salvar") and ni.strip():
                try: cur.execute("INSERT INTO estoque (item, quantidade) VALUES (?, ?)", (ni.strip(), qi)); conn.commit(); st.rerun()
                except: st.error("Erro.")
        dfe = pd.read_sql_query("SELECT id, item, quantidade FROM estoque", conn)
        if not dfe.empty: st.dataframe(dfe, hide_index=True)

# --- CARDÁPIO ---
with ab_m:
    st.subheader("Cardapio")
    if v_admin("p_card"):
        cur.execute("SELECT id, item FROM estoque")
        di = {i: i for i in cur.fetchall()}
        with st.form("fc"):
            n = st.text_input("Produto:")
            c = st.selectbox("Cat:", CATS)
            p = st.number_input("Preco:", min_value=0.0)
            sel_i = st.selectbox("Insumo:", ["Nenhum"] + list(di.keys()))
            qg = st.number_input("Gasto qtd:", min_value=0.0)
            if st.form_submit_button("Salvar") and n.strip() and p > 0:
                try:
                    cur.execute("INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) VALUES (?, ?, ?, ?, ?)", (n.strip(), c, p, di[sel_i] if sel_i != "Nenhum" else None, qg if sel_i != "Nenhum" else None))
                    conn.commit(); st.rerun()
                except: st.error("Erro.")
        dfp = pd.read_sql_query("SELECT id, nome, categoria, preco FROM produtos", conn)
        if not dfp.empty: st.dataframe(dfp, hide_index=True)
