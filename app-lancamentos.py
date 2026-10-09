from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & CONSTANTES
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

CATEGORIAS_VALIDAS = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]

st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
    header [data-testid="stToolbar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
if "carrinho" not in st.session_state: st.session_state.carrinho = []

# ---------------------------------------------------------
# CONEXÃO COM O BANCO DE DADOS (NEON / POSTGRES)
# ---------------------------------------------------------
def obter_conexao():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: 
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

def executar_query(query, params=None, commit=False, retornar_dados=False):
    resultado = None
    try:
        with obter_conexao() as conn:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute(query, params)
                if retornar_dados:
                    resultado = cur.fetchall()
                if commit:
                    conn.commit()
    except Exception as e:
        st.error(f"Erro operacional no banco de dados: {e}")
    return resultado

# ---------------------------------------------------------
# INICIALIZAÇÃO DO BANCO (DDL)
# ---------------------------------------------------------
def inicializar_banco_dados():
    with obter_conexao() as conn:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO public;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS empresas (
                    id SERIAL PRIMARY KEY, 
                    nome_empresa TEXT UNIQUE NOT NULL, 
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY, 
                    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                    usuario TEXT, 
                    senha TEXT,
                    CONSTRAINT unique_empresa_usuario UNIQUE(empresa_id, usuario)
                );
                CREATE TABLE IF NOT EXISTS estoque (
                    id SERIAL PRIMARY KEY, 
                    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                    item TEXT, 
                    quantidade REAL,
                    CONSTRAINT unique_empresa_item UNIQUE(empresa_id, item)
                );
                CREATE TABLE IF NOT EXISTS produtos (
                    id SERIAL PRIMARY KEY, 
                    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                    nome TEXT, 
                    categoria TEXT, 
                    preco REAL,
                    CONSTRAINT unique_empresa_produto UNIQUE(empresa_id, nome)
                );
                CREATE TABLE IF NOT EXISTS receitas (
                    id SERIAL PRIMARY KEY, 
                    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                    produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE, 
                    insumo_id INTEGER REFERENCES estoque(id) ON DELETE CASCADE, 
                    qtd_insumo REAL,
                    CONSTRAINT unique_empresa_receita UNIQUE(empresa_id, produto_id, insumo_id)
                );
                CREATE TABLE IF NOT EXISTS pedidos (
                    id SERIAL PRIMARY KEY, 
                    empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                    mesa TEXT, 
                    produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE, 
                    quantidade INTEGER, 
                    status TEXT DEFAULT 'Pendente', 
                    horario TEXT, 
                    taxa_paga INTEGER DEFAULT 1, 
                    pago TEXT DEFAULT 'Sim', 
                    garcom TEXT
                );
            """)
            conn.commit()

inicializar_banco_dados()

# ---------------------------------------------------------
# LOGÍSTICA DE ACESSO DO ESTABELECIMENTO
# ---------------------------------------------------------
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
                    with obter_conexao() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("INSERT INTO empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                            id_da_empresa = cur.fetchone()[0]
                            cur.execute("INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                            conn.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as e: 
                    st.error(f"Erro no cadastro: Verifique os dados inseridos. ({e})")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            
            with obter_conexao() as conn_busca:
                df_lista_empresas = pd.read_sql("SELECT id, nome_empresa FROM empresas ORDER BY nome_empresa", conn_busca)
            dict_empresas = {row["nome_empresa"]: row["id"] for _, row in df_lista_empresas.iterrows()} if not df_lista_empresas.empty else {}
            
            if dict_empresas:
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                user_input = st.text_input("Usuário Master da Empresa:")
                senha_input = st.text_input("Senha Master:", type="password")
                submetido = st.form_submit_button("Liberar Terminal", type="primary")
                
                if submetido and user_input and senha_input:
                    id_empresa_login = dict_empresas[empresa_selecionada]
                    res = executar_query(
                        "SELECT empresa_id, senha FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s",
                        (id_empresa_login, user_input.strip(), senha_input.strip()), retornar_dados=True
                    )
                    
                    if res:
                        st.session_state.logado = True
                        st.session_state.empresa_id_atual = int(res[0][0])
                        st.session_state.senha_master_empresa = str(res[0][1])
                        st.rerun()
                    else: 
                        st.error("Credenciais da empresa incorretas!")
            else: 
                st.info("Nenhuma empresa cadastrada ainda.")
    st.stop()

# ---------------------------------------------------------
# INTERFACE PRINCIPAL MULTI-TENANT
# ---------------------------------------------------------
emp_id = st.session_state.empresa_id_atual
aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])

# --- GERENCIAL ---
with aba_master_sistema:
    st.subheader("🔐 Área Restrita ao Gerente")
    senha_gerente_input = st.text_input("Digite a Senha Master para liberar o painel:", type="password", key="senha_painel_gerente")
    
    if senha_gerente_input == st.session_state.senha_master_empresa:
        st.success("🔓 Acesso Gerencial Autorizado")
        
        if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True):
            st.session_state.logado = False
            st.session_state.empresa_id_atual = None
            st.session_state.senha_master_empresa = ""
            st.session_state.garcom_logado = False
            st.session_state.carrinho = []
            st.rerun()
        
        with obter_conexao() as conn_gerencial:
            df_est = pd.read_sql("SELECT id, item, quantidade FROM estoque WHERE empresa_id = %s ORDER BY item", conn_gerencial, params=[emp_id])
            df_prods = pd.read_sql("SELECT id, nome FROM produtos WHERE empresa_id = %s ORDER BY nome", conn_gerencial, params=[emp_id])
        
        subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])

        # Estoque
        with subtabs[0]:
            st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
            if not df_est.empty: 
                df_est_visual = df_est.copy()
                df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual"]
                st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum insumo no estoque.")
            
            with st.expander("➕ Alimentar Estoque"):
                with st.form("f_ins", clear_on_submit=True):
                    n_i = st.text_input("Insumo:").strip()
                    q_i = st.number_input("Qtd a somar:", min_value=0.0, value=1.0, step=1.0)
                    if st.form_submit_button("Salvar Insumo") and n_i:
                        executar_query(
                            """INSERT INTO estoque (empresa_id, item, grandmother) VALUES (%s, %s, %s) 
                               ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade""",
                            (emp_id, n_i, q_i), commit=True
                        )
                        st.success(f"Estoque de '{n_i}' atualizado!")
                        st.rerun()

        # Cancelamentos
        with subtabs[1]:
            st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
            with obter_conexao() as conn_cancel:
                p_ab = pd.read_sql("""
                    SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id 
                    FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id 
                    WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa
                """, conn_cancel, params=[emp_id])
            
            if p_ab.empty: 
                st.info("Nenhuma comanda aberta.")
            else:
                m_sel = st.selectbox("Selecione a Mesa para auditar:", sorted(list(set(p_ab['mesa'].tolist()))))
                for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
                    col1, col2 = st.columns(2)
                    col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
                    if col2.button("Deletar Item", key=f"cn_{it['id']}"):
                        with obter_conexao() as conn:
                            with conn.cursor() as cur:
                                cur.execute("SET search_path TO public;")
                                cur.execute("SELECT insumo_id, qtd_insumo FROM receitas WHERE empresa_id = %s AND produto_id = %s", (emp_id, int(it['produto_id'])))
                                receitas = cur.fetchall()
                                for r_id, r_qtd in receitas:
                                    qtd_devolver = (float(r_qtd) / 1000.0) * int(it['quantidade'])
                                    cur.execute("UPDATE estoque SET quantidade = quantidade + %s WHERE empresa_id = %s AND id = %s", (qtd_devolver, emp_id, int(r_id)))
                                cur.execute("DELETE FROM pedidos WHERE id = %s AND empresa_id = %s", (int(it['id']), emp_id))
                                conn.commit()
                        st.success("Item removido!"); st.rerun()

        # Cadastro em Massa
        with subtabs[2]:
            st.subheader("🍔 Cadastro de Produtos Rápido (Copiar e Colar)")
            with st.form("f_prod_massa_texto_direto", clear_on_submit=True):
                texto_produtos = st.text_area("Cole seus produtos aqui (Nome, Categoria, Preço):", height=200)
                botao_gravar = st.form_submit_button("🔥 Gravar Todos")
                if botao_gravar and texto_produtos.strip():
                    linhas = texto_produtos.strip().split("\n")
                    with obter_conexao() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            for linha in linhas:
                                if "," in linha:
                                    partes = linha.split(",")
                                    if len(partes) == 3:
                                        n_p, c_p, p_p = partes[0].strip(), partes[1].strip(), partes[2].strip()
                                        cat_valida = [c for c in CATEGORIAS_VALIDAS if c.lower() == c_p.lower()]
                                        if n_p and cat_valida:
                                            try:
                                                cur.execute("""
                                                    INSERT INTO produtos (empresa_id, nome, categoria, preco) VALUES (%s, %s, %s, %s) 
                                                    ON CONFLICT (empresa_id, nome) DO UPDATE SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco
                                                """, (emp_id, n_p, str(cat_valida[0]), float(p_p)))
                                            except ValueError: pass
                            conn.commit()
                    st.success("Processamento em lote concluído!"); st.rerun()

        # Ficha Técnica
        with subtabs[3]:
            st.subheader("🔬 Montar Ficha Técnica (Até 4 Ingreedientes)")
            if not df_prods.empty and not df_est.empty:
                lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
                lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
                d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
                d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
                
                with st.form("f_vinc_multi", clear_on_submit=True):
                    p_sel = d_p[st.selectbox("Selecione o Produto final:", lista_prods)]
                    col1, col2 = st.columns(2); i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="rec_i1"); q1 = col2.number_input("Qtd gasta 1:", min_value=0.0, step=5.0, key="rec_q1")
                    col3, col4 = st.columns(2); i2 = col3.selectbox("Ingrediente 2:", lista_insumos, key="rec_i2"); q2 = col4.number_input("Qtd gasta 2:", min_value=0.0, step=5.0, key="rec_q2")
                    col5, col6 = st.columns(2); i3 = col5.selectbox("Ingrediente 3:", lista_insumos, key="rec_i3"); q3 = col6.number_input("Qtd gasta 3:", min_value=0.0, step=5.0, key="rec_q3")
                    col7, col8 = st.columns(2); i4 = col7.selectbox("Ingrediente 4:", lista_insumos, key="rec_i4"); q4 = col8.number_input("Qtd gasta 4:", min_value=0.0, step=5.0, key="rec_q4")
                    
                    if st.form_submit_button("🔥 Gravar Receita Completa"):
                        links = [(i1, q1), (i2, q2), (i3, q3), (i4, q4)]
                        with obter_conexao() as conn:
                            with conn.cursor() as cur:
                                cur.execute("SET search_path TO public;")
                                for ing, qtd in links:
                                    if ing != "---" and qtd > 0:
                                        cur.execute("""INSERT INTO receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) 
                                                       ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo""", 
                                                    (emp_id, p_sel, d_i[ing], qtd))
                                conn.commit()
                        st.success("Receita salva!"); st.rerun()
            else: 
                st.info("Cadastre insumos no estoque e produtos antes de montar receitas.")

        # Relatórios
        with subtabs[4]:
            st.subheader("📊 Resumo Financeiro Detalhado")
            with obter_conexao() as conn_rel:
                vendas_df = pd.read_sql("""
                    SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario 
                    FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id 
                    WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC
                """, conn_rel, params=[emp_id])
                
            if vendas_df.empty: 
                st.info("Nenhuma comanda paga registrada.")
            else:
                empresa_total = float(vendas_df[vendas_df['status']=='Finalizado (Pago)']['subtotal'].sum())
                garcons_total = float(vendas_df[(vendas_df['status']=='Finalizado (Pago)') & (vendas_df['taxa_paga']==1)]['subtotal'].sum() * 0.10)
                pendente_total = float(vendas_df[vendas_df['status']=='Fechado (Não Pago)']['subtotal'].sum())
                        
                c1, c2, c3 = st.columns(3)
                c1.metric("💰 Faturamento Líquido", f"R$ {empresa_total:.2f}")
                c2.metric("🍹 Caixinha (10%)", f"R$ {garcons_total:.2f}")
                c3.metric("⚠️ Perdas (Calotes)", f"R$ {pendente_total:.2f}")
                st.dataframe(vendas_df, use_container_width=True, hide_index=True)

        # Excluir
        with subtabs[5]:
            st.subheader("🗑️ Remover Produtos ou Insumos")
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if not df_prods.empty:
                    prod_para_excluir = st.selectbox("Produto para deletar permanentemente:", [r['nome'] for _, r in df_prods.iterrows()])
                    if st.button("❌ Excluir Produto", use_container_width=True):
                        executar_query("DELETE FROM produtos WHERE empresa_id = %s AND nome = %s", (emp_id, prod_para_excluir), commit=True)
                        st.success("Removido!"); st.rerun()
            with col_del2:
                if not df_est.empty:
                    insumo_para_excluir = st.selectbox("Insumo para deletar permanentemente:", [r['item'] for _, r in df_est.iterrows()])
                    if st.button("❌ Excluir Insumo", use_container_width=True):
                        executar_query("DELETE FROM estoque WHERE empresa_id = %s AND item = %s", (emp_id, insumo_para_excluir), commit=True)
                        st.success("Removido!"); st.rerun()
                        
    elif senha_gerente_input != "":
        st.error("❌ Senha incorreta!")

# --- TERMINAL DO GARÇOM ---
with aba_master_operador:
    if not st.session_state.garcom_logado:
        st.subheader("👤 Identificação do Garçom")
        with st.form("login_garcom_form"):
            garcom_input = st.text_input("Usuário/Nome do Garçom:").strip()
            senha_garcom = st.text_input("Senha do Garçom:", type="password").strip()
            if st.form_submit_button("Entrar no Sistema", type="primary") and garcom_input and senha_garcom:
                res_garcom = executar_query(
                    "SELECT usuario FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s",
                    (emp_id, garcom_input.lower(), senha_garcom), retornar_dados=True
                )
                if res_garcom:
                    st.session_state.garcom_logado = True
                    st.session_state.usuario_atual = str(res_garcom[0][0])
                    st.rerun()
                else: st.error("Credenciais incorretas!")

        st.markdown("---")
        with st.expander("➕ Cadastrar Novo Garçom"):
            with st.form("cadastro_garcom_form", clear_on_submit=True):
                novo_g_user = st.text_input("Nome/Usuário do Garçom:").strip()
                novo_g_senha = st.text_input("Senha de Acesso:", type="password").strip()
                if st.form_submit_button("💼 Confirmar Cadastro") and novo_g_user and novo_g_senha:
                    executar_query("INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", (emp_id, novo_g_user, novo_g_senha), commit=True)
                    st.success("Garçom cadastrado!")
                    
    if st.session_state.garcom_logado:
        st.subheader(f"📋 Atendimento — Operador: {st.session_state.usuario_atual.upper()}")
        if st.button("🔒 Sair / Trocar de Garçom", use_container_width=True):
            st.session_state.garcom_logado = False
            st.session_state.usuario_atual = ""
            st.session_state.carrinho = []
            st.rerun()
            
        aba_operacao = st.radio("Ação:", ["➕ Lançar Pedido", "🧾 Gerenciar Contas / Fechar Mesas"], horizontal=True)
        
        if aba_operacao == "➕ Lançar Pedido":
            with obter_conexao() as conn_vendas:
                df_prods_venda = pd.read_sql("SELECT id, nome, categoria, preco FROM produtos WHERE empresa_id = %s ORDER BY nome", conn_vendas, params=[emp_id])
                
            if df_prods_venda.empty: st.info("Nenhum produto cadastrado.")
            else:
                mesa_operacao = st.text_input("Mesa ou Comanda:", value="Mesa 01").strip()
                prod_map_venda = {f"{row['nome']} - R$ {row['preco']:.2f}": (row['id'], row['nome']) for _, row in df_prods_venda.iterrows()}
                
                if prod_map_venda:
                    produto_selecionado_string = st.selectbox("Escolha o Item:", list(prod_map_venda.keys()))
                    qtd_solicitada = st.number_input("Quantidade:", min_value=1, value=1, step=1)
                    if st.button("➕ Adicionar ao Carrinho", use_container_width=True):
                        id_p_venda, nome_p_venda = prod_map_venda[produto_selecionado_string]
                        st.session_state.carrinho.append({"id": id_p_venda, "nome": nome_p_venda, "qtd": qtd_solicitada})
                        st.toast(f"{nome_p_venda} adicionado!")
                
                if st.session_state.carrinho:
                    st.markdown("### 🛒 Carrinho")
                    for item in st.session_state.carrinho: st.write(f"▪ *{item['qtd']}x* - {item['nome']}")
                    confirmacao_garcom = st.checkbox("✅ Conferi os itens com o cliente.", value=False)
                    col_limpar, col_enviar = st.columns(2)
                    if col_limpar.button("🗑️ Limpar Carrinho", use_container_width=True): st.session_state.carrinho = []; st.rerun()
                    if col_enviar.button("🚀 Enviar Pedido", type="primary", use_container_width=True):
                        if not confirmacao_garcom: st.error("Marque a confirmação!")
                        else:
                            horario_atual = datetime.now().strftime("%H:%M:%S")
                            with obter_conexao() as conn:
                                with conn.cursor() as cur:
                                    cur.execute("SET search_path TO public;")
                                    for item in st.session_state.carrinho:
                                        cur.execute("INSERT INTO pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom) VALUES (%s, %s, %s, %s, 'Pendente', %s, %s)", (emp_id, mesa_operacao, item['id'], item['qtd'], horario_atual, st.session_state.usuario_atual))
                                        cur.execute("SELECT insumo_id, qtd_insumo FROM receitas WHERE empresa_id = %s AND produto_id = %s", (emp_id, item['id']))
                                        receitas = cur.fetchall()
                                        for ins_id, qtd_rec in   receitas:
                                            total_descontar = (float(qtd_rec) / 1000.0) * int(item['qtd'])
                                            cur.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE empresa_id = %s AND id = %s", (total_descontar, emp_id, int(ins_id)))
                                    conn.commit()
                            st.success("Pedido lançado!"); st.session_state.carrinho = []; st.rerun()

        elif aba_operacao == "🧾 Gerenciar Contas / Fechar Mesas":
            with obter_conexao() as conn_pedidos:
                pedidos_ativos = pd.read_sql("""
                    SELECT p.id, p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status 
                    FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id 
                    WHERE p.empresa_id = %s AND p.status IN ('Pendente', 'Confirmado') ORDER BY p.mesa
                """, conn_pedidos, params=[emp_id])
            
            if pedidos_ativos.empty: st.info("Não há comandas abertas.")
            else:
                lupa_busca = st.text_input("🔍 Buscar por Mesa:").strip()
                df_mesas_ativas = pedidos_ativos[pedidos_ativos['mesa'].str.contains(lupa_busca, case=False, na=False)] if lupa_busca else pedidos_ativos
                
                if not df_mesas_ativas.empty:
                    mesas_abertas = sorted(list(set(df_mesas_ativas['mesa'].tolist())))
                    mesa_ver = st.selectbox("Selecione a Mesa:", mesas_abertas)
                    df_mesa_filtrada = pedidos_ativos[pedidos_ativos['mesa'] == mesa_ver]
                    
                    if 'Pendente' in df_mesa_filtrada['status'].tolist():
                        if st.button("✅ Confirmar Todos os Itens Pendentes", use_container_width=True):
                            executar_query("UPDATE pedidos SET status = 'Confirmado' WHERE empresa_id = %s AND mesa = %s AND status = 'Pendente'", (emp_id, mesa_ver), commit=True)
                            st.success("Itens confirmados!"); st.rerun()
                    
                    for _, row in df_mesa_filtrada.iterrows():
                        c_item, c_status, c_acao = st.columns(3)
                        c_item.write(f"▪ **{row['quantidade']}x** {row['produto']} *(R$ {row['subtotal']:.2f})*")
                        if row['status'] == 'Pendente':
                            c_status.warning("⏳ Pendente")
                            if c_acao.button("Confirmar", key=f"conf_ind_{row['id']}"):
                                executar_query("UPDATE pedidos SET status = 'Confirmado' WHERE id = %s AND empresa_id = %s", (int(row['id']), emp_id), commit=True)
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
                    
                    inclui_taxa = st.checkbox("Cliente aceitou pagar a taxa?", value=True)
                    if st.button("💰 Finalizar e Receber Pagamento", type="primary", use_container_width=True):
                        valor_taxa_salvar = 1 if inclui_taxa else 0
                        executar_query("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE empresa_id = %s AND mesa = %s AND status IN ('Pendente', 'Confirmado')", (valor_taxa_salvar, emp_id, mesa_ver), commit=True)
                        st.success("Mesa fechada!"); st.rerun()
