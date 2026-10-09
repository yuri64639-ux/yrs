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
    conn.commit()
        
    # CORREÇÃO DO ERRO: Derruba explicitamente índices únicos antigos baseados apenas em uma coluna global
    try: cur.execute("ALTER TABLE public.produtos DROP CONSTRAINT IF EXISTS produtos_nome_key CASCADE;")
    except Exception: conn.rollback()
    try: cur.execute("ALTER TABLE public.produtos DROP CONSTRAINT IF EXISTS unique_produto CASCADE;")
    except Exception: conn.rollback()
    try: cur.execute("ALTER TABLE public.estoque DROP CONSTRAINT IF EXISTS estoque_item_key CASCADE;")
    except Exception: conn.rollback()
    try: cur.execute("ALTER TABLE public.usuarios DROP CONSTRAINT IF EXISTS usuarios_usuario_key CASCADE;")
    except Exception: conn.rollback()
    conn.commit()

    # Adicionando de forma protegida as constraints necessárias para o ON CONFLICT compostas por empresa
    try: cur.execute("ALTER TABLE public.usuarios ADD CONSTRAINT unique_empresa_usuario UNIQUE(empresa_id, usuario);")
    except Exception: conn.rollback()
    try: cur.execute("ALTER TABLE public.estoque ADD CONSTRAINT unique_empresa_item UNIQUE(empresa_id, item);")
    except Exception: conn.rollback()
    try: cur.execute("ALTER TABLE public.produtos ADD CONSTRAINT unique_empresa_produto UNIQUE(empresa_id, nome);")
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
    conn.close()
    st.stop()

# --- CONTROLE DINÂMICO DE VISUALIZAÇÃO DAS ABAS MASTERS ---
if st.session_state.garcom_logado:
    st.markdown("### 📱 Ambiente do Funcionário")
    aba_master_operador = st.container()
    aba_master_sistema = st.empty() 
else:
    aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Garçom"])

