import os
from datetime import datetime
import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor
import pandas as pd

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

# Gerenciamento Centralizado de Conexão com o Banco de Dados (Singleton Pattern para o Estado da Aplicação)
@st.cache_resource
def inicializar_pool_conexao():
    """Mantém uma conexão persistente e reutilizável com tratamento dinâmico de configurações"""
    try:
        c = st.secrets["connections"]["postgresql"]
        if "url" in c:
            return psycopg2.connect(c["url"])
        return psycopg2.connect(
            host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
            user=c.get("username"), password=c.get("password"), sslmode="require"
        )
    except Exception as e:
        st.error(f"Erro fatal ao conectar ao PostgreSQL: {e}")
        st.stop()

def obter_conexao_segura():
    """Retorna a conexão ativa, restabelecendo-a caso tenha caído (Auto-Reconnect)"""
    conn_obj = inicializar_pool_conexao()
    if conn_obj.closed != 0:
        st.cache_resource.clear()
        conn_obj = inicializar_pool_conexao()
    return conn_obj

# Execução segura da inicialização estrutural das tabelas relacionais
conn = obter_conexao_segura()
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
    try: cur.execute("ALTER TABLE public.estoque ADD CONSTRAINT unique_empresa_item UNIQUE(empresa_id, item);")
    except Exception: conn.rollback()
    try: cur.execute("ALTER TABLE public.produtos ADD CONSTRAINT unique_empresa_produto UNIQUE(empresa_id, nome);")
    except Exception: conn.rollback()
    try: cur.execute("ALTER TABLE public.receitas ADD CONSTRAINT unique_empresa_produto_insumo UNIQUE(empresa_id, produto_id, insumo_id);")
    except Exception: conn.rollback()
conn.commit()

