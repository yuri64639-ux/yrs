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
tabs = st.tabs(["🍸 Drinks", "🍺 Cervejas", "🥤 Sem Álcool", "🍟 Porções", "🍽️ Principais", "🍰 Sobremesas", "💵 Contas", "🚀 Lançar Vários"])

# --- INTERFACE POR CATEGORIAS (ÍNDICES 0 A 5) ---
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
# --- CONTAS (ÍNDICE 6) ---
with tabs[6]:
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
                    st.success(f"Conta da mesa {m} fechada!"); st.rerun()

# --- NOVA ABA: SELECIONAR PRIMEIRO E LANÇAR DEPOIS (ÍNDICE 7 CORRIGIDO) ---
with tabs[7]:
    st.subheader("🚀 Lançamento Rápido por Seleção Múltipla")
    m_massa = st.text_input("Mesa / Comanda para o Lançamento:", key="m_massa_input")
    df_prods_all = pd.read_sql("SELECT id, nome, categoria, preco FROM public.produtos ORDER BY categoria, nome", conn)
    
    if not df_prods_all.empty and m_massa.strip():
        produtos_selecionados = st.multiselect("1. Selecione TODOS os produtos que saíram para esta mesa:", list(df_prods_all['nome']))
        
        if produtos_selecionados:
            st.markdown("---")
            st.markdown("**2. Ajuste as quantidades dos itens selecionados:**")
            
            itens_a_enviar = {}
            for p_nome in produtos_selecionados:
                linha_prod = df_prods_all[df_prods_all['nome'] == p_nome].iloc[0]
                qtd_item = st.number_input(f"Quantidade de {p_nome} (R$ {linha_prod['preco']:.2f}):", min_value=1, value=1, key=f"mass_q_{linha_prod['id']}")
                itens_a_enviar[p_nome] = {"id": int(linha_prod['id']), "qtd": int(qtd_item)}
            
            st.markdown("---")
            if st.button("🔥 Confirmar e Enviar Todos os Itens Selecionados", type="primary"):
                pedidos_ok = []
                estoque_ok = True
                
                for p_nome, dados in itens_a_enviar.items():
                    rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.item, e.quantidade FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn, params=[dados["id"]])
                    for _, r in rec.iterrows():
                        qtd_necessaria = (float(r['qtd_insumo']) / 1000.0) * dados["qtd"]
                        if r['quantidade'] < qtd_necessaria:
                            st.error(f"🚨 Estoque insuficiente do ingrediente '{r['item']}' para fazer o item '{p_nome}'!")
                            estoque_ok = False
                    if estoque_ok:
                        pedidos_ok.append((dados["id"], dados["qtd"]))
                
                if estoque_ok and pedidos_ok:
                    with ob_cx() as c_massa, c_massa.cursor() as cur_trans:
                        cur_trans.execute("SET search_path TO public;")
                        for pid, qtd in pedidos_ok:
                            cur_trans.execute("INSERT INTO public.pedidos (mesa, produto_id, quantity, horario)" if "quantity" in pd.read_sql("SELECT * FROM public.pedidos LIMIT 1", conn).columns else "INSERT INTO public.pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m_massa.strip(), pid, qtd, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            rec = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", conn, params=[pid])
                            for _, r in rec.iterrows():
                                qtd_convertida = float((float(r['qtd_insumo']) / 1000.0) * qtd)
                                cur_trans.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (qtd_convertida, int(r['insumo_id'])))
                        c_massa.commit()
                    st.success(f"✅ Sucesso! Todos os itens foram lançados na comanda {m_massa.strip()}!")
                    st.rerun()
    elif not m_massa.strip():
        st.info("💡 Digite o número da mesa ou comanda acima para liberar a seleção de produtos.")
    else:
        st.warning("Cadastre produtos no cardápio primeiro.")
