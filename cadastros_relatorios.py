import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Gestão de Equipe & Performance", layout="wide")

def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão relacional: {e}")
        return None

def init_db_funcionarios():
    conn = init_connection()
    if conn:
        with conn.cursor() as cur:
            # Estrutura base Multi-Tenant integrada com a tabela global do ecossistema Neon
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.cadastros_garcons (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    codigo_operacional VARCHAR(100) NOT NULL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    empresa_id INT
                );
            """)
            # Injeção de segurança retroativa para a coluna de isolamento empresarial
            cur.execute("ALTER TABLE public.cadastros_garcons ADD COLUMN IF NOT EXISTS empresa_id INT;")
            cur.execute("ALTER TABLE public.pedidos_realizados ADD COLUMN IF NOT EXISTS empresa_id INT;")
            
            # Remove a restrição única antiga que impedia nomes iguais em empresas diferentes
            cur.execute("ALTER TABLE public.cadastros_garcons DROP CONSTRAINT IF EXISTS cadastros_garcons_nome_key;")
            cur.execute("ALTER TABLE public.cadastros_garcons DROP CONSTRAINT IF EXISTS unique_garcom_por_empresa;")
            
            # Aplica nova regra que protege duplicidade APENAS dentro da mesma empresa
            cur.execute("ALTER TABLE public.cadastros_garcons ADD CONSTRAINT unique_garcom_por_empresa UNIQUE (nome, empresa_id);")
            conn.commit()
        conn.close()

init_db_funcionarios()

# --- RECONHECIMENTO AUTOMÁTICO DO INQUILINO COM PORTÃO DE SEGURANÇA ---
id_empresa_contexto = None

if "empresa_id_ativo" in st.session_state and st.session_state.empresa_id_ativo:
    id_empresa_contexto = st.session_state.empresa_id_ativo
elif "empresa_id_garcom" in st.session_state and st.session_state.empresa_id_garcom:
    id_empresa_contexto = st.session_state.empresa_id_garcom
elif "emp_id" in st.query_params:
    id_empresa_contexto = int(st.query_params["emp_id"])

# BARREIRA DE AUTENTICAÇÃO: Exige login corporativo se o app for aberto isoladamente
if not id_empresa_contexto:
    st.markdown("<h2 style='text-align: center;'>🔒 Autenticação de Auditoria e Relatórios</h2>", unsafe_allow_html=True)
    conn = init_connection()
    lista_opcoes_emp = []
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome_fantasia FROM public.empresas ORDER BY nome_fantasia;")
            lista_opcoes_emp = cur.fetchall()
        conn.close()
    
    # CORREÇÃO CRÍTICA: Mapeia o nome de exibição (Texto) diretamente para o ID numérico (Inteiro)
    mapa_fallback = {row[1]: row[0] for row in lista_opcoes_emp} if lista_opcoes_emp else {}
    
    if not mapa_fallback:
        st.error("Nenhuma empresa localizada na nuvem Neon para associação.")
        st.stop()
        
    with st.form("login_relatorios_seguro"):
        emp_manual = st.selectbox("Selecione sua Empresa para liberar este terminal:", options=list(mapa_fallback.keys()))
        senha_comercial = st.text_input("Senha Master da Empresa:", type="password")
        
        if st.form_submit_button("Liberar Módulo de Auditoria", type="primary", use_container_width=True):
            id_selecionado = mapa_fallback[emp_manual]
            
            conn = init_connection()
            autenticado = False
            if conn:
                with conn.cursor() as cur:
                    # Agora a consulta recebe o ID numérico perfeitamente filtrado
                    cur.execute("SELECT id FROM public.empresas WHERE id = %s AND senha_master = %s;", (int(id_selecionado), senha_comercial.strip()))
                    if cur.fetchone():
                        autenticado = True
                conn.close()
                
            if autenticado:
                st.session_state.empresa_id_ativo = id_selecionado
                st.query_params["emp_id"] = str(id_selecionado)
                st.success("Terminal Vinculado e Protegido!")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("❌ Senha incorreta para o estabelecimento selecionado!")
    st.stop()
# Interface Principal de Business Intelligence (Focada em Relatórios)
col_titulo, col_logoff = st.columns([0.8, 0.2])
with col_titulo:
    st.title("📊 Central de Relatórios & Performance de Vendas")
    st.caption("Auditoria de faturamento analítico e métricas financeiras integradas")
with col_logoff:
    if st.button("🔒 Bloquear Painel", use_container_width=True, key="btn_lock_relatorios"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

st.markdown("---")
st.subheader("🔍 Filtro de Fechamento por Período e Garçom")

conn = init_connection()
lista_busca_garcons = ["Todos os Garçons"]
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            # FILTRO CRÍTICO: Carrega no seletor apenas os garçons da empresa logada
            cur.execute("SELECT nome FROM public.cadastros_garcons WHERE empresa_id = %s ORDER BY nome;", (id_empresa_contexto,))
            for row in cur.fetchall():
                lista_busca_garcons.append(row['nome'])
        except:
            pass
    conn.close()

c_f1, c_f2, c_f3, c_f4 = st.columns(4)
with c_f1:
    sel_garcao_filtro = st.selectbox("Selecione o Garçom:", options=lista_busca_garcons, key="f_sel_garc")
with c_f2:
    ano_atual = datetime.now().year
    ano_sel = st.selectbox("Ano:", options=list(range(ano_atual, ano_atual - 4, -1)), key="f_sel_ano")
with c_f3:
    meses_nome = {0: "Todos os Meses", 1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
    mes_sel = st.selectbox("Mês:", options=list(meses_nome.keys()), format_func=lambda x: meses_nome[x], index=datetime.now().month, key="f_sel_mes")
with c_f4:
    dia_sel = st.selectbox("Dia:", options=["Todos os Dias"] + list(range(1, 32)), key="f_sel_dia")
# VALIDAÇÃO MULTI-TENANT OBRIGATÓRIA: Restringe os dados unicamente ao id_empresa_contexto ativo
query = "SELECT produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo, garcao_nome, data_hora FROM pedidos_realizados WHERE empresa_id = %s"
parametros = [id_empresa_contexto]

if sel_garcao_filtro != "Todos os Garçons":
    query += " AND garcao_nome = %s"
    parametros.append(sel_garcao_filtro)
if ano_sel:
    query += " AND EXTRACT(YEAR FROM data_hora) = %s"
    parametros.append(ano_sel)
if mes_sel != 0:
    query += " AND EXTRACT(MONTH FROM data_hora) = %s"
    parametros.append(mes_sel)
if dia_sel != "Todos os Dias":
    query += " AND EXTRACT(DAY FROM data_hora) = %s"
    parametros.append(dia_sel)

query += " ORDER BY data_hora DESC;"

conn = init_connection()
vendas_filtradas = []
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, tuple(parametros))
        vendas_filtradas = cur.fetchall()
    conn.close()

if vendas_filtradas:
    df = pd.DataFrame(vendas_filtradas)
    df['valor_total'] = df['valor_total'].astype(float)
    
    faturamento_total = df['valor_total'].sum()
    pedidos_total = len(df)
    
    df['comissao_item'] = df.apply(lambda row: (row['valor_total'] / 1.10) * 0.10 if row['taxa_inclusa'] else row['valor_total'] * 0.10, axis=1)
    comissao_total = df['comissao_item'].sum()
    
    m_c1, m_c2, m_c3 = st.columns(3)
    with m_c1:
        st.metric("Total Vendido pelo Filtro", f"R$ {faturamento_total:.2f}")
    with m_c2:
        st.metric("Total de Itens Lançados", f"{pedidos_total} produtos")
    with m_c3:
        st.metric("Comissão Acumulada (10% Garçom)", f"R$ {comissao_total:.2f}")
            
    st.markdown("---")
    st.write("**Extrato de Lançamentos Privado do Período:**")
    
    df_exibir = df.copy()
    df_exibir['data_hora'] = pd.to_datetime(df_exibir['data_hora']).dt.strftime('%d/%m/%Y %H:%M')
    df_exibir['Taxa (10%)'] = df_exibir['taxa_inclusa'].apply(lambda x: "🟢 Paga" if x else "⚪ Não cobrada")
    df_exibir['Comissão do Item'] = df_exibir['comissao_item'].apply(lambda x: f"R$ {x:.2f}")
    
    df_exibir = df_exibir[['produto_nome', 'quantidade_pedida', 'valor_total', 'Taxa (10%)', 'Comissão do Item', 'mesa_numero', 'comanda_codigo', 'garcao_nome', 'data_hora']]
    df_exibir.columns = ['Produto', 'Qtd', 'Valor (R$)', 'Taxa (10%)', 'Comissão', 'Mesa', 'Comanda', 'Garçom Responsável', 'Data/Hora']
    
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum lançamento de venda registrado para os filtros selecionados no ambiente desta empresa.")
