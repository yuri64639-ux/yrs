# --- RECONHECIMENTO AUTOMÁTICO DO INQUILINO (ATUALIZADO) ---
id_empresa_contexto = None

if "empresa_id_ativo" in st.session_state and st.session_state.empresa_id_ativo:
    id_empresa_contexto = st.session_state.empresa_id_ativo
elif "empresa_id_garcom" in st.session_state and st.session_state.empresa_id_garcom:
    id_empresa_contexto = st.session_state.empresa_id_garcom
elif "emp_id" in st.query_params:
    id_empresa_contexto = int(st.query_params["emp_id"])

# CORREÇÃO DE SEGURANÇA: Permite selecionar a empresa direto se o token de sessão estiver vazio
if not id_empresa_contexto:
    st.markdown("<h3>🔒 Autenticação de Almoxarifado</h3>", unsafe_allow_html=True)
    conn = DatabaseManager.get_connection()
    lista_opcoes_emp = []
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome_fantasia FROM public.empresas ORDER BY nome_fantasia;")
            lista_opcoes_emp = cur.fetchall()
        conn.close()
    
    mapa_fallback = {row[1]: row[0] for row in lista_opcoes_emp}
    if not mapa_fallback:
        st.error("Nenhuma empresa localizada na nuvem Neon para associação.")
        st.stop()
        
    emp_manual = st.selectbox("Selecione sua Empresa para liberar este terminal:", options=list(mapa_fallback.keys()))
    if st.button("Liberar Módulo de Estoque", type="primary", use_container_width=True):
        st.session_state.empresa_id_ativo = mapa_fallback[emp_manual]
        st.query_params["emp_id"] = str(mapa_fallback[emp_manual])
        st.success("Terminal Vinculado!")
        time.sleep(0.3)
        st.rerun()
    st.stop()
# --- DASHBOARD PRIVADO COM FILTRAGEM POR EMPRESA ---
@st.fragment(run_every="1s")
def render_dashboard_estoque():
    st.subheader("📊 Indicadores de Volume de Estoque Bruto")
    conn = DatabaseManager.get_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT nome, quantidade_atual FROM insumos WHERE empresa_id = %s ORDER BY nome;", (id_empresa_contexto,))
            items = cur.fetchall()
        conn.close()
        
        if items:
            cols = st.columns(min(len(items), 5))
            for idx, item in enumerate(items):
                qtd = float(item['quantidade_atual'])
                label_status = "🔴 Crítico" if qtd <= Config.LOW_STOCK_THRESHOLD else "🟢 Normal"
                with cols[idx % 5]:
                    st.metric(
                        label=f"{item['nome']} ({label_status})",
                        value=f"{qtd:.3f} Unidades",
                        delta=f"{qtd - Config.LOW_STOCK_THRESHOLD:.3f} acima" if qtd > Config.LOW_STOCK_THRESHOLD else "Abaixo da Margem",
                        delta_color="normal" if qtd > Config.LOW_STOCK_THRESHOLD else "inverse"
                    )
        else:
            st.info("Nenhum ativo de insumo cadastrado na base de dados desta empresa.")

# Interface Principal do Administrador
st.title("💼 Enterprise Resource Planning (ERP) - Inteligência Operacional")
render_dashboard_estoque()
st.markdown("---")

menu_tabs = st.tabs(["📥 Entrada de Insumos (Lote)", "🏗️ Engenharia de Fichas Técnicas", "📋 Auditoria e Controle de Cardápio"])

