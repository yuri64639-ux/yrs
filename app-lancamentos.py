import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# Configuração global da página do ecossistema multi-tenant
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

# Inicialização e manutenção estrita de todas as variáveis de sessão
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# Ocultação do menu nativo do Streamlit via injeção de CSS
st.markdown("<style>#MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; } header [data-testid='stToolbar'] { display: none !important; } [data-testid='collapsedControl'] { display: none !important; } header { background-color: transparent !important; }</style>", unsafe_allow_html=True)

# Conexão dinâmica com o Banco de Dados PostgreSQL
def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

# Inicialização relacional de tabelas
conn = ob_cx()
with conn.cursor() as cur:
    cur.execute("SET search_path TO public;")
    cur.execute("CREATE TABLE IF NOT EXISTS empresas (id SERIAL PRIMARY KEY, nome_empresa TEXT UNIQUE NOT NULL, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, senha TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS estoque (id SERIAL PRIMARY KEY, item TEXT, quantidade REAL);")
    cur.execute("CREATE TABLE IF NOT EXISTS produtos (id SERIAL PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL);")
    cur.execute("CREATE TABLE IF NOT EXISTS receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL);")
    cur.execute("CREATE TABLE IF NOT EXISTS pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Não', garcom TEXT, modo_pagamento TEXT);")
    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE estoque ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE produtos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE receitas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS modo_pagamento TEXT;")
    conn.commit()
    try: cur.execute("ALTER TABLE produtos DROP CONSTRAINT IF EXISTS produtos_nome_key CASCADE;")
    except: conn.rollback()
    try: cur.execute("ALTER TABLE estoque DROP CONSTRAINT IF EXISTS estoque_item_key CASCADE;")
    except: conn.rollback()
    try: cur.execute("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_usuario_key CASCADE;")
    except: conn.rollback()
    conn.commit()
    try: cur.execute("ALTER TABLE usuarios ADD CONSTRAINT unique_empresa_usuario UNIQUE(empresa_id, usuario);")
    except: conn.rollback()
    try: cur.execute("ALTER TABLE estoque ADD CONSTRAINT unique_empresa_item UNIQUE(empresa_id, item);")
    except: conn.rollback()
    try: cur.execute("ALTER TABLE produtos ADD CONSTRAINT unique_empresa_produto UNIQUE(empresa_id, nome);")
    except: conn.rollback()
conn.commit()

# --- FASE 1: ACESSO DO ESTABELECIMENTO ---
if not st.session_state.logado:
    aba_acesso = st.radio("Selecione uma opção:", ["Fazer Login", "Cadastrar Nova Empresa (Criar Conta)"], horizontal=True)
    if aba_acesso == "Cadastrar Nova Empresa (Criar Conta)":
        with st.form("cadastro_empresa_form"):
            st.subheader("🏢 Cadastrar Empresa no Sistema")
            nova_empresa = st.text_input("Nome do seu Estabelecimento / Empresa:").strip()
            adm_usuario = st.text_input("Usuário Administrador (ex: admin):").strip()
            adm_senha = st.text_input("Defina a Senha do Administrador:", type="password").strip()
            if st.form_submit_button("Criar Minha Conta", type="primary") and nova_empresa and adm_usuario and adm_senha:
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; INSERT INTO empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as e: st.error(f"Erro no cadastro: {e}")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            df_lista_empresas = pd.read_sql("SELECT id, nome_empresa FROM empresas ORDER BY nome_empresa", conn)
            dict_empresas = {row["nome_empresa"]: row["id"] for _, row in df_lista_empresas.iterrows()} if not df_lista_empresas.empty else {}
            if dict_empresas:
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                user_input = st.text_input("Usuário Master da Empresa:")
                senha_input = st.text_input("Senha Master:", type="password")
                if st.form_submit_button("Liberar Terminal", type="primary"):
                    id_empresa_login = dict_empresas[empresa_selecionada]
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; SELECT empresa_id, senha FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (id_empresa_login, user_input.strip(), senha_input.strip()))
                        resultado = cur.fetchone()
                    if resultado:
                        st.session_state.logado = True
                        st.session_state.empresa_id_atual = int(resultado[0])
                        st.session_state.senha_master_empresa = str(resultado[1])
                        st.rerun()
                    else: st.error("Credenciais da empresa incorretas!")
            else: st.info("Nenhuma empresa cadastrada ainda.")
    conn.close()
    st.stop()

