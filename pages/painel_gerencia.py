# ==============================================================================
# PAGES/GERENCIAL.PY - PARTE 1 DE 2: CONFIGURAÇÕES E ESTOQUE
# ==============================================================================
import streamlit as st
import psycopg2
import pandas as pd

# 1. Configuração da Página (obrigatório ser o primeiro comando Streamlit)
st.set_page_config(page_title="Painel Gerencial", layout="centered")

# 2. Função de conexão dinâmica (caso precise recriar na página)
def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c:
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

# 3. Barreira de Segurança Multi-empresas
if "logado" not in st.session_state or not st.session_state.logado:
    st.error("🔒 Acesso restrito! Por favor, faça login na página inicial primeiro.")
    st.stop()

# 4. Variáveis de ambiente locais baseadas no login ativo
emp_id = st.session_state.empresa_id_atual
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]

st.title("⚙️ Painel de Controle Gerencial")

# Carregamento assíncrono e isolado de tabelas por Empresa ativa
try:
    conn = ob_cx()
    df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque WHERE empresa_id = %s ORDER BY item", conn, params=[emp_id])
    df_prods = pd.read_sql("SELECT id, nome FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
except Exception as e:
    st.error(f"Erro ao conectar com a base de dados: {e}")
    st.stop()

# Criação das abas nativas estruturadas
subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])

# --- ABA 0: ESTOQUE ---
with subtabs[0]:
    st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
    df_est_visual = df_est.copy()
    if not df_est_visual.empty: 
        df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual (L / Kg)"]
    st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
    
    with st.expander("➕ Alimentar Estoque"):
        with st.form("f_ins", clear_on_submit=True):
            n_i = st.text_input("Insumo:")
            q_i = st.number_input("Qtd Inteira (Litros, Quilos ou Un):", min_value=0.0, value=1.0, step=1.0)
            if st.form_submit_button("Salvar") and n_i.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("""
                        INSERT INTO public.estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) 
                        ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = public.estoque.quantidade + EXCLUDED.quantidade
                    """, (emp_id, n_i.strip(), q_i))
                    c.commit()
                st.success("Estoque atualizado!")
                st.rerun()

