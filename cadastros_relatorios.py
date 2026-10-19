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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cadastros_garcons (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE NOT NULL,
                    codigo_operacional VARCHAR(100) NOT NULL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        conn.close()

init_db_funcionarios()

st.title("👥 Dashboard de Garçons & Performance de Vendas")
st.caption("Controle centralizado de colaboradores e auditoria de faturamento analítico")

tabs = st.tabs(["📝 Cadastrar Novo Garçom", "📊 Relatório e Performance de Vendas"])
with tabs[0]:
    st.subheader("📝 Registrar Colaborador no Sistema")
    
    col_cad1, col_dados2 = st.columns(2)
    with col_cad1:
        novo_garcao = st.text_input("Nome Completo do Garçom:", placeholder="Ex: Carlos Silva", key="f_nome_novo")
    with col_dados2:
        cod_garcao = st.text_input("Código Operacional / Senha rápida:", type="password", placeholder="Ex: 1234", key="f_senha_novo")
        
    if st.button("Salvar Registro de Funcionário", type="primary", use_container_width=True, key="f_btn_salvar"):
        if not novo_garcao.strip() or not cod_garcao.strip():
            st.error("Validação Recusada: Preencha todos os campos obrigatórios.")
        else:
            conn = init_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("INSERT INTO cadastros_garcons (nome, codigo_operacional) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (novo_garcao.strip(), cod_garcao.strip()))
                        conn.commit()
                    st.success(f"Funcionário '{novo_garcao}' homologado e ativo no banco Neon!")
                    time.sleep(0.4)
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro ao salvar: {err}")
                finally:
                    conn.close()

    st.markdown("---")
    st.subheader("👥 Equipe Ativa e Cadastrada")
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT nome, data_cadastro FROM cadastros_garcons ORDER BY nome;")
            equipe = cur.fetchall()
        conn.close()
        if equipe:
            for f in equipe:
                st.markdown(f"- 🟢 **{f['nome']}** *(Admitido em: {f['data_cadastro'].strftime('%d/%m/%Y')})*")
        else:
            st.info("Nenhum garçom cadastrado até o momento.")
with tabs[1]:
    st.subheader("🔍 Filtro de Fechamento por Período e Garçom")
    
    conn = init_connection()
    lista_busca_garcons = ["Todos os Garçons"]
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute("SELECT nome FROM cadastros_garcons ORDER BY nome;")
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

    query = "SELECT produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo, garcao_nome, data_hora FROM pedidos_realizados WHERE 1=1"
    parametros = []

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
        st.write("**Extrato de Lançamentos do Período:**")
        
        df_exibir = df.copy()
        df_exibir['data_hora'] = pd.to_datetime(df_exibir['data_hora']).dt.strftime('%d/%m/%Y %H:%M')
        df_exibir['Taxa (10%)'] = df_exibir['taxa_inclusa'].apply(lambda x: "🟢 Paga" if x else "⚪ Não cobrada")
        df_exibir['Comissão do Item'] = df_exibir['comissao_item'].apply(lambda x: f"R$ {x:.2f}")
        
        df_exibir = df_exibir[['produto_nome', 'quantidade_pedida', 'valor_total', 'Taxa (10%)', 'Comissão do Item', 'mesa_numero', 'comanda_codigo', 'garcao_nome', 'data_hora']]
        df_exibir.columns = ['Produto', 'Qtd', 'Valor (R$)', 'Taxa (10%)', 'Comissão', 'Mesa', 'Comanda', 'Garçom Responsável', 'Data/Hora']
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento de venda registrado para os filtros selecionados.")
