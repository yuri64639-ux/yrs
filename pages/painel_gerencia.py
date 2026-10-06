# ==============================================================================
# PAINEL GERENCIAL - PARTE 1: SEGURANÇA, CONEXÃO, ESTOQUE E CANCELAMENTOS
# ==============================================================================
import streamlit as st
import psycopg2
import pandas as pd

# Configuração global da página
st.set_page_config(page_title="Painel Gerencial", layout="centered")
ADMIN = "admin123"

# Fluxo de segurança e controle de sessão
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

# Conexão dinâmica com o Banco de Dados PostgreSQL
def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c:
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

conn = ob_cx()
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]

# Consultas globais de dados para alimentar os seletores
df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque ORDER BY item", conn)
df_prods = pd.read_sql("SELECT id, nome FROM public.produtos ORDER BY nome", conn)

subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])

# --- ESTOQUE (INDEX 0) ---
with subtabs:
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
                    cur.execute("INSERT INTO public.estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (n_i.strip(), q_i))
                    c.commit()
                st.success("Estoque updated!")
                st.rerun()

# --- CANCELAMENTOS (INDEX 1) ---
with subtabs:
    st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
    p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn)
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
                    rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", c, params=[int(it['produto_id'])])
                    for _, r in rc.iterrows(): 
                        cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE id = %s", ((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade']), int(r['insumo_id'])))
                    cur.execute("DELETE FROM public.pedidos WHERE id = %s", (int(it['id']),))
                    c.commit()
                st.success("Item removido e estoque devolvido!")
                st.rerun()
# ==============================================================================
# PAINEL GERENCIAL - PARTE 2: CADASTRO, RECEITAS (4 SLOTS), RELATÓRIOS E EXCLUSÃO
# ==============================================================================

# --- CADASTRO EM MASSA CORRIGIDO (INDEX 2) ---
with subtabs[2]: # CORREÇÃO AQUI: Especificado o índice 2 para a aba de cadastro
    st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
    st.write("Cole a sua lista abaixo seguindo o formato exato: **Nome, Categoria, Preço** (um produto por linha).")
    st.caption("Categorias aceitas: Drinks, Cervejas, Sem Álcool, Porções, Pratos Principais, Sobremesas")
    
    with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
        texto_produtos = st.text_area(
            "Cole seus produtos aqui:", 
            height=250, 
            placeholder="Exemplo:\nCaipirinha, Drinks, 15.0\nHeineken, Cervejas, 12.0\nBatata Frita, Porções, 35.0"
        )
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
                            # Limpa os espaços em branco de cada item individualmente
                            n_p = partes[0].strip()
                            c_p = partes[1].strip()
                            p_p = partes[2].strip()
                            
                            # Procura a categoria correspondente ignorando maiúsculas/minúsculas
                            cat_valida = [c for c in cats if c.lower() == c_p.lower()]
                            
                            if n_p and cat_valida:
                                try:
                                    preco_float = float(p_p)
                                    # Extrai a string pura evitando passar o objeto list ao banco
                                    categoria_final = str(cat_valida[0])
                                    
                                    cur.execute("""
                                        INSERT INTO public.produtos (nome, categoria, preco) 
                                        VALUES (%s, %s, %s) 
                                        ON CONFLICT (nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco
                                    """, (n_p, categoria_final, preco_float))
                                    itens_gravados += 1
                                except ValueError:
                                    pass
                c.commit()
            
            if itens_gravados > 0:
                st.success(f"🚀 Sucesso! {itens_gravados} produtos foram processados e salvos no banco!")
                st.rerun()
            else:
                st.error("❌ Nenhum produto cadastrado. Verifique se usou as vírgulas corretamente e se as categorias existem.")

