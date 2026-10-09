import psycopg2
import streamlit as st

def ob_cx():
    """Gerencia a conexão dinâmica com o Banco de Dados PostgreSQL baseado nos secrets do Streamlit."""
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: 
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), 
        port=c.get("port", 5432), 
        database=c.get("database"), 
        user=c.get("username"), 
        password=c.get("password"), 
        sslmode="require"
    )

def inicializar_banco():
    """Executa as DDLs e garante o ecossistema relacional e multi-tenant isolado."""
    conn = ob_cx()
    with conn.cursor() as cur:
        cur.execute("SET search_path TO public;")
        cur.execute("CREATE TABLE IF NOT EXISTS empresas (id SERIAL PRIMARY KEY, nome_empresa TEXT UNIQUE NOT NULL, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, senha TEXT);")
        cur.execute("CREATE TABLE IF NOT EXISTS estoque (id SERIAL PRIMARY KEY, item TEXT, quantidade REAL);")
        cur.execute("CREATE TABLE IF NOT EXISTS produtos (id SERIAL PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL);")
        cur.execute("CREATE TABLE IF NOT EXISTS receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL);")
        cur.execute("CREATE TABLE IF NOT EXISTS pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Não', garcom TEXT, modo_pagamento TEXT);")
        
        # Adição segura de colunas e chaves estrangeiras
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE estoque ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE produtos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE receitas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        conn.commit()
        
        # Remoção de constraints globais legadas
        try: cur.execute("ALTER TABLE produtos DROP CONSTRAINT IF EXISTS produtos_nome_key CASCADE;")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE estoque DROP CONSTRAINT IF EXISTS estoque_item_key CASCADE;")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_usuario_key CASCADE;")
        except: conn.rollback()
        conn.commit()
        
        # Criação de chaves únicas compostas por Tenant (empresa_id)
        try: cur.execute("ALTER TABLE usuarios ADD CONSTRAINT unique_empresa_usuario UNIQUE(empresa_id, usuario);")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE estoque ADD CONSTRAINT unique_empresa_item UNIQUE(empresa_id, item);")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE produtos ADD CONSTRAINT unique_empresa_produto UNIQUE(empresa_id, nome);")
        except: conn.rollback()
    conn.commit()
    conn.close()
import streamlit as st
import pandas as pd
from core_db import ob_cx

def render_login_cadastro():
    """Gerencia as telas de autenticação e criação de conta multi-tenant."""
    conn = ob_cx()
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
                except Exception as e: 
                    st.error(f"Erro no cadastro: {e}")
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
                    else: 
                        st.error("Credenciais da empresa incorretas!")
            else: 
                st.info("Nenhuma empresa cadastrada ainda.")
    conn.close()
    st.stop()
import streamlit as st
import pandas as pd
from core_db import ob_cx

