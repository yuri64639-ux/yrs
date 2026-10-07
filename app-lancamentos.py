import streamlit as st
import psycopg2

def ob_cx():
    """Conexão dinâmica e isolada com o PostgreSQL para suportar concorrência nativa."""
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

def inicializar_tabelas():
    """Garante a criação segura de todas as tabelas e constraints relacionais."""
    try:
        with ob_cx() as conn_init, conn_init.cursor() as cur:
            cur.execute("SET search_path TO public;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.empresas (id SERIAL PRIMARY KEY, nome_empresa TEXT UNIQUE NOT NULL, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS public.usuarios (id SERIAL PRIMARY KEY, usuario TEXT, senha TEXT);
                CREATE TABLE IF NOT EXISTS public.estoque (id SERIAL PRIMARY KEY, item TEXT, quantidade REAL);
                CREATE TABLE IF NOT EXISTS public.produtos (id SERIAL PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL);
                CREATE TABLE IF NOT EXISTS public.receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL);
                CREATE TABLE IF NOT EXISTS public.pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Sim', garcom TEXT);
            """)
            cur.execute("ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
            cur.execute("ALTER TABLE public.estoque ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
            cur.execute("ALTER TABLE public.produtos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
            cur.execute("ALTER TABLE public.receitas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
            cur.execute("ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
            
            try: cur.execute("ALTER TABLE public.usuarios ADD CONSTRAINT unique_empresa_usuario UNIQUE(empresa_id, usuario);")
            except Exception: conn_init.rollback()
            try: cur.execute("ALTER TABLE public.estoque ADD CONSTRAINT unique_empresa_item UNIQUE(empresa_id, item);")
            except Exception: conn_init.rollback()
            try: cur.execute("ALTER TABLE public.produtos ADD CONSTRAINT unique_empresa_produto UNIQUE(empresa_id, nome);")
            except Exception: conn_init.rollback()
            try: cur.execute("ALTER TABLE public.receitas ADD CONSTRAINT unique_empresa_receita UNIQUE(empresa_id, produto_id, insumo_id);")
            except Exception: conn_init.rollback()
            conn_init.commit()
    except Exception as e:
        st.error(f"Erro na inicialização estrutural: {e}")
import streamlit as st
import pandas as pd
from banco import ob_cx

def renderizar_tela_acesso():
    """--- FASE 1: LOGÍSTICA DE ACESSO DO ESTABELECIMENTO ---"""
    aba_acesso = st.radio("Selecione uma opção:", ["Fazer Login", "Cadastrar Nova Empresa (Criar Conta)"], horizontal=True)

    if aba_acesso == "Cadastrar Nova Empresa (Criar Conta)":
        with st.form("cadastro_empresa_form"):
            st.subheader("🏢 Cadastrar Empresa no Sistema")
            nova_empresa = st.text_input("Nome do seu Estabelecimento / Empresa:").strip()
            adm_usuario = st.text_input("Usuário Administrador (ex: admin):").strip()
            adm_senha = st.text_input("Defina a Senha do Administrador:", type="password").strip()
            botao_cadastrar = st.form_submit_button("Criar Minha Conta", type="primary")
            
            if botao_cadastrar and nova_empresa and adm_usuario and adm_senha:
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("INSERT INTO public.empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as e: st.error(f"Erro no cadastro: {e}")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            with ob_cx() as conn_read:
                df_lista_empresas = pd.read_sql("SELECT id, nome_empresa FROM public.empresas ORDER BY nome_empresa", conn_read)
            dict_empresas = {row["nome_empresa"]: row["id"] for _, row in df_lista_empresas.iterrows()} if not df_lista_empresas.empty else {}
            
            if dict_empresas:
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                user_input = st.text_input("Usuário Master da Empresa:")
                senha_input = st.text_input("Senha Master:", type="password")
                submetido = st.form_submit_button("Liberar Terminal", type="primary")
                
                if submetido:
                    id_empresa_login = dict_empresas[empresa_selecionada]
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("SELECT empresa_id, senha FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (id_empresa_login, user_input.strip(), senha_input.strip()))
                        resultado = cur.fetchone()
                    
                    if resultado:
                        st.session_state.logado = True
                        st.session_state.empresa_id_atual = int(resultado)
                        st.session_state.senha_master_empresa = str(resultado)
                        st.rerun()
                    else: st.error("Credenciais da empresa incorretas!")
            else: st.info("Nenhuma empresa cadastrada ainda.")
    st.stop()
import streamlit as st
import pandas as pd
from banco import ob_cx
from gerencia_continua import renderizar_subtabs_restantes

def renderizar_painel_gerencial():
    """Painel de Controle Gerencial protegido por Senha Master."""
    emp_id = st.session_state.empresa_id_atual
    cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
    
    st.subheader("🔒 Acesso Restrito à Gerência")
    confirma_senha_master = st.text_input("Digite a Senha Master para liberar as ferramentas administrativas:", type="password", key="senha_master_gerencia_input")
    
    if confirma_senha_master != st.session_state.senha_master_empresa:
        if confirma_senha_master: st.error("❌ Senha Master incorreta! Acesso negado.")
        st.info("Aguardando autenticação do administrador.")
        return

    st.success("🔓 Acesso Gerencial Autorizado!")
    
    with ob_cx() as conn_tabs:
        df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque WHERE empresa_id = %s ORDER BY item", conn_tabs, params=[emp_id])
        df_prods = pd.read_sql("SELECT id, nome FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn_tabs, params=[emp_id])
        df_garcons = pd.read_sql("SELECT id, usuario FROM public.usuarios WHERE empresa_id = %s ORDER BY usuario", conn_tabs, params=[emp_id])
    
    subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])

    # --- 1. ESTOQUE ---
    with subtabs[0]:
        st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
        df_est_visual = df_est.copy()
        if not df_est_visual.empty: df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual"]
        st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
        
        with st.expander("➕ Alimentar Estoque"):
            with st.form("f_ins", clear_on_submit=True):
                n_i = st.text_input("Insumo:")
                q_i = st.number_input("Qtd Inteira (Litros, Quilos ou Un):", min_value=0.0, value=1.0, step=1.0)
                if st.form_submit_button("Salvar") and n_i.strip():
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; INSERT INTO public.estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = public.estoque.quantidade + EXCLUDED.quantidade", (emp_id, n_i.strip(), q_i))
                        c.commit()
                    st.success("Estoque updated!"); st.rerun()

    # --- 2. CANCELAMENTOS ---
    with subtabs[1]:
        st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
        with ob_cx() as conn_canc:
            p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn_canc, params=[emp_id])
        if p_ab.empty: st.info("Nenhuma comanda aberta para cancelamento.")
        else:
            m_sel = st.selectbox("Selecione a Mesa para auditar:", sorted(list(set(p_ab['mesa'].tolist()))))
            for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
                col1, col2 = st.columns(2); col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
                if col2.button("Deletar Item", key=f"cn_{it['id']}"):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(it['produto_id'])])
                        for _, r in rc.iterrows(): 
                             cur.execute("UPDATE public.estoque SET quantidade = quantity + %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])), emp_id, int(r['insumo_id'])))
                        cur.execute("DELETE FROM public.pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                        c.commit()
                    st.success("Item removido!"); st.rerun()

    # --- RENDERIZAÇÃO DAS SUBTABS RESTANTES COMPLEMENTARES ---
    renderizar_subtabs_restantes(subtabs, df_prods, df_est, df_garcons, cats, emp_id)
import streamlit as st
import pandas as pd
from banco import ob_cx

def renderizar_subtabs_restantes(subtabs, df_prods, df_est, df_garcons, cats, emp_id):
    # --- 3. CADASTRO EM MASSA ---
    with subtabs[2]:
        st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
        st.write("Cole a sua lista abaixo seguindo o formato exato: **Nome, Categoria, Preço** (um produto por linha).")
        with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
            texto_produtos = st.text_area("Cole seus produtos aqui:", height=200)
            if st.form_submit_button("🔥 Gravar Todos os Produtos") and texto_produtos.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    for linha in texto_produtos.strip().split("\n"):
                        if "," in linha:
                            partes = linha.split(",")
                            if len(partes) == 3:
                                n_p, c_p, p_p = partes[0].strip(), partes[1].strip(), partes[2].strip()
                                cat_valida = [c for c in cats if c.lower() == c_p.lower()]
                                if n_p and cat_valida:
                                    try: cur.execute("INSERT INTO public.produtos (empresa_id, nome, categoria, preco) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco", (emp_id, n_p, str(cat_valida[0]), float(p_p)))
                                    except ValueError: pass
                    c.commit()
                st.success("Produtos salvos!"); st.rerun()

    # --- 4. RECEITAS COM 4 INGREDIENTES ---
    with subtabs[3]:
        st.subheader("🔬 Montar Ficha Técnica (Até 4 Ingredientes)")
        if not df_prods.empty and not df_est.empty:
            lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
            lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
            d_p, d_i = {r['nome']: r['id'] for _, r in df_prods.iterrows()}, {r['item']: r['id'] for _, r in df_est.iterrows()}
            with st.form("f_vinc_multi", clear_on_submit=True):
                p_sel = d_p[st.selectbox("Selecione o Produto final:", lista_prods)]
                st.markdown("---")
                col1, col2 = st.columns(2); i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="rec_i1"); q1 = col2.number_input("Qtd 1 (ml/g):", min_value=0.0, key="rec_q1")
                col3, col4 = st.columns(2); i2 = col3.selectbox("Ingrediente 2:", lista_insumos, key="rec_i2"); q2 = col4.number_input("Qtd 2 (ml/g):", min_value=0.0, key="rec_q2")
                col5, col6 = st.columns(2); i3 = col5.selectbox("Ingrediente 3:", lista_insumos, key="rec_i3"); q3 = col6.number_input("Qtd 3 (ml/g):", min_value=0.0, key="rec_q3")
                col7, col8 = st.columns(2); i4 = col7.selectbox("Ingrediente 4:", lista_insumos, key="rec_i4"); q4 = col8.number_input("Qtd 4 (ml/g):", min_value=0.0, key="rec_q4")
                if st.form_submit_button("🔥 Gravar Receita Completa"):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        for ing, qtd in [(i1, q1), (i2, q2), (i3, q3), (i4, q4)]:
                            if ing != "---" and qtd > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, p_sel, d_i[ing], qtd))
                        c.commit()
                    st.success("Ficha técnica salva!"); st.rerun()
        else: st.info("Cadastre insumos e produtos antes.")

    # --- 5. RELATÓRIOS ---
    with subtabs[4]:
        st.subheader("📊 Resumo Financeiro Detalhado")
        with ob_cx() as conn_rep:
            vendas_df = pd.read_sql("SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC", conn_rep, params=[emp_id])
        if vendas_df.empty: st.info("Nenhuma comanda histórica.")
        else:
            empresa_total, garcons_total, pendente_total = 0.0, 0.0, 0.0
            for mesa_id, group in vendas_df.groupby('mesa'):
                sub_mesa = float(group['subtotal'].sum())
                if group['status'].iloc[0] == 'Finalizado (Pago)':
                    empresa_total += sub_mesa
                    if int(group['taxa_paga'].iloc[0]) == 1: garcons_total += (sub_mesa * 0.10)
                else: pendente_total += sub_mesa
            c1, c2, c3 = st.columns(3); c1.metric("💰 Faturamento Líquido", f"R$ {empresa_total:.2f}"); c2.metric("🍹 Caixinha (10%)", f"R$ {garcons_total:.2f}"); c3.metric("⚠️ Perdas", f"R$ {pendente_total:.2f}")
            st.dataframe(vendas_df, use_container_width=True, hide_index=True)

    # --- 6. EXCLUIR ---
    with subtabs[5]:
        st.subheader("🗑️ Remover do Sistema")
        col_del1, col_del2, col_del3 = st.columns(3)
        with col_del1:
            if not df_prods.empty:
                prod_para_excluir = st.selectbox("Deletar Produto:", [r['nome'] for _, r in df_prods.iterrows()], key="del_prod_sel")
                if st.button("❌ Excluir Produto", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; DELETE FROM public.receitas WHERE empresa_id = %s AND produto_id = (SELECT id FROM public.produtos WHERE empresa_id = %s AND nome = %s); DELETE FROM public.produtos WHERE empresa_id = %s AND nome = %s", (emp_id, emp_id, prod_para_excluir, emp_id, prod_para_excluir))
                        c.commit()
                    st.success("Removido!"); st.rerun()
        with col_del2:
            if not df_est.empty:
                insumo_para_excluir = st.selectbox("Deletar Insumo:", [r['item'] for _, r in df_est.iterrows()], key="del_ins_sel")
                if st.button("❌ Excluir Insumo", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; DELETE FROM public.receitas WHERE empresa_id = %s AND insumo_id = (SELECT id FROM public.estoque WHERE empresa_id = %s AND item = %s); DELETE FROM public.estoque WHERE empresa_id = %s AND item = %s;", (emp_id, emp_id, insumo_para_excluir, emp_id, insumo_para_excluir))
                        c.commit()
                    st.success("Removido!"); st.rerun()
        with col_del3:
            if not df_garcons.empty:
                garcom_para_excluir = st.selectbox("Remover Garçom:", [r['usuario'] for _, r in df_garcons.iterrows()], key="del_garcom_sel")
                if st.button("❌ Remover Funcionário", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; DELETE FROM public.usuarios WHERE empresa_id = %s AND usuario = %s", (emp_id, garcom_para_excluir))
                        c.commit()
                    st.success("Funcionário excluído!"); st.rerun()
import streamlit as st
import pandas as pd
from datetime import datetime
from banco import ob_cx

def renderizar_terminal_garcom():
    """Gerencia a identificação do operador do terminal."""
    emp_id = st.session_state.empresa_id_atual
    if not st.session_state.garcom_logado:
        st.subheader("👤 Identificação do Garçom")
        with st.form("login_garcom_form"):
            garcom_input = st.text_input("Usuário/Nome do Garçom:")
            senha_garcom = st.text_input("Senha do Garçom:", type="password")
            if st.form_submit_button("Entrar no Sistema", type="primary"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; SELECT usuario FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (emp_id, garcom_input.strip().lower(), senha_garcom.strip()))
                    res_garcom = cur.fetchone()
                if res_garcom:
                    st.session_state.garcom_logado = True
                    st.session_state.usuario_atual = str(res_garcom[0])
                    st.rerun()
                else: st.error("Credenciais do garçom incorretas!")
        
        st.markdown("---")
        with st.expander("➕ Não tem conta? Cadastrar Novo Garçom"):
            with st.form("cadastro_garcom_form", clear_on_submit=True):
                novo_g_user = st.text_input("Defina o Nome/Usuário do Garçom:").strip()
                novo_g_senha = st.text_input("Defina a Senha de Acesso:", type="password").strip()
                if st.form_submit_button("💼 Confirmar Cadastro do Funcionário") and novo_g_user and novo_g_senha:
                    try:
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public; INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (emp_id, novo_g_user, novo_g_senha))
                            c.commit()
                        st.success(f"Garçom '{novo_g_user}' cadastrado!")
                    except Exception as e: st.error(f"Erro ou funcionário já existente: {e}")
        return False
    
    st.subheader(f"📋 Terminal de Pedidos Ativo — Operador: {st.session_state.usuario_atual.upper()}")
    if st.button("🔒 Sair / Trocar de Garçom", use_container_width=True, key="logoff_garcom_atend"):
        st.session_state.garcom_logado = False
        st.session_state.usuario_atual = ""
        st.session_state.carrinho = []
        st.rerun()
    return True

def lancar_novo_pedido(emp_id):
    """1. LANÇAR PEDIDO E ADICIONAR ITENS AO CARRINHO NATIVO"""
    with ob_cx() as conn:
        df_prods_venda = pd.read_sql("SELECT id, nome, categoria, preco FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
    if df_prods_venda.empty: st.info("Nenhum produto cadastrado no sistema.")
    else:
        # Posição 1: Campo de Mesa
        mesa_operacao = st.text_input("Número / Nome da Mesa ou Comanda:", value="Mesa 01", key="mesa_operacao_garcom_input")
        
        # Posição 2: Lupa de produtos posicionada exatamente embaixo do campo da mesa
        lupa_produto = st.text_input("🔍 Lupa - Digite o nome do Produto para pesquisar e filtrar:").strip()
        
        categoria_filtro = st.selectbox("Filtrar Categoria:", ["Todos"] + sorted(list(set(df_prods_venda['categoria'].tolist()))))
        
        df_filtrado = df_prods_venda
        if categoria_filtro != "Todos": df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_filtro]
        if lupa_produto: df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(lupa_produto, case=False, na=False)]
            
        if df_filtrado.empty: st.warning("⚠️ Nenhum produto correspondente foi encontrado.")
        else:
            prod_map_venda = {f"{row['nome']} - R$ {row['preco']:.2f}": (row['id'], row['nome']) for _, row in df_filtrado.iterrows()}
            produto_selecionado_string = st.selectbox("Escolha o Item:", list(prod_map_venda.keys()))
            qtd_solicitada = st.number_input("Quantidade Desejada:", min_value=1, value=1, step=1)
            if st.button("➕ Adicionar ao Carrinho", use_container_width=True):
                id_p_venda, nome_p_venda = prod_map_venda[produto_selecionado_string]
                st.session_state.carrinho.append({"id": id_p_venda, "nome": nome_p_venda, "qtd": qtd_solicitada})
                st.toast(f"{nome_p_venda} adicionado ao carrinho!")
                        
        if st.session_state.carrinho:
            st.markdown("### 🛒 Itens no Carrinho Corrente")
            for item in st.session_state.carrinho: st.write(f"▪ *{item['qtd']}x* - {item['nome']}")
            confirmacao_garcom = st.checkbox("✅ Eu confirmo que conferi os itens do pedido com o cliente.", value=False)
            col_limpar, col_enviar = st.columns(2)
            if col_limpar.button("🗑️ Limpar Carrinho", use_container_width=True): st.session_state.carrinho = []; st.rerun()
            if col_enviar.button("🚀 Confirmar e Enviar Pedido", type="primary", use_container_width=True):
                if not confirmacao_garcom: st.error("🔒 Atenção: Você precisa marcar o campo de confirmação antes de enviar!")
                else:
                    horario_atual = datetime.now().strftime("%H:%M:%S")
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        for item in st.session_state.carrinho:
                            cur.execute("INSERT INTO public.pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom) VALUES (%s, %s, %s, %s, 'Pendente', %s, %s)", (emp_id, mesa_operacao.strip(), item['id'], item['qtd'], horario_atual, st.session_state.usuario_atual))
                            rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, item['id']])
                            for _, r in rc.iterrows(): cur.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(item['qtd'])), emp_id, int(r['insumo_id'])))
                        c.commit()
                    st.success("Pedido lançado!"); st.session_state.carrinho = []; st.rerun()
import streamlit as st
import pandas as pd
from banco import ob_cx

def gerenciar_contas_ativas(emp_id):
    """2. GERENCIAR CONTAS ATIVAS COM LUPA DE FILTRO TOTALIZADA E CONFIRMAÇÃO INDIVIDUAL ORIGINAL"""
    with ob_cx() as conn:
        pedidos_ativos = pd.read_sql("SELECT p.id, p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Pendente', 'Confirmado') ORDER BY p.mesa", conn, params=[emp_id])
    if pedidos_ativos.empty: st.info("Não há nenhuma comanda ou mesa ativa aberta no momento.")
    else:
        lupa_busca = st.text_input("🔍 Lupa - Digite o nome da Comanda/Mesa para pesquisar e filtrar:").strip()
        df_mesas_ativas = pedidos_ativos[pedidos_ativos['mesa'].str.contains(lupa_busca, case=False, na=False)] if lupa_busca else pedidos_ativos
        if df_mesas_ativas.empty: st.warning("⚠️ Nenhuma mesa correspondente foi encontrada na busca da lupa.")
        else:
            mesas_abertas = sorted(list(set(df_mesas_ativas['mesa'].tolist())))
            mesa_ver = st.selectbox("Selecione a Mesa para comanda ativa:", mesas_abertas)
            df_mesa_filtrada = pedidos_ativos[pedidos_ativos['mesa'] == mesa_ver]
            st.markdown(f"#### 📋 Comanda: {mesa_ver}")
            
            if 'Pendente' in df_mesa_filtrada['status'].tolist():
                if st.button("✅ Confirmar Todos os Itens Pendentes desta Mesa", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Confirmado' WHERE empresa_id = %s AND mesa = %s AND status = 'Pendente'", (emp_id, mesa_ver))
                        c.commit()
                    st.success("Todos os itens pendentes foram confirmados com sucesso!"); st.rerun()
            
            for _, row in df_mesa_filtrada.iterrows():
                col_item, col_status, col_acao = st.columns(3)
                col_item.write(f"▪ **{row['quantidade']}x** {row['produto']} *(R$ {row['subtotal']:.2f})*")
                if row['status'] == 'Pendente':
                    col_status.warning("⏳ Pendente")
                    if col_acao.button("Confirmar", key=f"conf_ind_{row['id']}"):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Confirmado' WHERE id = %s AND empresa_id = %s", (int(row['id']), emp_id))
                            c.commit()
                        st.rerun()
                else: col_status.success("🔥 Confirmado")
            
            subtotal_mesa = float(df_mesa_filtrada['subtotal'].sum())
            taxa_servico = subtotal_mesa * 0.10
            total_geral = subtotal_mesa + taxa_servico
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Subtotal Consumo", f"R$ {subtotal_mesa:.2f}")
            c2.metric("Taxa Serviço (10%)", f"R$ {taxa_servico:.2f}")
            c3.metric("TOTAL DA CONTA", f"R$ {total_geral:.2f}")
            
            inclui_taxa = st.checkbox("Cliente aceitou pagar os 10%?", value=True, key="chk_taxa_fechamento")
            if st.button("💰 Finalizar e Receber Pagamento (Fechar Mesa)", type="primary", use_container_width=True):
                valor_taxa_salvar = 1 if inclui_taxa else 0
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE empresa_id = %s AND mesa = %s AND status IN ('Pendente', 'Confirmado')", (valor_taxa_salvar, emp_id, mesa_ver))
                    c.commit()
                st.success(f"Conta da {mesa_ver} fechada com sucesso!"); st.rerun()
import streamlit as st
from banco import inicializar_tabelas
from acesso import renderizar_tela_acesso
from gerencia import renderizar_painel_gerencial
from garcom import renderizar_terminal_garcom, lancar_novo_pedido
from contas import gerenciar_contas_ativas

# Configuração global da página do ecossistema multi-tenant
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

# Inicialização e manutenção estrita de todas as variáveis de sessão originais
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# Ocultação do menu nativo do Streamlit via injeção de CSS
st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
    header [data-testid="stToolbar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# Inicializa as tabelas relacionais em lote de forma protegida
inicializar_tabelas()

# Controle de fluxo de acesso da empresa
if not st.session_state.logado: renderizar_tela_acesso()

# Layout Geral Demandado: Abas Masters de Nível Superior Logo Após o Login da Empresa
aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])

with aba_master_sistema:
    emp_id = st.session_state.empresa_id_atual
    if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True, key="master_lock_empresa"):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.garcom_logado = False
        st.session_state.carrinho = []
        st.rerun()
    renderizar_painel_gerencial()

with aba_master_operador:
    emp_id = st.session_state.empresa_id_atual
    garcom_ativo = renderizar_terminal_garcom()
    if garcom_ativo:
        aba_operacao = st.radio("Selecione a Ação:", ["➕ Lançar Pedido (Abrir/Adicionar Itens)", "🧾 Gerenciar Contas / Fechar Mesas"], horizontal=True)
        if aba_operacao == "➕ Lançar Pedido (Abrir/Adicionar Itens)": lancar_novo_pedido(emp_id)
        elif aba_operacao == "🧾 Gerenciar Contas / Fechar Mesas": gerenciar_contas_ativas(emp_id)
