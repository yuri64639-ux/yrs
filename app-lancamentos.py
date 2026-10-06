from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Vendas - Config", layout="centered")

for k in ["logado", "usuario_atual", "ocultar_css", "carrinho"]:
    if k not in st.session_state:
        st.session_state[k] = False if k=="logado" else True if k=="ocultar_css" else [] if k=="carrinho" else ""

if st.session_state.ocultar_css:
    st.markdown("<style>#MainMenu, .stAppDeployButton { visibility: hidden; display: none; } header [data-testid='stToolbar'] { display: none; } [data-testid='collapsedControl'] { display: flex; } header { background-color: transparent; }</style>", unsafe_allow_html=True)

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

conn = ob_cx()
with conn.cursor() as cur:
    cur.execute("SET search_path TO public;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.usuarios (id SERIAL PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT);
        CREATE TABLE IF NOT EXISTS public.estoque (id SERIAL PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);
        CREATE TABLE IF NOT EXISTS public.produtos (id SERIAL PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL);
        CREATE TABLE IF NOT EXISTS public.receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL, UNIQUE(produto_id, insumo_id));
        CREATE TABLE IF NOT EXISTS public.pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Sim', garcom TEXT);
    """)
    cur.execute("ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS quantidade INTEGER; ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS garcom TEXT;")
    cur.execute("INSERT INTO public.usuarios (usuario, senha) VALUES ('admin', 'orla123') ON CONFLICT DO NOTHING")
conn.commit()

if not st.session_state.logado:
    with st.form("f_log"):
        u = st.text_input("Usuário:").strip()
        s = st.text_input("Senha:", type="password").strip()
        if st.form_submit_button("Entrar"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SELECT usuario FROM public.usuarios WHERE LOWER(usuario)=LOWER(%s) AND senha=%s", (u, s))
                res = cur.fetchone()
            if res:
                st.session_state.logado, st.session_state.usuario_atual = True, str(res[0])
                st.success("Logado! Vá para a aba de pedidos.")
                st.rerun()
            else: st.error("Incorreto!")

    st.markdown("---")
    st.write("### 🛠️ Desenvolvedor")
    sp = st.text_input("Senha Master:", type="password")
    if st.button("Alternar Funções Nativas") and sp == "adm123":
        st.session_state.ocultar_css = not st.session_state.ocultar_css
        st.rerun()

    with st.expander("⚙️ Cadastro de Garçons"):
        nu = st.text_input("Nome Garçom:")
        ns = st.text_input("Senha Garçom:", type="password")
        sm = st.text_input("Autorização Master:", type="password")
        if st.button("Gravar") and nu.strip() and ns.strip() and sm == "adm123":
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("INSERT INTO public.usuarios (usuario, senha) VALUES (%s, %s) ON CONFLICT (usuario) DO UPDATE SET senha = EXCLUDED.senha", (nu.strip(), ns.strip()))
                c.commit()
            st.success("Salvo!")
            st.rerun()
from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Vendas - Pedidos", layout="centered")

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

conn = ob_cx()

if not st.session_state.get("logado", False):
    st.warning("Efetue o login no arquivo de configurações primeiro.")
else:
    st.write(f"f'👤 Operador: {st.session_state.usuario_atual}'")
    if st.button("🔒 Sair"):
        st.session_state.logado = False
        st.rerun()
        
    t1, t2 = st.tabs(["🚀 Pedidos", "💵 Contas"])
    
    with t1:
        m = st.text_input("Mesa:", value=st.session_state.get("m_at", ""))
        st.session_state["m_at"] = m
        busca = st.text_input("🔍 Buscar item:").strip()
        dp = {}
        
        q_sel = "SELECT id, nome, preco, categoria FROM public.produtos WHERE " + ("LOWER(nome) LIKE LOWER(%s)" if busca else "categoria = %s") + " ORDER BY nome"
        p_sel = f"%{busca}%" if busca else st.selectbox("Categoria:", ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"])
        df_p = pd.read_sql(q_sel, conn, params=[p_sel])
        
        if not df_p.empty:
            dp = {f"{r['nome']} - R$ {r['preco']:.2f}": r for _, r in df_p.iterrows()}
            ch = st.selectbox("Item:", list(dp.keys()))
            q = st.number_input("Qtd:", min_value=1, value=1)
            if st.button("➕ Adicionar") and m.strip() and ch in dp:
                it = dp[ch]
                st.session_state.carrinho.append({"id": int(it["id"]), "nome": it["nome"], "qtd": int(q), "preco": float(it["preco"])})
                st.rerun()

        if st.session_state.carrinho:
            tot = sum(i["qtd"]*i["preco"] for i in st.session_state.carrinho)
            st.write(f"### Total: R$ {tot:.2f}")
            if st.button("❌ Limpar"): st.session_state.carrinho=[]; st.rerun()
            if st.button("🔥 LANÇAR COMPLETO", type="primary"):
                ids = [i["id"] for i in st.session_state.carrinho]
                q_est = "SELECT r.produto_id, r.insumo_id, r.qtd_insumo, e.quantidade FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE " + ("r.produto_id = %s" if len(ids)==1 else "r.produto_id IN %s")
                p_est = ids if len(ids)==1 else tuple(ids)
                df_rec = pd.read_sql(q_est, conn, params=[p_est])
                
                with ob_cx() as c, c.cursor() as cur:
                    hr = datetime.now().strftime("%d/%m %H:%M")
                    for i in st.session_state.carrinho:
                        cur.execute("INSERT INTO public.pedidos(mesa,produto_id,quantidade,status,horario,garcom) VALUES(%s,%s,%s,'Pendente',%s,%s)", (str(m), i["id"], i["qtd"], hr, str(st.session_state.usuario_atual)))
                        for _, r in df_rec[df_rec["produto_id"]==i["id"]].iterrows():
                            cur.execute("UPDATE public.estoque SET quantidade=quantidade-%s WHERE id=%s", ((float(r["qtd_insumo"])/1000.0)*i["qtd"], int(r["insumo_id"])))
                    c.commit()
                st.session_state.carrinho = []; st.success("Lançado!"); st.rerun()

    with t2:
        df_ped = pd.read_sql("SELECT p.id, p.mesa, pr.nome, pr.preco, p.quantidade FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status='Pendente'", conn)
        if not df_ped.empty:
            m_c = st.selectbox("Mesa p/ fechar:", sorted(list(set(df_ped["mesa"].tolist()))))
            df_m = df_ped[df_ped["mesa"] == m_c]
            sub = sum(r["quantidade"]*r["preco"] for _, r in df_m.iterrows())
            tx = 0 if st.checkbox("Remover 10%") else sub * 0.1
            st.write(f"## Total: R$ {sub+tx:.2f}")
            if st.button("✅ Pago", type="primary"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("UPDATE public.pedidos SET status='Finalizado (Pago)' WHERE mesa=%s AND status='Pendente'", (str(m_c),))
                    c.commit()
                st.rerun()