def render_painel_gerencial(emp_id, cats):
    """Renderiza o painel gerencial administrativo protegido por senha."""
    permitir_render_gerencial = False
    
    if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.garcom_logado = False
        st.session_state.carrinho = []
        st.rerun()
        
    st.markdown("---")
    st.subheader("🔑 Autenticação Gerencial Requerida")
    senha_gerencial_digitada = st.text_input("Insira a Senha Master para desbloquear as funções de Gerência:", type="password")
    
    if senha_gerencial_digitada == st.session_state.senha_master_empresa:
        permitir_render_gerencial = True
        st.success("🔓 Acesso Gerencial Liberado!")
    elif senha_gerencial_digitada != "":
        st.error("🔒 Senha Gerencial Incorreta!")

    if permitir_render_gerencial:
        st.markdown("---")
        menu_gerencial = st.selectbox("Selecione o Módulo Gerencial:", ["Painel de Vendas & Caixa", "Estoque & Insumos", "Produtos & Ficha Técnica"])

        # --- MÓDULO GERENCIAL: PAINEL DE VENDAS & CAIXA ---
        if menu_gerencial == "Painel de Vendas & Caixa":
            st.subheader("📊 Relatório de Pedidos do Estabelecimento")
            with ob_cx() as c:
                df_pedidos = pd.read_sql(f"SELECT p.id, p.mesa, prod.nome, p.quantidade, p.status, p.horario, p.garcom, p.modo_pagamento, p.pago, prod.preco FROM pedidos p JOIN produtos prod ON p.produto_id = prod.id WHERE p.empresa_id = {emp_id} ORDER BY p.id DESC", c)
            
            if not df_pedidos.empty:
                df_pedidos["Total (R$)"] = df_pedidos["quantidade"] * df_pedidos["preco"]
                st.dataframe(df_pedidos[["id", "mesa", "nome", "quantidade", "Total (R$)", "status", "horario", "garcom", "pago", "modo_pagamento"]], use_container_width=True)
                
                st.subheader("🧾 Fechamento de Conta")
                mesas_ativas = df_pedidos[df_pedidos["pago"] == "Não"]["mesa"].unique()
                
                if len(mesas_ativas) > 0:
                    mesa_fechar = st.selectbox("Mesa para Fechamento:", mesas_ativas)
                    df_mesa = df_pedidos[(df_pedidos["mesa"] == mesa_fechar) & (df_pedidos["pago"] == "Não")]
                    
                    st.markdown(f"#### 📋 Consumo Atual - {mesa_fechar}:")
                    for _, row in df_mesa.iterrows():
                        st.text(f"• {int(row['quantidade'])}x {row['nome']} — R$ {row['Total (R$)']:.2f} ({row['horario']})")
                    
                    subtotal = df_mesa["Total (R$)"].sum()
                    taxa_servico = subtotal * 0.10
                    total_geral = subtotal + taxa_servico
                    
                    st.write("---")
                    st.metric("Subtotal", f"R$ {subtotal:.2f}")
                    st.metric("Taxa de Serviço (10%)", f"R$ {taxa_servico:.2f}")
                    st.markdown(f"### **Total Geral: R$ {total_geral:.2f}**")
                    
                    forma_pag = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"])
                    if st.button("Confirmar Pagamento e Baixar Conta", type="primary"):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("UPDATE pedidos SET pago = 'Sim', modo_pagamento = %s, status = 'Entregue' WHERE empresa_id = %s AND mesa = %s AND pago = 'Não'", (forma_pag, emp_id, mesa_fechar))
                            c.commit()
                        st.success(f"Conta da {mesa_fechar} baixada com sucesso!")
                        st.rerun()
                else: 
                    st.info("Nenhum pedido pendente de pagamento.")
            else: 
                st.info("Nenhum pedido realizado ainda.")

        # --- MÓDULO GERENCIAL: ESTOQUE ---
        elif menu_gerencial == "Estoque & Insumos":
            st.subheader("🥦 Controle de Insumos / Estoque")
            with st.form("add_estoque"):
                novo_insumo = st.text_input("Nome do Insumo (ex: Limão, Rum, Batata):").strip()
                qtd_inicial = st.number_input("Quantidade Inicial:", min_value=0.0, step=0.1)
                if st.form_submit_button("Cadastrar / Atualizar Insumo"):
                    if novo_insumo:
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("INSERT INTO estoque (empresa_id, item, quantidade) VALUES (%s, %s, %s) ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade;", (emp_id, novo_insumo, qtd_inicial))
                            c.commit()
                        st.success(f"Estoque de '{novo_insumo}' atualizado!")
                        st.rerun()
            
            with ob_cx() as c:
                df_est = pd.read_sql(f"SELECT id, item, quantidade FROM estoque WHERE empresa_id = {emp_id} ORDER BY item", c)
            st.subheader("Insumos Cadastrados")
            st.dataframe(df_est, use_container_width=True)

        # --- MÓDULO GERENCIAL: PRODUTOS & FICHA TÉCNICA ---
        elif menu_gerencial == "Produtos & Ficha Técnica":
            st.subheader("🍔 Cadastro de Produtos para o Cardápio")
            with st.form("cad_produto"):
                nome_prod = st.text_input("Nome do Produto Final:").strip()
                cat_prod = st.selectbox("Categoria:", cats)
                preco_prod = st.number_input("Preço de Venda (R$):", min_value=0.0, step=0.50)
                if st.form_submit_button("Salvar Produto"):
                    if nome_prod:
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("INSERT INTO produtos (empresa_id, nome, categoria, preco) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco;", (emp_id, nome_prod, cat_prod, preco_prod))
                            c.commit()
                        st.success(f"Produto '{nome_prod}' salvo com sucesso!")
                        st.rerun()
            
            with ob_cx() as c:
                df_prod_existentes = pd.read_sql(f"SELECT id, nome FROM produtos WHERE empresa_id = {emp_id} ORDER BY nome", c)
                df_insumos_existentes = pd.read_sql(f"SELECT id, item FROM estoque WHERE empresa_id = {emp_id} ORDER BY item", c)
            
            if not df_prod_existentes.empty and not df_insumos_existentes.empty:
                st.markdown("---")
                st.subheader("🧪 Ficha Técnica (Vincular Receita)")
                dict_p = {row["nome"]: row["id"] for _, row in df_prod_existentes.iterrows()}
                dict_i = {row["item"]: row["id"] for _, row in df_insumos_existentes.iterrows()}
                
                with st.form("ficha_tecnica_form"):
                    p_sel = st.selectbox("Selecione o Produto:", list(dict_p.keys()))
                    i_sel = st.selectbox("Insumo Usado na Receita:", list(dict_i.keys()))
                    qtd_gasta = st.number_input("Quantidade gasta por unidade vendida:", min_value=0.001, step=0.01, format="%.3f")
                    if st.form_submit_button("Vincular Insumo ao Produto"):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("INSERT INTO receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s);", (emp_id, dict_p[p_sel], dict_i[i_sel], qtd_gasta))
                            c.commit()
                        st.success(f"Insumo vinculado com sucesso ao produto {p_sel}!")
import streamlit as st
import pandas as pd
from datetime import datetime
from core_db import ob_cx, inicializar_banco
from auth import render_login_cadastro
from admin_panel import render_painel_gerencial

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

# Sincronização estrutural das tabelas relacionais do banco
try:
    inicializar_banco()
