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

if crit := cur.execute("SELECT item, quantidade FROM estoque WHERE quantidade <= 200").fetchall():
    st.error("⚠️ Estoque Baixo: " + ", ".join([f"{i} ({q:.0f})" for i, q in crit]))

st.title("📱 Gestão de Restaurante")

# Abas principais reduzidas. Relatório, Estoque e Cancelar agora estão dentro de Gerência.
tabs = st.tabs(["🍸 Drinks", "🍺 Cervejas", "🥤 Sem Álcool", "🍟 Entradas", "🍽️ Principais", "🍰 Sobremesas", "💵 Contas", "🍽️ Cardápio", "⚙️ Gerência"])

def lançar_pedido_aba(idx_tab, categoria_nome, legenda):
    with tabs[idx_tab]:
        prods = cur.execute("SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos WHERE categoria LIKE ? ORDER BY nome", (categoria_nome,)).fetchall()
        with st.form(f"f_ped_{categoria_nome}", clear_on_submit=True):
            st.subheader(legenda)
            m = st.text_input("Mesa / Comanda:", key=f"m_{categoria_nome}")
            if prods:
                dp = {f"{p} (R$ {p:.2f})": p for p in prods}
                ps = st.selectbox("Escolha o Item:", list(dp.keys()), key=f"ps_{categoria_nome}")
                q = st.number_input("Quantidade:", min_value=1, value=1, key=f"q_{categoria_nome}")
                if st.form_submit_button("🚀 Enviar Pedido", type="primary") and m.strip():
                    pid, _, _, iid, qins = dp[ps]
                    if iid and (res := cur.execute("SELECT quantidade FROM estoque WHERE id = ?", (iid,)).fetchone()) and res < (qins * q): 
                        st.error(f"Estoque insuficiente. Restam apenas {res:.0f}g/ml/un")
                    else:
                        cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        if iid: cur.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?", (qins * q, iid))
                        conn.commit(); st.success("Pedido enviado!"); st.rerun()
            else: st.warning(f"Nenhum item cadastrado em '{categoria_nome}'.")

lançar_pedido_aba(0, "Drinks", "🍸 Lançar Drinks")
lançar_pedido_aba(1, "Cervejas", "🍺 Lançar Cervejas")
lançar_pedido_aba(2, "Sem Álcool", "🥤 Lançar Sem Álcool")
lançar_pedido_aba(3, "Porções", "🍟 Lançar Entradas / Porções")
lançar_pedido_aba(4, "Pratos Principais", "🍽️ Lançar Pratos Principais")
lançar_pedido_aba(5, "Sobremesas", "🍰 Lançar Sobremesas")

