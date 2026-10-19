

[     UTC     ] Logs for cepo3eospdnckk2eqpsq2g.streamlit.app/

────────────────────────────────────────────────────────────────────────────────────────

[14:52:53] 🚀 Starting up repository: 'yrs', branch: 'main', main module: 'pedidos.py'

[14:52:53] 🐙 Cloning repository...

[14:52:54] 🐙 Cloning into '/mount/src/yrs'...

[14:52:54] 🐙 Cloned repository!

[14:52:54] 🐙 Pulling code changes from Github...

[14:52:56] 📦 Processing dependencies...

──────────────────────────────────────── uv ───────────────────────────────────────────

Using uv pip install.

Using Python 3.14.8 environment at /home/adminuser/venv

Resolved 5 packages in 249ms

Prepared 5 packages in 755ms

Installed 5 packages in 70ms

 + numpy==2.5.4

 [2026-10-19 14:52:57.538423] + pandas==3.0.6

 + psycopg2-binary==2.9.13

 + python-dateutil==2.9.0.post0

 + six==1.17.0

Checking if Streamlit is installed

Installing rich for an improved exception logging

Using uv pip install.

Using Python 3.14.8 environment at /home/adminuser/venv

Resolved 4 packages in 120ms

Prepared 4 packages in 128ms

Installed 4 packages in 19ms

 + markdown-it-py==4.2.0

 + mdurl==0.1.2

 + pygments==2.21.0

 + rich==15.0.0

────────────────────────────────────────────────────────────────────────────────────────

[14:52:59] 🐍 Python dependencies were installed from /mount/src/yrs/requirements.txt using uv.

Check if streamlit is installed

──────────────────────────────── Installing Streamlit ──────────────────────────────────

Using uv pip install.

Using Python 3.14.8 environment at /home/adminuser/venv

Resolved 34 packages in 421ms

Prepared 30 packages in 1.34s

Installed 30 packages in 31ms

 + altair==6.3.0

 + anyio==4.15.1

 + attrs==26.1.0

 + certifi==2026.10.18

 + charset-normalizer==3.5.2

 + click==8.5.0

 + h11==0.16.0

 + idna[2026-10-19 14:53:01.956425] ==3.20

 + itsdangerous==2.2.0

 + jinja2==3.1.6

 + jsonschema==4.26.0

 + jsonschema-specifications==2025.9.1

 + markupsafe==3.0.4[2026-10-19 14:53:01.956668] 

 + narwhals==2.27.1

 + packaging==26.3

 + pillow==12.3.0

 + protobuf==7.36.2

 + pyarrow[2026-10-19 14:53:01.957056] ==26.0.0

 + pydeck==0.9.3

 + python-multipart==0.0.32

 + referencing==0.37.0

 + requests==2.34.2

 + rpds-py==2026.9.1

 + starlette[2026-10-19 14:53:01.957385] ==1.9.0

 + streamlit==1.66.0

 + typing-extensions==4.16.0

 + urllib3==2.8.0

 + uvicorn==0.54.0[2026-10-19 14:53:01.957570] 

 + watchdog==6.0.0

 + websockets==17.2

────────────────────────────────────────────────────────────────────────────────────────

[14:53:02] 📦 Processed dependencies!

2026-10-19 14:53:05.034 Uvicorn server started on :::8501

2026-10-19 14:53:09.833 Script compilation error

Traceback (most recent call last):

  File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 743, in _run_script

    code = self._script_cache.get_bytecode(script_path)

  File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/scriptrunner/script_cache.py", line 72, in get_bytecode

    filebody = magic.add_magic(filebody, script_path)

  File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/scriptrunner/magic.py", line 44, in add_magic

    tree = ast.parse(code, script_path, "exec")

  File "/usr/local/lib/python3.14/ast.py", line 46, in parse

    return compile(source, filename, mode, flags,

                   _feature_version=feature_version, optimize=optimize)

  File "/mount/src/yrs/pedidos.py", line 55

    conn.close()if not produtos_filtrados:

                                         ^

SyntaxError: invalid syntax

2026-10-19 14:53:11.001 Script compilation error

Traceback (most recent call last):

  File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 743, in _run_script

    code = self._script_cache.get_bytecode(script_path)

  File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/scriptrunner/script_cache.py", line 72, in get_bytecode

    filebody = magic.add_magic(filebody, script_path)

  File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/scriptrunner/magic.py", line 44, in add_magic

    tree = ast.parse(code, script_path, "exec")

  File "/usr/local/lib/python3.14/ast.py", line 46, in parse

    return compile(source, filename, mode, flags,

                   _feature_version=feature_version, optimize=optimize)

  File "/mount/src/yrs/pedidos.py", line 55

    conn.close()if not produtos_filtrados:

                                         ^

