import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import time as time_module

st.set_page_config(page_title="marinote club - Gerência", page_icon="✂️", layout="wide")

st.markdown("""
    <style>
    header, [data-testid="stHeader"], [data-testid="stAppToolbar"] { display: none !important; visibility: hidden !important; height: 0px !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 0.4rem !important; padding-right: 0.4rem !important; max-width: 100% !important; }
    .stApp { background-color: #121212 !important; color: #E5E5E5 !important; }
    h1, h2, h3, h4, h5, h6, label, p { color: #D4AF37 !important; font-family: 'Helvetica Neue', sans-serif; white-space: normal !important; word-break: break-word !important; }
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div { background-color: #1E1E1E !important; border: 1px solid #D4AF37 !important; border-radius: 8px !important; }
    input, select { color: #FFFFFF !important; }
    .stButton>button { width: 100%; height: 3.4rem; font-weight: bold; font-size: 16px !important; border-radius: 8px !important; border: none !important; transition: all 0.3s ease; margin-top: 8px !important; }
    </style>
""", unsafe_allow_html=True)

def obter_conexao():
    try: return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e: st.error(f"Erro no banco: {e}"); return None
@st.fragment(run_every="5s")
def renderizar_painel_agenda_dinamico():
    conn = obter_conexao()
    df_agenda = pd.DataFrame()
    if conn:
        try: df_agenda = pd.read_sql("SELECT id, nome, whatsapp, servico, data_agenda, horario FROM public.agendamentos_marinote ORDER BY data_agenda, horario;", conn)
        except Exception as e: st.error(f"Erro: {e}")
        finally: conn.close()

    if df_agenda.empty:
        st.info("ℹ️ Nenhum agendamento ativo localizado na nuvem.")
    else:
        st.subheader("🗓️ Grade Geral de Horários Ativos")
        df_visual = df_agenda.copy()
        df_visual.columns = ["ID Ref", "Nome do Cliente", "WhatsApp", "Serviço Solicitado", "Data do Atendimento", "Horário Marcado"]
        st.dataframe(df_visual[["Horário Marcado", "Data do Atendimento", "Nome do Cliente", "Serviço Solicitado", "WhatsApp"]], use_container_width=True, hide_index=True)
        
        st.write("---")
        st.subheader("🛠️ Gerenciamento de Vagas e Ações")
        opcoes_baixa = {f"#{row['id']} - {row['data_agenda']} às {row['horario']} - {row['nome']}": row['id'] for _, row in df_agenda.iterrows()}
        selecionado_para_baixa = st.selectbox("Escolha um atendimento para gerenciar:", list(opcoes_baixa.keys()))
        id_registro = opcoes_baixa[selecionado_para_baixa]
        
        if st.button("🏁 Concluir Atendimento", type="primary", use_container_width=True):
            conn = obter_conexao()
            if conn:
                with conn:
                    with conn.cursor() as cur: cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                st.success("Atendimento concluído!"); time_module.sleep(0.5); st.rerun()
                    
        if st.button("❌ Cancelar Agendamento", type="secondary", use_container_width=True):
            conn = obter_conexao()
            if conn:
                with conn:
                    with conn.cursor() as cur: cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                st.warning("Agendamento cancelado!"); time_module.sleep(0.5); st.rerun()

st.markdown("""<div style='text-align: center; padding: 15px 0px;'><div style="font-family: 'Cinzel', serif; font-size: 38px; font-weight: 700; letter-spacing: 1px; background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase;">marinote club</div><div style='font-size: 12px; color: #8A8A8A; letter-spacing: 4px; text-transform: uppercase; margin-top: -3px;'>Painel de Controle Interno</div></div>""", unsafe_allow_html=True)
st.write("---")
renderizar_painel_agenda_dinamico()
st.markdown("---")
st.caption("🔄 Relatórios e grade atualizados em tempo real com a nuvem do Neon.")