# Inicializador estrutural de validação do escopo gerencial
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
         
        # --- BARREIRA DE SEGURANÇA COM SENHA PARA ACESSO GERENCIAL ---
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
            permitir_render_gerencial = True
            
        if permitir_render_gerencial:
            df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque WHERE empresa_id = %s ORDER BY item", conn, params=[emp_id])
            df_prods = pd.read_sql("SELECT id, nome FROM public.produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
                                     
            subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas", "📊 Relatórios", "🗑️ Excluir"])
                                 
            # --- 1. ESTOQUE ---
            with subtabs[0]:
                st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
                df_est_visual = df_est.copy()
                if not df_est_visual.empty: 
                     df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual"]
                st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
                                                     
                with st.expander("➕ Alimentar Estoque (Individual)"):
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
                 
                with st.expander("🍔 Alimentar Estoque em Massa (Copiar e Colar)"):
                    st.write("Cole a sua lista abaixo seguindo o formato exato: **Insumo, Quantidade** (um insumo por linha).")
                    with st.form("f_ins_massa_texto_direto", clear_on_submit=True):
                        texto_insumos = st.text_area("Cole seus insumos aqui:", height=200, placeholder="Exemplo:\nVodka, 10.0\nLimão, 50.0")
                        botao_gravar_insumos = st.form_submit_button("🔥 Gravar Todos os Insumos")
                                                 
                        if botao_gravar_insumos and texto_insumos.strip():
                            linhas_ins = texto_insumos.strip().split("\n")
                            insumos_gravados = 0
                            with ob_cx() as c, c.cursor() as cur:
                                cur.execute("SET search_path TO public;")
                                for linha_ins in linhas_ins:
                                    if "," in linha_ins:
                                        partes_ins = linha_ins.split(",")
                                        if len(partes_ins) == 2:
                                            n_ins = partes_ins[0].strip()
                                            q_ins = partes_ins[1].strip()
                                            if n_ins:
                                                try:
                                                    qtd_float = float(q_ins)
                                                    cur.execute("""
                                                        INSERT INTO public.estoque (empresa_id, item, quantidade) 
                                                        VALUES (%s, %s, %s) 
                                                        ON CONFLICT (empresa_id, item) DO UPDATE SET quantidade = public.estoque.quantidade + EXCLUDED.quantidade
                                                    """, (emp_id, n_ins, qtd_float))
                                                    insumos_gravados += 1
                                                except ValueError: pass
                                c.commit()
                            if insumos_gravados > 0: 
                                 st.success(f"🚀 Sucesso! {insumos_gravados} insumos adicionados!"); st.rerun()
            # --- 2. CANCELAMENTOS ---
            with subtabs[1]:
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
                            st.success("Item removido e estoque devolvido!"); st.rerun()
             
            # --- 3. CADASTRO EM MASSA ---
            with subtabs[2]:
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
                            c.commit()
                        if itens_gravados > 0: st.success(f"🚀 Sucesso! {itens_gravados} produtos salvos!"); st.rerun()
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
                            with ob_cx() as c, c.cursor() as cur:
                                cur.execute("SET search_path TO public;")
                                if i1 != "---" and q1 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, int(p_sel), int(d_i[i1]), float(q1)))
                                if i2 != "---" and q2 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, int(p_sel), int(d_i[i2]), float(q2)))
                                if i3 != "---" and q3 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, int(p_sel), int(d_i[i3]), float(q3)))
                                if i4 != "---" and q4 > 0: cur.execute("INSERT INTO public.receitas (empresa_id, produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s, %s) ON CONFLICT (empresa_id, produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (emp_id, int(p_sel), int(d_i[i4]), float(q4)))
                                c.commit()
                            st.success("Ficha técnica salva!"); st.rerun()
                else: st.info("Cadastre insumos e produtos na conta antes.")
             
            # --- 5. RELATÓRIOS ---
            with subtabs[4]:
                st.subheader("📊 Resumo Financeiro Detalhado")
                vendas_df = pd.read_sql("SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.horario DESC", conn, params=[emp_id])
                if vendas_df.empty: st.info("Nenhuma comanda histórica para esta empresa.")
                else:
                    vendas_df['data_somente'] = vendas_df['horario'].apply(lambda x: str(x).split(" ")[0] if " " in str(x) else "Sem Data")
                    lista_datas_disponiveis = sorted(list(set(vendas_df['data_somente'].tolist())), reverse=True)
                    data_filtro_relatorio = st.selectbox("📅 Selecione a Data para filtrar o relatório:", lista_datas_disponiveis)
                                                         
                    df_vendas_filtrado_data = vendas_df[vendas_df['data_somente'] == data_filtro_relatorio]
                                                         
                    empresa_total, garcons_total, pendente_total = 0.0, 0.0, 0.0
                    for mesa_id, group in df_vendas_filtrado_data.groupby('mesa'):
                        sub_mesa = float(group['subtotal'].sum())
                        status_mesa = group['status'].iloc[0]
                        taxa_marcada = int(group['taxa_paga'].iloc[0]) == 1
                        if status_mesa == 'Finalizado (Pago)':
                            empresa_total += sub_mesa
                            if taxa_marcada: garcons_total += (sub_mesa * 0.10)
                        else: pendente_total += sub_mesa
                    c1, c2, c3 = st.columns(3); c1.metric("💰 Faturamento Líquido", f"R$ {empresa_total:.2f}"); c2.metric("🍹 Caixinha (10%)", f"R$ {garcons_total:.2f}"); c3.metric("⚠️ Perdas", f"R$ {pendente_total:.2f}")
                                                         
                    df_relatorio_visual = df_vendas_filtrado_data.copy()
                    df_relatorio_visual = df_relatorio_visual.drop(columns=['data_somente'])
                    df_relatorio_visual.columns = ["Mesa/Comanda", "Produto", "Quantidade", "Preço Unitário", "Subtotal", "Status", "Taxa Paga", "Data/Hora"]
                    st.dataframe(df_relatorio_visual, use_container_width=True, hide_index=True)
             
            # --- 6. EXCLUIR ---
            with subtabs[5]:
                st.subheader("🗑️ Remover Produtos, Insumos ou Garçons do Sistema")
                col_del1, col_del2, col_del3 = st.columns(3)
                with col_del1:
                    if not df_prods.empty:
                      if lupa_produtos:
                    df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(lupa_produtos, case=False)]

                st.markdown("### Selecione os Produtos:")
                for _, prod in df_filtrado.iterrows():
                    col_p1, col_p2, col_p3 = st.columns(3)
                    col_p1.write(f"**{prod['nome']}** — R$ {prod['preco']:.2f}")
                    qtd_adicionar = col_p2.number_input("Qtd:", min_value=1, max_value=50, value=1, key=f"qtd_venda_{prod['id']}")
                    if col_p3.button("🛒 Add", key=f"btn_add_{prod['id']}", use_container_width=True):
                        item_existente = False
                        for idx, item in enumerate(st.session_state.carrinho):
                            if item["id"] == prod["id"]:
                                st.session_state.carrinho[idx]["quantidade"] += qtd_adicionar
                                item_existente = True
                                break
                        if not item_existente:
                            st.session_state.carrinho.append({"id": prod["id"], "nome": prod["nome"], "preco": prod["preco"], "quantidade": qtd_adicionar})
                        st.toast(f"{qtd_adicionar}x {prod['nome']} adicionado!")

                if st.session_state.carrinho:
                    st.markdown("---")
                    st.subheader(f"🛒 Carrinho — {mesa_operacao}")
                    total_carrinho = 0.0
                    carrinho_atualizado = []
                    for idx, item in enumerate(st.session_state.carrinho):
                        subtotal_item = item["quantidade"] * item["preco"]
                        total_carrinho += subtotal_item
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"▪ {item['quantidade']}x {item['nome']}")
                        c2.write(f"R$ {subtotal_item:.2f}")
                        if not c3.button("❌", key=f"del_car_{idx}"):
                            carrinho_atualizado.append(item)
                    st.session_state.carrinho = carrinho_atualizado
                    st.markdown(f"**Total Parcial: R$ {total_carrinho:.2f}**")
                    
                    if st.button("🔥 Confirmar e Enviar Pedido", type="primary", use_container_width=True):
                        horario_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            for item in st.session_state.carrinho:
                                cur.execute("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE empresa_id = %s AND produto_id = %s", (emp_id, int(item["id"])))
                                for insumo_id, qtd_insumo in cur.fetchall():
                                    cur.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE empresa_id = %s AND id = %s", (((float(qtd_insumo) / 1000.0) * int(item["quantidade"])), emp_id, int(insumo_id)))
                                cur.execute("INSERT INTO public.pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom, pago) VALUES (%s, %s, %s, %s, 'Pendente', %s, %s, 'Não')", (emp_id, mesa_operacao.strip(), int(item["id"]), int(item["quantidade"]), horario_atual, st.session_state.usuario_atual))
                            c.commit()
                        st.success("Pedido gravado!")
                        st.session_state.carrinho = []
                        st.rerun()

        elif aba_operacao == "🧾 Fechar Mesas":
            st.subheader("🧾 Fechamento de Comandas")
            df_comandas = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn, params=[emp_id])
            if df_comandas.empty:
                st.info("Nenhuma mesa aberta.")
            else:
                mesa_fechar = st.selectbox("Selecione a Mesa:", sorted(list(set(df_comandas['mesa'].tolist()))))
                df_m = df_comandas[df_comandas['mesa'] == mesa_fechar]
                st.dataframe(df_m.drop(columns=['id', 'mesa']), use_container_width=True, hide_index=True)
                sub_m = float(df_m['subtotal'].sum())
                pagar_taxa = st.checkbox("Incluir Taxa de Serviço (10%)", value=True)
                val_f = (sub_m * 1.10) if pagar_taxa else sub_m
                st.markdown(f"### **Total: R$ {val_f:.2f}**")
                
                b1, b2 = st.columns(2)
                if b1.button("✅ Confirmar Pagamento", type="primary", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s, pago = 'Sim' WHERE empresa_id = %s AND mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (1 if pagar_taxa else 0, emp_id, mesa_fechar))
                        c.commit()
                    st.success("Mesa fechada!"); st.rerun()
                if b2.button("⚠️ Fechar como Perda", type="secondary", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; UPDATE public.pedidos SET status = 'Fechado (Não Pago)', taxa_paga = 0, pago = 'Não' WHERE empresa_id = %s AND mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (emp_id, mesa_fechar))
                        c.commit()
                    st.warning("Registrado como perda!"); st.rerun()

conn.close()
