from datetime import datetime
import sqlite3
import streamlit as st

st.set_page_config(page_title="Gestão", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)
PASS, ADMIN = "orla123", "admin123"

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    if st.button("Entrar", type="primary") and st.text_input("Senha:", type="password") == PASS:
        st.session_state.logado = True; st.rerun()
    st.stop()

conn = sqlite3.connect("restaurante.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS estoque (id INTEGER PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);")
cur.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL, insumo_id INTEGER, qtd_insumo REAL);")
cur.execute("CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1);")
conn.commit()

if crit := cur.execute("SELECT item, quantidade FROM estoque WHERE quantidade <= 4").fetchall():
    st.error("⚠️ Estoque Baixo: " + ", ".join([f"{i} ({q})" for i, q in crit]))

st.title("📱 Gestão de Restaurante")

if ult := cur.execute("SELECT mesa, horario FROM pedidos WHERE status != 'Finalizado (Pago)' ORDER BY id DESC LIMIT 1").fetchone():
    try:
        m_dt = int((datetime.now() - datetime.strptime(ult[1], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60)
        t_txt = f"há {m_dt} min" if m_dt > 0 else "agora"
    except: t_txt = ""
    st.info(f"📌 **Última comanda ativa:** Mesa **{ult[0]}** ({t_txt}).")

tabs = st.tabs(["📝 Pedido", "🍳 Cozinha", "🍹 Bar", "💵 Contas", "❌ Cancelar", "📊 Vendas", "📦 Estoque", "🍽️ Cardápio"])

def admin(ch):
    if f"ok_{ch}" not in st.session_state: st.session_state[f"ok_{ch}"] = False
    if not st.session_state[f"ok_{ch}"]:
        with st.form(f"f_{ch}"):
            if st.form_submit_button("🔓 Liberar") and st.text_input("Senha:", type="password", key=f"s_{ch}") == ADMIN:
                st.session_state[f"ok_{ch}"] = True; st.rerun()
        return False
    return True

# --- PEDIDO (FILTROS VERTICAIS PARA BAR E COZINHA) ---
with tabs[0]:
    if "setor" not in st.session_state: st.session_state.setor = "Cozinha"
    if "sub_bar" not in st.session_state: st.session_state.sub_bar = "Drinks"
    if "sub_coz" not in st.session_state: st.session_state.sub_coz = "Pratos Principais"
    
    st.subheader("📍 Escolha o Setor")
    if st.button("🍹 BAR", type="primary" if st.session_state.setor == "Bar" else "secondary"): 
        st.session_state.setor = "Bar"; st.rerun()
    if st.button("🍳 COZINHA", type="primary" if st.session_state.setor == "Cozinha" else "secondary"): 
        st.session_state.setor = "Cozinha"; st.rerun()

    st.markdown("---")

    if st.session_state.setor == "Bar":
        st.subheader("🔍 Tipo de Bebida")
        if st.button("🍸 Drinks", type="primary" if st.session_state.sub_bar == "Drinks" else "secondary"): 
            st.session_state.sub_bar = "Drinks"; st.rerun()
        if st.button("🍺 Cervejas", type="primary" if st.session_state.sub_bar == "Cervejas" else "secondary"): 
            st.session_state.sub_bar = "Cervejas"; st.rerun()
        if st.button("🥤 Sem Álcool", type="primary" if st.session_state.sub_bar == "Sem Álcool" else "secondary"): 
            st.session_state.sub_bar = "Sem Álcool"; st.rerun()
        cats = [st.session_state.sub_bar]
    else: 
        st.subheader("🔍 Tipo de Prato")
        if st.button("🍟 Entrada / Porções", type="primary" if st.session_state.sub_coz == "Porções" else "secondary"): 
            st.session_state.sub_coz = "Porções"; st.rerun()
        if st.button("🍽️ Principal", type="primary" if st.session_state.sub_coz == "Pratos Principais" else "secondary"): 
            st.session_state.sub_coz = "Pratos Principais"; st.rerun()
        if st.button("🍰 Sobremesa", type="primary" if st.session_state.sub_coz == "Sobremesas" else "secondary"): 
            st.session_state.sub_coz = "Sobremesas"; st.rerun()
        cats = [st.session_state.sub_coz]

    prods = cur.execute(f"SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos WHERE categoria LIKE ? ORDER BY nome", (cats[0],)).fetchall()

    st.markdown("---")
    with st.form("f_ped", clear_on_submit=True):
        st.caption(f"Filtrado por: {st.session_state.setor} -> " + (st.session_state.sub_bar if st.session_state.setor == "Bar" else st.session_state.sub_coz))
        m = st.text_input("Mesa / Comanda:")
        if prods:
            dp = {f"{p[1]} (R$ {p[2]:.2f})": p for p in prods}
            ps = st.selectbox("Item:", list(dp.keys()))
            q = st.number_input("Quantidade:", min_value=1, value=1)
            if st.form_submit_button("🚀 Enviar Pedido", type="primary") and m.strip():
                pid, _, _, iid, qins = dp[ps]
                if iid and (res := cur.execute("SELECT quantidade FROM estoque WHERE id = ?", (iid,)).fetchone()) and res[0] < (qins * q): 
                    st.error("Estoque insuficiente.")
                else:
                    cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    if iid: cur.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?", (qins * q, iid))
                    conn.commit(); st.success("Enviado!"); st.rerun()
        else: 
            st.warning("Nenhum produto cadastrado nesta categoria.")
# --- PREPARO ---
def prep(cats, ch):
    condicoes = " OR ".join(["pr.categoria LIKE ?" for _ in cats])
    peds = cur.execute(f"SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)' AND p.status != 'Entregue' AND ({condicoes}) ORDER BY p.id ASC", cats).fetchall()
    if not peds: st.info("Tudo pronto!")
    for pid, mesa, nome, qtd, status in peds:
        with st.container(border=True):
            st.write(f"**Mesa {mesa}** ➔ {qtd}x {nome} (" + ("🔴" if status == "Pendente" else "🟡") + ")")
            if st.button("Avançar" if status == "Pendente" else "Entregar", key=f"b_{pid}_{ch}"):
                cur.execute("UPDATE pedidos SET status = ? WHERE id = ?", ("Preparando" if status == "Pendente" else "Entregue", pid))
                conn.commit(); st.rerun()

with tabs[1]: prep(["Porções", "Pratos Principais", "Sobremesas"], "coz")
with tabs[2]: prep(["Bebidas", "Drinks", "Cervejas", "Sem Álcool"], "bar")

# --- CONTAS ---
with tabs[3]:
    peds = cur.execute("SELECT p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'").fetchall()
    if not peds: st.info("Nenhuma mesa aberta.")
    else:
        for m in sorted(list(set([p[0] for p in peds]))):
            itens = [p for p in peds if p[0] == m]
            sub = sum([i[4] for i in itens])
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for i in itens: st.write(f"▪️ {i[2]}x {i[1]} (R$ {i[4]:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa 10%", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total: R$ {sub + tx:.2f}")
                if st.button(f"💵 Fechar Mesa {m}"):
                    cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = ? WHERE mesa = ? AND status != 'Finalizado (Pago)'", (1 if tx > 0 else 0, m))
                    conn.commit(); st.rerun()

# --- CANCELAR ---
with tabs[4]:
    if admin("canc"):
        if itens := cur.execute("SELECT p.id, p.mesa, pr.nome, p.quantidade FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'").fetchall():
            for pid, mesa, nome, qtd in itens:
                if st.button(f"❌ M-{mesa}: {qtd}x {nome}", key=f"c_{pid}"):
                    if v := cur.execute("SELECT pr.insumo_id, (p.quantidade * pr.qtd_insumo) FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.id = ?", (pid,)).fetchone():
                        if v[0] and v[1]: cur.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE id = ?", (v[1], v[0]))
                    cur.execute("DELETE FROM pedidos WHERE id = ?", (pid,)); conn.commit(); st.rerun()
        else: st.info("Vazio.")

# --- VENDAS ---
with tabs[5]:
    vds = cur.execute("SELECT pr.nome, p.quantidade, (p.quantidade * pr.preco), p.horario, p.taxa_paga FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'").fetchall()
    if not vds: st.info("Sem vendas.")
    else:
        dias = sorted(list(set([datetime.strptime(v[3], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") for v in vds])), reverse=True)
        sel = st.selectbox("Dia:", dias)
        v_dia = [v for v in vds if datetime.strptime(v[3], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") == sel]
        
        p_tot = sum([v[2] for v in v_dia])
        t_tot = sum([v[2] * 0.10 for v in v_dia if v[4] == 1])
        
        st.metric("📦 Produtos", f"R$ {p_tot:.2f}")
        st.metric("💰 Taxas (10%)", f"R$ {t_tot:.2f}")
        st.metric("💵 Total Geral", f"R$ {p_tot + t_tot:.2f}")
        
        for n in set([v[0] for v in v_dia]):
            q = sum([v[1] for v in v_dia if v[0] == n])
            st.write(f"▪️ **{n}**: {int(q)} un")

# --- ESTOQUE ---
with tabs[6]:
    if admin("est"):
        with st.form("f_e"):
            ni, qi = st.text_input("Insumo:"), st.number_input("Qtd:", min_value=0.0)
            if st.form_submit_button("Salvar") and ni.strip():
                cur.execute("INSERT INTO estoque (item, quantidade) VALUES (?, ?) ON CONFLICT(item) DO UPDATE SET quantidade = quantidade + excluded.quantidade", (ni.strip(), qi))
                conn.commit(); st.rerun()
        for i, q in cur.execute("SELECT item, quantidade FROM estoque ORDER BY item").fetchall(): 
            st.write(f"📦 **{i}**: {q}")

# --- CARDÁPIO ---
with tabs[7]:
    if admin("card"):
        ins = {i[1]: i[0] for i in cur.execute("SELECT id, item FROM estoque").fetchall()}
        with st.form("f_c"):
            n = st.text_input("Produto:")
            c = st.selectbox("Categoria:", ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"])
            p = st.number_input("Preço:", min_value=0.0)
            sel_i = st.selectbox("Descontar Insumo?", ["Nenhum"] + list(ins.keys()))
            qg = st.number_input("Qtd Gasto:", min_value=0.0)
            if st.form_submit_button("Salvar") and n.strip() and p > 0:
                cur.execute("INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) VALUES (?, ?, ?, ?, ?) ON CONFLICT(nome) DO UPDATE SET categoria=excluded.categoria, preco=excluded.preco, insumo_id=excluded.insumo_id, qtd_insumo=excluded.qtd_insumo", (n.strip(), c, p, ins[sel_i] if sel_i != "Nenhum" else None, qg if sel_i != "Nenhum" else None))
                conn.commit(); st.rerun()
        for n, c, p in cur.execute("SELECT nome, categoria, preco FROM produtos ORDER BY categoria, nome").fetchall(): 
            st.write(f"🔹 *{c}* | **{n}** — R$ {p:.2f}")
