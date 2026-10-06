# ==============================================================================
# PARTE 2: INTERFACE DE LANÇAMENTO DE PEDIDOS E FECHAMENTO DE CONTAS
# ==============================================================================
with tabs[0]:
    st.subheader("📝 Montar Comanda / Pedido")
    
    m = st.text_input("Mesa / Comanda:", value=st.session_state.get("mesa_atual", ""), key="mesa_global_input")
    st.session_state["mesa_atual"] = m
    
    busca_nome = st.text_input("🔍 Digite o nome do produto:", key="lupa_busca_topo_absoluto").strip()
    dp = {}
    
    if busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE LOWER(nome) LIKE LOWER(%s) ORDER BY nome", conn, params=[f"%{busca_nome}%"])
        if not prods_filtrados.empty:
            dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
            ps = st.selectbox("Confirmar Item selecionado:", list(dp.keys()), key="select_busca_lupa")
        else:
            st.warning("Nenhum item encontrado com esse nome.")
            
    st.markdown("---")
    st.markdown("**Ou navegue pelas Categorias:**")
    cat_sel = st.selectbox("Selecione a Categoria para listar:", cats, key="categoria_filtro")
    
    if not busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE categoria = %s ORDER BY nome", conn, params=[cat_sel])
        if not prods_filtrados.empty:
            dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
            ps = st.selectbox("Confirmar Item filtrado por Categoria:", list(dp.keys()), key="select_cat_refinado")
        else:
            st.warning("Nenhum item encontrado nesta categoria.")
            
    if dp:
        q = st.number_input("Quantidade:", min_value=1, value=1, key="quantidade_item")
        if st.button("➕ Adicionar ao Pedido", type="secondary"):
            if not m.strip():
                st.error("Por favor, digite o número da Mesa / Comanda antes de adicionar itens!")
            else:
                chave_sel = st.session_state.get("select_busca_lupa") if busca_nome else st.session_state.get("select_cat_refinado")
                if chave_sel in dp:
                    item_escolhido = dp[chave_sel]
                    st.session_state.carrinho.append({
                        "id": int(item_escolhido["id"]), "nome": item_escolhido["nome"],
                        "categoria": item_escolhido["categoria"], "qtd": int(q), "preco": float(item_escolhido["preco"])
                    })
                    st.success(f"{q}x {item_escolhido['nome']} adicionado ao rascunho!")
                    st.rerun()

    if st.session_state.carrinho:
        st.markdown("---")
        st.markdown(f"📋 **Resumo do Pedido Atual (Mesa: {m}):**")
        total_carrinho = 0.0
        for idx_c, item in enumerate(st.session_state.carrinho):
            sub_item = item["qtd"] * item["preco"]
            total_carrinho += sub_item
            col_txt, col_btn = st.columns([4, 1])
            col_txt.write(f"▪️ **{item['qtd']}x** {item['nome']} [{item['categoria']}] — R$ {sub_item:.2f}")
            if col_btn.button("🗑️ Remover", key=f"rem_{idx_c}"):
                st.session_state.carrinho.pop(idx_c)
                st.rerun()
                
        st.markdown(f"### 🧾 Total Parcial: R$ {total_carrinho:.2f}")
        col_cancelar, col_enviar = st.columns(2)
        if col_cancelar.button("❌ Limpar Todo o Rascunho"):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_enviar.button("🔥 LANÇAR COMANDA COMPLETA", type="primary"):
            estoque_geral_ok = True
            lista_ids = [item["id"] for item in st.session_state.carrinho]
            
            df_receitas = pd.read_sql("SELECT r.produto_id, r.insumo_id, r.qtd_insumo, e.item, e.quantidade as qtd_atual FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id IN %s", conn, params=[tuple(lista_ids)])
            
            est_simulado = {}
            for _, r_ins in df_receitas.iterrows():
                if r_ins["insumo_id"] not in est_simulado:
                    est_simulado[r_ins["insumo_id"]] = {"nome": r_ins["item"], "saldo": float(r_ins["qtd_atual"])}
            
            for item in st.session_state.carrinho:
                recs_prod = df_receitas[df_receitas["produto_id"] == item["id"]]
                for _, r_ins in recs_prod.iterrows():
                    qtd_total_gasta = (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                    est_simulado[r_ins["insumo_id"]]["saldo"] -= qtd_total_gasta
                    if est_simulado[r_ins["insumo_id"]]["saldo"] < 0:
                        st.error(f"❌ Estoque insuficiente de: {est_simulado[r_ins['insumo_id']]['nome']}")
                        estoque_geral_ok = False
            
            if estoque_geral_ok:
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    hr = datetime.now().strftime("%d/%m/%Y %H:%M")
                    for item in st.session_state.carrinho:
                        cur.execute("INSERT INTO public.pedidos (mesa, produto_id, quantity, status, horario) VALUES (%s, %s, %s, 'Pendente', %s)", (m.strip(), item["id"], item["qtd"], hr))
                        recs_prod = df_receitas[df_receitas["produto_id"] == item["id"]]
                        for _, r_ins in recs_prod.iterrows():
                            qtd_total_gasta = (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                            cur.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (qtd_total_gasta, int(r_ins["insumo_id"])))
                    c.commit()
                st.success("🚀 Pedido lançado com sucesso e estoque atualizado!")
                st.session_state.carrinho = []
                st.rerun()

with tabs[1]:
    st.subheader("💵 Gerenciamento de Contas e Mesas")
    df_pedidos = pd.read_sql("SELECT p.id, p.mesa, pr.nome, pr.preco, p.quantidade, p.status, p.taxa_paga FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    
    if df_pedidos.empty:
        st.info("Nenhuma mesa com consumo aberto.")
    else:
        mesas_abertas = sorted(list(set(df_pedidos["mesa"].tolist())))
        m_conta = st.selectbox("Selecione a Mesa para fechar:", mesas_abertas, key="selecao_mesa_conta")
        
        pedidos_da_mesa = df_pedidos[df_pedidos["mesa"] == m_conta]
        total_mesa = 0.0
        st.markdown(f"### 📋 Extrato da Comanda: {m_conta}")
        
        for _, row in pedidos_da_mesa.iterrows():
            sub = row["quantidade"] * row["preco"]
            total_mesa += sub
            st.write(f"▪️ {row['quantidade']}x {row['nome']} — R$ {sub:.2f} ({row['status']})")
        
        taxa = total_mesa * 0.10
        st.markdown(f"**Subtotal:** R$ {total_mesa:.2f}")
        st.markdown(f"**Taxa de Serviço (10%):** R$ {taxa:.2f}")
        st.markdown(f"## Total Geral: R$ {total_mesa + taxa:.2f}")
        
        col_paga, col_npaga = st.columns(2)
        if col_paga.button("✅ Confirmar Pagamento Completo", type="primary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = 1 WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (m_conta,))
                c.commit()
            st.success(f"Mesa {m_conta} finalizada com sucesso!")
            st.rerun()
            
        if col_npaga.button("⚠️ Fechar como Não Pago / Calote", type="secondary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("UPDATE public.pedidos SET status = 'Fechado (Não Pago)', taxa_paga = 0 WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (m_conta,))
                c.commit()
            st.warning(f"Mesa {m_conta} arquivada como prejuízo.")
            st.rerun()
            # ==============================================================================
# PARTE 2: INTERFACE DE LANÇAMENTO DE PEDIDOS E FECHAMENTO DE CONTAS
# ==============================================================================
with tabs[0]:
    st.subheader("📝 Montar Comanda / Pedido")
    
    m = st.text_input("Mesa / Comanda:", value=st.session_state.get("mesa_atual", ""), key="mesa_global_input")
    st.session_state["mesa_atual"] = m
    
    busca_nome = st.text_input("🔍 Digite o nome do produto:", key="lupa_busca_topo_absoluto").strip()
    dp = {}
    
    if busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE LOWER(nome) LIKE LOWER(%s) ORDER BY nome", conn, params=[f"%{busca_nome}%"])
        if not prods_filtrados.empty:
            dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
            ps = st.selectbox("Confirmar Item selecionado:", list(dp.keys()), key="select_busca_lupa")
        else:
            st.warning("Nenhum item encontrado com esse nome.")
            
    st.markdown("---")
    st.markdown("**Ou navegue pelas Categorias:**")
    cat_sel = st.selectbox("Selecione a Categoria para listar:", cats, key="categoria_filtro")
    
    if not busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE categoria = %s ORDER BY nome", conn, params=[cat_sel])
        if not prods_filtrados.empty:
            dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
            ps = st.selectbox("Confirmar Item filtrado por Categoria:", list(dp.keys()), key="select_cat_refinado")
        else:
            st.warning("Nenhum item encontrado nesta categoria.")
            
    if dp:
        q = st.number_input("Quantidade:", min_value=1, value=1, key="quantidade_item")
        if st.button("➕ Adicionar ao Pedido", type="secondary"):
            if not m.strip():
                st.error("Por favor, digite o número da Mesa / Comanda antes de adicionar itens!")
            else:
                chave_sel = st.session_state.get("select_busca_lupa") if busca_nome else st.session_state.get("select_cat_refinado")
                if chave_sel in dp:
                    item_escolhido = dp[chave_sel]
                    st.session_state.carrinho.append({
                        "id": int(item_escolhido["id"]), "nome": item_escolhido["nome"],
                        "categoria": item_escolhido["categoria"], "qtd": int(q), "preco": float(item_escolhido["preco"])
                    })
                    st.success(f"{q}x {item_escolhido['nome']} adicionado ao rascunho!")
                    st.rerun()

    if st.session_state.carrinho:
        st.markdown("---")
        st.markdown(f"📋 **Resumo do Pedido Atual (Mesa: {m}):**")
        total_carrinho = 0.0
        for idx_c, item in enumerate(st.session_state.carrinho):
            sub_item = item["qtd"] * item["preco"]
            total_carrinho += sub_item
            col_txt, col_btn = st.columns([4, 1])
            col_txt.write(f"▪️ **{item['qtd']}x** {item['nome']} [{item['categoria']}] — R$ {sub_item:.2f}")
            if col_btn.button("🗑️ Remover", key=f"rem_{idx_c}"):
                st.session_state.carrinho.pop(idx_c)
                st.rerun()
                
        st.markdown(f"### 🧾 Total Parcial: R$ {total_carrinho:.2f}")
        col_cancelar, col_enviar = st.columns(2)
        if col_cancelar.button("❌ Limpar Todo o Rascunho"):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_enviar.button("🔥 LANÇAR COMANDA COMPLETA", type="primary"):
            estoque_geral_ok = True
            lista_ids = [item["id"] for item in st.session_state.carrinho]
            
            df_receitas = pd.read_sql("SELECT r.produto_id, r.insumo_id, r.qtd_insumo, e.item, e.quantidade as qtd_atual FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id IN %s", conn, params=[tuple(lista_ids)])
            
            est_simulado = {}
            for _, r_ins in df_receitas.iterrows():
                if r_ins["insumo_id"] not in est_simulado:
                    est_simulado[r_ins["insumo_id"]] = {"nome": r_ins["item"], "saldo": float(r_ins["qtd_atual"])}
            
            for item in st.session_state.carrinho:
                recs_prod = df_receitas[df_receitas["produto_id"] == item["id"]]
                for _, r_ins in recs_prod.iterrows():
                    qtd_total_gasta = (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                    est_simulado[r_ins["insumo_id"]]["saldo"] -= qtd_total_gasta
                    if est_simulado[r_ins["insumo_id"]]["saldo"] < 0:
                        st.error(f"❌ Estoque insuficiente de: {est_simulado[r_ins['insumo_id']]['nome']}")
                        estoque_geral_ok = False
            
            if estoque_geral_ok:
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    hr = datetime.now().strftime("%d/%m/%Y %H:%M")
                    for item in st.session_state.carrinho:
                        cur.execute("INSERT INTO public.pedidos (mesa, produto_id, quantidade, status, horario) VALUES (%s, %s, %s, 'Pendente', %s)", (m.strip(), item["id"], item["qtd"], hr))
                        recs_prod = df_receitas[df_receitas["produto_id"] == item["id"]]
                        for _, r_ins in recs_prod.iterrows():
                            qtd_total_gasta = (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                            cur.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (qtd_total_gasta, int(r_ins["insumo_id"])))
                    c.commit()
                st.success("🚀 Pedido lançado com sucesso!")
                st.session_state.carrinho = []
                st.rerun()

with tabs[1]:
    st.subheader("💵 Gerenciamento de Contas e Mesas")
    df_pedidos = pd.read_sql("SELECT p.id, p.mesa, pr.nome, pr.preco, p.quantidade, p.status, p.taxa_paga FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    
    if df_pedidos.empty:
        st.info("Nenhuma mesa com consumo aberto.")
    else:
        mesas_abertas = sorted(list(set(df_pedidos["mesa"].tolist())))
        m_conta = st.selectbox("Selecione a Mesa para fechar:", mesas_abertas, key="selecao_mesa_conta")
        
        pedidos_da_mesa = df_pedidos[df_pedidos["mesa"] == m_conta]
        total_mesa = 0.0
        st.markdown(f"### 📋 Extrato da Comanda: {m_conta}")
        
        for _, row in pedidos_da_mesa.iterrows():
            sub = row["quantidade"] * row["preco"]
            total_mesa += sub
            st.write(f"▪️ {row['quantidade']}x {row['nome']} — R$ {sub:.2f} ({row['status']})")
        
        taxa = total_mesa * 0.10
        st.markdown(f"**Subtotal:** R$ {total_mesa:.2f}")
        st.markdown(f"**Taxa de Serviço (10%):** R$ {taxa:.2f}")
        st.markdown(f"## Total Geral: R$ {total_mesa + taxa:.2f}")
        
        col_paga, col_npaga = st.columns(2)
        if col_paga.button("✅ Confirmar Pagamento Completo", type="primary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = 1 WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (m_conta,))
                c.commit()
            st.success(f"Mesa {m_conta} finalizada com sucesso!")
            st.rerun()
            
        if col_npaga.button("⚠️ Fechar como Não Pago / Calote", type="secondary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("UPDATE public.pedidos SET status = 'Fechado (Não Pago)', taxa_paga = 0 WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (m_conta,))
                c.commit()
            st.warning(f"Mesa {m_conta} arquivada como prejuízo.")
            st.rerun()
