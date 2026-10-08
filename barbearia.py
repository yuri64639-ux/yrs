import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
from banco import init_db

# Configuração e inicialização estrutural
st.set_page_config(page_title="Barbearia Prime - Agendamento Cloud", layout="centered")
init_db()

# Gerenciamento nativo de variáveis de sessão da aplicação
if "aut" not in st.session_state: 
    st.session_state.aut = False
if "usr" not in st.session_state: 
    st.session_state.usr = ""
if "car" not in st.session_state: 
    st.session_state.car = []

# Customização da interface para ambiente mobile e ocultação de menus nativos
st.markdown("""
    <style>
    [data-testid="stHeader"], [data-testid="stAppToolbar"], header {
        visibility: hidden !important;
        display: none !important;
    }
    .stButton>button {
        width: 100%;
        height: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

# Consultas globais de dados para abastecer os seletores da interface
with sqlite3.connect("barber.db") as conn:
    df_servicos = pd.read_sql("SELECT id, nome, preco FROM servicos ORDER BY nome", conn)
    df_barbeiros = pd.read_sql("SELECT nome FROM barbeiros ORDER BY nome", conn)

# ------------------------------------------------------------------------------
# PORTAL DE DIRECIONAMENTO: CLIENTE OU PROFISSIONAL DA EQUIPE
# ------------------------------------------------------------------------------
if not st.session_state.aut:
    tipo_acesso = st.radio(
        "Selecione uma opção de acesso:", 
        ["📅 Sou Cliente (Agendar Meu Horário)", "💈 Sou da Equipe (Painel de Trabalho)"], 
        horizontal=True
    )
    
    # --- ÁREA EXCLUSIVA DE AUTOAGENDAMENTO DO CLIENTE ---
    if tipo_acesso == "📅 Sou Cliente (Agendar Meu Horário)":
        st.subheader("📅 Agende seu Horário Conosco")
        
        nome_cliente = st.text_input("Seu Nome Completo:").strip()
        barbeiro_sel = st.selectbox("Escolha o Profissional:", df_barbeiros['nome'].tolist() if not df_barbeiros.empty else ["Disponível"])
        servico_sel = st.selectbox("Escolha o Serviço desejado:", df_servicos['nome'].tolist() if not df_servicos.empty else ["Nenhum cadastrado"])
        
        col_data, col_hora = st.columns(2)
        data_sel = col_data.date_input("Escolha o Dia:", min_value=date.today())
        hora_sel = col_hora.time_input("Escolha o Horário:", value=time(9, 0))
        
        if st.button("💾 Confirmar Meu Agendamento", type="primary"):
            if not nome_cliente:
                st.error("❌ Por favor, digite seu nome completo para confirmar o agendamento.")
            elif servico_sel == "Nenhum cadastrado":
                st.error("❌ Não há serviços disponíveis para agendamento no momento.")
            else:
                data_string = data_sel.strftime("%Y-%m-%d")
                hora_string = hora_sel.strftime("%H:%M")
                
                with sqlite3.connect("barber.db") as conn:
                    cur = conn.cursor()
                    # Validação de choque de agenda: impede dois clientes no mesmo horário com o mesmo profissional
                    cur.execute("""
                        SELECT id FROM agenda 
                        WHERE barbeiro = ? AND data = ? AND horario = ? AND status = 'Agendado'
                    """, (barbeiro_sel, data_string, hora_string))
                    
                    if cur.fetchone():
                        st.error("❌ Este horário já se encontra ocupado com este profissional. Por favor, escolha outra hora!")
                    else:
                        cur.execute("SELECT id FROM servicos WHERE nome = ?", (servico_sel,))
                        servico_id = cur.fetchone()[0]
                        
                        cur.execute("""
                            INSERT INTO agenda (cliente, servico_id, barbeiro, data, horario) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (nome_cliente, servico_id, barbeiro_sel, data_string, hora_string))
                        conn.commit()
                        
                        st.success(f"🎉 Tudo pronto, {nome_cliente}! Seu horário foi reservado para o dia {data_sel.strftime('%d/%m/%Y')} às {hora_string}.")
        st.stop()
        
    # --- FORMULÁRIO DE AUTENTICAÇÃO DA EQUIPE INTERNA ---
    else:
        with st.form("formulario_login_equipe"):
            st.subheader("🔒 Acesso Restrito da Equipe")
            usuario_login = st.text_input("Nome do Barbeiro / Usuário:").strip()
            senha_login = st.text_input("Senha de Acesso:", type="password").strip()
            
            if st.form_submit_button("Entrar no Sistema", type="primary"):
                if usuario_login and senha_login:
                    with sqlite3.connect("barber.db") as conn:
                        cur = conn.cursor()
                        cur.execute("SELECT nome FROM barbeiros WHERE LOWER(nome) = ? AND senha = ?", (usuario_login.lower(), senha_login))
                        resultado_usuario = cur.fetchone()
                        
                    if resultado_usuario:
                        st.session_state.aut = True
                        st.session_state.usr = resultado_usuario[0]
                        st.rerun()
                    else:
                        st.error("❌ Nome de usuário ou senha de acesso incorretos.")
                else:
                    st.error("❌ Preencha todos os campos do formulário para efetuar o login.")
        st.stop()