# ==================== ABA 1: INGESTÃO DE MATÉRIA-PRIMA INDIVIDUAL ====================
with menu_tabs[0]:
    st.header("📥 Ingestão de Matéria-Prima em Lote")
    st.markdown("Cadastre novos insumos comerciais por linha. O estoque é indexado à sua conta corporativa.")
    
    txt_carga = st.text_area(
        "Massa de Dados para Importação (Um insumo por linha):",
        placeholder="Exemplo:\nQueijo Muçarela\nPeito de Frango\nÓleo de Soja",
        height=180,
        key="erp_txt_ingestao"
    )
    
    if st.button("Executar Carga em Massa", type="primary", use_container_width=True):
        if txt_carga.strip():
            ativos_linhas = [linha.strip() for list_item in txt_carga.split("\n") if (linha := list_item.strip())]
            db_conn = DatabaseManager.get_connection()
            if db_conn:
                novos_ativos = 0
                try:
                    with db_conn.cursor() as cur:
                        for item_nome in ativos_linhas:
                            # ON CONFLICT DO NOTHING baseado na nova restrição composta nome + empresa_id
                            cur.execute("""
                                INSERT INTO insumos (nome, empresa_id) 
                                VALUES (%s, %s) 
                                ON CONFLICT (nome, empresa_id) DO NOTHING;
                            """, (item_nome, id_empresa_contexto))
                            if cur.rowcount > 0:
                                novos_ativos += 1
                        db_conn.commit()
                    st.success(f"Ação executada. Adicionados {novos_ativos} novos insumos ao inventário exclusivo da sua empresa.")
                    time.sleep(1)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erro operacional durante o processamento: {ex}")
                finally:
                    db_conn.close()
        else:
            st.warning("O campo de texto está vazio.")