# --- FUNÇÕES COM CACHE DE DADOS PARA MINIMIZAR REQUISIÇÕES AO BANCO ---
@st.cache_data(ttl=60)
def listar_empresas_cadastradas():
    """Busca e faz cache da lista de empresas ativas no ecossistema"""
    try:
        c_local = obter_conexao_segura()
        df = pd.read_sql("SELECT id, nome_empresa FROM public.empresas ORDER BY nome_empresa", c_local)
        return {row["nome_empresa"]: row["id"] for _, row in df.iterrows()} if not df.empty else {}
    except Exception:
        return {}

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
                    c_local = obter_conexao_segura()
                    with c_local.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("INSERT INTO public.empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c_local.commit()
                    st.cache_data.clear()  # Invalida o cache para listar a nova empresa imediatamente
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as e: st.error(f"Erro no cadastro: {e}")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            dict_empresas = listar_empresas_cadastradas()
            
            if dict_empresas:
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                user_input = st.text_input("Usuário Master da Empresa:")
                senha_input = st.text_input("Senha Master:", type="password")
                submetido = st.form_submit_button("Liberar Terminal", type="primary")
                
                if submetido:
                    id_empresa_login = dict_empresas[empresa_selecionada]
                    c_local = obter_conexao_segura()
                    with c_local.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            SELECT empresa_id, senha FROM public.usuarios 
                            WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s
                        """, (id_empresa_login, user_input.strip(), senha_input.strip()))
                        resultado = cur.fetchone()
                    
                    if resultado:
                        st.session_state.logado = True
                        st.session_state.empresa_id_atual = int(resultado[0])
                        st.session_state.senha_master_empresa = str(resultado[1])
                        st.rerun()
                    else: st.error("Credenciais da empresa incorretas!")
            else: st.info("Nenhuma empresa cadastrada ainda.")
    st.stop()

# Layout Geral: Abas Masters de Nível Superior Logo Após o Login da Empresa
aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])
with aba_master_sistema:
    emp_id = st.session_state.empresa_id_atual
    cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
    
    if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True, key="master_lock_empresa"):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.garcom_logado = False
        st.session_state.carrinho = []
        st.rerun()
    
    # Carregamento pontual dos dados para exibição do painel gerencial
    c_gerencial = obter_conexao_segura()
    df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque WHERE empresa_id = %s ORDER BY item", c_gerencial, params=[emp_id])
    df_prods = pd.read_sql("SELECT id, nome FROM public.produtos WHERE empresa_id = %s ORDER BY nome", c_gerencial, params=[emp_id])
    
    subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])

    # --- 1. ESTOQUE ---
    with subtabs[0]:
        st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
        df_est_visual = df_est.copy()
        if not df_est_visual.empty: 
            df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual"]
        st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
        
        with st.expander("➕ Alimentar Estoque"):
            with st.form("f_ins", clear_on_submit=True):
                n_i = st.text_input("Insumo:")
                q_i = st.number_input("Qtd Inteira (Litros, Quilos ou Un):", min_value=0.0, value=1.0, step=1.0)
                if st.form_submit_button("Salvar") and n_i.strip():
                    c_local = obter_conexao_segura()
                    with c_local.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            INSERT INTO public.estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) 
                            ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = public.estoque.quantidade + EXCLUDED.quantidade
                        """, (emp_id, n_i.strip(), q_i))
                        c_local.commit()
                    st.success("Estoque atualizado!")
                    st.rerun()

    # --- 2. CANCELAMENTOS (SEGURO E ATÔMICO) ---
    with subtabs[1]:
        st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
        p_ab = pd.read_sql("""
            SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id 
            FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id 
            WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa
        """, c_gerencial, params=[emp_id])
        
        if p_ab.empty: st.info("Nenhuma comanda aberta para cancelamento.")
        else:
            m_sel = st.selectbox("Selecione a Mesa para auditar:", sorted(list(set(p_ab['mesa'].tolist()))))
            for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
                col1, col2 = st.columns(2); col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
                if col2.button("Deletar Item", key=f"cn_{it['id']}"):
                    c_local = obter_conexao_segura()
                    try:
                        with c_local.cursor(cursor_factory=DictCursor) as cur:
                            cur.execute("SET search_path TO public;")
                            # Busca todas as receitas associadas ao item de uma vez só
                            cur.execute("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", (emp_id, int(it['produto_id'])))
                            receitas = cur.fetchall()
                            
                            # Atualiza os insumos de forma atômica dentro da mesma transação do banco
                            for r in receitas:
                                qtd_calculada = (float(r['qtd_insumo']) / 1000.0) * int(it['quantidade'])
                                cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", (qtd_calculada, emp_id, int(r['insumo_id'])))
                            
                            cur.execute("DELETE FROM public.pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                            c_local.commit()
                        st.success("Item removido e estoque devolvido com segurança!")
                        st.rerun()
                    except Exception as e:
                        c_local.rollback()
                        st.error(f"Erro ao processar o estorno no estoque: {e}")
                        
    # --- 3. CADASTRO EM MASSA ---
    with subtabs[2]:
        st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
        st.write("Cole a sua lista abaixo seguindo o formato exato: **Nome, Categoria, Preço** (um produto por linha).")
        st.caption("Categorias aceitas: Drinks, Cervejas, Sem Álcool, Porções, Pratos Principais, Sobremesas")
        
        with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
            texto_produtos = st.text_area("Cole seus produtos aqui:", height=250, placeholder="""Exemplo:
Caipirinha, Drinks, 15.0
Heineken, Cervejas, 12.0""")
            botao_gravar = st.form_submit_button("🔥 Gravar Todos os Produtos")
            
            if botao_gravar and texto_produtos.strip():
                linhas = texto_produtos.strip().split("\n")
                itens_gravados = 0
                c_local = obter_conexao_segura()
                try:
                    with c_local.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        for linha in linhas:
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
                        c_local.commit()
                    if itens_gravados > 0: 
                        st.success(f"🚀 Sucesso! {itens_gravados} produtos salvos!")
                        st.rerun()
                except Exception as e:
                    c_local.rollback()
                    st.error(f"Erro ao salvar lote de produtos: {e}")

    # --- 4. RECEITAS COM 4 INGREDIENTES ---
    with subtabs[3]:
        st.subheader("🔬 Montar Ficha Técnica (Até 4 Ingredientes)")
        if not df_prods.empty and not df_est.empty:
            lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
            lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
            d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
            d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
            
            with st.form("f_vinc_multi", clear_on_submit=True):
                p_sel = d_p[st.selectbox("Selecione o Produto final:", lista_prods, key="sel_prod_receita_base")]
                st.markdown("---")
                col1, col2 = st.columns(2); i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="rec_i1"); q1 = col2.number_input("Qtd gasta 1 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q1")
                col3, col4 = st.columns(2); i2 = col3.selectbox("Ingrediente 2:", lista_insumos, key="rec_i2"); q2 = col4.number_input("Qtd gasta 2 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q2")
                col5, col6 = st.columns(2); i3 = col5.selectbox("Ingrediente 3:", lista_insumos, key="rec_i3"); q3 = col6.number_input("Qtd gasta 3 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q3")
                col7, col8 = st.columns(2); i4 = col7.selectbox("Ingrediente 4:", lista_insumos, key="rec_i4"); q4 = col8.number_input("Qtd gasta 4 (em ml ou g):", min_value=0.0, value=0.0, step=5.0, key="rec_q4")
                
                if st.form_submit_button("🔥 Gravar Receita Completa"):
                    c_local = obter_conexao_segura()
                    try:
                        with c_local.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            inputs_validados = [(i1, q1), (i2, q2), (i3, q3), (i4, q4)]
                            for insumo_nome, qtd in inputs_validados:
                                if insumo_nome != "---" and qtd > 0:
                                    cur.execute("""
                                        INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) 
                                        VALUES (%s, %s, %s, %s) 
                                        ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo
                                    """, (emp_id, p_sel, d_i[insumo_nome], qtd))
                            c_local.commit()
                        st.success("Ficha técnica salva de forma consistente!"); st.rerun()
                    except Exception as e:
                        c_local.rollback()
                        st.error(f"Erro ao salvar receita: {e}")
        else: st.info("Cadastre insumos e produtos na conta antes.")

    # --- 5. RELATÓRIOS ---
    with subtabs[4]:
        st.subheader("📊 Resumo Financeiro Detalhado")
        vendas_df = pd.read_sql("""
            SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario 
            FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id 
            WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC
        """, c_gerencial, params=[emp_id])
        
        if vendas_df.empty: st.info("Nenhuma comanda histórica para esta empresa.")
        else:
            empresa_total, garcons_total, pendente_total = 0.0, 0.0, 0.0
            for mesa_id, group in vendas_df.groupby('mesa'):
                sub_mesa = float(group['subtotal'].sum())
                status_mesa = group['status'].iloc[0]
                taxa_marcada = int(group['taxa_paga'].iloc[0]) == 1
                if status_mesa == 'Finalizado (Pago)':
                    empresa_total += sub_mesa
                    if taxa_marcada: garcons_total += (sub_mesa * 0.10)
                else: pendente_total += sub_mesa
            c1, c2, c3 = st.columns(3); c1.metric("💰 Faturamento Líquido", f"R$ {empresa_total:.2f}"); c2.metric("🍹 Caixinha (10%)", f"R$ {garcons_total:.2f}"); c3.metric("⚠️ Perdas", f"R$ {pendente_total:.2f}")
            st.dataframe(vendas_df, use_container_width=True, hide_index=True)

    # --- 6. EXCLUIR ---
    with subtabs[5]:
        st.subheader("🗑️ Remover Produtos ou Insumos do Sistema")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if not df_prods.empty:
                prod_para_excluir = st.selectbox("Selecione o Produto para deletar permanentemente:", [r['nome'] for _, r in df_prods.iterrows()], key="del_prod_sel")
                if st.button("❌ Excluir Produto", use_container_width=True):
                    c_local = obter_conexao_segura()
                    try:
                        with c_local.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("DELETE FROM public.receitas WHERE empresa_id = %s AND produto_id = (SELECT id FROM public.produtos WHERE empresa_id = %s AND nome = %s)", (emp_id, emp_id, prod_para_excluir))
                            cur.execute("DELETE FROM public.produtos WHERE empresa_id = %s AND nome = %s", (emp_id, prod_para_excluir))
                            c_local.commit()
                        st.success("Removido com sucesso!"); st.rerun()
                    except Exception as e:
                        c_local.rollback()
                        st.error(f"Erro ao deletar produto: {e}")
        with col_del2:
            if not df_est.empty:
                insumo_para_excluir = st.selectbox("Selecione o Insumo para deletar permanentemente:", [r['item'] for _, r in df_est.iterrows()], key="del_ins_sel")
                if st.button("❌ Excluir Insumo", use_container_width=True):
                    c_local = obter_conexao_segura()
                    try:
                        with c_local.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("DELETE FROM public.receitas WHERE empresa_id = %s AND insumo_id = (SELECT id FROM public.estoque WHERE empresa_id = %s AND item = %s);", (emp_id, emp_id, insumo_para_excluir))
                            cur.execute("DELETE FROM public.estoque WHERE empresa_id = %s AND item = %s;", (emp_id, insumo_para_excluir))
                            c_local.commit()
                        st.success("Removido com sucesso!"); st.rerun()
                    except Exception as e:
                        c_local.rollback()
                        st.error(f"Erro ao deletar insumo: {e}")

