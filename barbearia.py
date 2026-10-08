import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
from banco import init_db

# Configuração de Identidade Visual na Aba do Navegador
st.set_page_config(page_title="marinote club", layout="centered")
init_db()

# Inicialização das variáveis globais de estado do Streamlit
for k, v in [("aut", False), ("usr", ""), ("car", [])]:
    if k not in st.session_state: 
        st.session_state[k] = v

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

# Consulta local de serviços e profissionais ativos
with sqlite3.connect("barber.db") as conn:
    df_s = pd.read_sql("SELECT id, nome, preco FROM servicos ORDER BY nome", conn)
    df_b = pd.read_sql("SELECT nome FROM barbeiros ORDER BY nome", conn)

# Roteador Inicial: Filtra o acesso público do cliente e o restrito da equipe
if not st.session_state.aut:
    menu = st.radio("Selecione uma opção de acesso:", ["📅 Sou Cliente (Agendar Horário)", "💈 Sou da Equipe (Painel Interno)"], horizontal=True)
    
    # --- INTERFACE DE AUTOAGENDAMENTO PÚBLICO ---
    if menu == "📅 Sou Cliente (Agendar Horário)":
        st.title("💈 marinote club")
        st.markdown("### 📅 Agende seu Horário Conosco")
        
        c_nome = st.text_input("Seu Nome Completo:").strip()
        b_agenda = st.selectbox("Escolha o Barbeiro:", df_b['nome'].tolist() if not df_b.empty else ["Artur"])
        s_agenda = st.selectbox("Escolha o Serviço:", df_s['nome'].tolist() if not df_s.empty else ["Nenhum cadastrado"])
        
        col_d, col_h = st.columns(2)
        d_sel = col_d.date_input("Data desejada:", min_value=date.today())
        h_sel = col_h.time_input("Horário desejado:", value=time(9, 0))
        
        if st.button("💾 Confirmar Meu Agendamento") and c_nome and s_agenda != "Nenhum cadastrado":
            d_str, h_str = d_sel.strftime("%Y-%m-%d"), h_sel.strftime("%H:%M")
            with sqlite3.connect("barber.db") as conn:
                cur = conn.cursor()
                # Impede conflito de horários duplicados na agenda do mesmo profissional
                cur.execute("SELECT id FROM agenda WHERE barbeiro = ? AND data = ? AND horario = ? AND status = 'Agendado'", (b_agenda, d_str, h_str))
                if cur.fetchone(): 
                    st.error("❌ Este horário já está ocupado com este profissional. Escolha outro!")
                else:
                    cur.execute("SELECT id FROM servicos WHERE nome = ?", (s_agenda,))
                    s_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO agenda (cliente, servico_id, barbeiro, data, horario) VALUES (?, ?, ?, ?, ?)", (c_nome, s_id, b_agenda, d_str, h_str))
                    conn.commit()
                    st.success(f"🎉 Tudo certo, {c_nome}! Seu horário foi agendado na marinote club para o dia {d_sel.strftime('%d/%m/%Y')} às {h_str}.")
        st.stop()
    # --- FORMULÁRIO DE LOGIN DA EQUIPE INTERNA ---
    else:
        with st.form("l_f"):
            st.subheader("🔒 Acesso Restrito — marinote club")
            u = st.text_input("Barbeiro:").strip()
            p = st.text_input("Senha:", type="password").strip()
            if st.form_submit_button("Entrar no Sistema"):
                with sqlite3.connect("barber.db") as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT nome FROM barbeiros WHERE LOWER(nome) = ? AND senha = ?", (u.lower(), p))
                    res = cur.fetchone()
                if res:
                    st.session_state.aut, st.session_state.usr = True, res[0]
                    st.rerun()
                else: 
                    st.error("❌ Credenciais incorretas.")
        st.stop()

# ------------------------------------------------------------------------------
# AMBIENTE AUTENTICADO DA EQUIPE (LOGADO)
# ------------------------------------------------------------------------------
if st.sidebar.button("🔒 Sair do Painel", type="primary"):
    st.session_state.aut = False
    st.session_state.usr = ""
    st.session_state.car = []
    st.rerun()

# Criação das abas superiores de navegação para a equipe de barbeiros
tab_operacional, tab_gerencial = st.tabs(["📱 Terminal do Barbeiro", "⚙️ Painel Admin"])

