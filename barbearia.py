import streamlit as st
import psycopg2

def ob_cx():
    """Retorna a conexão com o banco de dados PostgreSQL usando as Secrets da nuvem."""
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: 
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), 
        user=c.get("username"), password=c.get("password"), sslmode="require"
    )

def inicializar_banco():
    """Cria a estrutura das tabelas na nuvem caso elas ainda não existam."""
    conn = ob_cx()
    with conn.cursor() as cur:
        cur.execute("SET search_path TO public;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.barbearias (
                id SERIAL PRIMARY KEY, 
                nome_barbearia TEXT UNIQUE NOT NULL, 
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS public.usuarios (
                id SERIAL PRIMARY KEY, 
                usuario TEXT, 
                senha TEXT, 
                cargo TEXT DEFAULT 'Barbeiro'
            );
            CREATE TABLE IF NOT EXISTS public.servicos (
                id SERIAL PRIMARY KEY, 
                nome TEXT, 
                preco REAL
            );
            CREATE TABLE IF NOT EXISTS public.agendamentos (
                id SERIAL PRIMARY KEY, 
                cliente TEXT, 
                servico_id INTEGER, 
                barbeiro TEXT, 
                status TEXT DEFAULT 'Pendente', 
                horario TEXT, 
                valor REAL, 
                comissao_paga INTEGER DEFAULT 1
            );
        """)
        # Adiciona colunas multi-tenant se não existirem
        cur.execute("ALTER TABLE public.usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.barbearias(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE public.servicos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.barbearias(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE public.agendamentos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.barbearias(id) ON DELETE CASCADE;")
        
        try: cur.execute("ALTER TABLE public.usuarios ADD CONSTRAINT unique_empresa_usuario_barber UNIQUE(empresa_id, usuario);")
        except Exception: conn.rollback()
        try: cur.execute("ALTER TABLE public.servicos ADD CONSTRAINT unique_empresa_servico UNIQUE(empresa_id, nome);")
        except Exception: conn.rollback()
    conn.commit()
    conn.close()
import streamlit as st
import pandas as pd
#from database import ob_cx

def renderizar_painel_gerencial():
    emp_id = st.session_state.empresa_id_atual
    
    if st.button("🔒 Bloquear Terminal do Estabelecimento por Completo", type="primary", use_container_width=True):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.barbeiro_logado = False
        st.session_state.carrinho_servicos = []
        st.rerun()
        
    st.markdown("---")
    st.subheader("🔑 Autenticação Gerencial Requerida")
    senha_gerencial_digitada = st.text_input("Digite a Senha Master da Empresa:", type="password")
    
    if senha_gerencial_digitada != st.session_state.senha_master_empresa:
        st.warning("🔒 Conteúdo restrito administrativo. Insira a senha master.")
        return

    conn = ob_cx()
    df_servicos = pd.read_sql("SELECT id, nome, preco FROM public.servicos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
    df_barbeiros_cad = pd.read_sql("SELECT id, usuario FROM public.usuarios WHERE empresa_id = %s ORDER BY usuario", conn, params=[emp_id])
    
    subtabs = st.tabs(["🛠️ Catálogo de Serviços", "👥 Equipe/Barbeiros", "📊 Relatório Financeiro", "🗑️ Exclusões"])
    
    with subtabs[0]:
        st.subheader("🍔 Cadastro de Serviços Rápido (Copiar e Colar)")
        texto_servicos = st.text_area("Formato: Nome do Serviço, Preço (um por linha)", placeholder="Corte Degradê, 45.0\nBarba, 35.0")
        if st.button("🔥 Gravar Serviços", use_container_width=True):
            if texto_servicos.strip():
                linhas = texto_servicos.strip().split("\n")
                gravados = 0
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    for linha in linhas:
                        if "," in linha:
                            partes = linha.split(",")
                            if len(partes) == 2:
                                n_s, p_s = partes[0].strip(), partes[1].strip()
                                try:
                                    cur.execute("""
                                        INSERT INTO public.servicos (empresa_id, nome, preco) VALUES (%s, %s, %s)
                                        ON CONFLICT (empresa_id, nome) DO UPDATE SET preco = EXCLUDED.preco
                                    """, (emp_id, n_s, float(p_s)))
                                    gravados += 1
                                except ValueError: pass
                    c.commit()
                st.success(f"🚀 {gravados} serviços atualizados!")
                st.rerun()
    
    with subtabs[1]:
        st.subheader("👥 Cadastro de Barbeiros")
        with st.form("f_cad_barber", clear_on_submit=True):
            n_b = st.text_input("Nome do Barbeiro:").strip()
            s_b = st.text_input("Senha do Barbeiro:", type="password").strip()
            if st.form_submit_button("💼 Confirmar Cadastro"):
                if n_b and s_b:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha, cargo) VALUES (%s, %s, %s, 'Barbeiro');", (emp_id, n_b, s_b))
                        c.commit()
                    st.success(f"Barbeiro '{n_b}' cadastrado!")
                    st.rerun()
    
    with subtabs[2]:
        st.subheader("📊 Faturamento e Comissões (50%)")
        vendas_df = pd.read_sql("""
            SELECT p.cliente, pr.nome as servico, p.barbeiro, p.valor, p.status, p.comissao_paga, p.horario 
            FROM public.agendamentos p JOIN public.servicos pr ON p.servico_id = pr.id 
            WHERE p.empresa_id = %s AND p.status = 'Finalizado (Pago)' ORDER BY p.horario DESC
        """, conn, params=[emp_id])
        
        if vendas_df.empty: 
            st.info("Nenhum atendimento finalizado registrado.")
        else:
            vendas_df['data_somente'] = vendas_df['horario'].apply(lambda x: str(x).split(" ")[0] if " " in str(x) else str(x))
            lista_datas = sorted(list(set(vendas_df['data_somente'].tolist())), reverse=True)
            data_filtro = st.selectbox("📅 Selecione a Data:", lista_datas)
            
            df_filtrado = vendas_df[vendas_df['data_somente'] == data_filtro]
            faturamento_total = float(df_filtrado['valor'].sum())
            comissoes_totais = float(df_filtrado[df_filtrado['comissao_paga'] == 1]['valor'].sum() * 0.50)
            liquido_casa = faturamento_total - comissoes_totais
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Faturamento Bruto", f"R$ {faturamento_total:.2f}")
            c2.metric("💈 Comissões", f"R$ {comissoes_totais:.2f}")
            c3.metric("📈 Líquido Casa", f"R$ {liquido_casa:.2f}")
            st.dataframe(df_filtrado.drop(columns=['data_somente']), use_container_width=True, hide_index=True)

    with subtabs[3]:
        st.subheader("🗑️ Remover Itens")
        col1, col2 = st.columns(2)
        with col1:
            if not df_servicos.empty:
                s_del = st.selectbox("Excluir Serviço:", [r['nome'] for _, r in df_servicos.iterrows()])
                if st.button("❌ Excluir Serviço", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; DELETE FROM public.servicos WHERE empresa_id = %s AND nome = %s", (emp_id, s_del))
                        c.commit()
                    st.success("Removido!"); st.rerun()
        with col2:
            if not df_barbeiros_cad.empty:
                b_del = st.selectbox("Excluir Barbeiro:", [r['usuario'] for _, r in df_barbeiros_cad.iterrows() if r['usuario'] != 'admin'])
                if st.button("❌ Remover Profissional", use_container_width=True):
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; DELETE FROM public.usuarios WHERE empresa_id = %s AND usuario = %s", (emp_id, b_del))
                        c.commit()
                    st.success("Removido!"); st.rerun()
    conn.close()
import streamlit as st
import pandas as pd
from datetime import datetime
#from database import ob_cx

def renderizar_terminal_barbeiro():
    emp_id = st.session_state.empresa_id_atual
    conn = ob_cx()
    
    if not st.session_state.barbeiro_logado:
        st.subheader("👤 Identificação do Barbeiro")
        with st.form("login_barber_form"):
            barber_input = st.text_input("Usuário do Barbeiro:")
            senha_barber = st.text_input("Senha:", type="password")
            if st.form_submit_button("Entrar no Sistema", type="primary"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("SELECT usuario FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (emp_id, barber_input.strip().lower(), senha_barber.strip()))
                    res = cur.fetchone()
                if res:
                    st.session_state.barbeiro_logado = True
                    st.session_state.usuario_atual = str(res[0])
                    st.rerun()
                else: st.error("Senha incorreta!")
    else:
        st.subheader(f"💈 Profissional Ativo: {st.session_state.usuario_atual.upper()}")
        if st.button("🔒 Sair / Trocar de Barbeiro", use_container_width=True):
            st.session_state.barbeiro_logado = False
            st.session_state.usuario_atual = ""
            st.session_state.carrinho_servicos = []
            st.rerun()
            
        aba_operacao = st.radio("Ação:", ["➕ Novo Atendimento", "🧾 Caixa / Comandas"], horizontal=True)
        
        if aba_operacao == "➕ Novo Atendimento":
            cliente_input = st.text_input("Identificação do Cliente / Cadeira:", value="Cadeira 01")
            df_servs_venda = pd.read_sql("SELECT id, nome, preco FROM public.servicos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
            
            if df_servs_venda.empty:
                st.info("Nenhum serviço no catálogo.")
            else:
                lupa_servs = st.text_input("🔍 Buscar Serviço:").strip()
                if lupa_servs:
                    df_servs_venda = df_servs_venda[df_servs_venda['nome'].str.contains(lupa_servs, case=False, na=False)]
                
                serv_map = {f"{row['nome']} - R$ {row['preco']:.2f}": (row['id'], row['nome'], row['preco']) for _, row in df_servs_venda.iterrows()}
                if serv_map:
                    serv_selecionado = st.selectbox("Escolha o Serviço:", list(serv_map.keys()))
                    if st.button("➕ Adicionar Serviço", use_container_width=True):
                        s_id, s_nome, s_preco = serv_map[serv_selecionado]
                        st.session_state.carrinho_servicos.append({"id": s_id, "nome": s_nome, "preco": s_preco})
                        st.toast(f"{s_nome} adicionado!")
                
                if st.session_state.carrinho_servicos:
                    st.markdown("### 🛒 Resumo da Cadeira")
                    total_carrinho = sum(item['preco'] for item in st.session_state.carrinho_servicos)
                    for item in st.session_state.carrinho_servicos:
                        st.write(f"▪ {item['nome']} - R$ {item['preco']:.2f}")
                    
                    st.markdown(f"**Total Parcial:** R$ {total_carrinho:.2f}")
                    conf_b = st.checkbox("✅ Confirmo os serviços na cadeira.")
                    
                    c_limpar, c_enviar = st.columns(2)
                    if c_limpar.button("🗑️ Limpar"): st.session_state.carrinho_servicos = []; st.rerun()
                    if c_enviar.button("🚀 Enviar para o Caixa", type="primary"):
                        if not conf_b: st.error("Marque a confirmação!")
                        else:
                            hr_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            with ob_cx() as c, c.cursor() as cur:
                                cur.execute("SET search_path TO public;")
                                for item in st.session_state.carrinho_servicos:
                                    cur.execute("""
                                        INSERT INTO public.agendamentos (empresa_id, cliente, servico_id, barbeiro, status, horario, valor)
                                        VALUES (%s, %s, %s, %s, 'Pendente', %s, %s)
                                    """, (emp_id, cliente_input.strip(), int(item['id']), st.session_state.usuario_atual, hr_atual, float(item['preco'])))
                                c.commit()
                            st.success("Enviado com sucesso!"); st.session_state.carrinho_servicos = []; st.rerun()

        elif aba_operacao == "🧾 Caixa / Comandas":
            ativos = pd.read_sql("""
                SELECT p.id, p.cliente, pr.nome as servico, p.valor, p.status 
                FROM public.agendamentos p JOIN public.servicos pr ON p.servico_id = pr.id 
                WHERE p.empresa_id = %s AND p.status IN ('Pendente', 'Confirmado') ORDER BY p.cliente
            """, conn, params=[emp_id])
            
            if ativos.empty:
                st.info("Nenhuma comanda aberta.")
            else:
                lupa_cliente = st.text_input("🔍 Pesquisar Cliente/Cadeira:").strip()
                df_caixa = ativos[ativos['cliente'].str.contains(lupa_cliente, case=False, na=False)] if lupa_cliente else ativos
                
                if not df_caixa.empty:
                    clientes_abertos = sorted(list(set(df_caixa['cliente'].tolist())))
                    cliente_ver = st.selectbox("Selecione o Cliente para Pagar:", clientes_abertos)
                    df_cliente_filtrado = ativos[ativos['cliente'] == cliente_ver]
                    
                    subtotal = sum(row['valor'] for _, row in df_cliente_filtrado.iterrows())
                    st.markdown(f"### 🧾 Total: R$ {subtotal:.2f}")
                    pagar_comissao = st.checkbox("Pagar comissão (50%) ao barbeiro?", value=True)
                    
                    if st.button("💰 Receber e Finalizar Conta", type="primary", use_container_width=True):
                        valor_comissao = 1 if pagar_comissao else 0
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("""
                                UPDATE public.agendamentos SET status = 'Finalizado (Pago)', comissao_paga = %s 
                                WHERE empresa_id = %s AND cliente = %s AND status IN ('Pendente', 'Confirmado')
                            """, (valor_comissao, emp_id, str(cliente_ver)))
                            c.commit()
                        st.success("Conta fechada!"); st.rerun()
    conn.close()
import streamlit as st
import pandas as pd
#from database import inicializar_banco, ob_cx
from gerencial import renderizar_painel_gerencial
from terminal import renderizar_terminal_barbeiro

st.set_page_config(page_title="Sistema Multitenant Barbearia", layout="centered")

# Inicializa variáveis de estado globais
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
if "empresa_id_atual" not in st.session_state: st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state: st.session_state.senha_master_empresa = ""
if "barbeiro_logado" not in st.session_state: st.session_state.barbeiro_logado = False
if "carrinho_servicos" not in st.session_state: st.session_state.carrinho_servicos = []

# Injeção de CSS para esconder cabeçalhos nativos do Streamlit
st.markdown("""
    <style>
    #MainMenu, .stAppDeployButton { visibility: hidden !important; display: none !important; }
    header [data-testid="stToolbar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header { background-color: transparent !important; }
    .stButton>button { width: 100%; height: 3rem; }
    </style>
""", unsafe_allow_html=True)

# Garante que o banco está pronto na nuvem
inicializar_banco()

# --- TELA DE ACESSO INICIAL ---
if not st.session_state.logado:
    aba_acesso = st.radio("Opção:", ["Fazer Login", "Cadastrar Nova Barbearia"], horizontal=True)
    
    if aba_acesso == "Cadastrar Nova Barbearia":
        with st.form("cadastro_empresa"):
            st.subheader("🏢 Cadastrar Barbearia")
            nova_empresa = st.text_input("Nome Comercial da Barbearia:").strip()
            adm_usuario = st.text_input("Usuário Admin (Ex: admin):").strip()
            adm_senha = st.text_input("Senha do Administrador:", type="password").strip()
            
            if st.form_submit_button("Criar Conta Master", type="primary") and nova_empresa and adm_usuario and adm_senha:
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; INSERT INTO public.barbearias (nome_barbearia) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO public.usuarios (empresa_id, usuario, senha, cargo) VALUES (%s, %s, %s, 'Admin');", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success("🎉 Barbearia registrada com sucesso! Mude para a aba de Login.")
                except Exception as e: st.error(f"Erro: Estabelecimento já registrado.")
    else:
        with st.form("login_empresa"):
            st.subheader("📱 Login do Estabelecimento")
            conn = ob_cx()
            df_lista = pd.read_sql("SELECT id, nome_barbearia FROM public.barbearias ORDER BY nome_barbearia", conn)
            conn.close()
            
            dict_empresas = {row["nome_barbearia"]: row["id"] for _, row in df_lista.iterrows()} if not df_lista.empty else {}
            
            if dict_empresas:
                empresa_sel = st.selectbox("Selecione sua Barbearia:", list(dict_empresas.keys()))
                user_input = st.text_input("Usuário Admin:")
                senha_input = st.text_input("Senha Admin:", type="password")
                
                if st.form_submit_button("Liberar Terminal", type="primary") and user_input and senha_input:
                    id_empresa_login = dict_empresas[empresa_sel]
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("SELECT empresa_id, senha FROM public.usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (id_empresa_login, user_input.strip(), senha_input.strip()))
                        resultado = cur.fetchone()
                    
                    if resultado:
                        st.session_state.logado = True
                        st.session_state.empresa_id_atual = int(resultado[0])
                        st.session_state.senha_master_empresa = str(resultado[1])
                        st.rerun()
                    else: st.error("Credenciais incorretas.")
            else: st.info("Nenhuma barbearia ativa.")
    st.stop()

# --- SISTEMA AUTENTICADO ---
aba_master_sistema, aba_master_operador = st.tabs(["⚙️ Painel de Controle Gerencial", "📱 Terminal do Barbeiro"])

with aba_master_sistema:
    renderizar_painel_gerencial()

with aba_master_operador:
    renderizar_terminal_barbeiro()
streamlit
psycopg2-binary
pandas
