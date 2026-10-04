from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Orla Bar - Ficha Técnica", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)

PASS, ADMIN = "orla123", "admin123"

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    with st.form("login_form"):
        st.subheader("📱 Acesso Orla Bar")
        if st.form_submit_button("Entrar", type="primary") and st.text_input("Senha:", type="password") == PASS:
            st.session_state.logado = True; st.rerun()
    st.stop()

def obter_conexao():
    credenciais = st.secrets["connections"]["postgresql"]
    if "url" in credenciais: return psycopg2.connect(credenciais["url"])
    return psycopg2.connect(host=credenciais.get("host"), port=credenciais.get("port", 5432), database=credenciais.get("database"), user=credenciais.get("username"), password=credenciais.get("password"), sslmode="require")

conn_raw = obter_conexao()

with conn_raw.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque (id SERIAL PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);
        CREATE TABLE IF NOT EXISTS produtos (id SERIAL PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL);
        CREATE TABLE IF NOT EXISTS receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL, UNIQUE(produto_id, insumo_id));
        CREATE TABLE IF NOT EXISTS pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1);
    """)
    conn_raw.commit()

crit = pd.read_sql("SELECT item, quantidade FROM estoque WHERE quantidade <= 200", conn_raw)
if not crit.empty:
    st.error("⚠️ Estoque Baixo: " + ", ".join([f"{r['item']} ({r['quantidade']:.0f})" for _, r in crit.iterrows()]))

st.title("🍹 Gestão Orla Bar")
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs(["🍸 Drinks", "🍺 Cervejas", "🥤 Sem Álcool", "🍟 Porções", "🍽️ Principais", "🍰 Sobremesas", "💵 Contas", "⚙️ Gerência"])

# --- LÓGICA DE LANÇAMENTO COM MÚLTIPLOS DESCONTOS ---
for idx, cat in enumerate(cats):
    with tabs[idx]:
        prods = pd.read_sql("SELECT id, nome, preco FROM produtos WHERE categoria = %s ORDER BY nome", conn_raw, params=[cat])
        with st.form(f"f_{idx}", clear_on_submit=True):
            st.subheader(f"Lançar {cat}")
            m = st.text_input("Mesa / Comanda:", key=f"m_{idx}")
            if not prods.empty:
                dp = {f"{r['nome']} (R$ {r['preco']:.2f})": r for _, r in prods.iterrows()}
                ps = st.selectbox("Escolha o Item:", list(dp.keys()), key=f"ps_{idx}")
                q = st.number_input("Quantidade:", min_value=1, value=1, key=f"q_{idx}")
                
                if st.form_submit_button("🔥 Enviar Pedido", type="primary") and m.strip():
                    pid = int(dp[ps]['id'])
                    rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.item, e.quantidade as est_atual FROM receitas r JOIN estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn_raw, params=[pid])
                    
                    ok = True
                    for _, row in rec.iterrows():
                        if row['est_atual'] < (row['qtd_insumo'] * q):
                            st.error(f"🚨 Falta {row['item']}. Restam apenas {row['est_atual']:.0f}. Necessário: {row['qtd_insumo'] * q:.0f}"); ok = False
                    
                    if ok:
                        with obter_conexao() as c:
                            with c.cursor() as cur:
                                cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                for _, row in rec.iterrows():
                                    cur.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s", ((row['qtd_insumo'] * q), int(row['insumo_id'])))
                                c.commit()
                        st.success("✅ Pedido enviado!"); st.rerun()
            else: st.warning("Nenhum item cadastrado.")

# --- FECHAMENTO DE COMANDAS ---
with tabs:
    st.subheader("🎟️ Contas Abertas")
    peds = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as sub FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'", conn_raw)
    if peds.empty: st.info("Nenhuma comanda aberta.")
    else:
        for m in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m]; sub = float(itens['sub'].sum())
            with st.expander(f"📋 Comanda {m} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): st.write(f"▪️ {i['quantidade']}x {i['nome']} (R$ {i['sub']:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa (10%)", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total: R$ {sub + tx:.2f}")
                if st.button(f"💵 Fechar Conta ({m})", key=f"b_{m}"):
                    with obter_conexao() as c:
                        with c.cursor() as cur:
                            cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE mesa = %s AND status != 'Finalizado (Pago)'", (1 if tx > 0 else 0, m))
                            c.commit()
                    st.success("Fechada!"); st.rerun()

# --- PASTA DA GERÊNCIA PROTEGIDA ---
with tabs:
    if "ok_g" not in st.session_state: st.session_state["ok_g"] = False
    if not st.session_state["ok_g"]:
        with st.form("f_adm"):
            if st.form_submit_button("🔓 Liberar Painel") and st.text_input("Senha Master:", type="password") == ADMIN:
                st.session_state["ok_g"] = True; st.rerun()
    else:
        if st.button("🔒 Bloquear Painel"): st.session_state["ok_g"] = False; st.rerun()
        
        st.subheader("📦 Painel de Estoque")
        df_est = pd.read_sql("SELECT id, item, quantidade FROM estoque ORDER BY item", conn_raw)
        st.dataframe(df_est, use_container_width=True, hide_index=True)

        with st.expander("➕ Alimentar / Cadastrar Insumo"):
            st.info("💡 **Regra de Unidades:** Converta Litros para **ml** e Quilos para **g** (Ex: 10 Litros = 10000 | 1 Kg = 1000)")
            with st.form("f_ins", clear_on_submit=True):
                n_i = st.text_input("Nome do Insumo (Ex: Velho Barreiro, Batata Frita):")
                q_i = st.number_input("Quantidade Total a Adicionar (g ou ml):", min_value=0.0, value=1000.0, step=100.0)
                if st.form_submit_button("Salvar Insumo") and n_i.strip():
                    with obter_conexao() as c:
                        with c.cursor() as cur:
                            cur.execute("INSERT INTO estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (n_i.strip(), q_i))
                            c.commit()
                    st.success("Estoque Atualizado!"); st.rerun()

        with st.expander("🍔 1. Cadastrar Produto no Menu"):
            with st.form("f_prod", clear_on_submit=True):
                n_p = st.text_input("Nome do Prato/Drink (Ex: Caipirinha):")
                c_p = st.selectbox("Categoria:", cats)
                p_p = st.number_input("Preço de Venda:", min_value=0.0, value=18.0)
                if st.form_submit_button("Gravar no Menu") and n_p.strip():
                    with obter_conexao() as c:
                        with c.cursor() as cur:
                            cur.execute("INSERT INTO produtos (nome, categoria, preco) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (n_p.strip(), c_p, p_p))
                            c.commit()
                    st.success("Produto Criado!"); st.rerun()

        with st.expander("🔬 2. Vincular Ingredientes à Receita (Ficha Técnica)"):
            df_prods = pd.read_sql("SELECT id, nome FROM produtos ORDER BY nome", conn_raw)
            if not df_prods.empty and not df_est.empty:
                with st.form("f_vinc", clear_on_submit=True):
                    d_p = {row['nome']: row['id'] for _, row in df_prods.iterrows()}
                    d_i = {row['item']: row['id'] for _, row in df_est.iterrows()}
                    
                    p_sel = d_p[st.selectbox("Selecione o Produto do Menu:", list(d_p.keys()))]
                    i_sel = d_i[st.selectbox("Selecione o Insumo que ele gasta:", list(d_i.keys()))]
                    qtd_g_ml = st.number_input("Quantidade gasta por cada venda (em g ou ml):", min_value=0.01, value=80.0, step=5.0)
                    
                    if st.form_submit_button("Vincular Ingrediente"):
                        with obter_conexao() as c:
                            with c.cursor() as cur:
                                cur.execute("INSERT INTO receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, i_sel, qtd_g_ml))
                                c.commit()
                        st.success("Ingrediente adicionado à receita!"); st.rerun()
            else: st.warning("Cadastre produtos e insumos primeiro.")

        with st.expander("📊 Relatório de Faturamento"):
            rel = pd.read_sql("SELECT pr.nome, p.quantidade, (p.quantidade * pr.preco) as tot FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'", conn_raw)
            if not rel.empty:
                st.dataframe(rel, use_container_width=True, hide_index=True)
                st.metric("Total Faturado", f"R$ {rel['tot'].sum():.2f}")
            else: st.info("Nenhuma venda hoje.")
