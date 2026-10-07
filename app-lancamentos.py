from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Sistema de Vendas Multi-Tenant", layout="centered")

if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
if "ocultar_css" not in st.session_state: st.session_state.ocultar_css = True
if "carrinho" not in st.session_state: st.session_state.carrinho = []

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
                        id_da_empresa = cur.fetchone()
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada! Mude para a aba de login.")
                except Exception as e:
                    st.error(f"Erro no cadastro: {e}")
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
                        cur.execute("SELECT empresa_id FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (id_empresa_login, user_input.strip(), senha_input.strip()))
                        resultado = cur.fetchone()
                    
                    if resultado:
                        st.session_state.logado = True
                        st.session_state.empresa_id_atual = int(resultado)
                        st.rerun()
                    else:
                        st.error("Credenciais da empresa incorretas!")
            else:
                st.info("Nenhuma empresa cadastrada ainda.")

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

if st.session_state.logado and not st.session_state.garcom_logado:
    with st.form("login_garcom_form"):
        st.subheader("👤 Identificação do Garçom")
        garcom_input = st.text_input("Usuário/Nome do Garçom:")
        senha_garcom = st.text_input("Senha do Garçom:", type="password")
        submetido_garcom = st.form_submit_button("Entrar no Sistema", type="primary")
        
        if submetido_garcom:
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("SELECT usuario FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (st.session_state.empresa_id_atual, garcom_input.strip().lower(), senha_garcom.strip()))
                res_garcom = cur.fetchone()
            
            if res_garcom:
                st.session_state.garcom_logado = True
                st.session_state.usuario_atual = str(res_garcom)
                st.rerun()
            else: st.error("Usuário ou senha do garçom incorretos!")

    with st.expander("⚙️ Gerenciamento e Cadastro de Garçons"):
        st.write("### ➕ Cadastrar Novo Garçom")
        with st.form("f_cad_garcom", clear_on_submit=True):
            novo_nome = st.text_input("Nome/Usuário do Garçom:").strip()
            nova_senha = st.text_input("Senha de Acesso:", type="password").strip()
            if st.form_submit_button("Gravar Funcionário"):
                if novo_nome and nova_senha:
                    try:
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s)", (st.session_state.empresa_id_atual, novo_nome.lower(), nova_senha))
                            c.commit()
                        st.success(f"Garçom '{novo_nome}' cadastrado com sucesso!")
                        st.rerun()
                    except psycopg2.errors.UniqueViolation: st.error("Este nome de usuário já está sendo usado.")
                else: st.error("Preencha todos os campos!")

        st.markdown("---")
        st.write("### 📋 Garçons Ativos")
        df_garcons = pd.read_sql("SELECT id, usuario FROM public.usuarios WHERE empresa_id = %s ORDER BY usuario", conn, params=[st.session_state.empresa_id_atual])
        if not df_garcons.empty:
            for _, row_g in df_garcons.iterrows():
                col_g_nome, col_g_btn = st.columns(2)
                col_g_nome.write(f"👤 {row_g['usuario'].upper()}")
                if col_g_btn.button("Remover", key=f"del_g_{row_g['id']}"):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("DELETE FROM public.usuarios WHERE id = %s", (int(row_g['id']),))
                        c.commit()
                    st.success("Funcionário removido!")
                    st.rerun()
        else: st.info("Nenhum garçom cadastrado ainda.")

    if st.button("🔒 Bloquear Terminal da Empresa"):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.rerun()
    st.stop()
if st.session_state.logado and st.session_state.garcom_logado:
    emp_id = st.session_state.empresa_id_atual

    col_user, col_info = st.columns(2)
    col_user.write(f"👤 **Operador:** {st.session_state.usuario_atual}")

    df_ultima_mesa = pd.read_sql("""
        SELECT mesa FROM public.pedidos 
        WHERE empresa_id = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') 
        ORDER BY id DESC LIMIT 1
    """, conn, params=[emp_id])
    
    if not df_ultima_mesa.empty:
        col_info.info(f"📌 **Última modificada:** Comanda {df_ultima_mesa['mesa'].iloc}")

    cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
    tabs = st.tabs(["🚀 Lançar Pedidos", "💵 Contas"])

    with tabs:
        col_titulo, col_bloqueio = st.columns(2)
        col_titulo.subheader("Mesa / Comanda")
        
        if col_bloqueio.button("🔒 Trocar Operador", key="bloqueio_lancador", type="secondary", use_container_width=True):
            st.session_state.garcom_logado = False
            st.session_state.usuario_atual = ""
            st.session_state.carrinho = []
            st.rerun()

        m = st.text_input("Mesa / Comanda:", value=st.session_state.get("mesa_atual", ""), key="mesa_global_input", label_visibility="collapsed")
        st.session_state["mesa_atual"] = m
        
        busca_nome = st.text_input("🔍 Digite o nome do produto:", key="lupa_busca_topo_absoluto").strip()
        dp = {}

        if busca_nome:
            prods_filtrados = pd.read_sql("""
                SELECT id, nome, preco, categoria FROM public.produtos 
                WHERE empresa_id = %s AND LOWER(nome) LIKE LOWER(%s) ORDER BY nome
            """, conn, params=[emp_id, f"%{busca_nome}%"])
            if not prods_filtrados.empty:
                dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
                ps = st.selectbox("Confirmar Item selecionado:", list(dp.keys()), key="select_busca_lupa")
            else:
                st.warning("Nenhum item encontrado com esse nome.")
        
        chave_sel = st.session_state.get("select_busca_lupa") if busca_nome else st.session_state.get("select_cat_refinado")
        
        if dp and chave_sel in dp:
            texto_exibicao = f"{dp[chave_sel]['nome']} — R$ {dp[chave_sel]['preco']:.2f}"
        else:
            texto_exibicao = ""
            
        st.text_input("📌 Produto Escolhido:", value=texto_exibicao, disabled=True, key="campo_visual_produto_escolhido_identico_final")
        
        st.markdown("---")
        st.markdown("**Ou navegue pelas Categorias:**")
        cat_sel = st.selectbox("Selecione a Categoria para listar:", cats, key="categoria_filtro")

        if not busca_nome:
            prods_filtrados = pd.read_sql("""
                SELECT id, nome, preco, categoria FROM public.produtos 
                WHERE empresa_id = %s AND categoria = %s ORDER BY nome
            """, conn, params=[emp_id, cat_sel])
            if not prods_filtrados.empty:
                dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
                ps = st.selectbox("Confirmar Item filtrado por Categoria:", list(dp.keys()), key="select_cat_refinado")
            else:
                st.warning("Nenhum item encontrado nesta categoria.")

        if dp:
            q = st.number_input("Quantidade:", min_value=1, value=1, key="quantidade_item")
            if st.button("➕ Adicionar ao Pedido", type="secondary"):
                if not m.strip():
                    st.error("Por favor, digite o número da Mesa / Comanda antes de adicionar itens!")
                else:
                    chave_sel = st.session_state.get("select_busca_lupa") if busca_nome else st.session_state.get("select_cat_refinado")
                    if chave_sel in dp:
                        item_escolhido = dp[chave_sel]
                        st.session_state.carrinho.append({
                            "id": int(item_escolhido["id"]), "nome": item_escolhido["nome"],
                            "categoria": item_escolhido["categoria"], "qtd": int(q), "preco": float(item_escolhido["preco"])
                        })
                        st.success(f"{q}x {item_escolhido['nome']} adicionado ao rascunho!")
                        st.rerun()

        if st.session_state.carrinho:
            st.markdown("---")
            st.markdown(f"📋 **Resumo do Pedido Atual (Mesa: {m}):**")
            total_carrinho = 0.0
            for idx_c, item in enumerate(st.session_state.carrinho):
                sub_item = item["qtd"] * item["preco"]
                total_carrinho += sub_item
                col_txt, col_btn = st.columns()
                col_txt.write(f"▪️ **{item['qtd']}x** {item['nome']} [{item['categoria']}] — R$ {sub_item:.2f}")
                if col_btn.button("🗑️ Remover", key=f"rem_{idx_c}"):
                    st.session_state.carrinho.pop(idx_c)
                    st.rerun()
                                     
            st.markdown(f"### 🧾 Total Parcial: R$ {total_carrinho:.2f}")
            col_cancelar, col_enviar = st.columns(2)
            if col_cancelar.button("❌ Limpar Todo o Rascunho"):
                st.session_state.carrinho = []
                st.rerun()
            if col_enviar.button("🔥 LANÇAR COMANDA COMPLETA", type="primary"):
                estoque_geral_ok = True
                lista_ids = [item["id"] for item in st.session_state.carrinho]
                q_ids = tuple(int(i) for i in lista_ids)
                
                df_receitas = pd.read_sql("""
                    SELECT r.produto_id, r.insumo_id, r.qtd_insumo, e.item, e.quantidade as qtd_atual 
                    FROM public.receitas r 
                    JOIN public.estoque e ON r.insumo_id = e.id 
                    WHERE e.empresa_id = %s AND r.produto_id IN %s
                """, conn, params=(emp_id, q_ids))
                                         
                est_simulado = {}
                for _, r_ins in df_receitas.iterrows():
                    if r_ins["insumo_id"] not in est_simulado:
                        est_simulado[r_ins["insumo_id"]] = {"nome": r_ins["item"], "saldo": float(r_ins["qtd_atual"])}
                                         
                for item in st.session_state.carrinho:
                    recs_prod = df_receitas[df_receitas["produto_id"] == item["id"]]
                    for _, r_ins in recs_prod.iterrows():
                        qtd_total_gasta = (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                        est_simulado[r_ins["insumo_id"]]["saldo"] -= qtd_total_gasta
                        if est_simulado[r_ins["insumo_id"]]["saldo"] < 0:
                            st.error(f"❌ Estoque insuficiente de: {est_simulado[r_ins['insumo_id']]['nome']}")
                            estoque_geral_ok = False
                                             
                if estoque_geral_ok:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        hr = datetime.now().strftime("%d/%m/%Y %H:%M")
                        for item in st.session_state.carrinho:
                            cur.execute("""
                                INSERT INTO public.pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom) 
                                VALUES (%s, %s, %s, %s, 'Pendente', %s, %s)
                            """, (emp_id, str(m).strip(), int(item["id"]), int(item["qtd"]), hr, str(st.session_state.usuario_atual)))
                            
                            recs_prod = df_receitas[df_receitas["produto_id"] == item["id"]]
                            for _, r_ins in recs_prod.iterrows():
                                qtd_total_gasta = (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                                cur.execute("""
                                    UPDATE public.estoque SET quantidade = quantidade - %s 
                                    WHERE empresa_id = %s AND id = %s
                                """, (qtd_total_gasta, emp_id, int(r_ins["insumo_id"])))
                        c.commit()
                    st.success("🚀 Pedido lançado com sucesso e estoque atualizado!")
                    st.session_state.carrinho = []
                    st.rerun()

    with tabs:
        st.subheader("💵 Gerenciamento de Contas e Mesas")
        df_pedidos = pd.read_sql("""
            SELECT p.id, p.mesa, pr.nome, pr.preco, p.quantidade, p.status, p.taxa_paga 
            FROM public.pedidos p 
            JOIN public.produtos pr ON p.produto_id = pr.id 
            WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')
        """, conn, params=[emp_id])
                         
        if df_pedidos.empty:
            st.info("Nenhuma mesa com consumo aberto.")
        else:
            mesas_abertas = sorted(list(set(df_pedidos["mesa"].tolist())))
            m_conta = st.selectbox("Selecione a Mesa para fechar:", mesas_abertas, key="selecao_mesa_conta")
                                     
            pedidos_da_mesa = df_pedidos[df_pedidos["mesa"] == m_conta]
            total_mesa = 0.0
            st.markdown(f"### 📋 Extrato da Comanda: {m_conta}")
                                     
            for _, row in pedidos_da_mesa.iterrows():
                sub = row["quantidade"] * row["preco"]
                total_mesa += sub
                st.write(f"▪️ {row['quantidade']}x {row['nome']} — R$ {sub:.2f} ({row['status']})")
                                         
            taxa = total_mesa * 0.10
            st.markdown("---")
            st.markdown(f"**Subtotal:** R$ {total_mesa:.2f}")
                                     
            tirar_10 = st.checkbox("Tirar 10% da conta (Remover Taxa de Serviço)", key="chk_remover_10_porcento")
                                     
            if tirar_10:
                st.warning("🎁 Taxa de serviço de 10% removida do total.")
                total_geral = total_mesa
                valor_taxa_banco = 0
            else:
                st.markdown(f"**Taxa de Serviço (10%):** R$ {taxa:.2f}")
                total_geral = total_mesa + taxa
                valor_taxa_banco = 1
                                         
            st.markdown(f"## Total Geral: R$ {total_geral:.2f}")
                                     
            col_paga, col_npaga = st.columns(2)
            if col_paga.button("✅ Confirmar Pagamento Completo", type="primary", use_container_width=True):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("""
                        UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s 
                        WHERE empresa_id = %s AND mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')
                    """, (int(valor_taxa_banco), emp_id, str(m_conta)))
                    c.commit()
                st.success(f"Conta da comanda {m_conta} fechada com sucesso!")
                st.rerun()
