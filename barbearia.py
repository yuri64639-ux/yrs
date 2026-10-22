import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, date, time
import requests

# Configuração de Identidade Visual na Aba do Navegador
st.set_page_config(page_title="marinote club", page_icon="💈", layout="centered")

# --- INJEÇÃO DE ARTWORK CSS PREMIUM (PRETO CARBONO & DOURADO METÁLICO) ---
st.markdown("""
    <style>
    /* Esconde as barras de cabeçalho nativas e menus de deploy */
    [data-testid="stHeader"], [data-testid="stAppToolbar"], header, .stAppDeployDropdown {
        visibility: hidden !important;
        display: none !important;
    }
    [data-testid="collapsedControl"] { display: none !important; }
         
    /* Configuração do fundo dark de alto padrão */
    .stApp {
        background-color: #121212 !important;
        color: #E5E5E5 !important;
    }
         
    /* Estilização da Tipografia Dourada */
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700 !important;
        letter-spacing: 1px;
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
    label, p {
        color: #CCCCCC !important;
        font-weight: 500 !important;
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
    </style>
""", unsafe_allow_html=True)

def obter_conexao():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão com o banco Neon: {e}")
        return None

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
        except Exception as e:
            st.error(f"Erro ao inicializar tabelas: {e}")
        finally:
            conn.close()

garantir_tabela_existe()

def enviar_notificacao_criacao(nome_cliente, data_agenda, horario, servico):
    """Dispara um push instantâneo para o aplicativo ntfy no celular"""
    try:
        topico_secreto = "marinote_club_avisos_secretos_99" 
        url = f"https://ntfy.sh{topico_secreto}"
        
        try:
            data_formatada = datetime.strptime(data_agenda, "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            data_formatada = data_agenda

        mensagem = f"👤 Cliente: {nome_cliente}\n📅 Data: {data_formatada}\n⏰ Horário: {horario}\n🪒 Serviço: {servico}"
        
        headers = {
            "Title": "✂️ NOVO HORÁRIO AGENDADO!",
            "Tags": "barber,calendar,white_check_mark",
            "Priority": "high"
        }
        
        resposta = requests.post(url, data=mensagem.encode('utf-8'), headers=headers, timeout=10)
        return resposta.status_code == 200
    except:
        return False
# --- INTERFACE DE AUTOAGENDAMENTO PÚBLICO DOS CLIENTES ---
st.markdown(
    """
    <div style='text-align: center; padding: 15px 0px;'>
        <div style="font-family: 'Cinzel', serif; font-size: 38px; font-weight: 700; letter-spacing: 1px; background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase;">marinote club</div>
        <div style='font-size: 12px; color: #8A8A8A; letter-spacing: 4px; text-transform: uppercase; margin-top: -3px;'>Agendamento de Clientes Online</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("---")

# Seleção de opções estruturadas para o cliente
c_nome = st.text_input("Seu Nome Completo:", placeholder="Digite seu nome aqui...")
c_whatsapp = st.text_input("Seu WhatsApp com DDD:", placeholder="Ex: 17999999999")
s_agenda = st.selectbox("Escolha o Serviço Desejado:", ["Cabelo", "Barba", "Cabelo e Barba"])

col_d, col_h = st.columns(2)
with col_d:
    d_sel = st.date_input("Data do Atendimento:", min_value=date.today())
with col_h:
    h_sel = st.time_input("Horário do Atendimento:", value=time(9, 0))

if st.button("💾 Confirmar Meu Agendamento", type="primary"):
    if not c_nome.strip():
        st.error("❌ Por favor, preencha o seu nome completo!")
    elif not c_whatsapp.strip():
        st.error("❌ Por favor, preencha o seu número de WhatsApp!")
    else:
        d_str = d_sel.strftime("%Y-%m-%d")
        h_str = h_sel.strftime("%H:%M")
        
        conn = obter_conexao()
        if conn:
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        
                        # Impede agendamentos duplicados no mesmo dia e horário exato
                        cur.execute("""
                            SELECT id FROM public.agendamentos_marinote 
                            WHERE data_agenda = %s AND horario = %s;
                        """, (d_str, h_str))
                        
                        if cur.fetchone():
                            st.error("❌ Desculpe, este horário já está ocupado! Escolha outro momento.")
                        else:
                            # Grava o agendamento de forma permanente na nuvem do Neon
                            cur.execute("""
                                INSERT INTO public.agendamentos_marinote (nome, whatsapp, servico, data_agenda, horario) 
                                VALUES (%s, %s, %s, %s, %s);
                            """, (c_nome.strip(), c_whatsapp.strip(), s_agenda, d_str, h_str))
                            conn.commit()
                            
                            st.success(f"🎉 Tudo certo, {c_nome}! Seu horário foi reservado para o dia {d_sel.strftime('%d/%m/%Y')} às {h_str}.")
                            
                            # NOTIFICAÇÃO IMEDIATA: Executa o disparo instantâneo para o seu celular
                            enviar_notificacao_criacao(c_nome.strip(), d_str, h_str, s_agenda)
                            st.toast("📱 Alerta enviado com sucesso para a gerência!")
            except Exception as e:
                st.error(f"Erro ao salvar seu agendamento no banco: {e}")
            finally:
                conn.close()

st.markdown("---")
st.caption("🔒 Seus dados estão seguros e sincronizados em tempo real com a nossa equipe.")
