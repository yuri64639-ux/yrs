from datetime import datetime
import sqlite3
import streamlit as st

# --- CONFIGURAÇÃO MOBILE ---
st.set_page_config(page_title="Sistema de Gestão", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)

PASS, ADMIN = "orla123", "admin123"

# --- LOGIN ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    senha = st.text_input("Senha:", type="password")
    if st.button("Entrar", type="primary") and senha == PASS:
        st.session_state["logado"] = True
        st.rerun()
    st.stop()

# --- BANCO DE DADOS ---
conn = sqlite3.connect("restaurante.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS estoque (id INTEGER PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);")
cur.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL, insumo_id INTEGER, qtd_insumo REAL);")
cur.execute("CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1);")
conn.commit()

# --- AVISO DE ESTOQUE ---
if crit := cur.execute("SELECT item, quantidade FROM estoque WHERE quantidade <= 4").fetchall():
    st.error(f"⚠️ Estoque Baixo: " + ", ".join([f"{i} ({q})" for i, q in crit]))

st.title("📱 Gestão de Restaurante")
ab_g, ab_c, ab_b, ab_co, ab_can, ab_r, ab_e, ab_m = st.tabs(["📝 Pedido", "🍳 Cozinha", "🍹 Bar", "💵 Contas", "❌ Cancelar", "📊 Vendas", "📦 Estoque", "🍽️ Cardápio"])

def verificar_admin(chave):
    if f"ok_{chave}" not in st.session_state: st.session_state[f"ok_{chave}"] = False
    if not st.session_state[f"ok_{chave}"]:
        with st.form(f"f_{chave}"):
            if st.form_submit_button("🔓 Liberar Aba") and st.text_input("Senha Gerência:", type="password", key=f"s_{chave}") == ADMIN:
                st.session_state[f"ok_{chave}"] = True; st.rerun()
        return False
    return True

# --- LANÇAR PEDIDO ---
with ab_g:
    if prods := cur.execute("SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos ORDER BY nome").fetchall():
        with st.form("f_ped", clear_on_submit=True):
            m = st.text_input("Mesa/Comanda:")
            dp = {f"{p[1]} (R$ {p[2]:.2f})": p for p in prods}
            ps = st.selectbox("Item:", list(dp.keys()))
            q = st.number_input("Qtd:", min_value=1, value=1)
            if st.form_submit_button("🚀 Enviar", type="primary") and m.strip():
                pid, _, _, iid, qins = dp[ps]
                if iid and (res := cur.execute("SELECT quantidade FROM estoque WHERE id = ?", (iid,)).fetchone()) and res[0] < (qins * q):
                    st.error("Estoque insuficiente.")
                else:
                    cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    if iid: cur.execute("UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?", (qins * q, iid))
                    conn.commit(); st.success("Enviado!"); st.rerun()
    else: st.warning("Cadastre produtos no Cardápio.")

# --- TELAS DE PREPARO (COZINHA e BAR) ---
def tela_preparo(categorias, chave):
    pedidos = cur.execute(f"SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)' AND p.status != 'Entregue' AND pr.categoria IN ({','.join('?'*len(categorias))}) ORDER BY p.id ASC", categorias).fetchall()
    if not pedidos: st.info("Tudo pronto por aqui!")
    for pid, mesa, nome, qtd, status in pedidos:
        with st.container(border=True):
            lbl = "🔴 Pendente" if status == "Pendente" else "🟡 Em preparo"
            st.write(f"**Mesa {mesa}** ➔ {qtd}x {nome} ({lbl})")
            if st.button("Avançar Status" if status == "Pendente" else "Marcar como Entregue", key=f"b_{pid}_{chave}"):
                cur.execute("UPDATE pedidos SET status = ? WHERE id = ?", ("Preparando" if status == "Pendente" else "Entregue", pid))
                conn.commit(); st.rerun()

with ab_c: tela_preparo(["Porções", "Pratos Principais", "Sobremesas"], "coz")
with ab_b: tela_preparo(["Bebidas", "Drinks"], "bar")