# --- CONTROLE DINÂMICO DE VISUALIZAÇÃO ---
if st.session_state.garcom_logado:
    st.markdown("### 📱 Ambiente do Funcionário")
    aba_master_operador = st.container()
    aba_master_sistema = st.empty()
else:
    aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])

permitir_render_gerencial = False
if not st.session_state.garcom_logado:
    with aba_master_sistema:
        emp_id = st.session_state.empresa_id_atual
        cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
        if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True):
            st.session_state.logado = False
            st.session_state.empresa_id_atual = None
            st.session_state.senha_master_empresa = ""
            st.session_state.garcom_logado = False
            st.session_state.carrinho = []
            st.rerun()
        st.markdown("---")
        st.subheader("🔑 Autenticação Gerencial Requerida")
        senha_gerencial_digitada = st.text_input("Digite a Senha Master da Empresa para liberar este painel:", type="password", key="senha_painel_gerencial_input")
        if senha_gerencial_digitada != st.session_state.senha_master_empresa:
            st.warning("🔒 Conteúdo restrito. Insira a senha master correta.")
        else:
            if st.button("❌ Bloquear Aba Gerencial Imediatamente", type="secondary", use_container_width=True):
                if "senha_painel_gerencial_input" in st.session_state: st.session_state["senha_painel_gerencial_input"] = ""
                st.rerun()
            permitir_render_gerencial = True
            
        if permitir_render_gerencial:
            df_est = pd.read_sql("SELECT id, item, quantidade FROM estoque WHERE empresa_id = %s ORDER BY item", conn, params=[emp_id])
            df_prods = pd.read_sql("SELECT id, nome FROM produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
            
            tab_estoque, tab_cancelamento, tab_cadastro, tab_receitas, tab_relatorios, tab_excluir = st.tabs([
                "📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"
            ])
            
            with tab_estoque:
                st.subheader("📦 Estoque Atual")
                df_est_visual = df_est.copy()
                if not df_est_visual.empty: df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual"]
                st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
                with st.form("f_ins", clear_on_submit=True):
                    n_i = st.text_input("Insumo:")
                    q_i = st.number_input("Quantidade:", min_value=0.0, value=1.0)
                    if st.form_submit_button("Salvar Insumo") and n_i.strip():
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public; INSERT INTO estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (emp_id, n_i.strip(), q_i))
                            c.commit()
                        st.rerun()
                        
            with tab_cancelamento:
                st.subheader("❌ Cancelamentos")
                p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn, params=[emp_id])
                if p_ab.empty: st.info("Nenhuma comanda aberta.")
                else:
                    m_sel = st.selectbox("Selecione a Mesa:", sorted(list(set(p_ab['mesa'].tolist()))))
                    for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
                        col1, col2 = st.columns(2); col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
                        if col2.button("Deletar", key=f"cn_{it['id']}"):
                            with ob_cx() as c, c.cursor() as cur:
                                cur.execute("SET search_path TO public;")
                                rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(it['produto_id'])])
                                for _, r in rc.iterrows(): cur.execute("UPDATE estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])), emp_id, int(r['insumo_id'])))
                                cur.execute("DELETE FROM pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                                c.commit()
                            st.rerun()
                            
            with tab_cadastro:
                st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
                with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
                    texto_produtos = st.text_area("Formato: Nome, Categoria, Preço", placeholder="Caipirinha, Drinks, 15.0\nHeineken, Cervejas, 12.0")
                    if st.form_submit_button("🔥 Gravar Produtos") and texto_produtos.strip():
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            for linha in texto_produtos.strip().split("\n"):
                                if "," in linha:
                                    partes = linha.split(",")
                                    if len(partes) == 3:
                                        n_p, c_p, p_p = partes[0].strip(), partes[1].strip(), partes[2].strip()
                                        cat_valida = [c for c in cats if c.lower() == c_p.lower()]
                                        if n_p and cat_valida:
                                            try: cur.execute("INSERT INTO produtos (empresa_id, nome, categoria, preco) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco", (emp_id, n_p, str(cat_valida[0]), float(p_p)))
                                            except: pass
                            c.commit()
                        st.rerun()
                        
            with tab_receitas:
                st.subheader("🔬 Ficha Técnica")
                if not df_prods.empty and not df_est.empty:
                    d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
                    d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
                    with st.form("f_vinc_multi", clear_on_submit=True):
                        p_sel = d_p[st.selectbox("Produto:", list(d_p.keys()))]
                        i1 = st.selectbox("Ingrediente 1:", ["---"] + list(d_i.keys()))
                        q1 = st.number_input("Qtd 1 (g/ml):", min_value=0.0)
                        if st.form_submit_button("Gravar Receita") and i1 != "---" and q1 > 0:
                            with ob_cx() as c, c.cursor() as cur:
                                cur.execute("SET search_path TO public; INSERT INTO receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, int(p_sel), int(d_i[i1]), float(q1)))
                                c.commit()
                            st.rerun()
                            
            with tab_relatorios:
                st.subheader("📊 Relatórios Financeiros")
                vendas_df = pd.read_sql("SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario, p.modo_pagamento FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC", conn, params=[emp_id])
                if vendas_df.empty: st.info("Sem histórico de faturamento.")
                else:
                    vendas_df['data_somente'] = vendas_df['horario'].apply(lambda x: str(x).split(" ")[0] if " " in str(x) else "Sem Data")
                    d_sel = st.selectbox("Selecione a Data:", sorted(list(set(vendas_df['data_somente'].tolist())), reverse=True))
                    df_f = vendas_df[vendas_df['data_somente'] == d_sel]
                    
                    empresa_total = df_f[df_f['status']=='Finalizado (Pago)']['subtotal'].sum()
                    
                    pix_total = df_f[(df_f['status']=='Finalizado (Pago)') & (df_f['modo_pagamento']=='Pix')]['subtotal'].sum()
                    cred_total = df_f[(df_f['status']=='Finalizado (Pago)') & (df_f['modo_pagamento']=='Cartão de Crédito')]['subtotal'].sum()
                    deb_total = df_f[(df_f['status']=='Finalizado (Pago)') & (df_f['modo_pagamento']=='Cartão de Débito')]['subtotal'].sum()
                    din_total = df_f[(df_f['status']=='Finalizado (Pago)') & (df_f['modo_pagamento']=='Dinheiro')]['subtotal'].sum()
                    
                    st.metric("💰 Faturamento Líquido Total", f"R$ {empresa_total:.2f}")
                    st.markdown("#### 💳 Divisão por Meio de Recebimento")
                    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                    col_p1.metric("⚡ Pix", f"R$ {pix_total:.2f}")
                    col_p2.metric("💳 Crédito", f"R$ {cred_total:.2f}")
                    col_p3.metric("💵 Débito", f"R$ {deb_total:.2f}")
                    col_p4.metric("💰 Dinheiro", f"R$ {din_total:.2f}")
                    
                    st.markdown("---")
                    st.dataframe(df_f.drop(columns=['data_somente']), use_container_width=True, hide_index=True)
                    
            with tab_excluir:
                st.subheader("🗑️ Excluir Dados")
                if not df_prods.empty:
                    p_del = st.selectbox("Produto para Deletar:", [r['nome'] for _, r in df_prods.iterrows()])
                    if st.button("Remover Produto"):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public; DELETE FROM receitas WHERE empresa_id = %s AND produto_id = (SELECT id FROM produtos WHERE empresa_id = %s AND nome = %s); DELETE FROM produtos WHERE empresa_id = %s AND nome = %s", (emp_id, emp_id, p_del, emp_id, p_del))
                            c.commit()
                        st.rerun()

# --- AMBIENTE OPERACIONAL DO GARÇOM ---
with aba_master_operador:
    emp_id = st.session_state.empresa_id_atual
    if not st.session_state.garcom_logado:
        st.subheader("👤 Identificação do Garçom")
        with st.form("login_garcom_form"):
            g_in = st.text_input("Usuário do Garçom:")
            s_in = st.text_input("Senha:", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; SELECT usuario FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (emp_id, g_in.strip().lower(), s_in.strip()))
                    res = cur.fetchone()
                if res:
                    st.session_state.garcom_logado = True
                    st.session_state.usuario_atual = str(res[0])
                    st.rerun()
                else: st.error("Incorreto!")
        with st.expander("Cadastrar Novo Garçom"):
            with st.form("cad_g"):
                ng = st.text_input("Nome Garçom:")
                sg = st.text_input("Senha Garçom:", type="password")
                sm = st.text_input("Senha Master Empresa:", type="password")
                if st.form_submit_button("Confirmar") and ng and sg and sm == st.session_state.senha_master_empresa:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (emp_id, ng.strip(), sg.strip()))
                        c.commit()
                    st.success("Salvo!")
                    
    if st.session_state.garcom_logado:
        st.subheader(f"📋 Operador: {st.session_state.usuario_atual.upper()}")
        if st.button("🔒 Sair do Terminal", use_container_width=True):
            st.session_state.garcom_logado = False
            st.session_state.usuario_atual = ""
            st.session_state.carrinho = []
            st.rerun()
        op = st.radio("Ação:", ["➕ Lançar Pedido", "🧾 Fechar Mesas"], horizontal=True)
        
        # --- LANÇAMENTO DIRETO (SEM CATEGORIAS) ---
        if op == "➕ Lançar Pedido":
            df_pv = pd.read_sql("SELECT id, nome, preco FROM produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
            if df_pv.empty: st.info("Sem produtos.")
            else:
                mesa = st.text_input("Mesa/Comanda:", value="Mesa 01")
                lupa = st.text_input("🔍 Buscar Produto:").strip()
                df_f = df_pv[df_pv['nome'].str.contains(lupa, case=False)] if lupa else df_pv
                p_map = {f"{r['nome']} - R$ {r['preco']:.2f}": (r['id'], r['nome']) for _, r in df_f.iterrows()}
                if p_map:
                    p_sel = st.selectbox("Item:", list(p_map.keys()))
                    qtd = st.number_input("Qtd:", min_value=1, value=1)
                    if st.button("➕ Adicionar", use_container_width=True):
                        id_prod, nome_prod = p_map[p_sel]
                        st.session_state.carrinho.append({"id": int(id_prod), "nome": str(nome_prod), "qtd": int(qtd)})
                if st.session_state.carrinho:
                    for i in st.session_state.carrinho: st.write(f"▪ *{i['qtd']}x* - {i['nome']}")
                    if st.button("🚀 Enviar Pedido", type="primary", use_container_width=True):
                        h = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            for i in st.session_state.carrinho:
                                cur.execute("INSERT INTO pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom, pago) VALUES (%s, %s, %s, %s, 'Pendente', %s, %s, 'Não')", (emp_id, mesa.strip(), int(i['id']), int(i['qtd']), h, st.session_state.usuario_atual))
                                rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(i['id'])])
                                for _, r in rc.iterrows(): cur.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(i['qtd'])), emp_id, int(r['insumo_id'])))
                            c.commit()
                        st.session_state.carrinho = []; st.rerun()
                        
        # --- FECHAMENTO E REGISTRO DA FORMA DE PAGAMENTO ---
        elif op == "🧾 Fechar Mesas":
            p_at = pd.read_sql("SELECT p.id, p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Pendente', 'Confirmado') ORDER BY p.mesa", conn, params=[emp_id])
            if p_at.empty: st.info("Sem comandas abertas.")
            else:
                l_b = st.text_input("🔍 Buscar Mesa:").strip()
                df_m = p_at[p_at['mesa'].str.contains(l_b, case=False)] if l_b else p_at
                if not df_m.empty:
                    mesas_disponiveis = sorted(list(set(df_m['mesa'].tolist())))
                    m_ver = st.selectbox("Selecione a Mesa:", mesas_disponiveis)
                    df_mf = p_at[p_at['mesa'] == m_ver]
                    if 'Pendente' in df_mf['status'].tolist() and st.button("✅ Confirmar Todos"):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public; UPDATE pedidos SET status = 'Confirmado' WHERE empresa_id = %s AND mesa = %s AND status = 'Pendente'", (emp_id, m_ver))
                            c.commit()
                        st.rerun()
                    sub = float(df_mf['subtotal'].sum())
                    st.metric("Total Consumo", f"R$ {sub:.2f}")
                    
                    f_pag = st.selectbox("Forma de Pagamento:", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"])
                    if st.button("💰 Fechar Mesa", type="primary", use_container_width=True):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public; UPDATE pedidos SET status = 'Finalizado (Pago)', pago = 'Sim', modo_pagamento = %s WHERE empresa_id = %s AND mesa = %s", (f_pag, emp_id, m_ver))
                            c.commit()
                        st.rerun()
conn.close()
