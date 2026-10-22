import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time as time_module
import requests

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
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS public.historico_alertas (
                            id_agendamento INT PRIMARY KEY,
                            ultimo_envio TIMESTAMP NOT NULL
                        );
                    """)
                    conn.commit()
        except Exception as e:
            st.error(f"Erro ao verificar tabelas: {e}")
        finally:
            conn.close()

def enviar_notificacao_celular(nome_cliente, horario, servico, id_agendamento, minutos_restantes):
    try:
        topico_secreto = "marinote_club_avisos_secretos_99" 
        url = f"https://ntfy.sh{topico_secreto}"
        
        tempo_str = f"Faltam {int(minutos_restantes)} minutos!" if minutos_restantes > 0 else "Está na hora!"
        mensagem = f"⏰ {tempo_str}\n👤 Cliente: {nome_cliente}\n⏰ Horário Marcado: {horario}\n🪒 Serviço: {servico}"
        
        headers = {
            "Title": f"✂️ Lembrete: {nome_cliente} ({horario})",
            "Tags": "barber,alarm_clock,glowing_star",
            "Priority": "high"
        }
        
        resposta = requests.post(url, data=mensagem.encode('utf-8'), headers=headers, timeout=10)
        
        if resposta.status_code == 200:
            conn = obter_conexao()
            if conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO public.historico_alertas (id_agendamento, ultimo_envio) 
                            VALUES (%s, NOW()) 
                            ON CONFLICT (id_agendamento) 
                            DO UPDATE SET ultimo_envio = NOW();
                        """, (id_agendamento,))
                conn.close()
            return True
    except:
        pass
    return False

def gerenciar_sistema_alertas(df_agenda, historico_alertas):
    if not df_agenda.empty:
        data_hoje_str = datetime.now().strftime("%Y-%m-%d")
        df_hoje = df_agenda[df_agenda["data_agenda"] == data_hoje_str]
        
        if not df_hoje.empty:
            agora = datetime.now()
            for _, row in df_hoje.iterrows():
                try:
                    horario_cliente = datetime.strptime(f"{data_hoje_str} {row['horario']}", "%Y-%m-%d %H:%M")
                    diferenca_minutos = (horario_cliente - agora).total_seconds() / 60
                    
                    if 0 <= diferenca_minutos <= 15:
                        id_cli = row['id']
                        deve_enviar = False
                        
                        if id_cli not in historico_alertas:
                            deve_enviar = True
                        else:
                            ultimo_envio = historico_alertas[id_cli]
                            tempo_decorrido = (agora - ultimo_envio.replace(tzinfo=None)).total_seconds() / 60
                            if tempo_decorrido >= 4.9:
                                deve_enviar = True
                        
                        if deve_enviar:
                            enviar_notificacao_celular(row['nome'], row['horario'], row['servico'], id_cli, diferenca_minutos)
                            st.toast(f"📱 Alerta push enviado ao celular!", icon="🔔")
                except:
                    pass
import streamlit as st
import pandas as pd
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time as time_module

# Importação limpa e segura do backend unificado
import banco

# Configuração de Ambiente para o Painel de Controle Privado Mobile
st.set_page_config(page_title="marinote club", page_icon="✂️", layout="wide")

st.markdown(
    """
    <style>
    header, [data-testid="stHeader"], [data-testid="stAppToolbar"] { display: none !important; visibility: hidden !important; height: 0px !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 0.4rem !important; padding-right: 0.4rem !important; max-width: 100% !important; }
    .stApp { background-color: #121212 !important; color: #E5E5E5 !important; }
    h1, h2, h3, h4, h5, h6, label, p { color: #D4AF37 !important; font-family: 'Helvetica Neue', sans-serif; white-space: normal !important; word-break: break-word !important; }
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div { background-color: #1E1E1E !important; border: 1px solid #D4AF37 !important; border-radius: 8px !important; }
    input, select { color: #FFFFFF !important; }
    .stButton>button { width: 100%; height: 3.4rem; font-weight: bold; font-size: 16px !important; border-radius: 8px !important; border: none !important; transition: all 0.3s ease; margin-top: 8px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializa as tabelas no Neon
banco.garantir_tabelas_existem()

@st.fragment(run_every="5s")
def renderizar_painel_agenda_dinamico():
    conn = banco.obter_conexao()
    df_agenda = pd.DataFrame()
    historico_alertas = {}

    if conn:
        try:
            df_agenda = pd.read_sql("SELECT id, nome, whatsapp, servico, data_agenda, horario FROM public.agendamentos_marinote ORDER BY data_agenda, horario;", conn)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id_agendamento, ultimo_envio FROM public.historico_alertas;")
                for rows in cur.fetchall():
                    historico_alertas[rows['id_agendamento']] = rows['ultimo_envio']
        except Exception as e:
            st.error(f"Erro ao ler os dados do banco: {e}")
        finally:
            conn.close()

    # Dispara a varredura automática recorrente
    banco.gerenciar_sistema_alertas(df_agenda, historico_alertas)

    # Exibição da Grade Mobile
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
            conn = banco.obter_conexao()
            if conn:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                            cur.execute("DELETE FROM public.historico_alertas WHERE id_agendamento = %s;", (id_registro,))
                            conn.commit()
                    st.success("Atendimento concluído!")
                    time_module.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao concluir: {e}")
                finally:
                    conn.close()
                    
        if st.button("❌ Cancelar Agendamento", type="secondary", use_container_width=True, key="btn_cancelar_mobile"):
            conn = banco.obter_conexao()
            if conn:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("DELETE FROM public.agendamentos_marinote WHERE id = %s;", (id_registro,))
                            cur.execute("DELETE FROM public.historico_alertas WHERE id_agendamento = %s;", (id_registro,))
                            conn.commit()
                    st.warning("Agendamento cancelado!")
                    time_module.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cancelar: {e}")
                finally:
                    conn.close()

# Cabeçalho Visual da Marca
st.markdown(
    """
    <div style='text-align: center; padding: 15px 0px;'>
        <div style="font-family: 'Cinzel', serif; font-size: 38px; font-weight: 700; letter-spacing: 1px; background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase;">marinote club</div>
        <div style='font-size: 12px; color: #8A8A8A; letter-spacing: 4px; text-transform: uppercase; margin-top: -3px;'>Painel de Controle Interno</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("---")

renderizar_painel_agenda_dinamico()

st.markdown("---")
st.caption("🔄 Monitor Recorrente Ativo. O celular receberá bipes a cada 5 minutos dentro da janela do cliente.")
