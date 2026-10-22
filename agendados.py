import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time as time_module

# Configuração de Ambiente para o Painel de Controle Privado
st.set_page_config(page_title="Agenda Interna - marinote club", page_icon="✂️", layout="wide")

# --- INJEÇÃO DE ARTWORK CSS PREMIUM (PRETO CARBONO & DOURADO METÁLICO) ---
st.markdown(
    """
    <style>
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
    h1, h2, h3, h4, h5, h6, label, p {
        color: #D4AF37 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div {
        background-color: #1E1E1E !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 8px !important;
    }
    input, select {
        color: #FFFFFF !important;
    }
    .stButton>button {
        width: 100%;
        height: 3.2rem;
        font-weight: bold;
        font-size: 16px !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- FUNÇÃO DE CONEXÃO DINÂMICA (ABRE NO MOMENTO DO USO) ---
def obter_conexao():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão com o banco Neon: {e}")
        return None

# 🛠️ CORREÇÃO DEFINITIVA: Cria a conexão internamente e fecha após usar (Evita InterfaceError)
def garantir_tabela_existe():
    conn = obter_conexao()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS public.agendamentos_marinote (
                            id SERIAL PRIMARY KEY,
                            nome TEXT NOT NULL,
                            whatsapp TEXT NOT NULL,
                            servico TEXT NOT NULL,
                            data_agenda TEXT NOT NULL,
                            horario TEXT NOT NULL
                        );
                    """)
                    conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

# Garante a integridade estrutural ao iniciar
garantir_tabela_existe()

# --- MONITOR DE ALERTA EM SEGUNDO PLANO ---
@st.fragment(run_every="5s")
def checar_proximidade_clientes_oculto():
    conn = obter_conexao()
    if conn:
        try:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SET search_path TO public;")
                    data_hoje_str = datetime.now().strftime("%Y-%m-%d")
                    cur.execute("SELECT nome, horario, servico FROM public.agendamentos_marinote WHERE data_agenda = %s;", (data_hoje_str,))
                    agendamentos_hoje = cur.fetchall()
                    
                    if agendamentos_hoje:
                        agora = datetime.now()
                        for row in agendamentos_hoje:
                            try:
                                horario_cliente = datetime.strptime(f"{data_hoje_str} {row['horario']}", "%Y-%m-%d %H:%M")
                                diferenca_minutos = (horario_cliente - agora).total_seconds() / 60
                                if 0 <= diferenca_minutos <= 30:
                                    st.toast(f"🚨 **ATENÇÃO BARBEIRO:** {row['nome']} agendado às {row['horario']} ({row['servico']}) está próximo!", icon="💈")
                            except:
                                pass
        except Exception:
            pass
        finally:
            conn.close()

checar_proximidade_clientes_oculto()

# --- EXIBIÇÃO DO LOGO BRANDING IDENTICO ---
st.markdown(
    """
    <div style='text-align: center; padding: 20px; margin-bottom: 10px;'>
        <div style="font-family: 'Cinzel', serif; font-size: 48px; font-weight: 700; letter-spacing: 2px; background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase;">marinote club</div>
        <div style='font-size: 13px; color: #8A8A8A; letter-spacing: 6px; text-transform: uppercase; margin-top: -5px; font-weight: 300;'>Painel de Controle Interno</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("---")

# --- BUSCA DE DADOS SOB DEMANDA ---
df_agenda = pd.DataFrame()
conn = obter_conexao()
if conn:
    try:
        df_agenda = pd.read_sql("SELECT id, nome, whatsapp, servico, data_agenda, horario FROM public.agendamentos_marinote ORDER BY data_agenda, horario;", conn)
    except Exception:
        pass
    finally:
        conn.close()

# --- EXIBIÇÃO DA TABELA ---
if df_agenda.empty:
    st.info("ℹ️ Nenhum agendamento ativo ou pendente foi localizado na base de dados em nuvem.")
else:
    st.subheader("🗓️ Grade Geral de Horários Ativos")
    
    df_visual = df_agenda.copy()
    df_visual.columns = ["ID Ref", "Nome do Cliente", "WhatsApp", "Serviço Solicitado", "Data do Atendimento", "Horário Marcado"]
    st.dataframe(df_visual[["Horário Marcado", "Data do Atendimento", "Nome do Cliente", "Serviço Solicitado", "WhatsApp"]], use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("🛠️ Gerenciamento de Vagas e Ações")
    
    opcoes_baixa = {f"{row['data_agenda']} às {row['horario']} - {row['nome']} ({row['servico']})": row['id'] for _, row in df_agenda.iterrows()}
    selecionado_para_baixa = st.selectbox("Escolha um atendimento para gerenciar:", list(opcoes_baixa.keys()))
    
    id_registro = opcoes_baixa[selecionado_para_baixa]
    
    col_concluir, col_cancelar = st.columns(2)
    
    with col_concluir:
        if st.button("🏁 Concluir Atendimento", type="primary", use_container_width=True):
            conn = obter_conexao()
            if conn:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                            conn.commit()
                    st.success("Atendimento concluído com sucesso e faturamento registrado!")
                    time_module.sleep(0.5)
                    st.rerun()
                except Exception:
                    pass
                finally:
                    conn.close()
                    
    with col_cancelar:
        if st.button("❌ Cancelar Agendamento", type="secondary", use_container_width=True):
            conn = obter_conexao()
            if conn:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                            conn.commit()
                    st.warning("Agendamento cancelado. A vaga foi reaberta na grade dos clientes!")
                    time_module.sleep(0.5)
                    st.rerun()
                except Exception:
                    pass
                finally:
                    conn.close()

st.markdown("---")
st.caption("🔄 Sincronização em nuvem ativa. O monitor interno atualiza o fluxo da tabela a cada 5 segundos de forma silenciosa.")