# ==================== ABA 2: ENGENHARIA DE PRODUTOS E MATRIZ DE COMPOSIÇÃO ====================
with menu_tabs[1]:
    st.header("🏗️ Engenharia de Fichas Técnicas")
    
    db_conn = DatabaseManager.get_connection()
    lista_ativos_insumos = []
    if db_conn:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome FROM insumos WHERE empresa_id = %s ORDER BY nome;", (id_empresa_contexto,))
            lista_ativos_insumos = cur.fetchall()
        db_conn.close()
        
    opcoes_obrigatorias = [item["nome"] for item in lista_ativos_insumos] if lista_ativos_insumos else ["- Cadastre insumos primeiro -"]
    opcoes_opcionais = ["- Nenhum -"] + ([item["nome"] for item in lista_ativos_insumos] if lista_ativos_insumos else [])
    mapeamento_insumos = {item["nome"]: item["id"] for item in lista_ativos_insumos}
    
    c_dados1, c_dados2 = st.columns(2)
    with c_dados1:
        input_nome_sku = st.text_input("Nome Comercial do Produto (SKU):", key="erp_nome_sku")
    with c_dados2:
        input_preco_sku = st.number_input("Preço de Venda Comercial (R$):", min_value=0.00, step=1.00, format="%.2f", key="erp_preco_sku")
        
    st.markdown("---")
    st.subheader("📋 Matriz de Formulação (Limite de 1 a 6 Insumos por SKU)")
    
    componentes_selecionados = []
    
    for index_row in range(3):
        col_esq, col_dir = st.columns(2)
        idx_esq = index_row * 2
        with col_esq:
            st.markdown(f"**Componente Operacional {idx_esq + 1}**")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sel_ins_l = st.selectbox(f"Insumo Ativo {idx_esq + 1}", options=opcoes_obrigatorias if idx_esq == 0 else opcoes_opcionais, key=f"matriz_ins_{idx_esq}")
            with sc2:
                qtd_ins_l = st.number_input(f"Consumo Proporcional {idx_esq + 1}", min_value=0.01, value=100.00, step=10.00, key=f"matriz_qtd_{idx_esq}")
            with sc3:
                uni_ins_l = st.selectbox(f"Unidade de Medida {idx_esq + 1}", options=["g", "ml"], key=f"matriz_uni_{idx_esq}")
                if sel_ins_l != "- Nenhum -" and sel_ins_l != "- Cadastre insumos primeiro -":
                    componentes_selecionados.append({"nome": sel_ins_l, "quantidade": qtd_ins_l, "unidade": uni_ins_l})
                    
        idx_dir = idx_esq + 1
        with col_dir:
            st.markdown(f"**Componente Operacional {idx_dir + 1}**")
            sc4, sc5, sc6 = st.columns(3)
            with sc4:
                sel_ins_r = st.selectbox(f"Insumo Ativo {idx_dir + 1}", options=opcoes_opcionais, key=f"matriz_ins_{idx_dir}")
            with sc5:
                qtd_ins_r = st.number_input(f"Consumo Proporcional {idx_dir + 1}", min_value=0.01, value=100.00, step=10.00, key=f"matriz_qtd_{idx_dir}")
            with sc6:
                uni_ins_r = st.selectbox(f"Unidade de Medida {idx_dir + 1}", options=["g", "ml"], key=f"matriz_uni_{idx_dir}")
                if sel_ins_r != "- Nenhum -":
                    componentes_selecionados.append({"nome": sel_ins_r, "quantidade": qtd_ins_r, "unidade": uni_ins_r})

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Gravar Produto & Ficha Técnica", type="primary", use_container_width=True):
        if not input_nome_sku.strip() or input_preco_sku <= 0:
            st.error("Insira informações válidas de nome e preço de venda.")
        elif not componentes_selecionados:
            st.error("Vincule insumos para salvar a composição.")
        else:
            db_conn = DatabaseManager.get_connection()
            if db_conn:
                try:
                    with db_conn.cursor() as cur:
                        # Insere o produto respeitando a restrição de unicidade por empresa
                        cur.execute("""
                            INSERT INTO produtos (nome, preco, empresa_id) 
                            VALUES (%s, %s, %s) 
                            ON CONFLICT (nome, empresa_id) DO UPDATE SET preco = EXCLUDED.preco 
                            RETURNING id;
                        """, (input_nome_sku.strip(), input_preco_sku, id_empresa_contexto))
                        id_novo_produto = cur.fetchone()[0]
                        
                        # Limpa composições antigas para evitar resíduos se o produto já existia
                        cur.execute("DELETE FROM ficha_tecnica WHERE produto_id = %s AND empresa_id = %s;", (id_novo_produto, id_empresa_contexto))
                        
                        for comp in componentes_selecionados:
                            id_insumo_alvo = mapeamento_insumos.get(comp["nome"])
                            if id_insumo_alvo:
                                cur.execute("""
                                    INSERT INTO ficha_tecnica (produto_id, insumo_id, quantidade, unidade, empresa_id) 
                                    VALUES (%s, %s, %s, %s, %s);
                                """, (id_novo_produto, id_insumo_alvo, comp["quantidade"], comp["unidade"], id_empresa_contexto))
                        db_conn.commit()
                    st.success(f"Produto '{input_nome_sku}' integrado e blindado para sua empresa!")
                    time.sleep(1)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erro ao salvar produto no Neon: {ex}")
                finally:
                    db_conn.close()

# ==================== ABA 3: AUDITORIA E CARDÁPIO PRIVADO ====================
with menu_tabs[2]:
    st.header("📋 Auditoria e Controle de Cardápio")
    conn = DatabaseManager.get_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, preco FROM produtos WHERE empresa_id = %s ORDER BY nome;", (id_empresa_contexto,))
            produtos_auditoria = cur.fetchall()
            
            if not produtos_auditoria:
                st.info("Nenhum produto cadastrado no ambiente logado.")
            else:
                for p in produtos_auditoria:
                    with st.expander(f"🍔 {p['nome']} — R$ {float(p['preco']):.2f}"):
                        cur.execute("""
                            SELECT i.nome, f.quantidade, f.unidade 
                            FROM ficha_tecnica f
                            JOIN insumos i ON f.insumo_id = i.id
                            WHERE f.produto_id = %s AND f.empresa_id = %s;
                        """, (p["id"], id_empresa_contexto))
                        detalhes_ficha = cur.fetchall()
                        if detalhes_ficha:
                            for linha in detalhes_ficha:
                                st.write(f"• **{linha['nome']}**: {float(linha['quantidade'])} {linha['unidade']}")
                        else:
                            st.caption("Nenhum insumo atrelado a este item.")
        conn.close()
