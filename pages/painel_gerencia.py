# ==============================================================================
# PARTE 1: CONFIGURAÇÕES, SEGURANÇA E CONEXÃO DINÂMICA COM O BANCO DE DADOS
# ==============================================================================
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Painel Gerencial", layout="centered")
ADMIN = "admin123"

if "ok_g" not in st.session_state: 
    st.session_state["ok_g"] = False

if st.session_state["ok_g"]:
    st.markdown("""<style>
        #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
        header [data-testid="stToolbar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: flex !important; }
        header { background-color: transparent !important; }
    </style>""", unsafe_allow_html=True)

if not st.session_state["ok_g"]:
    with st.form("f_adm"):
        st.subheader("🔒 Acesso Restrito da Gerência")
        senha_input = st.text_input("Senha Master:", type="password")
        if st.form_submit_button("🔓 Liberar") and senha_input == ADMIN:
            st.session_state["ok_g"] = True
            st.rerun()
    st.stop()

if st.button("🔒 Bloquear Painel"): 
    st.session_state["ok_g"] = False
    st.rerun()

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

conn = ob_cx()
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque ORDER BY item", conn)
df_prods = pd.read_sql("SELECT id, nome FROM public.produtos ORDER BY nome", conn)

subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])
# ==============================================================================
# PARTE 2: INTERFACE DO PAINEL GERENCIAL E PROCESSAMENTO EM MASSA
# ==============================================================================

# --- ESTOQUE MASSIVO (INDEX 0) ---
with subtabs[0]:
    st.subheader("📦 Estoque Atual")
    st.dataframe(df_est, use_container_width=True, hide_index=True)
    with st.expander("➕ Alimentar Estoque em Massa (Formato: Insumo; Quantidade)"):
        with st.form("f_ins_massa", clear_on_submit=True):
            ent_est = st.text_area("Insumos (um por linha):", placeholder="Gelo; 10\nLaranja; 15")
            if st.form_submit_button("Salvar Estoque") and ent_est.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    for l in ent_est.strip().split("\n"):
                        p = l.split(";")
                        if len(p) == 2: cur.execute("INSERT INTO public.estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = public.estoque.quantidade + EXCLUDED.quantidade", (p[0].strip(), float(p[1])))
                    c.commit()
                st.success("Estoque atualizado!")
                st.rerun()

# --- CANCELAMENTOS (INDEX 1) ---
with subtabs[1]:
    st.subheader("❌ Cancelamentos")
    p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn)
    if p_ab.empty: st.info("Nenhuma comanda aberta.")
    else:
        m_sel = st.selectbox("Selecione a Mesa:", sorted(list(set(p_ab['mesa'].tolist()))))
        for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
            c1, c2 = st.columns(2)
            c1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
            if c2.button("Deletar", key=f"cn_{it['id']}"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", c, params=[int(it['produto_id'])])
                    for _, r in rc.iterrows(): cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE id = %s", ((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade']), int(r['insumo_id'])))
                    cur.execute("DELETE FROM public.pedidos WHERE id = %s", (int(it['id']),))
                    c.commit()
                st.success("Item removido!")
                st.rerun()

# --- CADASTRO EM MASSA (INDEX 2) ---
with subtabs[2]:
    st.subheader("🍔 Cadastro em Massa (Formato: Nome; Categoria; Preço)")
    with st.form("f_prod_massa", clear_on_submit=True):
        ent_prod = st.text_area("Produtos (um por linha):", placeholder="Caipirinha; Drinks; 18.00")
        if st.form_submit_button("🔥 Gravar Todos"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for l in ent_prod.strip().split("\n"):
                    p = l.split(";")
                    if len(p) == 3 and p[1].strip() in cats: cur.execute("INSERT INTO public.produtos (nome, categoria, preco) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (p[0].strip(), p[1].strip(), float(p[2])))
                c.commit()
            st.success("Produtos gravados!")
            st.rerun()

# --- RECEITAS MULTIPLAS (INDEX 3) ---
with subtabs[3]:
    st.subheader("🔬 Ficha Técnica")
    if not df_prods.empty and not df_est.empty:
        l_p, l_i = [r['nome'] for _, r in df_prods.iterrows()], ["---"] + [r['item'] for _, r in df_est.iterrows()]
        d_p, d_i = {r['nome']: r['id'] for _, r in df_prods.iterrows()}, {r['item']: r['id'] for _, r in df_est.iterrows()}
        with st.form("f_vinc_multi", clear_on_submit=True):
            p_sel = d_p[st.selectbox("Produto:", l_p)]
            c1, c2 = st.columns(2); i1 = c1.selectbox("Ingrediente 1:", l_i, key="i1"); q1 = c2.number_input("Qtd 1 (g/ml):", min_value=0.0, step=5.0, key="q1")
            c3, c4 = st.columns(2); i2 = c3.selectbox("Ingrediente 2:", l_i, key="i2"); q2 = c4.number_input("Qtd 2 (g/ml):", min_value=0.0, step=5.0, key="q2")
            if st.form_submit_button("🔥 Gravar"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    if i1 != "---" and q1 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i1], q1))
                    if i2 != "---" and q2 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i2], q2))
                    c.commit()
                st.success("Configurado!")
                st.rerun()

# --- RELATÓRIOS (INDEX 4) ---
with subtabs[4]:
    st.subheader("📊 Relatório Financeiro")
    v_df = pd.read_sql("SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    if v_df.empty: st.info("Sem vendas.")
    else:
        emp, gar, pen = 0.0, 0.0, 0.0
        for _, g in v_df.groupby('mesa'):
            sub, stt, tx = float(g['subtotal'].sum()), g['status'].iloc[0], int(g['taxa_paga'].iloc[0]) == 1
            if stt == 'Finalizado (Pago)':
                emp += sub
                if tx: gar += (sub * 0.1)
            else: pen += sub
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Líquido", f"R$ {emp:.2f}"); c2.metric("🍹 Caixinha", f"R$ {gar:.2f}"); c3.metric("⚠️ Prejuízo", f"R$ {pen:.2f}")
        st.dataframe(v_df, use_container_width=True, hide_index=True)

# --- EXCLUIR (INDEX 5) ---
with subtabs[5]:
    st.subheader("🗑️ Remover do Sistema")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if not df_prods.empty:
            p_ex = st.selectbox("Deletar Produto:", [r['nome'] for _, r in df_prods.iterrows()])
            if st.button("❌ Excluir Produto"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; DELETE FROM public.receitas WHERE produto_id = (SELECT id FROM public.produtos WHERE nome = %s); DELETE FROM public.produtos WHERE nome = %s;", (p_ex, p_ex))
                    c.commit()
                st.rerun()
    with col_d2:
        if not df_est.empty:
            i_ex = st.selectbox("Deletar Insumo:", [r['item'] for _, r in df_est.iterrows()])
            if st.button("❌ Excluir Insumo"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; DELETE FROM public.receitas WHERE insumo_id = (SELECT id FROM public.estoque WHERE item = %s); DELETE FROM public.estoque WHERE item = %s;", (i_ex, i_ex))
                    c.commit()
                st.rerun()
