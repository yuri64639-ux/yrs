import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Painel Gerencial", layout="centered")
ADMIN = "admin123"

if "ok_g" not in st.session_state: st.session_state["ok_g"] = False
if not st.session_state["ok_g"]:
    with st.form("f_adm"):
        st.subheader("🔒 Acesso Restrito da Gerência")
        if st.form_submit_button("🔓 Liberar") and st.text_input("Senha Master:", type="password") == ADMIN:
            st.session_state["ok_g"] = True; st.rerun()
    st.stop()

if st.button("🔒 Bloquear Painel"): st.session_state["ok_g"] = False; st.rerun()

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    return psycopg2.connect(c["url"]) if "url" in c else psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

conn = ob_cx()
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque ORDER BY item", conn)
df_prods = pd.read_sql("SELECT id, nome, categoria, preco FROM public.produtos ORDER BY nome", conn)

subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro em Massa", "🔬 Receitas em Massa", "📊 Relatórios", "🗑️ Excluir"])

# --- ESTOQUE (INDEX 0) ---
with subtabs[0]:
    st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
    df_est_visual = df_est.copy()
    if not df_est_visual.empty: df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual (L / Kg)"]
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
                st.success("Estoque atualizado!"); st.rerun()

# --- CANCELAMENTOS (INDEX 1) ---
with subtabs[1]:
    st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
    p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn)
    if p_ab.empty: st.info("Nenhuma comanda aberta para cancelamento.")
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
                st.success("Item removido!"); st.rerun()

# --- CADASTRO EM MASSA (INDEX 2) ---
with subtabs[2]:
    st.subheader("🍔 Cadastrar Vários Produtos de Uma Vez")
    st.info("💡 Preencha a tabela abaixo como uma planilha. Clique nas linhas de baixo para adicionar mais itens.")
    
    # Cria uma estrutura vazia para inserção de dados em massa
    df_novo_prod = pd.DataFrame([{"Nome do Produto": "", "Categoria": "Drinks", "Preço de Venda (R$)": 15.0}])
    grid_prods = st.data_editor(df_novo_prod, num_rows="dynamic", use_container_width=True, key="grid_p", column_config={
        "Categoria": st.column_config.SelectboxColumn(options=cats)
    })
    
    if st.button("🔥 Salvar Todos os Produtos Cadastrados", type="primary"):
        salvos = 0
        with ob_cx() as c, c.cursor() as cur:
            cur.execute("SET search_path TO public;")
            for _, row in grid_prods.iterrows():
                nome = str(row["Nome do Produto"]).strip()
                cat = str(row["Categoria"])
                preco = float(row["Preço de Venda (R$)"])
                if nome:
                    cur.execute("INSERT INTO public.produtos (nome, categoria, preco) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (nome, cat, preco))
                    salvos += 1
            c.commit()
        if salvos > 0:
            st.success(f"Sucesso! {salvos} produtos foram gravados no cardápio de uma só vez.")
            st.rerun()
# --- RECEITAS EM MASSA (INDEX 3) ---
with subtabs[3]:
    st.subheader("🔬 Vincular Receitas / Fichas Técnicas em Massa")
    if not df_prods.empty and not df_est.empty:
        st.info("💡 Insira o Produto, o Insumo do estoque e a quantidade gasta em ml ou gramas.")
        
        lista_prods = sorted(list(df_prods['nome']))
        lista_insumos = sorted(list(df_est['item']))
        
        df_nova_rec = pd.DataFrame([{"Produto do Cardápio": lista_prods[0], "Ingrediente/Insumo": lista_insumos[0], "Qtd Gasta (ml ou g)": 50.0}])
        grid_refeitas = st.data_editor(df_nova_rec, num_rows="dynamic", use_container_width=True, key="grid_r", column_config={
            "Produto do Cardápio": st.column_config.SelectboxColumn(options=lista_prods),
            "Ingrediente/Insumo": st.column_config.SelectboxColumn(options=lista_insumos)
        })
        
        if st.button("🔥 Gravar Todas as Receitas Juntas", type="primary"):
            recs_salvas = 0
            d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
            d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
            
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for _, row in grid_refeitas.iterrows():
                    p_nome = row["Produto do Cardápio"]
                    i_nome = row["Ingrediente/Insumo"]
                    qtd = float(row["Qtd Gasta (ml ou g)"])
                    if p_nome in d_p and i_nome in d_i and qtd > 0:
                        cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (d_p[p_nome], d_i[i_nome], qtd))
                        recs_salvas += 1
                c.commit()
            if recs_salvas > 0:
                st.success(f"Sucesso! {recs_salvas} vínculos de receita foram atualizados.")
                st.rerun()
    else: st.warning("Cadastre produtos e insumos primeiro.")

# --- 📊 RELATÓRIOS (INDEX 4) ---
with subtabs[4]:
    st.subheader("📊 Resumo Financeiro Detalhado")
    vendas_df = pd.read_sql("""
        SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario 
        FROM public.pedidos p 
        JOIN public.produtos pr ON p.produto_id = pr.id 
        WHERE p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)')
        ORDER BY p.horario DESC
    """, conn)
    
    if vendas_df.empty: st.info("Nenhuma comanda foi finalizada no sistema até o momento.")
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
        col_emp.metric("💰 Faturamento Líquido (Empresa)", f"R$ {empresa_total:.2f}")
        col_garc.metric("🍹 Caixinha Acumulada (10%)", f"R$ {garcons_total:.2f}")
        col_pen.metric("⚠️ Total Perdido (Não Pago)", f"R$ {pendente_total:.2f}")
        st.markdown(f"**📈 Caixa Bruto Total Movimentado: R$ {empresa_total + garcons_total:.2f}**")
        
        visual_vendas = vendas_df.copy()
        visual_vendas['taxa_paga'] = visual_vendas['taxa_paga'].map({1: "Inclusa (10%)", 0: "Isenta"})
        visual_vendas.columns = ["Mesa/Comanda", "Item Vendido", "Quantidade", "Preço Un. (R$)", "Subtotal (R$)", "Situação", "Taxa", "Data/Horário"]
        st.dataframe(visual_vendas, use_container_width=True, hide_index=True)

# --- EXCLUIR (INDEX 5) ---
with subtabs[5]:
    st.subheader("🗑 Excluir do Menu/Estoque")
    if not df_prods.empty:
        p_ex = st.selectbox("Remover do Cardápio:", ["---"] + list(df_prods['nome']))
        if p_ex != "---" and st.button("❌ Deletar Produto"):
            id_p = int(df_prods[df_prods['nome'] == p_ex]['id'].values[0])
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("DELETE FROM public.receitas WHERE produto_id = %s", (id_p,))
                cur.execute("DELETE FROM public.produtos WHERE id = %s", (id_p,))
                c.commit()
            st.success("Removido!"); st.rerun()
    if not df_est.empty:
        i_ex = st.selectbox("Remover do Estoque:", ["---"] + list(df_est['item']))
        if i_ex != "---" and st.button("❌ Deletar Insumo"):
            id_i = int(df_est[df_est['item'] == i_ex]['id'].values[0])
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("DELETE FROM public.receitas WHERE insumo_id = %s", (id_i,))
                cur.execute("DELETE FROM public.estoque WHERE id = %s", (id_i,))
                c.commit()
            st.success("Insumo removido!"); st.rerun()