SyntaxError: invalid syntax

principal
yuri64639-ux/yrs/main/pedidos.py
if not produtos_filtrados:
    st.warning("Nenhum produto encontrado no cardápio.")
else:
    for prod in produtos_filtrados:
        col_n, col_p, col_q, col_t, col_b = st.columns([0.3, 0.15, 0.15, 0.2, 0.2])
        p_base = float(prod['preco'])
        
        with col_n:
            st.markdown(f"**{prod['nome']}**")
        with col_p:
            st.markdown(f"R$ {p_base:.2f}")
        with col_q:
            qtd_p = st.number_input("Qtd", min_value=1, value=1, key=f"caixa_qtd_{prod['id']}")
        with col_t:
            p_taxa = st.checkbox("Pagar 10% serviço", value=True, key=f"caixa_taxa_{prod['id']}")
            sub = p_base * qtd_p
            v_final = sub * 1.10 if p_taxa else sub
            st.caption(f"Total: R$ {v_final:.2f}")
        with col_b:
            if st.button("🚀 Lançar", key=f"caixa_btn_{prod['id']}", type="primary"):
                st.session_state[f"caixa_conf_{prod['id']}"] = True
        
        # Confirmação detalhada exibindo a identificação do cliente na tela
        if st.session_state.get(f"caixa_conf_{prod['id']}", False):
            with st.status(f"⚠️ Confirmar lançamento para {input_mesa} / Comanda: {input_comanda}?", expanded=True):
                st.write(f"• **Produto:** {qtd_p}x {prod['nome']}")
                st.write(f"• **Valor total:** R$ {v_final:.2f} " + ("(Com 10%)" if p_taxa else "(Sem taxa)"))
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Confirmar", key=f"caixa_ok_{prod['id']}", type="primary"):
                        conn = init_connection()
                        if conn:
                            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                cur.execute("SELECT f.insumo_id, f.quantidade FROM ficha_tecnica f WHERE f.produto_id = %s;", (prod['id'],))
                                ficha = cur.fetchall()
                                
                                for item in ficha:
                                    consumo = (float(item['quantidade']) / 1000.0) * qtd_p
                                    cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual - %s WHERE id = %s;", (consumo, item['insumo_id']))
                                    
                                # Insere os dados adicionais de rastreabilidade
                                cur.execute("""
                                    INSERT INTO pedidos_realizados (produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo) 
                                    VALUES (%s, %s, %s, %s, %s, %s);
                                """, (prod['nome'], qtd_p, v_final, p_taxa, input_mesa.strip(), input_comanda.strip()))
                                conn.commit()
                            conn.close()
                            st.session_state[f"caixa_conf_{prod['id']}"] = False
                            st.success("Pedido finalizado com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                with c_btn2:
                    if st.button("❌ Cancelar", key=f"caixa_cancel_{prod['id']}"):
                        st.session_state[f"caixa_conf_{prod['id']}"] = False
                        st.rerun()

st.markdown("---")
st.subheader("📋 Histórico de Vendas Recentes")
filtro = st.radio("Filtrar histórico por status da taxa:", ["Todos", "Com 10%", "Sem Taxa"], horizontal=True, key="filtro_vendas_radio")

conn = init_connection()
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query_base = "SELECT produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo, data_hora FROM pedidos_realizados "
        if filtro == "Com 10%":
            cur.execute(query_base + "WHERE taxa_inclusa = TRUE ORDER BY data_hora DESC LIMIT 15;")
        elif filtro == "Sem Taxa":
            cur.execute(query_base + "WHERE taxa_inclusa = FALSE ORDER BY data_hora DESC LIMIT 15;")
        else:
            cur.execute(query_base + "ORDER BY data_hora DESC LIMIT 15;")
        historico = cur.fetchall()
    conn.close()
    
    if historico:
        for p in historico:
            txt_t = "🟢 (Com 10%)" if p['taxa_inclusa'] else "⚪ (Sem taxa)"
            # Exibe as informações completas de destino no log histórico
            st.text(f"⏱️ {p['data_hora'].strftime('%H:%M')} | {p['mesa_numero']} (Comanda: {p['comanda_codigo']}) -> {p['quantidade_pedida']}x {p['produto_nome']} | R$ {float(p['valor_total']):.2f} {txt_t}")
    else:
        st.info("Nenhum pedido lançado recentemente com este filtro.")