# --- RENDERIZAÇÃO DA ABA MASTER 2: TERMINAL OPERACIONAL DO GARÇOM ---
with aba_master_operador:
    if not st.session_state.garcom_logado:
        st.subheader("👤 Identificação do Garçom")
        
        with st.form("login_garcom_form"):
            garcom_input = st.text_input("Usuário/Nome do Garçom:")
            senha_garcom = st.text_input("Senha do Garçom:", type="password")
            if st.form_submit_button("Entrar no Sistema", type="primary"):
                c_local = obter_conexao_segura()
                with c_local.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("""
                        SELECT usuario FROM public.usuarios 
                        WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s
                    """, (st.session_state.empresa_id_atual, garcom_input.strip().lower(), senha_garcom.strip()))
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
                        c_local = obter_conexao_segura()
                        with c_local.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (st.session_state.empresa_id_atual, novo_g_user, novo_g_senha))
                            c_local.commit()
                        st.success(f"Garçom '{novo_g_user}' cadastrado com sucesso!")
                    except Exception as e: st.error(f"Erro ou funcionário já existente: {e}")

    if st.session_state.garcom_logado:
        emp_id = st.session_state.empresa_id_atual
        st.subheader(f"📋 Terminal de Pedidos Ativo — Operador: {st.session_state.usuario_atual.upper()}")
        
        if st.button("🔒 Sair / Trocar de Garçom", use_container_width=True, key="logoff_garcom_atend"):
            st.session_state.garcom_logado = False
            st.session_state.usuario_atual = ""
            st.session_state.carrinho = []
            st.rerun()
            
        aba_operacao = st.radio("Selecione a Ação:", ["➕ Lançar Pedido (Abrir/Adicionar Itens)", "🧾 Gerenciar Contas / Fechar Mesas"], horizontal=True)
        
        c_operacional = obter_conexao_segura()
        
        # 1. LANÇAR PEDIDO E ADICIONAR ITENS AO CARRINHO NATIVO
        if aba_operacao == "➕ Lançar Pedido (Abrir/Adicionar Itens)":
            df_prods_venda = pd.read_sql("SELECT id, nome, categoria, preco FROM public.produtos WHERE empresa_id = %s ORDER BY nome", c_operacional, params=[emp_id])
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
                    if col_limpar.button("🗑️ Limpar Carrinho", use_container_width=True): 
                        st.session_state.carrinho = []
                        st.rerun()
                    if col_enviar.button("🚀 Confirmar e Enviar Pedido", type="primary", use_container_width=True):
                        if not confirmacao_garcom:
                            st.error("🔒 Atenção: Você precisa marcar o campo de confirmação antes de enviar!")
                        else:
                            horario_atual = datetime.now().strftime("%H:%M:%S")
                            c_local = obter_conexao_segura()
                            try:
                                with c_local.cursor(cursor_factory=DictCursor) as cur:
                                    cur.execute("SET search_path TO public;")
                                    for item in st.session_state.carrinho:
                                        cur.execute("""
                                            INSERT INTO public.pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom) 
                                            VALUES (%s, %s, %s, %s, 'Pendente', %s, %s)
                                        """, (emp_id, mesa_operacao.strip(), item['id'], item['qtd'], horario_atual, st.session_state.usuario_atual))
                                        
                                        # Processa a baixa dos insumos de forma transacional e unificada
                                        cur.execute("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", (emp_id, item['id']))
                                        receitas = cur.fetchall()
                                        for r in receitas:
                                            qtd_calculada = (float(r['qtd_insumo']) / 1000.0) * int(item['qtd'])
                                            cur.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE empresa_id = %s AND id = %s", (qtd_calculada, emp_id, int(r['insumo_id'])))
                                    c_local.commit()
                                st.success("Pedido lançado com sucesso!"); st.session_state.carrinho = []; st.rerun()
                            except Exception as e:
                                c_local.rollback()
                                st.error(f"Erro ao processar baixa e registrar pedido: {e}")

        # 2. GERENCIAR CONTAS ATIVAS
        elif aba_operacao == "🧾 Gerenciar Contas / Fechar Mesas":
            pedidos_ativos = pd.read_sql("""
                SELECT p.id, p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status 
                FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id 
                WHERE p.empresa_id = %s AND p.status IN ('Pendente', 'Confirmado') ORDER BY p.mesa
            """, c_operacional, params=[emp_id])
            
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
                            c_local = obter_conexao_segura()
                            with c_local.cursor() as cur:
                                cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Confirmado' WHERE empresa_id = %s AND mesa = %s AND status = 'Pendente'", (emp_id, mesa_ver))
                                c_local.commit()
                            st.success("Todos os itens pendentes foram confirmados!"); st.rerun()
                    
                    for _, row in df_mesa_filtrada.iterrows():
                        c_item, c_status, c_acao = st.columns(3)
                        c_item.write(f"▪ **{row['quantidade']}x** {row['produto']} *(R$ {row['subtotal']:.2f})*")
                        if row['status'] == 'Pendente':
                            c_status.warning("⏳ Pendente")
                            if c_acao.button("Confirmar", key=f"conf_ind_{row['id']}"):
                                c_local = obter_conexao_segura()
                                with c_local.cursor() as cur:
                                    cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Confirmado' WHERE id = %s AND empresa_id = %s", (int(row['id']), emp_id))
                                    c_local.commit()
                                st.rerun()
                        else: c_status.success("🔥 Confirmado")
                    
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
                        c_local = obter_conexao_segura()
                        with c_local.cursor() as cur:
                            cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE empresa_id = %s AND mesa = %s AND status IN ('Pendente', 'Confirmado')", (valor_taxa_salvar, emp_id, mesa_ver))
                            c_local.commit()
                        st.success(f"Conta da {mesa_ver} fechada com sucesso!"); st.rerun()
