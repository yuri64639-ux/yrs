from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

# Configuração global da página do ecossistema multi-tenant
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

# Inicialização e manutenção estrita de todas as variáveis de sessão originais
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
if "ocultar_css" not in st.session_state: st.session_state.ocultar_css = True
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# Ocultação do menu nativo do Streamlit via injeção de CSS
if st.session_state.ocultar_css:
    st.markdown("""
        <style>
        #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
        header [data-testid="stToolbar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        header { background-color: transparent !important; }
        </style>
    """, unsafe_allow_html=True)

# Conexão dinâmica com o Banco de Dados PostgreSQL
def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

# Criação e checagem de tabelas relacionais em lote com chaves estrangeiras
conn = ob_cx()
with conn.cursor() as cur:
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
    except Exception: conn.rollback()
conn.commit()
# --- FASE 1: LOGÍSTICA DE ACESSO DO ESTABELECIMENTO ---
if not st.session_state.logado:
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
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as e: st.error(f"Erro no cadastro: {e}")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            df_lista_empresas = pd.read_sql("SELECT id, nome_empresa FROM public.empresas ORDER BY nome_empresa", conn)
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
                        st.session_state.empresa_id_atual = int(resultado[0])
                        st.session_state.senha_master_empresa = str(resultado[1])
                        st.rerun()
                    else: st.error("Credenciais da empresa incorretas!")
            else: st.info("Nenhuma empresa cadastrada ainda.")

    st.markdown("---")
    st.write("### 🛠️ Modo Desenvolvedor")
    col_senha, col_botao = st.columns(2)
    senha_painel = col_senha.text_input("Senha de Autorização:", type="password", key="senha_painel_nativo", label_visibility="collapsed", placeholder="Senha Master")
     
    if st.session_state.ocultar_css:
        if col_botao.button("🔓 Exibir Funções Nativas", type="secondary", use_container_width=True):
            if senha_painel == "orla123":
                st.session_state.ocultar_css = False
                st.rerun()
            else: st.error("Senha Master incorreta!")
    else:
        if col_botao.button("🔒 Ocultar Funções Nativas", type="secondary", use_container_width=True):
            if senha_painel == "orla123":
                st.session_state.ocultar_css = True
                st.rerun()
            else: st.error("Senha Master incorreta!")
    st.stop()
# --- FASE 2: BARREIRA DO MODO DESENVOLVEDOR LOGADO ---
if st.session_state.logado and not st.session_state.garcom_logado:
    st.markdown("---")
    st.write("### 🛠️ Modo Desenvolvedor / Gerência")
    col_senha, col_botao = st.columns(2)
    senha_painel = col_senha.text_input("Senha de Autorização:", type="password", key="senha_painel_nativo_logado", label_visibility="collapsed", placeholder="Senha Master da Empresa")
     
    if st.session_state.ocultar_css:
        if col_botao.button("🔓 Exibir Funções Nativas", type="secondary", use_container_width=True):
            if senha_painel == st.session_state.senha_master_empresa:
                st.session_state.ocultar_css = False
                st.rerun()
            else: st.error("Senha Master incorreta!")
    else:
        if col_botao.button("🔒 Ocultar Funções Nativas", type="secondary", use_container_width=True):
            if senha_painel == st.session_state.senha_master_empresa:
                st.session_state.ocultar_css = True
                st.rerun()
            else: st.error("Senha Master incorreta!")

