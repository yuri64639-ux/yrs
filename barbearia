import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
from banco import init_db

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit)
st.set_page_config(page_title="marinote club", layout="centered")

# Inicializa o banco de dados (tabelas e sementes se necessário)
init_db()

# 2. INICIALIZAÇÃO DO ESTADO DA SESSÃO (Session State)
for k, v in [("aut", False), ("usr", ""), ("car", [])]:
    if k not in st.session_state:
        st.session_state[k] = v

# 3. INJEÇÃO DE CSS PREMIUM (Carbono & Dourado Metálico)
st.markdown("""
    <style>
    [data-testid="stHeader"], [data-testid="stAppToolbar"], header, .stAppDeployDropdown {
        visibility: hidden !important;
        display: none !important;
    }
    [data-testid="collapsedControl"] { display: none !important; }
    
    .stApp {
        background-color: #121212 !important;
        color: #E5E5E5 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700 !important;
        letter-spacing: 1px;
    }
    
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

# 4. BUSCA DE DADOS INICIAIS
with sqlite3.connect("barber.db") as conn:
    df_s = pd.read_sql("SELECT id, nome, preco FROM servicos ORDER BY nome", conn)
    df_b = pd.read_sql("SELECT nome FROM barbeiros ORDER BY nome", conn)

# 5. ROTEADOR DE AMBIENTE (PÚBLICO VS AUTENTICADO)
if not st.session_state.aut:
    menu = st.radio("Selecione uma opção de acesso:", ["📅 Sou Cliente (Agendar Horário)", "💈 Sou da Equipe (Painel Interno)"], horizontal=True)
    
    # --- INTERFACE DO CLIENTE ---
    if menu == "📅 Sou Cliente (Agendar Horário)":
        st.title("💈 marinote club")
        st.markdown("### 📅 Agende seu Horário Conosco")
        
        c_nome = st.text_input("Seu Nome Completo:").strip()
        
        lista_barbeiros = df_b['nome'].tolist() if not df_b.empty else ["Artur"]
        b_agenda = st.selectbox("Escolha o Barbeiro:", lista_barbeiros)
        
        lista_servicos = df_s['nome'].tolist() if not df_s.empty else ["Nenhum cadastrado"]
        s_agenda = st.selectbox("Escolha o Serviço:", lista_servicos)
        
        col_d, col_h = st.columns(2)
        d_sel = col_d.date_input("Data desejada:", min_value=date.today())
        h_sel = col_h.time_input("Horário desejado:", value=time(9, 0))
        
        if st.button("💾 Confirmar Meu Agendamento"):
            if not c_nome:
                st.error("❌ Por favor, digite seu nome completo.")
            elif s_agenda == "Nenhum cadastrado":
                st.error("❌ Não é possível agendar sem um serviço válido selecionado.")
            else:
                d_str = d_sel.strftime("%Y-%m-%d")
                h_str = h_sel.strftime("%H:%M")
                
                with sqlite3.connect("barber.db") as conn:
                    cur = conn.cursor()
                    # Verifica conflito de horário
                    cur.execute("SELECT id FROM agenda WHERE barbeiro = ? AND data = ? AND horario = ? AND status = 'Agendado'", (b_agenda, d_str, h_str))
                    if cur.fetchone():
                        st.error("❌ Este horário já está ocupado com este profissional. Escolha outro!")
                    else:
                        cur.execute("SELECT id FROM servicos WHERE nome = ?", (s_agenda,))
                        s_id = cur.fetchone()[0]
                        cur.execute("INSERT INTO agenda (cliente, servico_id, barbeiro, data, horario) VALUES (?, ?, ?, ?, ?)", (c_nome, s_id, b_agenda, d_str, h_str))
                        conn.commit()
                        st.success(f"🎉 Tudo certo, {c_nome}! Seu horário foi agendado para o dia {d_sel.strftime('%d/%m/%Y')} às {h_str}.")

    # --- LOGIN DA EQUIPE ---
    else:
        st.title("💈 marinote club")
        with st.form("l_f"):
            st.subheader("🔒 Acesso Restrito — Painel Interno")
            u = st.text_input("Barbeiro / Usuário:").strip()
            p = st.text_input("Senha:", type="password").strip()
            
            if st.form_submit_button("Entrar no Sistema"):
                with sqlite3.connect("barber.db") as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT nome FROM barbeiros WHERE LOWER(nome) = ? AND senha = ?", (u.lower(), p))
                    res = cur.fetchone()
                if res:
                    st.session_state.aut = True
                    st.session_state.usr = res[0]
                    st.rerun()
                else:
                    st.error("❌ Credenciais incorretas.")

# --- AMBIENTE LOGADO (PAINEL DA EQUIPE) ---
else:
    # Botão de Logoff na barra lateral
    if st.sidebar.button("🔒 Sair do Painel", type="primary"):
        st.session_state.aut = False
        st.session_state.usr = ""
        st.session_state.car = []
        st.rerun()
        
    tab_operacional, tab_gerencial = st.tabs(["📱 Terminal do Barbeiro", "⚙️ Painel Admin"])
    
    # ==================== TERMINAL DO BARBEIRO ====================
    with tab_operacional:
        st.subheader(f"💈 Terminal de Atendimento — Profissional: {st.session_state.usr}")
        
        aba_interna = st.radio(
            "Selecione a ação de trabalho:", 
            ["➕ Atendimento em Cadeira", "🧾 Caixa & Agenda Ativa"], 
            horizontal=True
        )
        
        # 1. Atendimento Direto da Cadeira
        if aba_interna == "➕ Atendimento em Cadeira":
            cliente_cadeira = st.text_input("Identificação do Cliente / Cadeira:", value="Cadeira 01").strip()
            
            if df_s.empty:
                st.warning("⚠️ Nenhum serviço cadastrado no catálogo administrativo.")
            else:
                filtro_busca = st.text_input("🔍 Buscar Serviço por Nome:").strip()
                df_serv_filtrado = df_s.copy()
                
                if filtro_busca:
                    df_serv_filtrado = df_serv_filtrado[df_serv_filtrado['nome'].str.contains(filtro_busca, case=False, na=False)]
                
                mapeamento_servicos = {f"{row['nome']} - R$ {row['preco']:.2f}": (row['id'], row['nome'], row['preco']) for _, row in df_serv_filtrado.iterrows()}
                
                if mapeamento_servicos:
                    servico_selecionado_string = st.selectbox("Escolha o Serviço:", list(mapeamento_servicos.keys()))
                    
                    if st.button("➕ Adicionar ao Atendimento", use_container_width=True):
                        id_s, nome_s, preco_s = mapeamento_servicos[servico_selecionado_string]
                        st.session_state.car.append({"id": id_s, "nome": nome_s, "preco": preco_s})
                        st.toast(f"✅ {nome_s} adicionado ao rascunho!")
                
                if st.session_state.car:
                    st.markdown("---")
                    st.markdown("### 🛒 Resumo dos Serviços do Cliente")
                    
                    total_atendimento = sum(item['preco'] for item in st.session_state.car)
                    for item in st.session_state.car:
                        st.write(f"▪ *{item['nome']}* — R$ {item['preco']:.2f}")
                    
                    st.markdown(f"**Total Acumulado:** R$ {total_atendimento:.2f}")
                    checkbox_conferido = st.checkbox("✅ Confirmo que os serviços descritos foram realizados.")
                    
                    col_limpa, col_envia = st.columns(2)
                    if col_limpa.button("🗑️ Limpar Rascunho", use_container_width=True):
                        st.session_state.car = []
                        st.rerun()
                        
                    if col_envia.button("🚀 Confirmar e Enviar ao Caixa", type="primary", use_container_width=True):
                        if not checkbox_conferido:
                            st.error("🔒 Marque o campo de confirmação antes de lançar o pedido!")
                        elif not cliente_cadeira:
                            st.error("❌ Digite uma identificação para o cliente / cadeira.")
                        else:
                            data_string_hoje = datetime.now().strftime("%Y-%m-%d")
                            with sqlite3.connect("barber.db") as conn:
                                cur = conn.cursor()
                                for item in st.session_state.car:
                                    cur.execute("INSERT INTO comandas (cliente, servico_id, barbeiro, valor, data) VALUES (?, ?, ?, ?, ?)", (cliente_cadeira, item['id'], st.session_state.usr, item['preco'], data_string_hoje))
                                conn.commit()
                            st.success("🚀 Atendimento enviado com sucesso para a fila do caixa!")
                            st.session_state.car = []
                            st.rerun()
        
        # 2. Caixa e Agenda Ativa
        elif aba_interna == "🧾 Caixa & Agenda Ativa":
