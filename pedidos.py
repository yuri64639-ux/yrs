    yuri64639-ux
    yrs

Repository navigation

    Code
    Issues
    Pull requests
    Agents
    Actions
    Projects
    Security and quality
    Insights
    Settings

    yrs

/
in
main

    Edit
    Preview

Indent mode
Indent size
Line wrap mode
Editing pedidos.py file contents
354
355
356
357
358
359
360
361
362
363
364
365
366
367
368
369
370
371
372
373
374
375
376
377
378
379
380
381
382
383
384
385
386
387
388
389
390
391
392
393
394
395
396
397
398
399
400
401
402
403
404
405
406
407
408
409
410
411
412
413
414
415
416
                    with g_tab2:
                        if not lista_mesas_gerencia:
                            st.info("Nenhum ativo disponível para estorno.")
                        else:
                            mesa_estorno = st.selectbox("Selecione a Mesa:", options=lista_mesas_gerencia, key="sel_estorno_m")
                            cur.execute("SELECT id, produto_nome, quantidade_pedida FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_estorno,))
                            itens_estornar = cur.fetchall()
                            
                            opcoes_estorno = {f"{i['quantidade_pedida']}x {i['produto_nome']} (ID Ref: {i['id']})": i for i in itens_estornar}
                            if not opcoes_estorno:
                                st.info("Nenhum item em aberto nesta comanda.")
                            else:
                                item_sel_estorno = st.selectbox("Escolha o Lançamento Incorreto:", options=list(opcoes_estorno.keys()))
                                obj_estorno = opcoes_estorno[item_sel_estorno]
                                
                                if st.button("❌ Estornar Item e Reabastecer Estoque", type="primary", use_container_width=True):
                                    cur.execute("""
                                        SELECT f.insumo_id, f.quantidade 
                                        FROM ficha_tecnica f 
                                        JOIN produtos p ON f.produto_id = p.id 
                                        WHERE p.nome = %s LIMIT 6;
                                    """, (obj_estorno['produto_nome'],))
                                    ficha_estorno = cur.fetchall()
                                    
                                    for f_e in ficha_estorno:
                                        devolucao = (float(f_e['quantidade']) / 1000.0) * int(obj_estorno['quantidade_pedida'])
                                        cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual + %s WHERE id = %s;", (devolucao, f_e['insumo_id']))
                                        
                                    cur.execute("DELETE FROM pedidos_realizados WHERE id = %s;", (obj_estorno['id'],))
                                    conn.commit()
                                    st.success("Transação desfeita e inventário estornado!")
                                    time.sleep(0.4)
                                    st.rerun()
                                    
                    with g_tab3:
                        if not lista_mesas_gerencia:
                            st.info("Nenhum ativo disponível para transferência.")
                        else:
                            mesa_origem = st.selectbox("Mesa de Origem:", options=lista_mesas_gerencia, key="sel_trans_origem")
                            cur.execute("SELECT id, produto_nome, quantidade_pedida FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_origem,))
                            itens_trans = cur.fetchall()
                            
                            opcoes_trans = {f"{i['quantidade_pedida']}x {i['produto_nome']} (ID Ref: {i['id']})": i for i in itens_trans}
                            if not opcoes_trans:
                                st.info("Nenhum item ativo nesta comanda.")
                            else:
                                item_sel_trans = st.selectbox("Item a transferir:", options=list(opcoes_trans.keys()))
                                obj_trans = opcoes_trans[item_sel_trans]
                                mesa_destino = st.text_input("Número da Nova Mesa de Destino:")
                                
                                if st.button("🔄 Confirmar Transferência", type="primary", use_container_width=True):
                                    if not mesa_destino.strip():
                                        st.error("Erro: Identifique o destino.")
                                    else:
                                        File "/mount/src/yrs/pedidos.py", line 411
                                          time.sleep(0.5)
                                                         ^
SyntaxError: expected 'except' or 'finally' block
                                        cur.execute("UPDATE pedidos_realizados SET mesa_numero = %s WHERE id = %s;", (mesa_destino.strip(), obj_trans['id']))
                                        conn.commit()
                                        st.success(f"Item transferido de forma permanente para a {mesa_destino}!")
                                        time.sleep(0.5)

Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
