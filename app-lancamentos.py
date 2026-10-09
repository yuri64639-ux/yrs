import streamlit as st

# Configuração inicial da página
st.set_page_config(
    page_title="Sistema de Restaurante",
    page_icon="🍽️",
    layout="centered"
)

# 1. Inicializa as variáveis de controle no session_state (evita resetar ao interagir)
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_atual = None
    st.session_state.cargo = None

# ==========================================
# TELA DE LOGIN
# ==========================================
if not st.session_state.logado:
    st.title("🔐 Login - Sistema Restaurante")
    st.write("Insira suas credenciais para acessar o painel.")

    # Formulário de login
    with st.form("form_login"):
        usuario = st.text_input("Usuário (Dica: gerente ou garcom)", autocomplete="username")
        senha = st.text_input("Senha (Dica: 123)", type="password", autocomplete="current-password")
        botao_entrar = st.form_submit_button("Entrar")

        if botao_entrar:
            # Simulação simples de validação de usuários e cargos
            if usuario == "gerente" and senha == "123":
                st.session_state.logado = True
                st.session_state.usuario_atual = "Gerente Geral"
                st.session_state.cargo = "gerente"
                st.success("Login realizado com sucesso!")
                st.rerun()  # Recarrega a página para aplicar as mudanças
            elif usuario == "garcom" and senha == "123":
                st.session_state.logado = True
                st.session_state.usuario_atual = "Garçom Principal"
                st.session_state.cargo = "garcom"
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")

# ==========================================
# PAINEL DO SISTEMA (APÓS LOGIN)
# ==========================================
else:
    # --- MENU LATERAL (SIDEBAR) ---
    st.sidebar.title("📌 Menu de Navegação")
    st.sidebar.write(f"**Usuário:** {st.session_state.usuario_atual}")
    st.sidebar.write(f"**Cargo:** {st.session_state.cargo.capitalize()}")
    
    st.sidebar.divider()
    
    # Botão para deslogar do sistema
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.cargo = None
        st.rerun()

    # --- DEFINIÇÃO DINÂMICA DAS ABAS BASEADA NO CARGO ---
    st.title("🍽️ Painel de Operações")
    
    # Se for gerente, inclui a aba de gerência. Se for garçom, oculta ela.
    if st.session_state.cargo == "gerente":
        lista_abas = ["📋 Atendimento e Pedidos", "🍳 Cozinha", "📊 Gerência e Relatórios"]
    else:
        lista_abas = ["📋 Atendimento e Pedidos", "🍳 Cozinha"]

    # Cria as abas na tela com base na lista filtrada acima
    abas = st.tabs(lista_abas)

    # --- CONTEÚDO DA ABA 1: ATENDIMENTO (Visível para todos) ---
    with abas[0]:
        st.header("📋 Lançar e Monitorar Pedidos")
        st.info("Área de uso diário para atendimento de mesas e balcão.")
        
        # Exemplo de funcionalidade simulada
        mesa = st.number_input("Número da Mesa", min_value=1, max_value=50, step=1)
        item_pedido = st.selectbox("Escolha o item:", ["Hambúrguer Artesanal", "Pizza Grande", "Suco Natural", "Refrigerante"])
        quantidade = st.spinbox = st.number_input("Quantidade", min_value=1, max_value=10, step=1)
        
        if st.button("Enviar para a Cozinha"):
            st.success(f"Pedido enviado: {quantidade}x {item_pedido} para a Mesa {mesa}!")

    # --- CONTEÚDO DA ABA 2: COZINHA (Visível para todos) ---
    with abas[1]:
        st.header("🍳 Painel de Preparo - Cozinha")
        st.write("Acompanhe os pratos que estão na fila de produção.")
        
        # Simulando uma tabela de pedidos aguardando
        dados_cozinha = {
            "Mesa":,
            "Pedido": ["Pizza Grande", "Hambúrguer Artesanal", "Suco Natural"],
            "Status": ["Em Preparo ⏳", "Aguardando 🕒", "Pronto ✅"]
        }
        st.table(dados_cozinha)

    # --- CONTEÚDO DA ABA 3: GERÊNCIA (Apenas visível e acessível se for Gerente) ---
    if st.session_state.cargo == "gerente":
        with abas[2]:
            st.header("📊 Relatórios Financeiros e Gerência")
            st.warning("⚠️ Atenção: Esta área é estritamente confidencial e visível apenas para gerentes.")
            
            # Dados falsos para simular o faturamento
            st.metric(label="Faturamento do Dia", value="R$ 2.450,00", delta="+15% em relação a ontem")
            st.metric(label="Pedidos Cancelados", value="2", delta="-1", delta_color="inverse")
            
            st.subheader("Histórico de Fechamento de Caixa")
            st.bar_chart({"Dias":, "Vendas (R$)": [1200, 1500, 1800, 1100, 2450]})
