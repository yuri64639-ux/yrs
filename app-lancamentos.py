from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Gestão de Restaurante", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)

PASS, ADMIN = "orla123", "admin123"

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    with st.form("login_form"):
        senha = st.text_input("Senha de Acesso:", type="password")
        if st.form_submit_button("Entrar", type="primary") and senha == PASS:
            st.session_state.logado = True; st.rerun()
    st.stop()

def obter_conexao():
    credenciais = st.secrets["connections"]["postgresql"]
    if "url" in credenciais: return psycopg2.connect(credenciais["url"])
    return psycopg2.connect(
        host=credenciais.get("host"), port=credenciais.get("port", 5432),
        database=credenciais.get("database"), user=credenciais.get("username"),
        password=credenciais.get("password"), sslmode="require"
    )

conn_raw = obter_conexao()

with conn_raw.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque (id SERIAL PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);
        CREATE TABLE IF NOT EXISTS produtos (id SERIAL PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL, insumo_id INTEGER, qtd_insumo REAL);
        CREATE TABLE IF NOT EXISTS pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1);
    """)
    conn_raw.commit()

crit = pd.read_sql("SELECT item, quantidade FROM estoque WHERE quantidade <= 200", conn_raw)
if not crit.empty:
    st.error("⚠️ Estoque Baixo: " + ", ".join([f"{r['item']} ({r['quantidade']:.0f})" for _, r in crit.iterrows()]))

st.title("📱 Gestão de Restaurante")
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs([f"🍸 {cats[0]}", f"🍺 {cats[1]}", f"🥤 {cats[2]}", f"🍟 Entradas", f"🍽️ {cats[4]}", f"🍰 {cats[5]}", "💵 Contas", "⚙️ Gerência"])

# --- ABAS DE LANÇAMENTO DE PEDIDOS ---
for idx, cat in enumerate(cats):
    with tabs[idx]:
        prods = pd.read_sql("SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos WHERE categoria = %s ORDER BY nome", conn_raw, params=[cat if cat != "Porções" else "Porções"])
        with st.form(f"f_{idx}", clear_on_submit=True):
            m = st.text_input("Mesa / Comanda:", key=f"m_{idx}")
            if not prods.empty:
                dp = {f"{r['nome']} (R$ {r['preco']:.2f})": r for _, r in prods.iterrows()}
                ps = st.selectbox("Item:", list(dp.keys()), key=f"ps_{idx}")
                q = st.number_input("Qtd:", min_value=1, value=1, key=f"q_{idx}")
                if st.form_submit_button("🚀 Enviar Pedido", type="primary") and m.strip():
                    it = dp[ps]; pid, iid, qins = int(it['id']), it['insumo_id'], it['qtd_insumo']
                    ok = True
                    if iid and not pd.isna(iid):
                        res = pd.read_sql("SELECT quantidade FROM estoque WHERE id = %s", conn_raw, params=[int(iid)])
                        if not res.empty and res.iloc[0]['quantidade'] < (qins * q):
                            st.error(f"Falta estoque. Restam {res.iloc[0]['quantidade']:.0f}"); ok = False
                    if ok:
                        with obter_conexao() as c:
                            with c.cursor() as cur:
                                cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                if iid and not pd.isna(iid): cur.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s", ((qins * q), int(iid)))
                                c.commit()
                        st.success("Enviado!"); st.rerun()
            else: st.warning("Nenhum item cadastrado.")

# --- FECHAMENTO DE COMANDAS ---
with tabs[6]:
    peds = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as sub FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'", conn_raw)
    if peds.empty: st.info("Nenhuma comanda aberta.")
    else:
        for m in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m]; sub = float(itens['sub'].sum())
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): st.write(f"▪️ {i['quantidade']}x {i['nome']} (R$ {i['sub']:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa (10%)", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total: R$ {sub + tx:.2f}")
                if st.button(f"💵 Fechar Mesa {m}", key=f"b_{m}"):
                    with obter_conexao() as c:
                        with c.cursor() as cur:
                            cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE mesa = %s AND status != 'Finalizado (Pago)'", (1 if tx > 0 else 0, m))
                            c.commit()
                    st.rerun()

# --- GERÊNCIA PROTEGIDA ---
with tabs[7]:
    if "ok_g" not in st.session_state: st.session_state["ok_g"] = False
    if not st.session_state["ok_g"]:
        with st.form("f_adm"):
            if st.form_submit_button("🔓 Liberar Painel") and st.text_input("Senha Master:", type="password") == ADMIN:
                st.session_state["ok_g"] = True; st.rerun()
    else:
        if st.button("🔒 Bloquear Painel"): st.session_state["ok_g"] = False; st.rerun()
        
        st.subheader("📦 Estoque")
        df_est = pd.read_sql("SELECT id, item, quantidade FROM estoque ORDER BY item", conn_raw)
        st.dataframe(df_est, use_container_width=True, hide_index=True)

        with st.expander("➕ Alimentar Estoque"):
            with st.form("f_ins", clear_on_submit=True):
                n_i = st.text_input("Insumo:")
                q_i = st.number_input("Quantidade:", min_value=0.0, value=1000.0)
                if st.form_submit_button("Salvar") and n_i.strip():
                    with obter_conexao() as c:
                        with c.cursor() as cur:
                            cur.execute("INSERT INTO estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (n_i.strip(), q_i))
                            c.commit()
                    st.success("Estoque Atualizado!"); st.rerun()

        with st.expander("🍔 Novo Prato / Bebida"):
            with st.form("f_prod", clear_on_submit=True):
                n_p = st.text_input("Nome:")
                c_p = st.selectbox("Categoria:", cats)
                p_p = st.number_input("Preço (R$):", min_value=0.0, value=15.0)
                vinc = st.checkbox("Abater estoque?")
                i_id, q_g = None, 0.0
                if vinc and not df_est.empty:
                    d_i = {row['item']: row['id'] for _, row in df_est.iterrows()}
                    i_id = d_i[st.selectbox("Insumo:", list(d_i.keys()))]
                    q_g = st.number_input("Gasta quanto (g/ml/un)?", min_value=0.1, value=50.0)
                if st.form_submit_button("Cadastrar") and n_p.strip():
                    with obter_conexao() as c:
                        with c.cursor() as cur:
                            cur.execute("INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s, %s)", (n_p.strip(), c_p, p_p, i_id, q_g if vinc else None))
                            c.commit()
                    st.success("Cadastrado!"); st.rerun()

        with st.expander("📊 Relatório de Vendas"):
            rel = pd.read_sql("SELECT pr.nome, p.quantidade, (p.quantidade * pr.preco) as tot FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'", conn_raw)
            if not rel.empty:
                st.dataframe(rel, use_container_width=True)
                st.metric("Total Faturado", f"R$ {rel['tot'].sum():.2f}")
            else: st.info("Nenhuma venda finalizada.")