# --- RECEITAS COM 4 INGREDIENTES (INDEX 3) ---
with subtabs[3]: # CORREÇÃO AQUI: Especificado o índice 3 para a aba de receitas
    st.subheader("🔬 Montar Ficha Técnica (Até 4 Ingredientes)")
    if not df_prods.empty and not df_est.empty:
        lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
        lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
        d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
        d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
        
        with st.form("f_vinc_multi", clear_on_submit=True):
            p_sel = d_p[st.selectbox("Selecione o Produto:", lista_prods, key="sel_prod_receita_base")]
            st.markdown("---")
            col1, col2 = st.columns(2); i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="i1"); q1 = col2.number_input("Qtd gasta 1 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q1")
            col3, col4 = st.columns(2); i2 = col3.selectbox("Ingrediente 2:", lista_insumos, key="i2"); q2 = col4.number_input("Qtd gasta 2 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q2")
            col5, col6 = st.columns(2); i3 = col5.selectbox("Ingrediente 3:", lista_insumos, key="i3"); q3 = col6.number_input("Qtd gasta 3 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q3")
            col7, col8 = st.columns(2); i4 = col7.selectbox("Ingrediente 4:", lista_insumos, key="i4"); q4 = col8.number_input("Qtd gasta 4 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q4")
            
            if st.form_submit_button("🔥 Gravar Receita"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    if i1 != "---" and q1 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i1], q1))
                    if i2 != "---" and q2 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i2], q2))
                    if i3 != "---" and q3 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i3], q3))
                    if i4 != "---" and q4 > 0: cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i4], q4))
                    c.commit()
                st.success("Receita configurada com sucesso!")
                st.rerun()

# --- 📊 RELATÓRIOS (INDEX 4) ---
with subtabs[4]: # CORREÇÃO AQUI: Especificado o índice 4 para a aba de relatórios
    st.subheader("📊 Resumo Financeiro Detalhado")
    vendas_df = pd.read_sql("SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC", conn)
            
    if vendas_df.empty:
        st.info("Nenhuma comanda foi finalizada no sistema até o momento.")
    else:
        empresa_total, garcons_total, pendente_total = 0.0, 0.0, 0.0
        for mesa_id, grupo in vendas_df.groupby('mesa'):
            sub_mesa = float(grupo['subtotal'].sum())
            status_mesa = grupo['status'].iloc[0]
            taxa_marcada = int(grupo['taxa_paga'].iloc[0]) == 1
            if status_mesa == 'Finalizado (Pago)':
                empresa_total += sub_mesa
                if taxa_marcada: garcons_total += (sub_mesa * 0.10)
            else:
                pendente_total += sub_mesa
                        
        col_emp, col_garc, col_pen = st.columns(3)
        col_emp.metric("💰 Faturamento Líquido", f"R$ {empresa_total:.2f}")
        col_garc.metric("🍹 Caixinha (10%)", f"R$ {garcons_total:.2f}")
        col_pen.metric("⚠️ Perdas (Não Pago)", f"R$ {pendente_total:.2f}")
        st.markdown("---")
        st.dataframe(vendas_df, use_container_width=True, hide_index=True)

# --- 🗑️ EXCLUIR ITENS (INDEX 5) ---
with subtabs[5]: # CORREÇÃO AQUI: Especificado o índice 5 para a aba de exclusão
    st.subheader("🗑️ Remover Produtos ou Insumos")
    col_del1, col_del2 = st.columns(2)
            
    with col_del1:
        st.markdown("#### 🍔 Remover Produto do Cardápio")
        if not df_prods.empty:
            prod_para_excluir = st.selectbox("Deletar Produto do Cardápio:", [r['nome'] for _, r in df_prods.iterrows()], key="del_prod_sel")
            if st.button("❌ Excluir Produto", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("DELETE FROM public.receitas WHERE produto_id = (SELECT id FROM public.produtos WHERE nome = %s)", (prod_para_excluir,))
                    cur.execute("DELETE FROM public.produtos WHERE nome = %s", (prod_para_excluir,))
                    c.commit()
                st.success(f"'{prod_para_excluir}' removido!")
                st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")
                
    with col_del2:
        st.markdown("#### 📦 Remover Insumo do Estoque")
        if not df_est.empty:
            insumo_para_excluir = st.selectbox("Deletar Insumo do Estoque:", [r['item'] for _, r in df_est.iterrows()], key="del_ins_sel")
            if st.button("❌ Excluir Insumo", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("DELETE FROM public.receitas WHERE insumo_id = (SELECT id FROM public.estoque WHERE item = %s)", (insumo_para_excluir,))
                    cur.execute("DELETE FROM public.estoque WHERE item = %s", (insumo_para_excluir,))
                    c.commit()
                st.success(f"'{insumo_para_excluir}' removido com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum insumo cadastrado.")
