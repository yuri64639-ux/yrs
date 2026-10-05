from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Sistema de Vendas", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)
PASS = "orla123"

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    with st.form("login_form"):
        st.subheader("📱 Acesso ao Sistema")
        if st.form_submit_button("Entrar", type="primary") and st.text_input("Senha:", type="password") == PASS:
            st.session_state.logado = True; st.rerun()
    st.stop()

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

conn = ob_cx()
with conn.cursor() as cur:
    cur.execute("SET search_path TO public;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.estoque (id SERIAL PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);
        CREATE TABLE IF NOT EXISTS public.produtos (id SERIAL PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL);
        CREATE TABLE IF NOT EXISTS public.receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL, UNIQUE(produto_id, insumo_id));
        CREATE TABLE IF NOT EXISTS public.pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Sim');
    """)
    conn.commit()

cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs(["🍸 Drinks", "🍺 Cervejas", "🥤 Sem Álcool", "🍟 Porções", "🍽️ Principais", "🍰 Sobremesas", "💵 Contas"])

for idx, cat in enumerate(cats):
    with tabs[idx]:
        prods = pd.read_sql("SELECT id, nome, preco FROM public.produtos WHERE categoria = %s ORDER BY nome", conn, params=[cat])
        with st.form(f"f_{idx}", clear_on_submit=True):
            m = st.text_input("Mesa / Comanda:", key=f"m_{idx}")
            if not prods.empty:
                dp = {f"{r['nome']} (R$ {r['preco']:.2f})": r for _, r in prods.iterrows()}
                ps = st.selectbox("Escolha o Item:", list(dp.keys()), key=f"ps_{idx}")
                q = st.number_input("Quantidade:", min_value=1, value=1, key=f"q_{idx}")
                if st.form_submit_button("🚀 Enviar", type="primary") and m.strip():
                    pid = int(dp[ps]['id'])
                    rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.quantidade FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn, params=[pid])
                    if all([r['quantidade'] >= ((r['qtd_insumo'] / 1000.0) * q) for _, r in rec.iterrows()]):
                        with ob_cx() as c_trans, c_trans.cursor() as cur_trans:
                            cur_trans.execute("SET search_path TO public;")
                            cur_trans.execute("INSERT INTO public.pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m.strip(), pid, int(q), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            for _, r in rec.iterrows(): 
                                cur_trans.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (float((float(r['qtd_insumo']) / 1000.0) * int(q)), int(r['insumo_id'])))
                            c_trans.commit()
                        st.success("Pedido enviado com sucesso!")
                    else: st.error("Estoque insuficiente!")
            else: st.warning("Nenhum item cadastrado.")

with tabs:
    st.subheader("🎟️ Contas Abertas")
    peds = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as sub FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    if peds.empty: st.info("Nenhuma comanda aberta.")
    else:
        for m in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m]; sub = float(itens['sub'].sum())
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): st.write(f"▪️ {i['quantidade']}x {i['nome']} (R$ {i['sub']:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa de Serviço (10%)", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total Final: R$ {sub + tx:.2f}")
                pago_opcao = st.radio("O cliente pagou a conta?", ["Sim", "Não"], key=f"pago_{m}", horizontal=True)
                if st.button(f"💵 Fechar Conta {m}", key=f"b_{m}"):
                    status_final = 'Finalizado (Pago)' if pago_opcao == "Sim" else 'Fechado (Não Pago)'
                    with ob_cx() as c_fechar, c_fechar.cursor() as cur_fechar:
                        cur_fechar.execute("SET search_path TO public;")
                        cur_fechar.execute("UPDATE public.pedidos SET status = %s, taxa_paga = %s, pago = %s WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (status_final, 1 if tx > 0 else 0, pago_opcao, m))
                        c_fechar.commit()
                    st.success(f"Conta da mesa {m} fechada!")