# --- CONTAS ---
with tabs[6]:
    peds = cur.execute("SELECT p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'").fetchall()
    if not peds: st.info("Nenhuma comanda aberta.")
    else:
        for m in sorted(list(set([p for p in peds]))):
            itens = [p for p in peds if p == m]
            sub = sum([i for i in itens])
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for i in itens: st.write(f"▪️ {i}x {i} (R$ {i:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa 10%", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total: R$ {sub + tx:.2f}")
                if st.button(f"💵 Fechar Mesa {m}"):
                    cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = ? WHERE mesa = ? AND status != 'Finalizado (Pago)'", (1 if tx > 0 else 0, m))
                    conn.commit(); st.rerun()
# --- CARDÁPIO ---
with tabs[7]:
    ins = {i: i for i in cur.execute("SELECT id, item FROM estoque").fetchall()}
    with st.form("f_c"):
        n = st.text_input("Nome do Produto:")
        c = st.selectbox("Categoria:", ["Porções", "Pratos Principais", "Sobremesas", "Drinks", "Cervejas", "Sem Álcool"])
        p = st.number_input("Preço de Venda:", min_value=0.0)
        sel_i = st.selectbox("Insumo para descontar:", ["Nenhum"] + list(ins.keys()))
        qg = st.number_input("Gasto por unidade vendida:", min_value=0.0)
        if st.form_submit_button("Salvar no Cardápio") and n.strip() and p > 0:
            cur.execute("INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) VALUES (?, ?, ?, ?, ?) ON CONFLICT(nome) DO UPDATE SET categoria=excluded.categoria, preco=excluded.preco, insumo_id=excluded.insumo_id, qtd_insumo=excluded.qtd_insumo", (n.strip(), c, p, ins[sel_i] if sel_i != "Nenhum" else None, qg if sel_i != "Nenhum" else None))
            conn.commit(); st.rerun()
    for n, c, p in cur.execute("SELECT nome, categoria, preco FROM produtos ORDER BY categoria, nome").fetchall(): 
        st.write(f"🔹 *{c}* | **{n}** — R$ {p:.2f}")

# --- ABA DE GERÊNCIA PROTEGIDA (REÚNE RELATÓRIO, ESTOQUE E CANCELAR) ---
with tabs[8]:
    if "ok_gerencia" not in st.session_state: st.session_state["ok_gerencia"] = False
    
    if not st.session_state["ok_gerencia"]:
        with st.form("f_adm_geral"):
            st.subheader("🔒 Acesso Restrito da Gerência")
            senha_adm = st.text_input("Digite a Senha Master:", type="password")
            if st.form_submit_button("🔓 Liberar Painel"):
                if senha_adm == ADMIN:
                    st.session_state["ok_gerencia"] = True; st.rerun()
                else: st.error("Senha incorreta!")
    else:
        if st.button("🔒 Bloquear Painel Novamente"):
            st.session_state["ok_gerencia"] = False; st.rerun()
            
        st.markdown("---")
        # 1. SEÇÃO DE RELATÓRIO DE VENDAS
        st.subheader("📊 Relatório de Vendas")
        vds = cur.execute("SELECT pr.nome, p.quantidade, (p.quantidade * pr.preco), p.horario, p.taxa_paga FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'").fetchall()
        if not vds: st.info("Sem vendas.")
        else:
            dias = sorted(list(set([datetime.strptime(v, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") for v in vds])), reverse=True)
            sel = st.selectbox("Filtrar Dia:", dias)
            v_dia = [v for v in vds if datetime.strptime(v, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") == sel]
            p_tot = sum([v for v in v_dia]); t_tot = sum([v * 0.10 for v in v_dia if v == 1])
            st.metric("📦 Valor em Produtos", f"R$ {p_tot:.2f}")
            st.metric("💰 Taxas de 10%", f"R$ {t_tot:.2f}")
            st.metric("💵 Total Geral", f"R$ {p_tot + t_tot:.2f}")
            for n in set([v for v in v_dia]):
                st.write(f"▪️ **{n}**: {int(sum([v for v in v_dia if v == n]))} un")

        st.markdown("---")
        # 2. SEÇÃO DE CONTROLE DE ESTOQUE
        st.subheader("📦 Controle de Estoque")
        with st.form("f_e_gerencia"):
            ni, qi = st.text_input("Novo Insumo:"), st.number_input("Quantidade:", min_value=0.0)
            if st.form_submit_button("📥 Adicionar ao Estoque") and ni.strip():
                cur.execute("INSERT INTO estoque (item, quantidade) VALUES (?, ?) ON CONFLICT(item) DO UPDATE SET quantidade = quantidade + excluded.quantidade", (ni.strip(), qi))
                conn.commit(); st.rerun()
        for i, q in cur.execute("SELECT item, quantidade FROM estoque ORDER BY item").fetchall(): 
            st.write(f"📦 **{i}**: {q:.0f} (g/ml/un)")

        st.markdown("---")
        # 3. SEÇÃO DE CANCELAMENTO DE ITENS
        st.subheader("❌ Cancelar Pedidos Ativos")
        if itens := cur.execute("SELECT p.id, p.mesa, pr.nome, p.quantidade FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'").fetchall():
            for pid, mesa, nome, qtd in itens:
                if st.button(f"❌ Cancelar Mesa {mesa}: {qtd}x {nome}", key=f"c_{pid}"):
                    if v := cur.execute("SELECT pr.insumo_id, (p.quantidade * pr.qtd_insumo) FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.id = ?", (pid,)).fetchone():
                        if v and v: cur.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE id = ?", (v, v))
                    cur.execute("DELETE FROM pedidos WHERE id = ?", (pid,)); conn.commit(); st.rerun()
        else: st.info("Nenhum pedido ativo para cancelamento no momento.")
