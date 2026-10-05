from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

# CONFIGURAÇÃO ÚNICA DA PÁGINA
st.set_page_config(page_title="Sistema de Gestão Integrado", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)
PASS, ADMIN = "orla123", "admin123"

# --- LOGIN GLOBAL ---
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
tabs = st.tabs(["🍸 Drinks", "🍺 Cervejas", "🥤 Sem Álcool", "🍟 Porções", "🍽️ Principais", "🍰 Sobremesas", "💵 Contas", "❌ Cancelamentos", "⚙️ Gerência"])

# --- PEDIDOS (ABAS 0 A 5) ---
for idx, cat in enumerate(cats):
    with tabs[idx]:
        prods = pd.read_sql("SELECT id, nome, preco FROM public.produtos WHERE categoria = %s ORDER BY nome", conn, params=[cat])
        with st.form(f"f_{idx}", clear_on_submit=True):
            m = st.text_input("Mesa / Comanda:", key=f"m_{idx}")
            if not prods.empty:
                dp = {f"{r['nome']} (R$ {r['preco']:.2f})": r for _, r in prods.iterrows()}
                ps = st.selectbox("Item:", list(dp.keys()), key=f"ps_{idx}")
                q = st.number_input("Qtd:", min_value=1, value=1, key=f"q_{idx}")
                if st.form_submit_button("🚀 Enviar", type="primary") and m.strip():
                    pid = int(dp[ps]['id'])
                    rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.quantidade FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn, params=[pid])
                    if all([r['quantidade'] >= ((r['qtd_insumo'] / 1000.0) * q) for _, r in rec.iterrows()]):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("INSERT INTO public.pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m.strip(), pid, int(q), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            for _, r in rec.iterrows(): cur.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (float((float(r['qtd_insumo']) / 1000.0) * int(q)), int(r['insumo_id'])))
                            c.commit()
                        st.success("Enviado!")
                    else: st.error("Estoque insuficiente!")
            else: st.warning("Nenhum item cadastrado.")

# --- CONTAS (ABA INDEX 6) ---
with tabs[6]:
    st.subheader("🎟️ Contas Abertas")
    peds = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as sub FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    if peds.empty: st.info("Nenhuma comanda aberta.")
    else:
        for m in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m]; sub = float(itens['sub'].sum())
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): st.write(f"▪ {i['quantidade']}x {i['nome']} (R$ {i['sub']:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa (10%)", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total: R$ {sub + tx:.2f}")
                pago_opcao = st.radio("Pago?", ["Sim", "Não"], key=f"pago_{m}", horizontal=True)
                if st.button(f"💵 Fechar Conta {m}", key=f"b_{m}"):
                    st_fn = 'Finalizado (Pago)' if pago_opcao == "Sim" else 'Fechado (Não Pago)'
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("UPDATE public.pedidos SET status = %s, taxa_paga = %s, pago = %s WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (st_fn, 1 if tx > 0 else 0, pago_opcao, m))
                        c.commit()
                    st.success("Fechada!"); st.rerun()
# --- CANCELAMENTOS (ABA INDEX 7) ---
with tabs[7]:
    st.subheader("❌ Cancelamento de Itens")
    if "ok_c" not in st.session_state: st.session_state["ok_c"] = False
    if not st.session_state["ok_c"]:
        with st.form("f_c_auth"):
            if st.form_submit_button("🔑 Validar Gerente") and st.text_input("Senha Master:", type="password") == ADMIN: st.session_state["ok_c"] = True; st.rerun()
    else:
        if st.button("🔒 Bloquear Cancelamento"): st.session_state["ok_c"] = False; st.rerun()
        p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn)
        if p_ab.empty: st.info("Nenhuma comanda aberta.")
        else:
            m_sel = st.selectbox("Selecione a Mesa:", sorted(list(set(p_ab['mesa'].tolist()))))
            for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
                col1, col2 = st.columns(2)
                col1.write(f"▪ {it['quantidade']}x {it['nome']}")
                if col2.button("🗑️ Cancelar", key=f"cn_{it['id']}"):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", conn, params=[int(it['produto_id'])])
                        for _, r in rc.iterrows(): cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE id = %s", (float((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])), int(r['insumo_id'])))
                        cur.execute("DELETE FROM public.pedidos WHERE id = %s", (int(it['id']),))
                        c.commit()
                    st.success("Estornado!"); st.rerun()

# --- GERÊNCIA (ABA INDEX 8) ---
with tabs[8]:
    if "ok_g" not in st.session_state: st.session_state["ok_g"] = False
    if not st.session_state["ok_g"]:
        with st.form("f_adm"):
            if st.form_submit_button("🔓 Liberar Gerência") and st.text_input("Senha Master:", type="password") == ADMIN: st.session_state["ok_g"] = True; st.rerun()
    else:
        if st.button("🔒 Bloquear Gerência"): st.session_state["ok_g"] = False; st.rerun()
        df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque ORDER BY item", conn)
        df_prods = pd.read_sql("SELECT id, nome FROM public.produtos ORDER BY nome", conn)
        st.subheader("📦 Estoque Atual (L / Kg / Un)")
        df_v = df_est.copy()
        if not df_v.empty: df_v.columns = ["ID", "Insumo", "Qtd Atual (L/Kg)"]
        st.dataframe(df_v, use_container_width=True, hide_index=True)

        with st.expander("➕ Alimentar Estoque"):
            with st.form("f_ins", clear_on_submit=True):
                n_i = st.text_input("Insumo:")
                q_i = st.number_input("Qtd Inteira (L ou Kg):", min_value=0.0, value=1.0)
                if st.form_submit_button("Salvar") and n_i.strip():
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("INSERT INTO public.estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (n_i.strip(), q_i))
                        c.commit()
                    st.success("Abastecido!"); st.rerun()

        with st.expander("🍔 1. Criar Produto"):
            with st.form("f_prod", clear_on_submit=True):
                n_p = st.text_input("Nome:")
                c_p = st.selectbox("Categoria:", cats)
                p_p = st.number_input("Preço de Venda:", min_value=0.0, value=15.0)
                if st.form_submit_button("Gravar") and n_p.strip():
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("INSERT INTO public.produtos (nome, categoria, preco) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (n_p.strip(), c_p, p_p))
                        c.commit()
                    st.success("Criado!"); st.rerun()

        with st.expander("🔬 2. Montar Receita (ml / g)"):
            if not df_prods.empty and not df_est.empty:
                l_p = [r['nome'] for _, r in df_prods.iterrows()]
                l_i = ["---"] + [r['item'] for _, r in df_est.iterrows()]
                d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
                d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
                with st.form("f_vinc_multi", clear_on_submit=True):
                    p_sel = d_p[st.selectbox("Produto:", l_p)]
                    c1, col2 = st.columns(2); i1 = c1.selectbox("Ingrediente 1:", l_i); q1 = col2.number_input("Qtd 1 (ml/g):", min_value=0.0, value=0.0, step=5.0)
                    col3, col4 = st.columns(2); i2 = col3.selectbox("Ingrediente 2:", l_i); q2 = col4.number_input("Qtd 2 (ml/g):", min_value=0.0, value=0.0, step=5.0)
                    col5, col6 = st.columns(2); i3 = col5.selectbox("Ingrediente 3:", l_i); q3 = col6.number_input("Qtd 3 (ml/g):", min_value=0.0, value=0.0, step=5.0)
                    if st.form_submit_button("🔥 Gravar Receita"):
                        v = 0
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            if i1 != "---" and q1 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i1], q1)); v+=1
                            if i2 != "---" and q2 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i2], q2)); v+=1
                            if i3 != "---" and q3 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i3], q3)); v+=1
                            c.commit()
                        if v > 0: st.success("Gravado!"); st.rerun()
            else: st.warning("Cadastre produtos e insumos primeiro.")

        with st.expander("🗑️ Excluir Itens"):
            if not df_prods.empty:
                p_ex = st.selectbox("Remover do Cardápio:", ["---"] + list(df_prods['nome']))
                if p_ex != "---" and st.button("❌ Deletar Produto"):
                    id_p = int(df_prods[df_prods['nome'] == p_ex]['id'].values)
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;"); cur.execute("DELETE FROM public.receitas WHERE produto_id = %s", (id_p,)); cur.execute("DELETE FROM public.produtos WHERE id = %s", (id_p,)); c.commit()
                    st.success("Removido!"); st.rerun()
            if not df_est.empty:
                i_ex = st.selectbox("Remover do Estoque:", ["---"] + list(df_est['item']))
                if i_ex != "---" and st.button("❌ Deletar Insumo"):
                    id_i = int(df_est[df_est['item'] == i_ex]['id'].values)
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;"); cur.execute("DELETE FROM public.receitas WHERE insumo_id = %s", (id_i,)); cur.execute("DELETE FROM public.estoque WHERE id = %s", (id_i,)); c.commit()
                    st.success("Deletado!"); st.rerun()
