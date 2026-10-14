        col_cancelar, col_fechar = st.columns(2)
        
        if col_cancelar.button("🗑️ Limpar Sacola", width='stretch'):
            st.session_state.carrinho = []
            st.rerun()
            
        # Aciona o fluxo de envio do pedido
        if col_fechar.button("✅ Confirmar e Enviar Pedido", type="primary", width='stretch'):
            if not mesa_ou_comanda:
                st.error("Por favor, preencha o número da Mesa ou Comanda antes de finalizar!")
            else:
                # Pergunta visual explícita adicionada antes da transação com o banco
                st.warning(f"❓ Confirmar fechamento da **{mesa_ou_comanda}** via **{metodo_pag}**?")
                
                try:
                    texto_itens = ", ".join([f"{qtd}x {nome}" for nome, qtd in resumo_carrinho.items()])
                    with ob_cx() as conn_venda:
                        if conn_venda:
                            with conn_venda.cursor() as cur:
                                try:
                                    # Tenta registrar usando a coluna 'mesa_comanda'
                                    cur.execute("""
                                        INSERT INTO pedidos (empresa_id, mesa_comanda, itens, total, metodo_pagamento)
                                        VALUES (%s, %s, %s, %s, %s);
                                    """, (empresa_id, mesa_ou_comanda, texto_itens, total_conta, metodo_pag))
                                except psycopg2.errors.UndefinedColumn:
                                    # Fallback automático se a coluna correta for 'mesa'
                                    conn_venda.rollback()
                                    cur.execute("""
                                        INSERT INTO pedidos (empresa_id, mesa, itens, total, metodo_pagamento)
                                        VALUES (%s, %s, %s, %s, %s);
                                    """, (empresa_id, mesa_ou_comanda, texto_itens, total_conta, metodo_pag))
                                
                                # Atualização e baixa de inventário
                                for item in st.session_state.carrinho:
                                    cur.execute("""
                                        UPDATE produtos 
                                        SET estoque = estoque - 1 
                                        WHERE id = %s AND empresa_id = %s;
                                    """, (item["id"], empresa_id))
                                    
                                conn_venda.commit()
                                
                            st.success(f"🚀 Pedido da {mesa_ou_comanda} computado com sucesso via {metodo_pag}!")
                            st.session_state.carrinho = []
                            st.rerun()
                except Exception as error:
                    st.error(f"Erro ao processar baixa de pedido: {error}")
