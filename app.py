import os
import sys
from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

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

# Conexão dinâmica com o Banco de Dados PostgreSQL
def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

# Trazendo os outros módulos que funcionam perfeitamente
try:
    from views.caixa import renderizar_fechamento_caixa                     
    from views.gerencia import renderizar_painel_gerencial                  
except Exception as e:
    st.error(f"Erro ao carregar dependências locais: {e}")

# --- FUNÇÃO DO GARÇOM INTEGRADA LOCALMENTE (FIM DO MODULENOTFOUNDERROR) ---
def renderizar_terminal_garcom_local():
    st.subheader("👤 Identificação do Garçom")
    with st.form("login_garcom_form"):
        garcom_input = st.text_input("Usuário/Nome do Garçom:")
        senha_garcom = st.text_input("Senha do Garçom:", type="password")
        if st.form_submit_button("Entrar no Sistema", type="primary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("SELECT usuario FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (st.session_state.empresa_id_atual, garcom_input.strip().lower(), senha_garcom.strip()))
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
            senha_admin_validacao = st.text_input("Digite a Senha Master da Empresa para Autorizar:", type="password").strip()
            
            if st.form_submit_button("💼 Confirmar Cadastro do Funcionário") and novo_g_user and novo_g_senha:
                if senha_admin_validacao != st.session_state.senha_master_empresa:
                    st.error("🔒 Autorização negada: A senha master da empresa está incorreta!")
                else:
                    try:
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (st.session_state.empresa_id_atual, novo_g_user, novo_g_senha))
                            c.commit()
                        st.success(f"Garçom '{novo_g_user}' cadastrado! Digite os dados acima para efetuar o login.")
                    except Exception as e: st.error(f"Erro ou funcionário já existente no banco: {e}")

# Inicialização e checagem de tabelas relacionais em lote com chaves estrangeiras
conn = ob_cx()
with conn.cursor() as cur:
    cur.execute("SET search_path TO public;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.empresas (id SERIAL PRIMARY KEY, nome_empresa TEXT UNIQUE NOT NULL, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS public.usuarios (id SERIAL PRIMARY KEY, usuario TEXT, senha TEXT);
        CREATE TABLE IF NOT EXISTS public.estoque (id SERIAL PRIMARY KEY, item TEXT, quantidade REAL);
        CREATE TABLE IF NOT EXISTS public.produtos (id SERIAL PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL);
        CREATE TABLE IF NOT EXISTS public.receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL);
        CREATE TABLE IF NOT EXISTS public.pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Sim', garcom TEXT, modo_pagamento TEXT);
    """)
    cur.execute("ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE public.estoque ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE public.produtos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE public.receitas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE CASCADE;")
    cur.execute("ALTER TABLE public.pedidos ADD COLUMN IF NOT EXISTS modo_pagamento TEXT;")
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
    conn.close()
    st.stop()

# --- CONTROLE DINÂMICO DE VISUALIZAÇÃO DAS ABAS MASTERS ---
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
        
        if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True, key="master_lock_empresa"):
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
            st.warning("🔒 Conteúdo restrito. Insira a senha master correta para acessar as ferramentas de gestão.")
        else:
            if st.button("❌ Bloquear Aba Gerencial Imediatamente", type="secondary", use_container_width=True, key="btn_bloquear_aba_gerencial"):
                if "senha_painel_gerencial_input" in st.session_state:
                    st.session_state["senha_painel_gerencial_input"] = ""
                st.rerun()
            renderizar_painel_gerencial()

# --- CONTEÚDO DA ABA MASTER 2: TERMINAL OPERACIONAL DO GARÇOM ---
with aba_master_operador:
    emp_id = st.session_state.empresa_id_atual
    if not st.session_state.garcom_logado:
        # Chama a nossa função interna sem depender de imports externos quebrados
        renderizar_terminal_garcom_local()
        
    if st.session_state.garcom_logado:
        st.subheader(f"📋 Terminal de Pedidos Ativo — Operador: {st.session_state.usuario_atual.upper()}")
        if st.button("🔒 Sair / Trocar de Garçom", use_container_width=True, key="logoff_garcom_atend"):
            st.session_state.garcom_logado = False
            st.session_state.usuario_atual = ""
            st.session_state.carrinho = []
            st.rerun()
            
        aba_operacao = st.radio("Selecione a Ação:", ["➕ Lançar Pedido (Abrir/Adicionar Itens)", "🧾 Gerenciar Contas / Fechar Mesas"], horizontal=True)
        
        if aba_operacao == "➕ Lançar Pedido (Abrir/Adicionar Itens)":
            df_prods_venda = pd.read_sql("SELECT id, nome, categoria, preco FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
            if df_prods_venda.empty: st.info("Nenhum produto cadastrado no sistema.")
            else:
                mesa_operacao = st.text_input("Número / Nome da Mesa ou Comanda:", value="Mesa 01")
                lupa_produtos = st.text_input("🔍 Lupa - Digite o nome do Produto para pesquisar e filtrar:").strip()
                categoria_filtro = st.selectbox("Filtrar Categoria:", ["Todos"] + sorted(list(set(df_prods_venda['categoria'].tolist()))))
                df_filtrado = df_prods_venda if categoria_filtro == "Todos" else df_prods_venda[df_prods_venda['categoria'] == categoria_filtro]
                
                if lupa_produtos:
                    df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(lupa_produtos, case=False, na=False)]
                    
                prod_map_venda = {f"{row['nome']} - R$ {row['preco']:.2f}": (row['id'], row['nome']) for _, row in df_filtrado.iterrows()}
                if prod_map_venda:
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
                            horario_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            with ob_cx() as c, c.cursor() as cur:
                                cur.execute("SET search_path TO public;")
                                for item in st.session_state.carrinho:
                                    cur.execute("INSERT INTO public.pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom) VALUES (%s, %s, %s, %s, 'Pendente', %s, %s)", (emp_id, mesa_operacao.strip(), int(item['id']), int(item['qtd']), horario_atual, st.session_state.usuario_atual))
                                c.commit()
                            st.success("Pedido lançado!"); st.session_state.carrinho = []; st.rerun()
        else:
            renderizar_fechamento_caixa()
conn.close()