# ------------------------------------------------------------------------------
# AMBIENTE AUTENTICADO DA EQUIPE (LOGADO)
# ------------------------------------------------------------------------------
if st.sidebar.button("🔒 Sair do Painel", type="primary"):
    st.session_state.aut = False
    st.session_state.usr = ""
    st.session_state.car = []
    st.rerun()

# Criação das abas superiores de navegação da equipe
tab_operacional, tab_gerencial = st.tabs(["📱 Terminal do Barbeiro", "⚙️ Painel Admin"])

# ==================== TERMINAL DO BARBEIRO ====================
with tab_operacional:
    st.subheader(f"💈 Terminal de Atendimento — Profissional: {st.session_state.usr}")
    
    aba_interna = st.radio(
        "Selecione a ação de trabalho:", 
        ["➕ Atendimento em Cadeira", "🧾 Caixa & Agenda Ativa"], 
        horizontal=True
    )

    # --- 1. LANÇAR ATENDIMENTO DIRETO DA CADEIRA ---
    if aba_interna == "➕ Atendimento em Cadeira":
        cliente_cadeira = st.text_input("Identificação do Cliente / Cadeira:", value="Cadeira 01").strip()
        
        if df_servicos.empty:
            st.warning("⚠️ Nenhum serviço cadastrado no catálogo administrativo.")
        else:
            filtro_busca = st.text_input("🔍 Buscar Serviço por Nome:").strip()
            df_serv_filtrado = df_servicos.copy()
            
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
                                cur.execute("""
                                    INSERT INTO comandas (cliente, servico_id, barbeiro, valor, data) 
                                    VALUES (?, ?, ?, ?, ?)
                                """, (cliente_cadeira, item['id'], st.session_state.usr, item['preco'], data_string_hoje))
                            conn.commit()
                        st.success("🚀 Atendimento enviado com sucesso para a fila do caixa!")
                        st.session_state.car = []
                        st.rerun()

    # --- 2. GERENCIAR AGENDA PÚBLICA E FECHAR COMANDAS NO CAIXA ---
    elif aba_interna == "🧾 Caixa & Agenda Ativa":
        with sqlite3.connect("barber.db") as conn:
            df_comandas_abertas = pd.read_sql("SELECT c.id, c.cliente, s.nome as servico, c.valor, c.barbeiro FROM comandas c JOIN servicos s ON c.servico_id = s.id WHERE c.status = 'Aberto'", conn)
            df_agenda_clientes = pd.read_sql("SELECT a.id, a.cliente, s.nome as servico, s.preco, a.barbeiro, a.data, a.horario FROM agenda a JOIN servicos s ON a.servico_id = s.id WHERE a.status = 'Agendado' ORDER BY a.data, a.horario", conn)
        
        # Exibição dos horários marcados pelos próprios clientes no portal externo
        if not df_agenda_clientes.empty:
            st.markdown("### 📅 Próximos Clientes Agendados (Portal do Cliente)")
            for _, row_a in df_agenda_clientes.iterrows():
                coluna_texto, col_botao_acao = st.columns([3, 1])
                coluna_texto.write(f"⏰ **{row_a['horario']}** ({row_a['data']}) — **{row_a['cliente']}** com {row_a['barbeiro']} [{row_a['servico']}]")
                
                if col_botao_acao.button("Atender", key=f"btn_agenda_{row_a['id']}", use_container_width=True):
                    with sqlite3.connect("barber.db") as conn:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO comandas (cliente, servico_id, barbeiro, valor, data) VALUES (?, ?, ?, ?, ?)", (row_a['cliente'], row_a['id'], row_a['barbeiro'], row_a['preco'], row_a['data']))
                        cur.execute("UPDATE agenda SET status = 'Atendido' WHERE id = ?", (row_a['id'],))
                        conn.commit()
                    st.success(f"Comanda de {row_a['cliente']} aberta com sucesso!"); st.rerun()
        
        st.markdown("---")
        st.markdown("### 🧾 Comandas em Atendimento (Aguardando Pagamento)")
        
        if df_comandas_abertas.empty:
            st.info("ℹ️ Não há comandas ou cadeiras abertas no caixa no momento.")
        else:
            pesquisa_caixa = st.text_input("🔍 Pesquisar Comanda por Cliente:").strip()
            if pesquisa_caixa:
                df_comandas_abertas = df_comandas_abertas[df_comandas_abertas['cliente'].str.contains(pesquisa_caixa, case=False, na=False)]
                
            if not df_comandas_abertas.empty:
                clientes_ativos = sorted(list(set(df_comandas_abertas['cliente'].tolist())))
                cliente_caixa_selecionado = st.selectbox("Selecione o Cliente para fechar a conta:", clientes_ativos)
                
                df_cliente_comanda = df_comandas_abertas[df_comandas_abertas['cliente'] == cliente_caixa_selecionada]
                subtotal_caixa = sum(row['valor'] for _, row in df_cliente_comanda.iterrows())
                
                st.markdown(f"#### Detalhes do Consumo: {cliente_caixa_selecionado}")
                for _, row in df_cliente_comanda.iterrows():
                    st.write(f"▪ **{row['servico']}** (Profissional: {row['barbeiro']}) — R$ {row['valor']:.2f}")
                    
                st.markdown(f"## Total Geral: R$ {subtotal_caixa:.2f}")
                calcular_comissao = st.checkbox("Pagar comissão padrão (50%) ao profissional por este serviço?", value=True)
                
                if st.button("💰 Finalizar e Receber Pagamento", type="primary", use_container_width=True):
                    with sqlite3.connect("barber.db") as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE comandas SET status = 'Finalizado', comissao = ? WHERE cliente = ? AND status = 'Aberto'", (1 if calcular_comissao else 0, cliente_caixa_selecionado))
                        conn.commit()
                    st.success(f"✅ Conta de {cliente_caixa_selecionado} fechada e arquivada com sucesso!"); st.rerun()

