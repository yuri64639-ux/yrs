import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import time as time_module
import re

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

servicos = ["Cabelo", "Barba", "Cabelo e Barba"]
servico_selecionado = st.selectbox("Escolha o Serviço Essencial:", servicos)

data_atual = datetime.now().date()
data_limite = data_atual + timedelta(days=14)
data_selecionada = st.date_input("Escolha o Dia do Atendimento:", value=data_atual, min_value=data_atual, max_value=data_limite)

# 🕒 CORREÇÃO: Substituído por campo de texto livre digitável para não travar no celular
horario_digitado = st.text_input("Digite o Horário Desejado (Formato 24h):", placeholder="Ex: 14:30").strip()

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Confirmar Meu Agendamento"):
    # 1. Validação inicial de campos vazios
    if nome.strip() == "" or whatsapp.strip() == "":
        st.error("⚠️ Atenção: Por favor, preencha os campos de Nome e WhatsApp para concluir.")
    # 2. Validação do formato do horário via Expressão Regular (Regex)
    elif not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", horario_digitado):
        st.error("⚠️ Formato de horário inválido! Por favor, digite o horário usando duas casas e dois pontos. Exemplo: 09:30, 14:00, 17:15.")
    else:
        # Padroniza a string digitada (adiciona o zero à esquerda se o cliente digitar "9:30" vira "09:30")
        partes_hora = horario_digitado.split(":")
        horario_selecionado_str = f"{int(partes_hora[0]):02d}:{partes_hora[1]}"

        # 🕒 REGRA DOS 40 MINUTOS: Busca todos os horários já agendados naquele dia para validar o intervalo
        conn = obter_conexao()
        conflito_horario = False
        proximo_cliente_info = ""
        
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("SELECT horario, nome FROM public.agendamentos_marinote WHERE data_agenda = %s;", (str(data_selecionada),))
                    agendados_dia = cur.fetchall()
                    
                    data_base_str = str(data_selecionada)
                    dt_escolhido = datetime.strptime(f"{data_base_str} {horario_selecionado_str}", "%Y-%m-%d %H:%M")
                    
                    for agendamento in agendados_dia:
                        dt_existente = datetime.strptime(f"{data_base_str} {agendamento['horario']}", "%Y-%m-%d %H:%M")
                        
                        # Calcula a diferença absoluta em minutos entre os dois horários
                        diferenca = abs((dt_escolhido - dt_existente).total_seconds() / 60)
                        
                        if diferenca < 40:
                            conflito_horario = True
                            proximo_cliente_info = f"{agendamento['horario']}"
                            break
            except Exception:
                if conn: conn.rollback()
        
        if conflito_horario:
            st.error(f"❌ Horário indisponível! Devido ao intervalo de segurança de 40 minutos entre os clientes, sua escolha conflita com o horário das {proximo_cliente_info}. Por favor, digite um horário mais cedo ou mais tarde.")
        else:
            conn = obter_conexao()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            INSERT INTO public.agendamentos_marinote (nome, whatsapp, servico, data_agenda, horario)
                            VALUES (%s, %s, %s, %s, %s);
                        """, (nome.strip(), whatsapp.strip(), servico_selecionado, str(data_selecionada), horario_selecionado_str))
                        conn.commit()
                    st.success(f"🎉 Pronto, {nome}! Seu horário para '{servico_selecionado}' foi agendado com sucesso para o dia {data_selecionada.strftime('%d/%m/%Y')} às {horario_selecionado_str}.")
                    st.balloons()
                    time_module.sleep(0.8)
                    st.rerun()
                except Exception:
                    if conn: conn.rollback()
