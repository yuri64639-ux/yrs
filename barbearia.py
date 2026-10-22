import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import time as time_module
import re

# Configuração e injeção de CSS responsivo focado em telas de celulares
st.set_page_config(page_title="marinote club", page_icon="💈", layout="centered")

st.markdown(
    """
    <style>
    /* Oculta os cabeçalhos nativos e menus de deploy do Streamlit */
    [data-testid="stHeader"], [data-testid="stAppToolbar"], header {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* COMPACTAÇÃO MOBILE: Remove margens exageradas que esmagam o conteúdo no celular */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
        max-width: 100% !important;
    }
    
    /* Configuração do fundo dark de alto padrão */
    .stApp {
        background-color: #121212 !important;
        color: #E5E5E5 !important;
    }
    
    /* Estilização da Tipografia Responsiva */
    h1, h2, h3, h4, h5, h6, label {
        color: #D4AF37 !important;
        font-family: 'Helvetica Neue', sans-serif;
        white-space: normal !important; /* Impede o texto de ser cortado */
        word-break: break-word !important;
    }

    /* Caixa de Inputs, Dropdowns e Date Pickers Personalizados */
    div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div {
        background-color: #1E1E1E !important;
        border: 1px solid #D4AF37 !important;
        border-radius: 8px !important;
    }
    input, select, textarea {
        color: #FFFFFF !important;
    }

    /* Botão Principal Adaptado para o Polegar no Smartphone */
    .stButton>button {
        width: 100%;
        height: 3.4rem;
        background-color: #D4AF37 !important;
        color: #121212 !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease;
        box-shadow: 0px 4px 10px rgba(212, 175, 55, 0.2);
        margin-top: 10px !important;
    }
    .stButton>button:hover {
        background-color: #AA8226 !important;
    }
    .logo-container {
        text-align: center;
        padding: 10px 0px;
        margin-bottom: 5px;
    }
    .logo-text {
        font-family: 'Cinzel', 'Playfair Display', serif;
        font-size: 38px; /* Reduzido ligeiramente para não cortar em telas finas */
        font-weight: 700;
        letter-spacing: 1px;
        background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
    }
    .sub-logo {
        font-size: 11px;
        color: #8A8A8A;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-top: -2px;
        font-weight: 300;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def obter_conexao():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro ao conectar ao banco Neon: {e}")
        return None

def inicializar_banco():
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

inicializar_banco()

st.markdown(
    """
    <div class="logo-container">
        <div class="logo-text">marinote club</div>
        <div class="sub-logo">Agendamento de Horários</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("---")

nome = st.text_input("Seu Nome Completo:", key="input_nome_cliente")
whatsapp = st.text_input("Seu WhatsApp (com DDD):", placeholder="Ex: (17) 99999-9999", key="input_whatsapp_cliente")

servicos = ["Cabelo", "Barba", "Cabelo e Barba"]
servico_selecionado = st.selectbox("Escolha o Serviço Essencial:", servicos, key="select_servico_cliente")

data_atual = datetime.now().date()
data_limite = data_atual + timedelta(days=14)
data_selecionada = st.date_input("Escolha o Dia do Atendimento:", value=data_atual, min_value=data_atual, max_value=data_limite, key="date_dia_cliente")

horario_digitado = st.text_input("Digite o Horário Desejado (Formato 24h):", placeholder="Ex: 14:30", key="campo_horario_livre").strip()

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Confirmar Meu Agendamento", key="btn_confirmar_agendamento_cliente"):
    if nome.strip() == "" or whatsapp.strip() == "":
        st.error("⚠️ Atenção: Por favor, preencha os campos de Nome e WhatsApp para concluir.")
    elif not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", horario_digitado):
        st.error("⚠️ Formato inválido! Por favor, digite usando duas casas e dois pontos. Exemplo: 09:30, 14:00, 17:15.")
    else:
        partes_hora = horario_digitado.split(":")
        hora_ajustada = int(partes_hora[0])
        minuto_ajustada = int(partes_hora[1])
        horario_selecionado_str = f"{hora_ajustada:02d}:{minuto_ajustada:02d}"

        agendados_dia = []
        conn = obter_conexao()
        if conn:
            try:
                with conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("SELECT horario, nome FROM public.agendamentos_marinote WHERE data_agenda = %s;", (str(data_selecionada),))
                        agendados_dia = cur.fetchall()
            except Exception:
                pass
            finally:
                conn.close()

        conflito_horario = False
        proximo_cliente_info = ""
        data_base_str = str(data_selecionada)
        dt_escolhido = datetime.strptime(f"{data_base_str} {horario_selecionado_str}", "%Y-%m-%d %H:%M")
        
        for agendamento in agendados_dia:
            dt_existente = datetime.strptime(f"{data_base_str} {agendamento['horario']}", "%Y-%m-%d %H:%M")
            diferenca = abs((dt_escolhido - dt_existente).total_seconds() / 60)
            
            if diferenca < 40:
                conflito_horario = True
                proximo_cliente_info = f"{agendamento['horario']}"
                break
        
        if conflito_horario:
            st.error(f"❌ Horário indisponível! Devido ao intervalo de segurança de 40 minutos entre os clientes, sua escolha conflita com o horário das {proximo_cliente_info}.")
        else:
            conn = obter_conexao()
            if conn:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("SET search_path TO public;")
                            cur.execute("""
                                INSERT INTO public.agendamentos_marinote (nome, whatsapp, servico, data_agenda, horario)
                                VALUES (%s, %s, %s, %s, %s);
                            """, (nome.strip(), whatsapp.strip(), servico_selecionado, str(data_selecionada), horario_selecionado_str))
                            conn.commit()
                    st.success(f"🎉 Pronto! Horário agendado para o dia {data_selecionada.strftime('%d/%m/%Y')} às {horario_selecionado_str}.")
                    st.balloons()
                    time_module.sleep(0.8)
                    st.rerun()
                except Exception:
                    pass
                finally:
                    conn.close()
