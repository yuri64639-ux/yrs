import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import time as time_module
import requests

# Configuração de Ambiente para o Painel de Controle Privado Mobile
st.set_page_config(page_title="marinote club", page_icon="✂️", layout="wide")

# (O CSS antigo permanece o mesmo...)
st.markdown("""<style>header, [data-testid="stHeader"], [data-testid="stAppToolbar"] { display: none !important; visibility: hidden !important; height: 0px !important; } .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 0.4rem !important; padding-right: 0.4rem !important; max-width: 100% !important; } .stApp { background-color: #121212 !important; color: #E5E5E5 !important; } h1, h2, h3, h4, h5, h6, label, p { color: #D4AF37 !important; font-family: 'Helvetica Neue', sans-serif; white-space: normal !important; word-break: break-word !important; } div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div { background-color: #1E1E1E !important; border: 1px solid #D4AF37 !important; border-radius: 8px !important; } input, select { color: #FFFFFF !important; } .stButton>button { width: 100%; height: 3.4rem; font-weight: bold; font-size: 16px !important; border-radius: 8px !important; border: none !important; transition: all 0.3s ease; margin-top: 8px !important; }</style>""", unsafe_allow_html=True)

def obter_conexao():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão com o banco Neon: {e}")
        return None

def garantir_tabelas_existem():
    conn = obter_conexao()
    if conn:
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    # Tabela de agendamentos
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
                    # Tabela para controle de notificações (Evita loops de envio)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS public.notificacoes_enviadas (
                            agendamento_id INT PRIMARY KEY,
                            enviado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    conn.commit()
        except Exception as e:
            st.error(f"Erro ao verificar estrutura das tabelas: {e}")
        finally:
            conn.close()

garantir_tabelas_existem()

def enviar_notificacao_whatsapp(nome_cliente, horario, servico, id_agendamento):
    """Envia uma mensagem para o SEU WhatsApp avisando do próximo cliente"""
    # Configurações do seu Gateway de WhatsApp (Exemplo genérico - configure no st.secrets)
    # Você deve cadastrar essas chaves no arquivo .streamlit/secrets.toml
    try:
        api_url = st.secrets.get("API_WHATSAPP_URL") # Ex: https://suaapi.com
        token = st.secrets.get("API_WHATSAPP_TOKEN")
        seu_numero = st.secrets.get("SEU_NUMERO_WHATSAPP") # Seu número com DDD (ex: 5511999999999)
        
        if not api_url or not seu_numero:
            return False # Ignora se não estiver configurado nas secrets ainda
            
        payload = {
            "number": seu_numero,
            "message": f"✂️ *MARINOTE CLUB*\n\n🚨 *PRÓXIMO CLIENTE EM 15 MINUTOS!*\n👤 *Nome:* {nome_cliente}\n⏰ *Horário:* {horario}\n🪒 *Serviço:* {servico}"
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        resposta = requests.post(api_url, json=payload, headers=headers, timeout=10)
        
        if resposta.status_code in:
            # Registra no banco que já enviou para não repetir
            conn = obter_conexao()
            if conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("INSERT INTO public.notificacoes_enviadas (agendamento_id) VALUES (%s) ON CONFLICT DO NOTHING;", (id_agendamento,))
                conn.close()
            return True
    except Exception as e:
        print(f"Erro ao enviar WhatsApp: {e}")
    return False

@st.fragment(run_every="5s")
def renderizar_painel_agenda_dinamico():
    conn = obter_conexao()
    df_agenda = pd.DataFrame()
    notificadas = []

    if conn:
        try:
            # Busca agendamentos ativos
            df_agenda = pd.read_sql("SELECT id, nome, whatsapp, servico, data_agenda, horario FROM public.agendamentos_marinote ORDER BY data_agenda, horario;", conn)
            # Busca IDs que já foram notificados hoje
            df_notif = pd.read_sql("SELECT agendamento_id FROM public.notificacoes_enviadas;", conn)
            notificadas = df_notif["agendamento_id"].tolist()
        except Exception as e:
            st.error(f"Erro ao ler os dados: {e}")
        finally:
            conn.close()

    # Verificação de Notificações Próximas (Roda em background de 5 em 5s)
    if not df_agenda.empty:
        data_hoje_str = datetime.now().strftime("%Y-%m-%d")
        df_hoje = df_agenda[df_agenda["data_agenda"] == data_hoje_str]
        
        if not df_hoje.empty:
            agora = datetime.now()
            for _, row in df_hoje.iterrows():
                try:
                    horario_cliente = datetime.strptime(f"{data_hoje_str} {row['horario']}", "%Y-%m-%d %H:%M")
                    diferenca_minutos = (horario_cliente - agora).total_seconds() / 60
                    
                    # Se faltar entre 0 e 15 minutos E ainda não foi enviado lembrete por WhatsApp
                    if 0 <= diferenca_minutos <= 15 and row['id'] not in notificadas:
                        # Dispara o envio em segundo plano
                        enviar_notificacao_whatsapp(row['nome'], row['horario'], row['servico'], row['id'])
                        st.toast(f"📱 Notificação enviada para seu WhatsApp!", icon="💬")
                except:
                    pass

    # Exibição da Interface Geral (Mesma do anterior)
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
        
        if st.button("🏁 Concluir Atendimento", type="primary", use_container_width=True, key="btn_concluir_mobile"):
            conn = obter_conexao()
            if conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                        cur.execute("DELETE FROM public.notificacoes_enviadas WHERE agendamento_id = %s;", (id_registro,))
                st.success("Atendimento concluído!")
                time_module.sleep(0.5)
                st.rerun()
                    
        if st.button("❌ Cancelar Agendamento", type="secondary", use_container_width=True, key="btn_cancelar_mobile"):
            conn = obter_conexao()
            if conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                        cur.execute("DELETE FROM public.notificacoes_enviadas WHERE agendamento_id = %s;", (id_registro,))
                st.warning("Agendamento cancelado!")
                time_module.sleep(0.5)
                st.rerun()

# Layout Inicial
st.markdown("""<div style='text-align: center; padding: 15px 0px;'><div style="font-family: 'Cinzel', serif; font-size: 38px; font-weight: 700; letter-spacing: 1px; background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase;">marinote club</div><div style='font-size: 12px; color: #8A8A8A; letter-spacing: 4px; text-transform: uppercase; margin-top: -3px;'>Painel de Controle Interno</div></div>""", unsafe_allow_html=True)
st.write("---")

renderizar_painel_agenda_dinamico()
st.markdown("---")
st.caption("🔄 Sincronização em nuvem ativa. Sistema integrado com disparos de notificações.")