# INTERFACE ADMINISTRATIVA COMPLETA
if st.session_state.logado and not st.session_state.ocultar_css:
    emp_id = st.session_state.empresa_id_atual
    cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
    
    st.markdown("---")
    st.title("⚙️ Painel de Controle Gerencial")
    
    if st.button("🔒 Bloquear Terminal da Empresa", type="primary", use_container_width=True):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.garcom_logado = False
        st.session_state.ocultar_css = True
        st.session_state.carrinho = []
        st.rerun()
    
    try:
        df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque WHERE empresa_id = %s ORDER BY item", conn, params=[emp_id])
        df_prods = pd.read_sql("SELECT id, nome FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
    except Exception as e:
        st.error(f"Erro ao carregar tabelas do banco: {e}")
        st.stop()

    subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])

    # --- 1. ESTOQUE ---
    with subtabs:
        st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
        df_est_visual = df_est.copy()
        if not df_est_visual.empty: 
            df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual (L / Kg)"]
        st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
        
        with st.expander("➕ Alimentar Estoque"):
            with st.form("f_ins", clear_on_submit=True):
                n_i = st.text_input("Insumo:")
                q_i = st.number_input("Qtd Inteira (Litros, Quilos ou Un):", min_value=0.0, value=1.0, step=1.0)
                if st.form_submit_button("Salvar") and n_i.strip():
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            INSERT INTO public.estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) 
                            ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = public.estoque.quantidade + EXCLUDED.quantidade
                        """, (emp_id, n_i.strip(), q_i))
                        c.commit()
                    st.success("Estoque atualizado!")
                    st.rerun()

    # --- 2. CANCELAMENTOS ---
    with subtabs:
        st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
        p_ab = pd.read_sql("""
            SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id 
            FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id 
            WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa
        """, conn, params=[emp_id])
        
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
                            cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])), emp_id, int(r['insumo_id'])))
                        cur.execute("DELETE FROM public.pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                        c.commit()
                    st.success("Item removido e estoque devolvido com segurança!"); st.rerun()
    # --- 3. CADASTRO EM MASSA ---
    with subtabs:
        st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
        st.write("Cole a sua lista abaixo seguindo o formato exato: **Nome, Categoria, Preço** (um produto por linha).")
        st.caption("Categorias aceitas: Drinks, Cervejas, Sem Álcool, Porções, Pratos Principais, Sobremesas")
        
        with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
            texto_produtos = st.text_area("Cole seus produtos aqui:", height=250, placeholder="Exemplo:\nCaipirinha, Drinks, 15.0\nHeineken, Cervejas, 12.0")
            botao_gravar = st.form_submit_button("🔥 Gravar Todos os Produtos")
            
            if botao_gravar and texto_produtos.strip():
                linhas = texto_produtos.strip().split("\n")
                itens_gravados = 0
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    for linha in hashtags:
                        if "," in linha:
                            partes = linha.split(",")
                            if len(partes) == 3:
                                n_p = partes[0].strip()
                                c_p = partes[1].strip()
                                p_p = partes[2].strip()
                                cat_valida = [c for c in cats if c.lower() == c_p.lower()]
                                if n_p and cat_valida:
                                    try:
                                        preco_float = float(p_p)
                                        categoria_final = str(cat_valida[0])
                                        cur.execute("""
                                            INSERT INTO public.produtos (empresa_id, nome, categoria, preco) 
                                            VALUES (%s, %s, %s, %s) 
                                            ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco
                                        """, (emp_id, n_p, categoria_final, preco_float))
                                        itens_gravados += 1
                                    except ValueError: pass
                    c.commit()
                if itens_gravados > 0: st.success(f"🚀 Sucesso! {itens_gravados} produtos processados e salvos!"); st.rerun()

    # --- 4. RECEITAS COM 4 INGREDIENTES ---
    with subtabs:
        st.subheader("🔬 Montar Ficha Técnica (Até 4 Ingredientes)")
        if not df_prods.empty and not df_est.empty:
            lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
            lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
            d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
            d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
            
            with st.form("f_vinc_multi", clear_on_submit=True):
                p_sel = d_p[st.selectbox("Selecione o Produto final:", lista_prods, key="sel_prod_receita_base")]
                st.markdown("---")
                col1, col2 = st.columns(2)
                i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="rec_i1")
                q1 = col2.number_input("Qtd gasta 1 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q1")
                col3, col4 = st.columns(2)
                i2 = col3.selectbox("Ingrediente 2:", lista_insumos, key="rec_i2")
                q2 = col4.number_input("Qtd gasta 2 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q2")
                col5, col6 = st.columns(2)
                i3 = col5.selectbox("Ingrediente 3:", lista_insumos, key="rec_i3")
                q3 = col6.number_input("Qtd gasta 3 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q3")
                col7, col8 = st.columns(2)
                i4 = col7.selectbox("Ingrediente 4:", lista_insumos, key="rec_i4")
                q4 = col8.number_input("Qtd gasta 4 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q4")
                
                if st.form_submit_button("🔥 Gravar Receita Completa"):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        if i1 != "---" and q1 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, p_sel, d_i[i1], q1))
                        if i2 != "---" and q2 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, p_sel, d_i[i2], q2))
                        if i3 != "---" and q3 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, p_sel, d_i[i3], q3))
                        if i4 != "---" and q4 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, p_sel, d_i[i4], q4))
                        c.commit()
                    st.success("Ficha técnica salva!"); st.rerun()
        else: st.info("Cadastre insumos e produtos antes.")

    # --- 5. RELATÓRIOS ---
    with subtabs:
        st.subheader("📊 Resumo Financeiro Detalhado")
        vendas_df = pd.read_sql("SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC", conn, params=[emp_id])
        if vendas_df.empty: st.info("Nenhuma comanda histórica para esta empresa.")
        else:
            empresa_total, garcons_total, pendente_total = 0.0, 0.0, 0.0
            for mesa_id, grupo in vendas_df.groupby('mesa'):
                sub_mesa = float(grupo['subtotal'].sum())
                status_mesa = grupo['status'].iloc[0]
                taxa_marcada = int(grupo['taxa_paga'].iloc[0]) == 1
                if status_mesa == 'Finalizado (Pago)':
                    empresa_total += sub_mesa
                    if taxa_marcada: garcons_total += (sub_mesa * 0.10)
                else: pendente_total += sub_mesa
            c1, c2, c3 = st.columns(3); c1.metric("💰 Faturamento Líquido", f"R$ {empresa_total:.2f}"); c2.metric("🍹 Caixinha (10%)", f"R$ {garcons_total:.2f}"); c3.metric("⚠️ Perdas", f"R$ {pendente_total:.2f}")
            st.dataframe(vendas_df, use_container_width=True, hide_index=True)
    # --- 6. EXCLUIR ---
    with subtabs:
        st.subheader("🗑️ Remover Produtos ou Insumos do Sistema")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if not df_prods.empty:
                prod_para_excluir = st.selectbox("Selecione o Produto para deletar permanentemente:", [r['nome'] for _, r in df_prods.iterrows()], key="del_prod_sel")
                if st.button("❌ Excluir Produto", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("DELETE FROM public.receitas WHERE empresa_id = %s AND produto_id = (SELECT id FROM public.produtos WHERE empresa_id = %s AND nome = %s)", (emp_id, emp_id, prod_para_excluir))
                        cur.execute("DELETE FROM public.produtos WHERE empresa_id = %s AND nome = %s", (emp_id, prod_para_excluir))
                        c.commit()
                    st.success("Removido com sucesso!"); st.rerun()
        with col_del2:
            if not df_est.empty:
                insumo_para_excluir = st.selectbox("Selecione o Insumo para deletar permanentemente:", [r['item'] for _, r in df_est.iterrows()], key="del_ins_sel")
                if st.button("❌ Excluir Insumo", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; DELETE FROM public.receitas WHERE empresa_id = %s AND insumo_id = (SELECT id FROM public.estoque WHERE empresa_id = %s AND item = %s); DELETE FROM public.estoque WHERE empresa_id = %s AND item = %s;", (emp_id, emp_id, insumo_para_excluir, emp_id, insumo_para_excluir))
                        c.commit()
                    st.success("Removido com sucesso!"); st.rerun()
    st.stop()
# --- FASE 3: IDENTIFICAÇÃO OU CADASTRO DO GARÇOM OPERADOR ---
if st.session_state.logado and not st.session_state.garcom_logado:
    aba_garcom_acesso = st.radio("Selecione o Acesso do Garçom:", ["Fazer Login", "Cadastrar Novo Garçom"], horizontal=True)
    
    if aba_garcom_acesso == "Cadastrar Novo Garçom":
        with st.form("cadastro_garcom_form", clear_on_submit=True):
            st.subheader("👤 Cadastrar Novo Garçom no Terminal")
            novo_g_user = st.text_input("Defina o Nome/Usuário do Garçom:").strip()
            novo_g_senha = st.text_input("Defina a Senha de Acesso:", type="password").strip()
            if st.form_submit_button("💼 Confirmar Cadastro do Funcionário", type="primary") and novo_g_user and novo_g_senha:
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (st.session_state.empresa_id_atual, novo_g_user, novo_g_senha))
                        c.commit()
                    st.success(f"Garçom '{novo_g_user}' cadastrado com sucesso! Mude para a aba de login.")
                except Exception as e: st.error(f"Erro ou funcionário já existente no banco: {e}")
    else:
        with st.form("login_garcom_form"):
            st.subheader("👤 Identificação do Garçom")
            garcom_input = st.text_input("Usuário/Nome do Garçom:")
            senha_garcom = st.text_input("Senha do Garçom:", type="password")
            if st.form_submit_button("Entrar no Sistema", type="primary") and garcom_input and senha_garcom:
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("SELECT usuario FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (st.session_state.empresa_id_atual, garcom_input.strip().lower(), senha_garcom.strip()))
                    res_garcom = cur.fetchone()
                if res_garcom:
                    st.session_state.garcom_logado = True
                    st.session_state.usuario_atual = str(res_garcom[0])
                    st.rerun()
                else: st.error("Credenciais do garçom incorretas!")
    st.stop()

# --- FASE 4: TERMINAL ATIVO DE OPERAÇÕES DO GARÇOM ---
if st.session_state.garcom_logado:
    emp_id = st.session_state.empresa_id_atual
    st.title(f"📋 Terminal Operacional de Pedidos")
    st.caption(f"Operador: {st.session_state.usuario_atual.upper()}")
    
    if st.button("🔒 Sair / Trocar de Garçom", use_container_width=True):
        st.session_state.garcom_logado = False; st.session_state.usuario_atual = ""; st.session_state.carrinho = []; st.rerun()
        
    aba_operacao = st.radio("Selecione a Ação:", ["➕ Lançar Pedido (Abrir/Adicionar Itens)", "🧾 Gerenciar Contas / Fechar Mesas"], horizontal=True)
    
    if aba_operacao == "➕ Lançar Pedido (Abrir/Adicionar Itens)":
        df_prods_venda = pd.read_sql("SELECT id, nome, categoria, preco FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
        if df_prods_venda.empty: st.info("Nenhum produto cadastrado no sistema.")
        else:
            mesa_operacao = st.text_input("Número / Nome da Mesa ou Comanda:", value="Mesa 01")
            categoria_filtro = st.selectbox("Filtrar Categoria:", ["Todos"] + sorted(list(set(df_prods_venda['categoria'].tolist()))))
            df_filtrado = df_prods_venda if categoria_filtro == "Todos" else df_prods_venda[df_prods_venda['categoria'] == categoria_filtro]
            prod_map_venda = {f"{row['nome']} - R$ {row['preco']:.2f}": (row['id'], row['nome']) for _, row in df_filtrado.iterrows()}
            
            if prod_map_venda:
                produto_selecionado_string = st.selectbox("Escolha o Item:", list(prod_map_venda.keys()))
                qtd_solicitada = st.number_input("Quantidade Desejada:", min_value=1, value=1, step=1)
                if st.button("➕ Adicionar ao Carrinho", use_container_width=True):
                    id_p_venda, nome_p_venda = prod_map_venda[produto_selecionado_string]
                    st.session_state.carrinho.append({"id": id_p_venda, "nome": nome_p_venda, "qtd": qtd_solicitada})
                    st.toast(f"{nome_p_venda} adicionado!")
            
            if st.session_state.carrinho:
                st.markdown("### 🛒 Itens no Carrinho Corrente")
                for item in st.session_state.carrinho: st.write(f"▪ *{item['qtd']}x* - {item['nome']}")
                
                confirmacao_garcom = st.checkbox("✅ Eu confirmo que conferi os itens do pedido com o cliente.", value=False)
                
                col_limpar, col_enviar = st.columns(2)
                if col_limpar.button("🗑️ Limpar Carrinho", use_container_width=True): st.session_state.carrinho = []; st.rerun()
                
                if col_enviar.button("🚀 Confirmar e Enviar Pedido", type="primary", use_container_width=True):
                    if not confirmacao_garcom:
                        st.error("🔒 Atenção: Você precisa marcar o campo de confirmação antes de enviar!")
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

    elif aba_operacao == "🧾 Gerenciar Contas / Fechar Mesas":
        pedidos_ativos = pd.read_sql("""
            SELECT p.id, p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status 
            FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id 
            WHERE p.empresa_id = %s AND p.status = 'Pendente' ORDER BY p.mesa
        """, conn, params=[emp_id])
        
        if pedidos_ativos.empty: st.info("Não há nenhuma conta ou mesa aberta no momento.")
        else:
            mesas_abertas = sorted(list(set(pedidos_ativos['mesa'].tolist())))
            mesa_ver = st.selectbox("Selecione a Mesa para Fechamento:", mesas_abertas)
            df_mesa_filtrada = pedidos_ativos[pedidos_ativos['mesa'] == mesa_ver]
            
            lupa_busca = st.text_input("🔍 Lupa de Busca (Pesquisar item lançado nesta mesa):", value="", placeholder="Digite o nome do produto...")
            if lupa_busca.strip():
                df_mesa_filtrada = df_mesa_filtrada[df_mesa_filtrada['produto'].str.contains(lupa_busca, case=False, na=False)]
            
            st.markdown(f"#### 📋 Consumo Atual da {mesa_ver}")
            st.dataframe(df_mesa_filtrada[["produto", "quantidade", "preco", "subtotal"]], use_container_width=True, hide_index=True)
            
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
                    cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE empresa_id = %s AND mesa = %s AND status = 'Pendente'", (valor_taxa_salvar, emp_id, mesa_ver))
                    c.commit()
                st.success(f"Conta da {mesa_ver} fechada com sucesso!"); st.rerun()
conn.close()
