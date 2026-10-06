# ==============================================================================
# PARTE 1: CONFIGURAÇÕES, LOGIN INDIVIDUAL E CONEXÃO COM O BANCO DE DADOS
# ==============================================================================
from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Sistema de Vendas", layout="centered")

if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "ocultar_css" not in st.session_state: st.session_state.ocultar_css = True

# O estilo CSS só é aplicado se ocultar_css for True
if st.session_state.ocultar_css:
    st.markdown("""
        <style>
        #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
        header [data-testid="stToolbar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: flex !important; }
        header { background-color: transparent !important; }
        </style>
    """, unsafe_allow_html=True)

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

# Inicialização e checagem das tabelas do banco de dados
conn = ob_cx()
with conn.cursor() as cur:
    cur.execute("SET search_path TO public;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.usuarios (id SERIAL PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT);
        CREATE TABLE IF NOT EXISTS public.estoque (id SERIAL PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);
        CREATE TABLE IF NOT EXISTS public.produtos (id SERIAL PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL);
        CREATE TABLE IF NOT EXISTS public.receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL, UNIQUE(produto_id, insumo_id));
        CREATE TABLE IF NOT EXISTS public.pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Sim', garcom TEXT);
    """)
    cur.execute("INSERT INTO public.usuarios (usuario, senha) VALUES ('admin', 'orla123') ON CONFLICT DO NOTHING")
conn.commit()

# Tela de Autenticação / Login Individual
if not st.session_state.logado:
    with st.form("login_form"):
        st.subheader("📱 Acesso Individual ao Sistema")
        user_input = st.text_input("Usuário:")
        senha_input = st.text_input("Senha:", type="password")
        submetido = st.form_submit_button("Entrar", type="primary")
        
    if submetido:
        user_limpo = user_input.strip()
        senha_limpa = senha_input.strip()
        
        with ob_cx() as c, c.cursor() as cur:
            cur.execute("SET search_path TO public;")
            cur.execute("SELECT usuario FROM public.usuarios WHERE LOWER(usuario) = LOWER(%s) AND senha = %s", (user_limpo, senha_limpa))
            resultado = cur.fetchone()
            
        if resultado:
            st.session_state.logado = True
            st.session_state.usuario_atual = str(resultado[0])
            st.session_state.ocultar_css = True 
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
            
    # --- BOTÃO DE ALTERNAR FUNÇÕES NATIVAS COM SENHA MASTER ---
    st.markdown("---")
    st.write("### 🛠️ Modo Desenvolvedor")
    col_senha, col_botao = st.columns(2)
    senha_painel = col_senha.text_input("Senha de Autorização:", type="password", key="senha_painel_nativo", label_visibility="collapsed", placeholder="Senha Master")
    
    if st.session_state.ocultar_css:
        if col_botao.button("🔓 Exibir Funções Nativas", type="secondary", use_container_width=True):
            if senha_painel == "orla123":
                st.session_state.ocultar_css = False
                st.rerun()
            else:
                st.error("Senha Master incorreta!")
    else:
        if col_botao.button("🔒 Ocultar Funções Nativas", type="secondary", use_container_width=True):
            if senha_painel == "orla123":
                st.session_state.ocultar_css = True
                st.rerun()
            else:
                st.error("Senha Master incorreta!")
                
    # --- GERENCIAMENTO INDIVIDUAL DE GARÇONS ---
    with st.expander("⚙️ Gerenciamento de Garçons (Apenas Administrador)"):
        st.write("### ➕ Novo Cadastro")
        novo_usuario = st.text_input("Nome do Usuário/Garçom:", key="cad_user_input")
        nova_senha = st.text_input("Defina a Senha:", type="password", key="cad_pass_input")
        senha_master = st.text_input("Senha Master para autorizar:", type="password", key="cad_master_input")
        
        if st.button("Gravar Usuário", type="secondary"):
            if novo_usuario.strip() and nova_senha.strip() and senha_master == "orla123":
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("""
                        INSERT INTO public.usuarios (usuario, senha) VALUES (%s, %s) 
                        ON CONFLICT (usuario) DO UPDATE SET senha = EXCLUDED.senha
                    """, (novo_usuario.strip(), nova_senha.strip()))
                    c.commit()
                st.success(f"Usuário '{novo_usuario.strip()}' salvo!")
                st.rerun()
            else:
                st.error("Preencha os campos ou verifique a Senha Master!")

        st.markdown("---")
        st.write("### 📋 Usuários Ativos")
        df_usuarios_cad = pd.read_sql("SELECT id, usuario FROM public.usuarios ORDER BY usuario", conn)
        
        if not df_usuarios_cad.empty:
            for _, row_u in df_usuarios_cad.iterrows():
                if str(row_u['usuario']).strip().lower() != 'admin':
                    c_user, c_btn = st.columns(2)
                    c_user.write(f"👤 **{row_u['usuario']}**")
                    if c_btn.button("Excluir", key=f"del_usr_{row_u['id']}"):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("DELETE FROM public.usuarios WHERE id = %s", (int(row_u['id']),))
                            c.commit()
                        st.success("Usuário removido!")
                        st.rerun()
        else:
            st.info("Nenhum funcionário cadastrado.")
    st.stop()

if "carrinho" not in st.session_state: st.session_state.carrinho = []
# ==============================================================================
# PARTE 2: INTERFACE DE LANÇAMENTO DE PEDIDOS E FECHAMENTO DE CONTAS
# ==============================================================================

col_user, col_info = st.columns(2)
col_user.write(f"👤 **Operador:** {st.session_state.usuario_atual}")

df_ultima_mesa = pd.read_sql("SELECT mesa FROM public.pedidos WHERE status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY id DESC LIMIT 1", conn)
if not df_ultima_mesa.empty:
    col_info.info(f"📌 **Última modificada:** Comanda {df_ultima_mesa['mesa'].iloc[0]}")

cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs(["🚀 Lançar Pedidos", "💵 Contas"])

# --- ABA 1: Lançar Pedidos ---
with tabs[0]:
    col_titulo, col_bloqueio = st.columns(2)
    col_titulo.subheader("Mesa / Comanda")
    if col_bloqueio.button("🔒 Sair", key="bloqueio_lancador", type="secondary", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = ""
        st.rerun()

    m = st.text_input("Mesa / Comanda:", value=st.session_state.get("mesa_atual", ""), key="mesa_global_input", label_visibility="collapsed")
    st.session_state["mesa_atual"] = m
    busca_nome = st.text_input("🔍 Buscar produto por nome:", key="lupa_busca_topo_absoluto").strip()

    st.write("---")
    st.caption("Selecione os itens e adicione ao carrinho para processar o pedido.")

# --- ABA 2: Contas (Fechamento com Opção de Desconto de 10%) ---
with tabs[1]:
    st.subheader("💵 Fechamento de Conta")
    
    df_mesas_ativas = pd.read_sql("SELECT DISTINCT mesa FROM public.pedidos WHERE status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY mesa", conn)
    
    if not df_mesas_ativas.empty:
        mesa_selecionada = st.selectbox("Escolha a Mesa/Comanda para fechar:", df_mesas_ativas["mesa"])
        
        query_itens = """
            SELECT p.id, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as total_item
            FROM public.pedidos p
            JOIN public.produtos pr ON p.produto_id = pr.id
            WHERE p.mesa = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')
        """
        
        df_itens_conta = pd.read_sql(query_itens, conn, params=(str(mesa_selecionada),))
        
        if not df_itens_conta.empty:
            st.write("### 📋 Itens Consumidos")
            st.dataframe(df_itens_conta[["nome", "quantidade", "preco", "total_item"]], hide_index=True, use_container_width=True)
            
            subtotal = df_itens_conta["total_item"].sum()
            st.metric("Subtotal", f"R$ {subtotal:.2f}")
            
            # --- CAIXA DE SELEÇÃO DO DESCONTO DE 10% ---
            tirar_10_porcento = st.checkbox("Tirar 10% da conta (Desconto/Isenção de taxa)", key="chk_desconto_10")
            
            if tirar_10_porcento:
                desconto = subtotal * 0.10
                total_final = subtotal - desconto
                st.warning(f"🎁 Desconto de 10% aplicado: - R$ {desconto:.2f}")
            else:
                total_final = subtotal
                
            st.subheader(f"💰 Total a Pagar: R$ {total_final:.2f}")
            
            if st.button("Finalizar e Registrar Pagamento", type="primary", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("""
                        UPDATE public.pedidos 
                        SET status = 'Finalizado (Pago)', pago = 'Sim' 
                        WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')
                    """, (str(mesa_selecionada),))
                    c.commit()
                st.success(f"Conta da Comanda {mesa_selecionada} encerrada com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum item ativo encontrado para esta comanda.")
    else:
        st.info("Não há mesas ou comandas com pedidos pendentes no momento.")