# --- CONTAS ---
with ab_co:
    pedidos = cur.execute("SELECT p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'").fetchall()
    if not pedidos: st.info("Nenhuma mesa aberta.")
    else:
        mesas = set([p[0] for p in pedidos])
        for m in sorted(mesas):
            itens = [p for p in pedidos if p[0] == m]
            sub = sum([i[4] for i in itens])
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for i in itens: st.write(f"▪️ {i[2]}x {i[1]} (R$ {i[4]:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa 10%", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total: R$ {sub + tx:.2f}")
                if st.button(f"💵 Fechar Mesa {m}"):
                    cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = ? WHERE mesa = ? AND status != 'Finalizado (Pago)'", (1 if tx > 0 else 0, m))
                    conn.commit(); st.rerun()

# --- CANCELAR ---
with ab_can:
    if verificar_admin("canc"):
        if itens := cur.execute("SELECT p.id, p.mesa, pr.nome, p.quantidade FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'").fetchall():
            for pid, mesa, nome, qtd in itens:
                if st.button(f"❌ M-{mesa}: {qtd}x {nome}", key=f"c_{pid}"):
                    if v := cur.execute("SELECT pr.insumo_id, (p.quantidade * pr.qtd_insumo) FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.id = ?", (pid,)).fetchone():
                        if v[0] and v[1]: cur.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE id = ?", (v[1], v[0]))
                    cur.execute("DELETE FROM pedidos WHERE id = ?", (pid,))
                    conn.commit(); st.rerun()
        else: st.info("Vazio.")

# --- RELATÓRIO DE VENDAS CORES E DATAS CORRIGIDAS ---
with ab_r:
    vendas = cur.execute("SELECT pr.nome, p.quantidade, (p.quantidade * pr.preco) as item_tot, p.horario, p.taxa_paga FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'").fetchall()
    if not vendas: st.info("Sem vendas registradas.")
    else:
        # Extração correta da data do formato YYYY-MM-DD HH:MM:SS para DD/MM/YYYY
        dias = sorted(list(set([datetime.strptime(v[3], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") for v in vendas])), reverse=True)
        sel_dia = st.selectbox("Escolha o Dia:", dias)
        
        # Filtrando as vendas daquele dia selecionado
        v_dia = [v for v in vendas if datetime.strptime(v[3], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") == sel_dia]
        
        tot_produtos = sum([v[2] for v in v_dia])
        tot_taxas = sum([v[2] * 0.10 for v in v_dia if v[4] == 1])
        faturamento_geral = tot_produtos + tot_taxas
        
        st.metric("📦 Valor em Produtos", f"R$ {tot_produtos:.2f}")
        st.metric("💰 Total de 10% (Garçom)", f"R$ {tot_taxas:.2f}")
        st.metric("💵 Faturamento Geral (Total)", f"R$ {faturamento_geral:.2f}")
        
        st.markdown("---")
        st.markdown("**Quantidade por Item Vendido:**")
        
        # Agrupa itens unicos vendidos no dia
        itens_unicos = set([v[0] for v in v_dia])
        for n in itens_unicos:
            q = sum([v[1] for v in v_dia if v[0] == n])
            st.write(f"▪️ **{n}**: {int(q)} un")

# --- ESTOQUE ---
with ab_e:
    if verificar_admin("est"):
        with st.form("f_e"):
            ni, qi = st.text_input("Insumo:"), st.number_input("Qtd:", min_value=0.0)
            if st.form_submit_button("Salvar") and ni.strip():
                cur.execute("INSERT INTO estoque (item, quantidade) VALUES (?, ?) ON CONFLICT(item) DO UPDATE SET quantidade = quantidade + excluded.quantidade", (ni.strip(), qi))
                conn.commit(); st.rerun()
        for i, q in cur.execute("SELECT item, quantidade FROM estoque ORDER BY item").fetchall():
            st.write(f"📦 **{i}**: {q}")

# --- CARDÁPIO ---
with ab_m:
    if verificar_admin("card"):
        insumos = {i[1]: i[0] for i in cur.execute("SELECT id, item FROM estoque").fetchall()}
        with st.form("f_c"):
            n, c, p = st.text_input("Produto:"), st.selectbox("Categoria:", ["Bebidas", "Drinks", "Porções", "Pratos Principais", "Sobremesas"]), st.number_input("Preço:", min_value=0.0)
            sel_i, qg = st.selectbox("Descontar Insumo?", ["Nenhum"] + list(insumos.keys())), st.number_input("Qtd Gasto:", min_value=0.0)
            if st.form_submit_button("Salvar") and n.strip() and p > 0:
                cur.execute("INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) VALUES (?, ?, ?, ?, ?) ON CONFLICT(nome) DO UPDATE SET categoria=excluded.categoria, preco=excluded.preco, insumo_id=excluded.insumo_id, qtd_insumo=excluded.qtd_insumo", (n.strip(), c, p, insumos[sel_i] if sel_i != "Nenhum" else None, qg if sel_i != "Nenhum" else None))
                conn.commit(); st.rerun()
        for n, c, p in cur.execute("SELECT nome, categoria, preco FROM produtos ORDER BY categoria, nome").fetchall():
            st.write(f"🔹 *{c}* | **{n}** — R$ {p:.2f}")
