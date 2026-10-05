import streamlit as st
import pandas as pd

# --- RECEITAS MULTIPLAS (INDEX 3) ---
with subtabs[3]:
    st.subheader("🔬 Montar Ficha Técnica")
    
    if not df_prods.empty and not df_est.empty:
        lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
        lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
        
        d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
        d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
        
        with st.form("f_vinc_multi", clear_on_submit=True):
            p_sel = d_p[st.selectbox("Selecione o Produto:", lista_prods)]
            st.markdown("---")
            
            # Inputs estruturados em colunas
            col1, col2 = st.columns(2)
            i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="key_i1")
            q1 = col2.number_input("Qtd gasta 1 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="key_q1")
            
            col3, col4 = st.columns(2)
            i2 = col3.selectbox("Ingrediente 2:", lista_insumos, key="key_i2")
            q2 = col4.number_input("Qtd gasta 2 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="key_q2")
            
            col5, col6 = st.columns(2)
            i3 = col5.selectbox("Ingrediente 3:", lista_insumos, key="key_i3")
            q3 = col6.number_input("Qtd gasta 3 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="key_q3")
            
            if st.form_submit_button("🔥 Gravar Receita"):
                # Validação rápida de duplicatas no mesmo envio
                selecionados = [i for i in [i1, i2, i3] if i != "---"]
                if len(selecionados) != len(set(selecionados)):
                    st.error("Não selecione o mesmo ingrediente em campos diferentes.")
                else:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        
                        # Bloco de inserção otimizado
                        items_para_gravar = [(i1, q1), (i2, q2), (i3, q3)]
                        for insumo, qtd in items_para_gravar:
                            if insumo != "---" and qtd > 0:
                                cur.execute("""
                                    INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) 
                                    VALUES (%s, %s, %s) 
                                    ON CONFLICT (produto_id, insumo_id) 
                                    DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo
                                """, (p_sel, d_i[insumo], qtd))
                        
                        c.commit()
                    st.success("Receita configurada com sucesso!")
                    st.rerun()
    else:
        st.info("Cadastre produtos e insumos no estoque antes de criar uma ficha técnica.")

# --- 📊 RELATÓRIOS (INDEX 4) ---
with subtabs[4]:
    st.subheader("📊 Resumo Financeiro Detalhado")
    
    # Query de vendas ativa
    vendas_df = pd.read_sql("""
        SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, 
               (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario 
        FROM public.pedidos p 
        JOIN public.produtos pr ON p.produto_id = pr.id 
        WHERE p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') 
        ORDER BY p.horario DESC
    """, conn)
    
    if vendas_df.empty:
        st.info("Nenhuma comanda foi finalizada no sistema até o momento.")
    else:
        empresa_total = 0.0
        garcons_total = 0.0
        pendente_total = 0.0
        
        # Agrupamento correto por Mesa/Comanda
        for mesa_id, grupo in vendas_df.groupby('mesa'):
            sub_mesa = float(grupo['subtotal'].sum())
            status_mesa = grupo['status'].iloc[0]
            
            # Tratamento seguro do booleano/inteiro da taxa
            taxa_marcada = int(grupo['taxa_paga'].iloc[0] or 0) == 1
            
            if status_mesa == 'Finalizado (Pago)':
                empresa_total += sub_mesa
                if taxa_marcada:
                    garcons_total += (sub_mesa * 0.10)
            else:
                pendente_total += sub_mesa
                
        # Exibição dos KPIs cards
        col_emp, col_garc, col_pen = st.columns(3)
        col_emp.metric("💰 Faturamento Líquido (Empresa)", f"R$ {empresa_total:.2f}")
        col_garc.metric("🍹 Caixinha Acumulada (10%)", f"R$ {garcons_total:.2f}")
        col_pen.metric("⚠️ Total Perdido (Não Pago)", f"R$ {pendente_total:.2f}")
        
        st.markdown("---")
        st.subheader("📋 Histórico Detalhado de Vendas")
        
        df_vendas_visual = vendas_df.copy()
        df_vendas_visual.columns = [
            "Mesa/Comanda", "Produto", "Quantidade", "Preço Unitário", 
            "Subtotal", "Status", "Taxa (10%)", "Horário"
        ]
        df_vendas_visual["Taxa (10%)"] = df_vendas_visual["Taxa (10%)"].fillna(0).map({1: "Sim", 0: "Não"})
        
        # Formatação visual das colunas de dinheiro no dataframe
        st.dataframe(
            df_vendas_visual, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Preço Unitário": st.column_config.NumberColumn(format="R$ %.2f"),
                "Subtotal": st.column_config.NumberColumn(format="R$ %.2f")
            }
        )

# --- 🗑️ EXCLUIR ITENS DO CARDÁPIO OU ESTOQUE (INDEX 5) ---
with subtabs[5]:
    st.subheader("🗑️ Remover Produtos ou Insumos do Sistema")
    col_del1, col_del2 = st.columns(2)
    
    with col_del1:
        st.markdown("#### 🍔 Remover Produto do Cardápio")
        if not df_prods.empty:
            prod_para_excluir = st.selectbox(
                "Selecione o Produto para deletar permanentemente:", 
                [r['nome'] for _, r in df_prods.iterrows()], 
                key="del_prod_sel"
            )
            if st.button("❌ Excluir Produto", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    # Evita erro de FK limpando os históricos associados primeiro
                    cur.execute("DELETE FROM public.receitas WHERE produto_id = (SELECT id FROM public.produtos WHERE nome = %s)", (prod_para_excluir,))
                    cur.execute("DELETE FROM public.pedidos WHERE produto_id = (SELECT id FROM public.produtos WHERE nome = %s)", (prod_para_excluir,))
                    cur.execute("DELETE FROM public.produtos WHERE nome = %s", (prod_para_excluir,))
                    c.commit()
                st.success(f"'{prod_para_excluir}' removido com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")
            
    with col_del2:
        st.markdown("#### 📦 Remover Insumo do Estoque")
        if not df_est.empty:
            insumo_para_excluir = st.selectbox(
                "Selecione o Insumo para deletar permanentemente:", 
                [r['item'] for _, r in df_est.iterrows()], 
                key="del_ins_sel"
            )
            if st.button("❌ Excluir Insumo", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    # Limpa dependências na receita
                    cur.execute("DELETE FROM public.receitas WHERE insumo_id = (SELECT id FROM public.estoque WHERE item = %s)", (insumo_para_excluir,))
                    cur.execute("DELETE FROM public.estoque WHERE item = %s", (insumo_para_excluir,))
                    c.commit()
                st.success(f"'{insumo_para_excluir}' removido com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum insumo cadastrado.")