# ==================== PAINEL DO ADMINISTRADOR ====================
with tab_gerencial:
    st.subheader("⚙️ Autenticação Administrativa Gerencial")
    senha_administrativa = st.text_input("Digite a Senha do Usuário Admin:", type="password", key="input_senha_gerencia_final")
    
    if senha_administrativa != "1234":
        st.warning("🔒 Digite a senha master do usuário Admin para liberar as ferramentas de gestão (Padrão: 1234).")
    else:
        sub_abas_gerenciais = st.tabs(["🛠️ Catálogo de Serviços", "👥 Equipe de Barbeiros", "📊 Relatórios Financeiros"])
        
        # --- ABA GERENCIAL 1: CADASTRO DE SERVIÇOS EM MASSA ---
        with sub_abas_gerenciais[0]:
            st.markdown("Cole seus serviços seguindo o formato exato: **Nome do Serviço, Preço** (um serviço por linha).")
            texto_lote_servicos = st.text_area("Lista de Serviços:", placeholder="Corte Degradê, 45.0\nBarba Clássica, 30.0\nSobrancelha, 15.0", height=150)
            
            if st.button("🔥 Salvar Catálogo no Banco") and texto_lote_servicos.strip():
                linhas_texto = texto_lote_servicos.strip().split("\n")
                servicos_processados = 0
                
                with sqlite3.connect("barber.db") as conn:
                    cur = conn.cursor()
                    for linha in linhas_texto:
                        if "," in linha:
                            partes_linha = linha.split(",")
                            if len(partes_linha) == 2:
                                nome_serv_final = partes_linha[0].strip()
                                preco_serv_final = partes_linha[1].strip()
                                if nome_serv_final:
                                    try:
                                        cur.execute("""
