import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Painel Gerencial", layout="centered")

if "logado" not in st.session_state or not st.session_state.logado:
    st.error("🔒 Por favor, faça login pelo terminal principal antes de acessar o Painel Gerencial!")
    st.stop()

emp_id = st.session_state.empresa_id_atual
ADMIN_SENHA = "admin123"

if "ok_g" not in st.session_state: 
    st.session_state["ok_g"] = False

if not st.session_state["ok_g"]:
    with st.form("f_adm"):
        st.subheader("🔒 Acesso Restrito da Gerência")
        senha_input = st.text_input("Senha Master:", type="password")
        if st.form_submit_button("🔓 Liberar"):
            if senha_input == ADMIN_SENHA:
                st.session_state["ok_g"] = True
                st.rerun()
            else: st.error("Senha incorreta!")
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

df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque WHERE empresa_id = %s ORDER BY item", conn, params=[emp_id])
df_prods = pd.read_sql("SELECT id, nome FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])

subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas"])

with subtabs[0]:
    st.subheader("📦 Estoque Atual")
    df_est_visual = df_est.copy()
    if not df_est_visual.empty: 
        df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual (L / Kg)"]
    st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
    
    with st.expander("➕ Alimentar Estoque"):
        with st.form("f_ins", clear_on_submit=True):
            n_i = st.text_input("Insumo:")
            q_i = st.number_input("Qtd:", min_value=0.0, value=1.0, step=1.0)
            if st.form_submit_button("Salvar") and n_i.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("""
                        INSERT INTO public.estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) 
                        ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade
                    """, (emp_id, n_i.strip(), q_i))
                    c.commit()
                st.success("Estoque atualizado!")
                st.rerun()
with subtabs[1]:
    st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
    p_ab = pd.read_sql("""
        SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id 
        FROM public.pedidos p 
        JOIN public.produtos pr ON p.produto_id = pr.id 
        WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') 
        ORDER BY p.mesa
    """, conn, params=[emp_id])
    
    if p_ab.empty: 
        st.info("Nenhuma comanda aberta para cancelamento.")
    else:
        m_sel = st.selectbox("Selecione a Mesa:", sorted(list(set(p_ab['mesa'].tolist()))))
        for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
            col1, col2 = st.columns(2)
            col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
            if col2.button("Deletar", key=f"cn_{it['id']}"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(it['produto_id'])])
                    for _, r in rc.iterrows(): 
                        cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", ((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade']), emp_id, int(r['insumo_id'])))
                    cur.execute("DELETE FROM public.pedidos WHERE empresa_id = %s AND id = %s", (emp_id, int(it['id'])))
                    c.commit()
                st.success("Item removido e estoque devolvido!")
                st.rerun()

with subtabs[2]:
    st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
    st.write("Cole a sua lista abaixo seguindo o formato exato: **Nome, Categoria, Preço** (um produto por linha).")
    
    with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
        texto_produtos = st.text_area("Cole seus produtos aqui:", height=250, placeholder="Exemplo:\nCaipirinha, Drinks, 15.0\nHeineken, Cervejas, 12.0")
        botao_gravar = st.form_submit_button("🔥 Gravar Todos os Produtos")
        
        if botao_gravar and texto_produtos.strip():
            linhas = texto_produtos.strip().split("\n")
            itens_gravados = 0
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for linha in linhas:
                    if "," in linha:
                        partes = linha.split(",")
                        if len(partes) == 3:
                            n_p = partes[0].strip()
                            c_p = partes[1].strip()
                            p_p = partes[2].strip()
                            cat_valida = [c for c in cats if c.lower() == c_p.lower()]
                            if n_p and cat_valida:
                                try:
                                    preco_float = float(p_p)
                                    categoria_final = str(cat_valida[0])
                                    cur.execute("""
                                        INSERT INTO public.produtos (empresa_id, nome, categoria, preco) 
                                        VALUES (%s, %s, %s, %s) 
                                        ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco
                                    """, (emp_id, n_p, categoria_final, preco_float))
                                    itens_gravados += 1
                                except ValueError: pass
                c.commit()
            if itens_gravados > 0:
                st.success(f"🚀 Sucesso! {itens_gravados} produtos processados!")
                st.rerun()
            else: st.error("❌ Nenhum produto cadastrado. Verifique o formato ou categorias.")
with subtabs:
    st.subheader("🔬 Montar Ficha Técnico-Operacional")
    if not df_prods.empty and not df_est.empty:
        lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
        lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
        d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
        d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
        
        with st.form("f_vinc_multi", clear_on_submit=True):
            prod_nome_sel = st.selectbox("Selecione o Produto:", lista_prods, key="sel_prod_receita_base")
            p_sel_id = d_p[prod_nome_sel]
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="i1")
            q1 = col2.number_input("Qtd gasta 1 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q1")
            
            i2 = col1.selectbox("Ingrediente 2:", lista_insumos, key="i2")
            q2 = col2.number_input("Qtd gasta 2 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q2")
            
            i3 = col1.selectbox("Ingrediente 3:", lista_insumos, key="i3")
            q3 = col2.number_input("Qtd gasta 3 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q3")
            
            i4 = col1.selectbox("Ingrediente 4:", lista_insumos, key="i4")
            q4 = col2.number_input("Qtd gasta 4 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q4")
            
            if st.form_submit_button("🔥 Gravar Ficha Técnica"):
                ingredientes_validos = []
                if i1 != "---" and q1 > 0: ingredientes_validos.append((d_i[i1], q1))
                if i2 != "---" and q2 > 0: ingredientes_validos.append((d_i[i2], q2))
                if i3 != "---" and q3 > 0: ingredientes_validos.append((d_i[i3], q3))
                if i4 != "---" and q4 > 0: ingredientes_validos.append((d_i[i4], q4))
                
                if ingredientes_validos:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("DELETE FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", (emp_id, int(p_sel_id)))
                        for ins_id, qtd_ins in ingredientes_validos:
                            cur.execute("""
                                INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) 
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo
                            """, (emp_id, int(p_sel_id), int(ins_id), float(qtd_ins)))
                        c.commit()
                    st.success("Ficha técnica gravada com sucesso!")
                    st.rerun()
                else:
                    st.error("Adicione pelo menos um ingrediente com quantidade válida!")
    else:
        st.info("Cadastre produtos e insumos no estoque antes de criar fichas técnicas.")
