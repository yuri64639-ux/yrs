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
            st.session_state.usuario_atual = str(resultado[0]) # CORREÇÃO: Puxa o texto puríssimo do operador
            st.session_state.ocultar_css = True 
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
            
    # CORREÇÃO DEFINITIVA: Passado o número 2 explicitamente na criação das colunas
    col_vazia, col_btn_nativ = st.columns(2)
    if st.session_state.ocultar_css:
        if col_btn_nativ.button("🔓 Exibir Funções Nativas", type="secondary", use_container_width=True):
            st.session_state.ocultar_css = False
            st.rerun()
    else:
        if col_btn_nativ.button("🔒 Ocultar Funções Nativas", type="secondary", use_container_width=True):
            st.session_state.ocultar_css = True
            st.rerun()
                
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
                    c_user, c_btn = st.columns(2) # CORREÇÃO: Definido 2 colunas para evitar o mesmo erro aqui
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
    col_info.info(f"📌 **Última modificada:** Comanda {df_ultima_mesa['mesa'].iloc}")

cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs(["🚀 Lançar Pedidos", "💵 Contas"])

# --- ABA 1: Lançar Pedidos ---
with tabs:
    col_titulo, col_bloqueio = st.columns()
    col_titulo.subheader("Mesa / Comanda")
    if col_bloqueio.button("🔒 Sair", key="bloqueio_lancador", type="secondary", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = ""
        st.rerun()

    m = st.text_input("Mesa / Comanda:", value=st.session_state.get("mesa_atual", ""), key="mesa_global_input", label_visibility="collapsed")
    st.session_state["mesa_atual"] = m
    busca_nome = st.text_input("🔍 Buscar produto por nome:", key="lupa_busca_topo_absoluto").strip()
    dp = {}
    
    if busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE LOWER(nome) LIKE LOWER(%s) ORDER BY nome", conn, params=[f"%{busca_nome}%"])
        if not prods_filtrados.empty:
            dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
            ps = st.selectbox("Confirmar Item selecionado:", list(dp.keys()), key="select_busca_lupa")
        else: st.warning("Nenhum item encontrado.")
            
    st.markdown("---")
    cat_sel = st.selectbox("Ou filtre por Categoria:", cats, key="categoria_filtro")
    if not busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE categoria = %s ORDER BY nome", conn, params=[cat_sel])
        if not prods_filtrados.empty:
            dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
            ps = st.selectbox("Confirmar Item filtrado:", list(dp.keys()), key="select_cat_refinado")
        else: st.warning("Categoria vazia.")
            
    if dp:
        q = st.number_input("Quantidade:", min_value=1, value=1, key="quantidade_item")
        if st.button("➕ Adicionar ao Pedido", type="secondary"):
            if not m.strip(): st.error("Digite a Mesa / Comanda primeiro!")
            else:
                chave_sel = st.session_state.get("select_busca_lupa") if busca_nome else st.session_state.get("select_cat_refinado")
                if chave_sel in dp:
                    item_escolhido = dp[chave_sel]
                    st.session_state.carrinho.append({"id": int(item_escolhido["id"]), "nome": item_escolhido["nome"], "categoria": item_escolhido["categoria"], "qtd": int(q), "preco": float(item_escolhido["preco"])})
                    st.success(f"{q}x {item_escolhido['nome']} adicionado!")
                    st.rerun()

    if st.session_state.carrinho:
        st.markdown("---")
        total_carrinho = 0.0
        for idx_c, item in enumerate(st.session_state.carrinho):
            sub_item = item["qtd"] * item["preco"]
            total_carrinho += sub_item
            col_txt, col_btn = st.columns()
            col_txt.write(f"▪️ **{item['qtd']}x** {item['nome']} — R$ {sub_item:.2f}")
            if col_btn.button("🗑️", key=f"rem_{idx_c}"):
                st.session_state.carrinho.pop(idx_c)
                st.rerun()
                
        st.markdown(f"### Total Parcial: R$ {total_carrinho:.2f}")
        col_cancelar, col_enviar = st.columns(2)
        if col_cancelar.button("❌ Limpar Rascunho"):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_enviar.button("🔥 LANÇAR COMANDA COMPLETA", type="primary"):
            lista_ids = [item["id"] for item in st.session_state.carrinho]
            q_rec = "SELECT r.produto_id, r.insumo_id, r.qtd_insumo, e.item, e.quantidade as qtd_atual FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id " + ("= %s" if len(lista_ids) == 1 else "IN %s")
            p_rec = [lista_ids] if len(lista_ids) == 1 else [tuple(lista_ids)]
            df_receitas = pd.read_sql(q_rec, conn, params=p_rec)
            
            estoque_ok = True
            est_simulado = {r["insumo_id"]: {"nome": r["item"], "saldo": float(r["qtd_atual"])} for _, r in df_receitas.iterrows()}
            for item in st.session_state.carrinho:
                for _, r_ins in df_receitas[df_receitas["produto_id"] == item["id"]].iterrows():
                    est_simulado[r_ins["insumo_id"]]["saldo"] -= (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                    if est_simulado[r_ins["insumo_id"]]["saldo"] < 0:
                        st.error(f"❌ Estoque insuficiente de: {est_simulado[r_ins['insumo_id']]['nome']}")
                        estoque_ok = False
                        
            if estoque_ok:
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    hr = datetime.now().strftime("%d/%m/%Y %H:%M")
                    for item in st.session_state.carrinho:
                        cur.execute("INSERT INTO public.pedidos (mesa, produto_id, quantidade, status, horario, garcom) VALUES (%s, %s, %s, 'Pendente', %s, %s)", (m.strip(), item["id"], item["qtd"], hr, st.session_state.usuario_atual))
                        for _, r_ins in df_receitas[df_receitas["produto_id"] == item["id"]].iterrows():
                            cur.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", ((float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"], int(r_ins["insumo_id"])))
                    c.commit()
                st.success("🚀 Lançado!")
                st.session_state.carrinho = []
                st.rerun()

# --- ABA 2: Contas e Fechamentos ---
with tabs:
    st.subheader("Gerenciamento de Contas")
    df_pedidos = pd.read_sql("SELECT p.id, p.mesa, pr.nome, pr.preco, p.quantidade, p.status FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    if df_pedidos.empty: st.info("Nenhuma mesa aberta.")
    else:
        m_conta = st.selectbox("Mesa para fechar:", sorted(list(set(df_pedidos["mesa"].tolist()))))
        pedidos_da_mesa = df_pedidos[df_pedidos["mesa"] == m_conta]
        total_mesa = 0.0
        
        for _, row in pedidos_da_mesa.iterrows():
            sub = row["quantidade"] * row["preco"]
            total_mesa += sub
            st.write(f"▪️ {row['quantidade']}x {row['nome']} — R$ {sub:.2f}")
            
        taxa = total_mesa * 0.10
        st.markdown(f"**Subtotal:** R$ {total_mesa:.2f} | **Taxa (10%):** R$ {taxa:.2f}")
        st.markdown(f"## Total Geral: R$ {total_mesa + taxa:.2f}")
        
        col_paga, col_npaga = st.columns(2)
        if col_paga.button("✅ Confirmar Pagamento", type="primary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = 1 WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (m_conta,))
                c.commit()
            st.rerun()
        if col_npaga.button("⚠️ Não Pago / Calote", type="secondary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Fechado (Não Pago)', taxa_paga = 0 WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (m_conta,))
                c.commit()
            st.rerun()
