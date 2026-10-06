# Parte1.py
import streamlit as st
import psycopg2
import pandas as pd

# 1. CONFIGURAÇÃO GLOBAL E SEGURANÇA
st.set_page_config(page_title="Painel Gerencial", layout="wide")
ADMIN = st.secrets.get("credentials", {}).get("admin_password", "admin123")

if "ok_g" not in st.session_state:
    st.session_state["ok_g"] = False

if not st.session_state["ok_g"]:
    with st.form("f_adm"):
        st.subheader("🔒 Acesso Restrito da Gerência")
        senha_input = st.text_input("Senha Master:", type="password")
        if st.form_submit_button("🔓 Liberar"):
            if senha_input == ADMIN:
                st.session_state["ok_g"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

if st.button("🔒 Bloquear Painel"):
    st.session_state["ok_g"] = False
    st.rerun()

# 2. FUNÇÃO DE CONEXÃO COM O BANCO DE DADOS
def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c:
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432),
        database=c.get("database"), user=c.get("username"),
        password=c.get("password"), sslmode="require"
    )

# 3. CONSULTAS GLOBAIS DE DADOS
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
with ob_cx() as conn:
    df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque ORDER BY item", conn)
    df_prods = pd.read_sql("SELECT id, nome FROM public.produtos ORDER BY nome", conn)

# 4. CRIAÇÃO DAS ABAS COMPARTILHADAS
subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])

# --- ABA 0: ESTOQUE ---
with subtabs[0]:
    st.subheader("📦 Estoque Atual")
    df_est_v = df_est.copy()
    if not df_est_v.empty:
        df_est_v.columns = ["ID", "Insumo", "Quantidade Atual"]
    st.dataframe(df_est_v, use_container_width=True, hide_index=True)
    
    with st.expander("➕ Alimentar Estoque"):
        with st.form("f_ins", clear_on_submit=True):
            n_i = st.text_input("Insumo:")
            q_i = st.number_input("Qtd:", min_value=0.0, value=1.0, step=1.0)
            if st.form_submit_button("Salvar") and n_i.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("INSERT INTO public.estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (n_i.strip(), q_i))
                    c.commit()
                st.success("Estoque atualizado!")
                st.rerun()

# --- ABA 1: CANCELAMENTOS ---
with subtabs[1]:
    st.subheader("❌ Cancelar Itens")
    with ob_cx() as conn:
        p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn)
    
    if p_ab.empty:
        st.info("Nenhuma comanda aberta.")
    else:
        m_sel = st.selectbox("Selecione a Mesa:", sorted(list(set(p_ab['mesa'].tolist()))))
        for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
            col1, col2 = st.columns(2)
            col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
            if col2.button("Deletar", key=f"cn_{it['id']}"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", c, params=[int(it['produto_id'])])
                    for _, r in rc.iterrows():
                        cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE id = %s", ((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade']), int(r['insumo_id'])))
                    cur.execute("DELETE FROM public.pedidos WHERE id = %s", (int(it['id']),))
                    c.commit()
                st.success("Item removido!")
                st.rerun()

# --- ABA 2: CADASTRO ---
with subtabs[2]:
    st.subheader("🍔 Criar Produto")
    with st.form("f_prod", clear_on_submit=True):
        n_p = st.text_input("Nome:")
        c_p = st.selectbox("Categoria:", cats)
        p_p = st.number_input("Preço de Venda:", min_value=0.0, value=15.0)
        if st.form_submit_button("Gravar") and n_p.strip():
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("INSERT INTO public.produtos (nome, categoria, preco) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (n_p.strip(), c_p, p_p))
                c.commit()
            st.success("Produto gravado!")
            st.rerun()