# ==================== TERMINAL DO BARBEIRO ====================
with tab_operacional:
    st.subheader(f"💈 Terminal de Atendimento — Profissional: {st.session_state.usr}")
    
    aba_interna = st.radio(
        "Selecione a ação de trabalho:", 
        ["➕ Atendimento em Cadeira", "🧾 Caixa & Agenda Ativa"], 
        horizontal=True
    )

    # --- 1. LANÇAR ATENDIMENTO DIRETO DA CADEIRA (SEM AGENDAMENTO PREVIO) ---
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

    # --- 2. EXIBIÇÃO EM TABELA E FECHAMENTO DE CONTAS NO CAIXA ---
    elif aba_interna == "🧾 Caixa & Agenda Ativa":
        with sqlite3.connect("barber.db") as conn:
            df_comandas_abertas = pd.read_sql("SELECT c.id, c.cliente, s.nome as servico, c.valor, c.barbeiro FROM comandas c JOIN servicos s ON c.servico_id = s.id WHERE c.status = 'Aberto'", conn)
            df_agenda_clientes = pd.read_sql("SELECT a.id, a.cliente, s.nome as servico, s.preco, a.barbeiro, a.data, a.horario FROM agenda a JOIN servicos s ON a.servico_id = s.id WHERE a.status = 'Agendado' ORDER BY a.data, a.horario", conn)
        
        # --- TABELA DE CORTES AGENDADOS ATIVOS ---
        st.markdown("### 📅 Tabela de Atendimentos Agendados")
        if df_agenda_clientes.empty:
            st.info("ℹ️ Nenhum horário agendado por clientes para os próximos dias.")
        else:
            df_tabela_visual = df_agenda_clientes.copy()
            df_tabela_visual.columns = ["ID", "Cliente", "Serviço solicitado", "Preço", "Barbeiro", "Data", "Horário"]
            st.dataframe(df_tabela_visual[["Horário", "Data", "Cliente", "Barbeiro", "Serviço solicitado"]], use_container_width=True, hide_index=True)
            
            st.markdown("**Iniciar Atendimento da Agenda:**")
            lista_id_agenda = {f"{row['horario']} - {row['cliente']} c/ {row['barbeiro']}": row['id'] for _, row in df_agenda_clientes.iterrows()}
            agenda_atender = st.selectbox("Selecione o cliente agendado para iniciar:", list(lista_id_agenda.keys()), key="sb_atender_agenda")
            
            if st.button("🚀 Abrir Comanda do Cliente Selecionado", use_container_width=True):
                id_agenda_final = lista_id_agenda[agenda_atender]
                
                with sqlite3.connect("barber.db") as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT a.cliente, a.barbeiro, a.data, a.servico_id, s.preco FROM agenda a JOIN servicos s ON a.servico_id = s.id WHERE a.id = ?", (id_agenda_final,))
                    r_atend = cur.fetchone()
                    
                    if r_atend:
                        cur.execute("INSERT INTO comandas (cliente, servico_id, barbeiro, valor, data) VALUES (?, ?, ?, ?, ?)", (r_atend[0], r_atend[3], r_atend[1], r_atend[4], r_atend[2]))
                        cur.execute("UPDATE agenda SET status = 'Atendido' WHERE id = ?", (id_agenda_final,))
                        conn.commit()
                st.success("Comanda de atendimento iniciada com sucesso!"); st.rerun()

        st.markdown("---")
        st.markdown("### 🧾 Comandas em Atendimento")
        
        if df_comandas_abertas.empty:
            st.info("ℹ️ Não há comandas abertas no caixa no momento.")
        else:
            pesquisa_caixa = st.text_input("🔍 Pesquisar Comanda por Cliente:").strip()
            if pesquisa_caixa:
                df_comandas_abertas = df_comandas_abertas[df_comandas_abertas['cliente'].str.contains(pesquisa_caixa, case=False, na=False)]
                
            if not df_comandas_abertas.empty:
                clientes_ativos = sorted(list(set(df_comandas_abertas['cliente'].tolist())))
                cliente_caixa_selecionado = st.selectbox("Selecione o Cliente para fechar a conta:", clientes_ativos)
                
                df_cliente_comanda = df_comandas_abertas[df_comandas_abertas['cliente'] == cliente_caixa_selecionado]
                subtotal_caixa = sum(row['valor'] for _, row in df_cliente_comanda.iterrows())
                
                st.markdown(f"#### Detalhes do Consumo: {cliente_caixa_selecionado}")
                for _, row in df_cliente_comanda.iterrows():
                    st.write(f"▪ **{row['servico']}** ({row['barbeiro']}) — R$ {row['valor']:.2f}")
                    
                st.markdown(f"## Total Geral: R$ {subtotal_caixa:.2f}")
                calcular_comissao = st.checkbox("Pagar comissão padrão (50%) por este serviço?", value=True)
                
                if st.button("💰 Finalizar e Receber Pagamento", type="primary", use_container_width=True):
                    with sqlite3.connect("barber.db") as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE comandas SET status = 'Finalizado', comissao = ? WHERE cliente = ? AND status = 'Aberto'", (1 if calcular_comissao else 0, cliente_caixa_selecionado))
                        conn.commit()
                    st.success(f"✅ Conta de {cliente_caixa_selecionado} fechada com sucesso!"); st.rerun()

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
            texto_lote_servicos = st.text_area("Lista de Serviços:", placeholder="Corte Degradê, 45.0\nBarba Clássica, 30.0", height=150)
            
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
                                        cur.execute("INSERT INTO servicos (nome, preco) VALUES (?, ?) ON CONFLICT(nome) DO UPDATE SET preco = EXCLUDED.preco", (nome_serv_final, float(preco_serv_final)))
                                        servicos_processados += 1
                                    except: pass
                    conn.commit()
                st.success(f"🚀 {servicos_processados} serviços salvos no catálogo!"); st.rerun()
                
            st.markdown("---")
            if not df_s.empty:
                st.subheader("📋 Serviços Ativos")
                servico_para_remover = st.selectbox("Selecione um serviço para excluir:", df_s['nome'].tolist())
                
                if st.button("❌ Remover Serviço do Catálogo"):
                    with sqlite3.connect("barber.db") as conn:
                        conn.cursor().execute("DELETE FROM servicos WHERE nome = ?", (servico_para_remover,))
                        conn.commit()
                    st.success("Serviço removido!"); st.rerun()

        # --- ABA GERENCIAL 2: CADASTRO INDIVIDUAL DA EQUIPE ---
        with sub_abas_gerenciais[1]:
            st.subheader("👥 Registrar Novo Barbeiro")
            with st.form("form_novo_barbeiro", clear_on_submit=True):
                nome_novo_b = st.text_input("Nome do Profissional:").strip()
                senha_novo_b = st.text_input("Defina a Senha de Acesso:", type="password").strip()
                
                if st.form_submit_button("💼 Registrar Funcionário") and nome_novo_b and senha_novo_b:
                    try:
                        with sqlite3.connect("barber.db") as conn:
                            conn.cursor().execute("INSERT INTO barbeiros (nome, senha) VALUES (?, ?)", (nome_novo_b, senha_novo_b))
                            conn.commit()
                        st.success(f"🎉 Profissional '{nome_novo_b}' registrado!"); st.rerun()
                    except:
                        st.error("❌ Nome já existente na equipe.")
                        
            st.markdown("---")
            if not df_b.empty:
                st.subheader("👥 Equipe Ativa")
                lista_barbeiros_excluir = [nome for nome in df_b['nome'].tolist() if nome.lower() != 'admin']
                if lista_barbeiros_excluir:
                    barbeiro_para_remover = st.selectbox("Selecione um profissional para desligar:", lista_barbeiros_excluir)
                    if st.button("❌ Desativar Profissional da Equipe"):
                        with sqlite3.connect("barber.db") as conn:
                            conn.cursor().execute("DELETE FROM barbeiros WHERE nome = ?", (barbeiro_para_remover,))
                            conn.commit()
                        st.success("Profissional removido!"); st.rerun()
                else:
                    st.info("Apenas o usuário Admin master está registrado na equipe.")

        # --- ABA GERENCIAL 3: RELATÓRIOS FINANCEIROS E COMISSÕES ---
        with sub_abas_gerenciais[2]:
            st.subheader("📊 Faturamento e Desempenho Operacional")
            with sqlite3.connect("barber.db") as conn:
                df_historico_fechado = pd.read_sql("SELECT c.cliente, s.nome as servico, c.barbeiro, c.valor, c.comissao, c.data FROM comandas c JOIN servicos s ON c.servico_id = s.id WHERE c.status = 'Finalizado' ORDER BY c.id DESC", conn)
                
            if df_historico_fechado.empty:
                st.info("ℹ️ Nenhuma comanda fechada e paga no sistema até o momento.")
            else:
                lista_datas_fechamento = sorted(list(set(df_historico_fechado['data'].tolist())), reverse=True)
                data_filtro_relatorio = st.selectbox("📅 Selecione o Dia para auditoria:", lista_datas_fechamento)
                
                df_relatorio_dia = df_historico_fechado[df_historico_fechado['data'] == data_filtro_relatorio]
                
                faturamento_bruto_dia = float(df_relatorio_dia['valor'].sum())
                comissoes_totais_dia = float(df_relatorio_dia[df_relatorio_dia['comissao'] == 1]['valor'].sum() * 0.50)
                lucro_liquido_casa = faturamento_bruto_dia - comissoes_totais_dia
                
                col_b1, col_b2, col_b3 = st.columns(3)
                col_b1.metric("💰 Faturamento Bruto", f"R$ {faturamento_bruto_dia:.2f}")
                col_b2.metric("💈 Comissões Pagas (50%)", f"R$ {comissoes_totais_dia:.2f}")
                col_b3.metric("📈 Lucro Líquido da Casa", f"R$ {lucro_liquido_casa:.2f}")
                
                st.markdown("---")
                st.dataframe(df_relatorio_dia, use_container_width=True, hide_index=True)