# --- ABA 1: CANCELAMENTOS ---
with subtabs[1]:
    st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
    p_ab = pd.read_sql("""
        SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id 
        FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id 
        WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa
    """, conn, params=[emp_id])
    
    if p_ab.empty: 
        st.info("Nenhuma comanda aberta para cancelamento.")
    else:
        m_sel = st.selectbox("Selecione a Mesa para auditar:", sorted(list(set(p_ab['mesa'].tolist()))))
        for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
            col1, col2 = st.columns(2)
            col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
            if col2.button("Deletar Item", key=f"cn_{it['id']}"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(it['produto_id'])])
                    for _, r in rc.iterrows(): 
                        cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])), emp_id, int(r['insumo_id'])))
                    cur.execute("DELETE FROM public.pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                    c.commit()
                st.success("Item removido e estoque recalculado!")
                st.rerun()
# ==============================================================================
# PAGES/GERENCIAL.PY - PARTE 2 DE 2: CADASTROS, RELATÓRIOS E FLUXOS FINAIS
# ==============================================================================

# --- ABA 2: CADASTRO EM MASSA ---
with subtabs[2]:
    st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
    st.write("Cole a sua lista abaixo seguindo o formato exato: **Nome, Categoria, Preço** (um por linha).")
    
    with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
        texto_produtos = st.text_area("Cole seus produtos aqui:", height=200, placeholder="Exemplo:\nCaipirinha, Drinks, 15.0\nHeineken, Cervejas, 12.0")
        if st.form_submit_button("🔥 Gravar Todos os Produtos") and texto_produtos.strip():
            linhas = texto_produtos.strip().split("\n")
            itens_gravados = 0
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for linha in linhas:
                    if "," in linha:
                        partes = linha.split(",")
                        if len(partes) == 3:
                            n_p, c_p, p_p = partes[0].strip(), partes[1].strip(), partes[2].strip()
                            cat_valida = [c for c in cats if c.lower() == c_p.lower()]
                            if n_p and cat_valida:
                                try:
                                    preco_float = float(p_p)
                                    cur.execute("""
                                        INSERT INTO public.produtos (empresa_id, nome, categoria, preco) VALUES (%s, %s, %s, %s) 
                                        ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco
                                    """, (emp_id, n_p, str(cat_valida[0]), preco_float))
                                    itens_gravados += 1
                                except ValueError: pass
                c.commit()
            if itens_gravados > 0:
                st.success(f"🚀 Sucesso! {itens_gravados} produtos processados e salvos!")
                st.rerun()

# --- ABA 3: FICHA TÉCNICA (RECEITAS) ---
with subtabs[3]:
    st.subheader("🔬 Montar Ficha Técnica (Até 4 Ingredientes)")
    if not df_prods.empty and not df_est.empty:
        lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
        lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
        d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
        d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
        
        with st.form("f_vinc_multi", clear_on_submit=True):
            p_sel = d_p[st.selectbox("Selecione o Produto final:", lista_prods, key="sel_prod_receita_base")]
            st.markdown("---")
            col1, col2 = st.columns(2); i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="p_i1"); q1 = col2.number_input("Qtd gasta 1:", min_value=0.0, step=5.0, key="p_q1")
            col3, col4 = st.columns(2); i2 = col3.selectbox("Ingrediente 2:", lista_insumos, key="p_i2"); q2 = col4.number_input("Qtd gasta 2:", min_value=0.0, step=5.0, key="p_q2")
            col5, col6 = st.columns(2); i3 = col5.selectbox("Ingrediente 3:", lista_insumos, key="p_i3"); q3 = col6.number_input("Qtd gasta 3:", min_value=0.0, step=5.0, key="p_q3")
            col7, col8 = st.columns(2); i4 = col7.selectbox("Ingrediente 4:", lista_insumos, key="p_i4"); q4 = col8.number_input("Qtd gasta 4:", min_value=0.0, step=5.0, key="p_q4")
            
            if st.form_submit_button("🔥 Gravar Receita Completa"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    for ing, qtd in [(i1, q1), (i2, q2), (i3, q3), (i4, q4)]:
                        if ing != "---" and qtd > 0:
                            cur.execute("""
                                INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) 
                                ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo
                            """, (emp_id, p_sel, d_i[ing], qtd))
                    c.commit()
                st.success("Ficha técnica configurada com sucesso!")
                st.rerun()
    else: st.info("Cadastre insumos e produtos na conta antes de estruturar receitas.")

# --- ABA 4: RELATÓRIOS ---
with subtabs[4]:
    st.subheader("📊 Resumo Financeiro Detalhado")
    vendas_df = pd.read_sql("""
        SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario 
        FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id 
        WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC
    """, conn, params=[emp_id])
    
    if vendas_df.empty: st.info("Nenhuma comanda histórica para esta empresa.")
    else:
        empresa_total, garcons_total, pendente_total = 0.0, 0.0, 0.0
        for mesa_id, grupo in vendas_df.groupby('mesa'):
            sub_mesa = float(grupo['subtotal'].sum())
            status_mesa = grupo['status'].iloc[0]
            taxa_marcada = int(grupo['taxa_paga'].iloc[0]) == 1
            if status_mesa == 'Finalizado (Pago)':
                empresa_total += sub_mesa
                if taxa_marcada: garcons_total += (sub_mesa * 0.10)
            else: pendente_total += sub_mesa
                
        col_emp, col_garc, col_pen = st.columns(3)
        col_emp.metric("💰 Faturamento Líquido", f"R$ {empresa_total:.2f}")
        col_garc.metric("🍹 Caixinha (10%)", f"R$ {garcons_total:.2f}")
        col_pen.metric("⚠️ Prejuízo (Calotes)", f"R$ {pendente_total:.2f}")
        st.markdown("---")
        df_vendas_visual = vendas_df.copy()
        df_vendas_visual.columns = ["Mesa/Comanda", "Produto", "Quantidade", "Preço Unitário", "Subtotal", "Status", "Taxa", "Horário"]
        st.dataframe(df_vendas_visual, use_container_width=True, hide_index=True)

# --- ABA 5: EXCLUSÃO ---
with subtabs[5]:
    st.subheader("🗑️ Remover Produtos ou Insumos do Sistema")
    col_del1, col_del2 = st.columns(2)
    with col_del1:
        if not df_prods.empty:
            prod_para_excluir = st.selectbox("Deletar Produto:", [r['nome'] for _, r in df_prods.iterrows()], key="del_prod_sel")
            if st.button("❌ Excluir Produto", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("DELETE FROM public.receitas WHERE empresa_id = %s AND produto_id = (SELECT id FROM public.produtos WHERE empresa_id = %s AND nome = %s)", (emp_id, emp_id, prod_para_excluir))
                    cur.execute("DELETE FROM public.produtos WHERE empresa_id = %s AND nome = %s", (emp_id, prod_para_excluir))
                    c.commit()
                st.success("Produto removido!"); st.rerun()
    with col_del2:
        if not df_est.empty:
            insumo_para_excluir = st.selectbox("Deletar Insumo:", [r['item'] for _, r in df_est.iterrows()], key="del_ins_sel")
            if st.button("❌ Excluir Insumo", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("DELETE FROM public.receitas WHERE empresa_id = %s AND insumo_id = (SELECT id FROM public.estoque WHERE empresa_id = %s AND item = %s)", (emp_id, emp_id, insumo_para_excluir))
                    cur.execute("DELETE FROM public.estoque WHERE empresa_id = %s AND item = %s", (emp_id, insumo_para_excluir))
                    c.commit()
                st.success("Insumo removido!"); st.rerun()

conn.close()
