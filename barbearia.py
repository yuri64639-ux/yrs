with t_ger:
    if st.text_input("Senha Admin:", type="password") != "1234": st.warning("Insira a senha.")
    else:
        g_tab = st.tabs(["🛠️ Catálogo", "👥 Equipe", "📊 Relatório"])
        
        # --- PRIMEIRA ABA: CATÁLOGO (ÍNDICE 0) ---
        with g_tab[0]:
            txt = st.text_area("Formato: Nome, Preço", placeholder="Corte, 40.0")
            if st.button("🔥 Salvar") and txt.strip():
                with sqlite3.connect("barber.db") as conn:
                    for l in txt.strip().split("\n"):
                        if "," in l:
                            p = l.split(",")
                            try: conn.cursor().execute("INSERT INTO servicos (nome, preco) VALUES (?, ?) ON CONFLICT(nome) DO UPDATE SET preco=EXCLUDED.preco", (p[0].strip(), float(p[1].strip())))
                            except: pass
                    conn.commit()
                st.success("Salvo!"); st.rerun()
            if not df_s.empty:
                s_del = st.selectbox("Remover:", df_s['nome'].tolist())
                if st.button("❌ Remover"):
                    with sqlite3.connect("barber.db") as conn: conn.cursor().execute("DELETE FROM servicos WHERE nome = ?", (s_del,)); conn.commit()
                    st.success("Removido!"); st.rerun()
                    
        # --- SEGUNDA ABA: EQUIPE (ÍNDICE 1) ---
        with g_tab[1]:
            with st.form("c_b"):
                nb, sb = st.text_input("Nome:").strip(), st.text_input("Senha:", type="password").strip()
                if st.form_submit_button("Registrar") and nb and sb:
                    try:
                        with sqlite3.connect("barber.db") as conn: conn.cursor().execute("INSERT INTO barbeiros (nome, senha) VALUES (?, ?)", (nb, sb)); conn.commit()
                        st.success("Registrado!")
                    except: st.error("Erro ou já existe.")
                    
        # --- TERCEIRA ABA: RELATÓRIO (ÍNDICE 2) ---
        with g_tab[2]:
            with sqlite3.connect("barber.db") as conn: df_f = pd.read_sql("SELECT c.cliente, s.nome as servico, c.barbeiro, c.valor, c.comissao, c.data FROM comandas c JOIN servicos s ON c.servico_id = s.id WHERE c.status = 'Finalizado'", conn)
            if df_f.empty: st.info("Sem registros.")
            else:
                dt_s = st.selectbox("📅 Dia:", sorted(list(set(df_f['data'].tolist())), reverse=True))
                filt = df_f[df_f['data'] == dt_s]
                bruto = float(filt['valor'].sum())
                comis = float(filt[filt['comissao'] == 1]['valor'].sum() * 0.5)
                st.metric("💰 Bruto", f"R$ {bruto:.2f}")
                st.metric("💈 Comissões", f"R$ {comis:.2f}")
                st.metric("📈 Casa", f"R$ {bruto-comis:.2f}")
                st.dataframe(filt, use_container_width=True, hide_index=True)