except Exception as e:
    st.error(f"Falha ao sincronizar banco de dados: {e}")
    st.stop()

# --- FASE 1: ACESSO DO ESTABELECIMENTO ---
if not st.session_state.logado:
    render_login_cadastro()

# Carregamento do ID do Tenant pós autenticação
emp_id = st.session_state.empresa_id_atual
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]

# --- CONTROLE DINÂMICO DE VISUALIZAÇÃO ---
if st.session_state.garcom_logado:
    st.markdown("### 📱 Ambiente do Funcionário")
    aba_master_operador = st.container()
    aba_master_sistema = st.empty()
else:
    aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])

# Renderização do Painel de Controle Gerencial Administrador
if not st.session_state.garcom_logado:
    with aba_master_sistema:
        render_painel_gerencial(emp_id, cats)

# --- FASE 2: OPERAÇÃO / TERMINAL DO GARÇOM ---
with aba_master_operador:
    col_g1, col_g2 = st.columns()
    with col_g1:
        garcom_nome = st.text_input("Identificação do Garçom / Operador:", value=st.session_state.usuario_atual if st.session_state.usuario_atual else "Balcão")
    with col_g2:
        if not st.session_state.garcom_logado:
            if st.button("📌 Fixar Modo Garçom", use_container_width=True):
                st.session_state.garcom_logado = True
                st.session_state.usuario_atual = garcom_nome
                st.rerun()
        else:
            if st.button("🔓 Sair do Modo Garçom", use_container_width=True):
                st.session_state.garcom_logado = False
                st.rerun()

    st.markdown("---")
    st.subheader("🛒 Novo Pedido (Carrinho Dinâmico)")
    mesa_pedido = st.text_input("Mesa / Cliente:", "Mesa ").strip()

    with ob_cx() as c:
        df_cardapio = pd.read_sql(f"SELECT id, nome, categoria, preco FROM produtos WHERE empresa_id = {emp_id} ORDER BY categoria, nome", c)

    if not df_cardapio.empty:
        categorias_ativas = df_cardapio["categoria"].unique()
        cat_filtro = st.selectbox("Filtrar por Categoria:", categorias_ativas)
        df_filtrado = df_cardapio[df_cardapio["categoria"] == cat_filtro]

        dict_cardapio = {f"{row['nome']} - R$ {row['preco']:.2f}": row["id"] for _, row in df_filtrado.iterrows()}
        produto_selecionado_txt = st.selectbox("Escolha o Item:", list(dict_cardapio.keys()))
        qtd_pedido = st.number_input("Quantidade:", min_value=1, value=1, step=1)

        if st.button("Adicionar ao Carrinho ➕", use_container_width=True):
            id_p = dict_cardapio[produto_selecionado_txt]
            nome_p = produto_selecionado_txt.split(" - R$")[0]
            st.session_state.carrinho.append({"id": id_p, "nome": nome_p, "quantidade": qtd_pedido})
            st.toast(f"{qtd_pedido}x {nome_p} adicionado ao carrinho!")
            st.rerun()

        if len(st.session_state.carrinho) > 0:
            st.markdown("### 📋 Itens no Carrinho:")
            indices_para_remover = []

            for idx, item in enumerate(st.session_state.carrinho):
                c_item, c_btn = st.columns([0.85, 0.15])
                with c_item:
                    st.markdown(f"🔹 **{item['quantidade']}x** {item['nome']}")
                with c_btn:
                    if st.button("❌", key=f"del_{idx}"):
                        indices_para_remover.append(idx)

            if indices_para_remover:
                for index in sorted(indices_para_remover, reverse=True):
                    st.session_state.carrinho.pop(index)
                st.rerun()

            st.write("")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("🗑️ Limpar Todo o Carrinho", use_container_width=True):
                    st.session_state.carrinho = []
                    st.rerun()
            with col_c2:
                if st.button("🚀 Enviar Pedido", type="primary", use_container_width=True):
                    horario_atual = datetime.now().strftime("%H:%M")
                    with ob_cx() as c, c.cursor() as cur:
                        for item in st.session_state.carrinho:
                            # 1. Registrar Pedido
                            cur.execute("INSERT INTO pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom, pago) VALUES (%s, %s, %s, %s, 'Pendente', %s, %s, 'Não');",
                                       (emp_id, mesa_pedido, item["id"], item["quantidade"], horario_atual, garcom_nome))

                            # 2. Processar Desconto de Insumos da Ficha Técnica
                            cur.execute("SELECT insumo_id, qtd_insumo FROM receitas WHERE produto_id = %s AND empresa_id = %s", (item["id"], emp_id))
                            receita_itens = cur.fetchall()
                            for insumo_id, qtd_unitaria in receita_itens:
                                total_desconto = qtd_unitaria * item["quantidade"]
                                cur.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s AND empresa_id = %s", (total_desconto, insumo_id, emp_id))
                        c.commit()
                    st.success("✅ Pedido enviado e insumos debitados do estoque!")
                    st.session_state.carrinho = []
                    st.rerun()
    else:
        st.info("Nenhum produto cadastrado no cardápio desta empresa.")
