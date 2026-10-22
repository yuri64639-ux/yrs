import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time as time_module

# Configuração de Ambiente para o Painel de Controle Privado
st.set_page_config(page_title="Agenda Interna - marinote club", page_icon="✂️", layout="wide")

# --- INJEÇÃO DE ARTWORK CSS PREMIUM (PRETO CARBONO & DOURADO METÁLICO IDENTICO) ---
st.markdown(
    """
    <style>
    /* Oculta os cabeçalhos nativos e menus de deploy do Streamlit */
    header, [data-testid="stHeader"], [data-testid="stAppToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    .stApp {
        background-color: #121212 !important;
        color: #E5E5E5 !important;
    }
    
    /* Estilização da Tipografia e Cabeçalhos */
    h1, h2, h3, h4, h5, h6, label, p {
        color: #D4AF37 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* Caixa de Inputs, Dropdowns e Tabela Personalizados */
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div {
        background-color: #1E1E1E !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 8px !important;
    }
    input, select {
        color: #FFFFFF !important;
    }

    /* Botão Principal Dourado com Fonte Escura e Efeito Hover */
    .stButton>button {
        width: 100%;
        height: 3.2rem;
        background-color: #D4AF37 !important;
        color: #121212 !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease;
        box-shadow: 0px 4px 10px rgba(212, 175, 55, 0.2);
    }
    .stButton>button:hover {
        background-color: #AA8226 !important;
        box-shadow: 0px 6px 15px rgba(212, 175, 55, 0.4);
        transform: translateY(-2px);
    }

    /* Estilização do Logo Metálico Centralizado (Idêntico ao do Cliente) */
    .logo-container {
        text-align: center;
        padding: 20px;
        margin-bottom: 10px;
    }
    .logo-text {
        font-family: 'Cinzel', 'Playfair Display', serif;
        font-size: 48px;
        font-weight: 700;
        letter-spacing: 2px;
        background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
    }
    .sub-logo {
        font-size: 13px;
        color: #8A8A8A;
        letter-spacing: 6px;
        text-transform: uppercase;
        margin-top: -5px;
        font-weight: 300;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- CONEXÃO SEGURA COM O BANCO DE DADOS NEON CENTRAL ---
@st.cache_resource
def obter_conexao():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão com o banco Neon: {e}")
        return None

# --- MONITOR DE ALERTA E REFRESH AUTOMÁTICO EM SEGUNDO PLANO ---
@st.fragment(run_every="5s")
def checar_proximidade_clientes_oculto():
    conn = obter_conexao()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            data_hoje_str = datetime.now().strftime("%Y-%m-%d")
            cur.execute("SELECT nome, horario, servico FROM public.agendamentos_marinote WHERE data_agenda = %s;", (data_hoje_str,))
            agendamentos_hoje = cur.fetchall()
            
            if agendamentos_hoje:
                agora = datetime.now()
                for row in agendamentos_hoje:
                    try:
                        horario_cliente = datetime.strptime(f"{data_hoje_str} {row['horario']}", "%Y-%m-%d %H:%M")
                        diferenca_minutos = (horario_cliente - agora).total_seconds() / 60
                        
                        # Dispara a notificação se o cliente estiver a menos de 30 minutos do atendimento
                        if 0 <= diferenca_minutos <= 30:
                            st.toast(f"🚨 **ATENÇÃO BARBEIRO:** {row['nome']} agendado às {row['horario']} ({row['servico']}) está próximo!", icon="💈")
                    except:
                        pass

# Ativa o sistema automático de varredura e alertas de proximidade
checar_proximidade_clientes_oculto()

# --- EXIBIÇÃO DO LOGO BRANDING IDENTICO ---
st.markdown(
    """
    <div class="logo-container">
        <div class="logo-text">marinote club</div>
        <div class="sub-logo">Painel de Controle Interno</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("---")

# --- CONEXÃO E RENDERIZAÇÃO DA TABELA ---
conn = obter_conexao()
df_agenda = pd.DataFrame()

if conn:
    df_agenda = pd.read_sql("SELECT id, nome, whatsapp, servico, data_agenda, horario FROM public.agendamentos_marinote ORDER BY data_agenda, horario;", conn)

if df_agenda.empty:
    st.info("ℹ| Nenhum agendamento ativo ou pendente foi localizado na base de dados em nuvem.")
else:
    st.subheader("🗓| Grade Geral de Horários Ativos")
    
    # Formata a visualização das colunas da tabela
    df_visual = df_agenda.copy()
    df_visual.columns = ["ID Ref", "Nome do Cliente", "WhatsApp", "Serviço Solicitado", "Data do Atendimento", "Horário Marcado"]
    
    # Renderiza a tabela nativa de forma limpa e responsiva na tela
    st.dataframe(df_visual[["Horário Marcado", "Data do Atendimento", "Nome do Cliente", "Serviço Solicitado", "WhatsApp"]], use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("🛠| Gerenciamento de Vagas e Baixas")
    
    # Seletor baseado nos registros para dar baixa no corte
    opcoes_baixa = {f"{row['data_agenda']} às {row['horario']} - {row['nome']} ({row['servico']})": row['id'] for _, row in df_agenda.iterrows()}
    selecionado_para_baixa = st.selectbox("Escolha um atendimento para encerrar e liberar a grade:", list(opcoes_baixa.keys()))
    
    if st.button("🗑| Concluir e Dar Baixa no Atendimento", type="primary", use_container_width=True):
        id_registro = opcoes_baixa[selecionado_para_baixa]
        conn = obter_conexao()
        if conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                conn.commit()
            st.success("Atendimento concluído com sucesso e vaga liberada na nuvem!")
            time_module.sleep(0.5)
            st.rerun()

st.markdown("---")
st.caption("🔄 Sincronização em nuvem ativa. O monitor interno atualiza o fluxo da tabela a cada 5 segundos de forma silenciosa.")
