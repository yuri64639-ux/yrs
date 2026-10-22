import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import time as time_module

# Configuração de Identidade Visual na Aba do Navegador
st.set_page_config(page_title="marinote club", page_icon="💈", layout="centered")

# --- INJEÇÃO DE ARTWORK CSS PREMIUM (PRETO CARBONO & DOURADO METÁLICO) ---
st.markdown(
    """
    <style>
    /* Oculta os cabeçalhos nativos e menus de deploy do Streamlit */
    [data-testid="stHeader"], [data-testid="stAppToolbar"], header {
        visibility: hidden !important;
        display: none !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* Configuração do fundo dark de alto padrão */
    .stApp {
        background-color: #121212 !important;
        color: #E5E5E5 !important;
    }
    
    /* Estilização da Tipografia e Cabeçalhos */
    h1, h2, h3, h4, h5, h6, label {
        color: #D4AF37 !important;
        font-family: 'Helvetica Neue', sans-serif;
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

    /* Estilização do Logo Metálico Centralizado */
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

# --- CONEXÃO COM O BANCO DE DADOS NEON CENTRAL ---
@st.cache_resource
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
            if conn: conn.rollback()

inicializar_banco()

# --- EXIBIÇÃO DO LOGO BRANDING ---
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

# Formulário de Entrada do Cliente
nome = st.text_input("Seu Nome Completo:")
whatsapp = st.text_input("Seu WhatsApp (com DDD):", placeholder="Ex: (17) 99999-9999")

# Filtro de Serviços Demandado
servicos = [
    "Cabelo",
    "Barba",
    "Cabelo e Barba"
]
servico_selecionado = st.selectbox("Escolha o Serviço Essencial:", servicos)

# Seleção Dinâmica de Datas (Próximas 2 semanas disponíveis)
data_atual = datetime.now().date()
data_limite = data_atual + timedelta(days=14)
data_selecionada = st.date_input("Escolha o Dia do Atendimento:", value=data_atual, min_value=data_atual, max_value=data_limite)

# Lista Estruturada de Horários Disponíveis por Turno
horarios_disponiveis = [
    "09:00", "09:40", "10:20", "11:00", "11:40", 
    "13:30", "14:10", "14:50", "15:30", "16:10", "16:50", "17:30"
]

# Varredura dinâmica de horários ocupados direto no banco em nuvem da Neon
conn = obter_conexao()
horarios_ocupados = []
if conn:
    try:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO public;")
            cur.execute("SELECT horario FROM public.agendamentos_marinote WHERE data_agenda = %s;", (str(data_selecionada),))
            horarios_ocupados = [row[0] for row in cur.fetchall()]
    except Exception:
        if conn: conn.rollback()

horarios_livres = [h for h in horarios_disponiveis if h not in horarios_ocupados]

# Exibição e validação do Horário
if len(horarios_livres) > 0:
    horario_selecionado = st.selectbox("Escolha o Horário Livre:", horarios_livres)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Confirmar Meu Agendamento"):
        if nome.strip() == "" or whatsapp.strip() == "":
            st.error("⚠️ Atenção: Por favor, preencha os campos de Nome e WhatsApp para concluir.")
        else:
            conn = obter_conexao()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            INSERT INTO public.agendamentos_marinote (nome, whatsapp, servico, data_agenda, horario)
                            VALUES (%s, %s, %s, %s, %s);
                        """, (nome.strip(), whatsapp.strip(), servico_selecionado, str(data_selecionada), horario_selecionado))
                        conn.commit()
                    st.success(f"🎉 Pronto, {nome}! Seu horário para '{servico_selecionado}' foi agendado com sucesso para o dia {data_selecionada.strftime('%d/%m/%Y')} às {horario_selecionado}.")
                    st.balloons()
                    time_module.sleep(0.8)
                    st.rerun()
                except Exception:
                    if conn: conn.rollback()
else:
    st.warning("❌ Desculpe, todos os horários para este dia já estão preenchidos. Por favor, selecione outra data!")
