if st.session_state.carrinho:
    st.markdown("---")
    st.markdown(f"📋 **Resumo do Pedido Atual (Mesa: {m}):**")
    total_carrinho = 0.0
    
    # Criamos uma variável para monitorar se algum item deve ser removido
    item_para_remover = None
    
    for idx_c, item in enumerate(st.session_state.carrinho):
        sub_item = item['qtd'] * item['preco']
        total_carrinho += sub_item
        col_txt, col_btn = st.columns([4, 1])
        col_txt.write(f"▪️ **{item['qtd']}x** {item['nome']} [{item['categoria']}] — R$ {sub_item:.2f}")
        
        # Se o botão for clicado, apenas guardamos o índice
        if col_btn.button("🗑️ Remover", key=f"rem_{idx_c}"):
            item_para_remover = idx_c

    # Se um botão de remover foi acionado, removemos FORA do loop e reiniciamos
    if item_para_remover is not None:
        st.session_state.carrinho.pop(item_para_remover)
        st.rerun()
            
    st.markdown(f"### 🧾 Total Parcial: R$ {total_carrinho:.2f}")
    col_cancelar, col_enviar = st.columns(2)
    if col_cancelar.button("❌ Limpar Todo o Rascunho"):
        st.session_state.carrinho = []
        st.rerun()
        
    if col_enviar.button("🔥 LANÇAR COMANDA COMPLETA", type="primary"):
        pedidos_finais = []
        estoque_geral_ok = True
        
        for item in st.session_state.carrinho:
            rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.item, e.quantidade FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn, params=[item['id']])
            for _, r_ins in rec.iterrows():
                qtd_necessaria = (float(r_ins['qtd_insumo']) / 1000.0) * item['qtd']
                if r_ins['quantidade'] < qtd_necessaria:
                    st.error(f"🚨 Estoque insuficiente de '{r_ins['item']}' para fazer '{item['nome']}'!")
                    estoque_geral_ok = False
            if estoque_geral_ok:
                pedidos_finais.append((item['id'], item['qtd']))
        
        if estoque_geral_ok and pedidos_finais:
            with ob_cx() as c_massa, c_massa.cursor() as cur_trans:
                cur_trans.execute("SET search_path TO public;")
                for pid, qtd in pedidos_finais:
                    cur_trans.execute("INSERT INTO public.pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m.strip(), pid, qtd, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    rec = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", conn, params=[pid])
                    for _, r_ins in rec.iterrows():
                        qtd_convertida = float((float(r_ins['qtd_insumo']) / 1000.0) * qtd)
                        cur_trans.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (qtd_convertida, int(r_ins['insumo_id'])))
                c_massa.commit()
            st.success(f"✅ Sucesso! Comanda da mesa {m.strip()} enviada!")
            st.session_state.carrinho = []
            st.rerun()

with tabs[1]:
    st.subheader("🎟️ Contas Abertas")
    peds = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as sub FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    if peds.empty: 
        st.info("Nenhuma comanda aberta.")
    else:
        for m_aberta in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m_aberta]
            sub = float(itens['sub'].sum())
            with st.expander(f"📋 Mesa {m_aberta} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): 
                    st.write(f"▪️ {i['quantidade']}x {i['nome']} (R$ {i['sub']:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa de Serviço (10%)", value=True, key=f"t_{m_aberta}") else 0.0
                st.markdown(f"### Total Final: R$ {sub + tx:.2f}")
                pago_opcao = st.radio("O cliente pagou a conta?", ["Sim", "Não"], key=f"pago_{m_aberta}", horizontal=True)
                if st.button(f"💵 Fechar Conta {m_aberta}", key=f"b_{m_aberta}"):
                    status_final = 'Finalizado (Pago)' if pago_opcao == "Sim" else 'Fechado (Não Pago)'
                    with ob_cx() as c_fechar, c_fechar.cursor() as cur_fechar:
                        cur_fechar.execute("SET search_path TO public;")
                        cur_fechar.execute("UPDATE public.pedidos SET status = %s, taxa_paga = %s, pago = %s WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (status_final, 1 if tx > 0 else 0, pago_opcao, m_aberta))
                        c_fechar.commit()
                    st.success(f"Conta da mesa {m_aberta} fechada!")
                    st.rerun()

