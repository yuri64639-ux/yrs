from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Orla Bar", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)

PASS, ADMIN = "orla123", "admin123"

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    with st.form("login_form"):
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

st.title("🍹 Gestão Orla Bar")
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs(["🍸 Drinks", "🍺 Cervejas", "🥤 Sem Álcool", "🍟 Porções", "🍽️ Principais", "🍰 Sobremesas", "💵 Contas", "⚙️ Gerência"])

# --- LANÇAMENTO DE PEDIDOS ---
for idx, cat in enumerate(cats):
    with tabs[idx]:
        prods = pd.read_sql("SELECT id, nome, preco FROM produtos WHERE categoria = %s ORDER BY nome", conn_raw, params=[cat])
        with st.form(f"f_{idx}", clear_on_submit=True):
            m = st.text_input("Mesa / Comanda:", key=f"m_{idx}")
            if not prods.empty:
                dp = {f"{r['nome']} (R$ {r['preco']:.2f})": r for _, r in prods.iterrows()}
                ps = st.selectbox("Escolha o Item:", list(dp.keys()), key=f"ps_{idx}")
                q = st.number_input("Quantidade:", min_value=1, value=1, key=f"q_{idx}")
                
                if st.form_submit_button("🚀 Enviar", type="primary") and m.strip():
                    pid = int(dp[ps]['id'])
                    rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.item, e.quantidade FROM receitas r JOIN estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn_raw, params=[pid])
                    
                    if all([r['quantidade'] >= (r['qtd_insumo'] * q) for _, r in rec.iterrows()]):
                        with obter_conexao() as c:
                            with c.cursor() as cur:
                                cur.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                for _, r in rec.iterrows():
                                    cur.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s", ((r['qtd_insumo'] * q), int(r['insumo_id'])))
                                c.commit()
                        st.success("Enviado!"); st.rerun()
                    else: st.error("Falta estoque de ingredientes!")
            else: st.warning("Nenhum item cadastrado.")

# --- CONTAS ---
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
                if st.button(f"💵 Fechar Conta {m}", key=f"b_{m}"):
                    with obter_conexao() as c, c.cursor() as cur:
                        cur.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE mesa = %s AND status != 'Finalizado (Pago)'", (1 if tx > 0 else 0, m))
                        c.commit()
                    st.success("Fechada!"); st.rerun()

# --- GERÊNCIA ---
with tabs[7]:
    if "ok_g" not in st.session_state: st.session_state["ok_g"] = False
    if not st.session_state["ok_g"]:
        with st.form("f_adm"):
            if st.form_submit_button("🔓 Liberar") and st.text_input("Senha Master:", type="password") == ADMIN:
                st.session_state["ok_g"] = True; st.rerun()
    else:
        if st.button("🔒 Bloquear"): st.session_state["ok_g"] = False; st.rerun()
        
        df_est = pd.read_sql("SELECT id, item, quantidade FROM estoque ORDER BY item", conn_raw)
        st.subheader("📦 Estoque Atual (g / ml / un)")
        st.dataframe(df_est, use_container_width=True, hide_index=True)

        with st.expander("➕ Alimentar Estoque"):
            with st.form("f_ins", clear_on_submit=True):
                n_i = st.text_input("Insumo (Ex: Velho Barreiro, Batata):")
                q_i = st.number_input("Qtd (ml ou g):", min_value=0.0, value=1000.0)
                if st.form_submit_button("Salvar") and n_i.strip():
                    with obter_conexao() as c, c.cursor() as cur:
                        cur.execute("INSERT INTO estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (n_i.strip(), q_i))
                        c.commit()
                    st.rerun()

        with st.expander("🍔 1. Criar Produto"):
            with st.form("f_prod", clear_on_submit=True):
                n_p = st.text_input("Nome (Ex: Caipirinha):")
                c_p = st.selectbox("Categoria:", cats)
                p_p = st.number_input("Preço de Venda:", min_value=0.0, value=15.0)
                if st.form_submit_button("Gravar") and n_p.strip():
                    with obter_conexao() as c, c.cursor() as cur:
                        cur.execute("INSERT INTO produtos (nome, categoria, preco) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (n_p.strip(), c_p, p_p))
                        c.commit()
                    st.rerun()

        with st.expander("🔬 2. Montar Receita"):
            df_prods = pd.read_sql("SELECT id, nome FROM produtos ORDER BY nome", conn_raw)
            if not df_prods.empty and not df_est.empty:
                with st.form("f_vinc", clear_on_submit=True):
                    p_sel = {r['nome']: r['id'] for _, r in df_prods.iterrows()}[st.selectbox("Produto:", [r['nome'] for _, r in df_prods.iterrows()])]
                    i_sel = {r['item']: r['id'] for _, r in df_est.iterrows()}[st.selectbox("Insumo que gasta:", [r['item'] for _, r in df_est.iterrows()])]
                    qtd = st.number_input("Qtd gasta (g ou ml):", min_value=0.01, value=80.0)
                    if st.form_submit_button("Vincular"):
                        with obter_conexao() as c, c.cursor() as cur:
                            cur.execute("INSERT INTO receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, i_sel, qtd))
                            c.commit()
                        st.rerun()
