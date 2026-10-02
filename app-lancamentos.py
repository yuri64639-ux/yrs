import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração otimizada para telas verticais de celular
st.set_page_config(page_title="Sistema Mobile - Pedidos", layout="centered")

# --- CONTROLE DE ACESSO (SENHA) ---
SENHA_CORRETA = "sistema123"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔑 Acesso ao Sistema de Pedidos")
    senha_digitada = st.text_input("Digite a senha do estabelecimento:", type="password")
    if st.button("Entrar", type="primary", use_container_width=True):
        if senha_digitada == SENHA_CORRETA:
            st.session_state["autenticado"] = True
            st.success("Acesso liberado!")
            st.rerun()
        else:
            st.error("Senha incorreta. Tente novamente.")
    st.stop()

# --- BANCO DE DADOS ---
conn = sqlite3.connect("sistema_restaurante.db", check_same_thread=False, timeout=20)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=NORMAL;")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE,
        categoria TEXT,
        preco REAL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mesa TEXT,
        produto_id INTEGER,
        quantidade INTEGER,
        status TEXT DEFAULT 'Pendente',
        horario TEXT,
        taxa_servico REAL DEFAULT 0.0,
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
    )
""")
conn.commit()

# Atualização automática em tempo real a cada 5 segundos
st.fragment(run_every=5)

CATEGORIAS_BAR = ["Bebidas", "Drinks"]
CATEGORIAS_COZINHA = ["Porções", "Pratos Principais", "Sobremesas"]

st.title("📱 Gestão de Pedidos")

aba_garcom, aba_cozinha, aba_bar, aba_comandas, aba_relatorio, aba_gerencia = st.tabs([
    "🏃‍♂️ Lançar", "🍳 Cozinha", "🍹 Bar", "🎟️ Contas", "📊 Relatório", "⚙️ Cardápio"
])

# --- 1. ABA DO GARÇOM ---
with aba_garcom:
    st.subheader("📋 Novo Pedido")
    cursor.execute("SELECT DISTINCT categoria FROM produtos ORDER BY categoria")
    categorias_disponiveis = [c[0] for c in cursor.fetchall() if c[0]]
    
    if not categorias_disponiveis:
        st.warning("⚠️ Cadastre os produtos na aba 'Cardápio' primeiro.")
    else:
        filtro_categorias = ["Todas"] + categorias_disponiveis
        categoria_selecionada = st.selectbox("📂 Categoria:", filtro_categorias)
        
        if categoria_selecionada == "Todas":
            cursor.execute("SELECT id, nome, categoria, preco FROM produtos ORDER BY categoria, nome")
        else:
            cursor.execute("SELECT id, nome, categoria, preco FROM produtos WHERE categoria = ? ORDER BY nome", (categoria_selecionada,))
        lista_produtos = cursor.fetchall()
        
        with st.form("form_pedido", clear_on_submit=True):
            mesa = st.text_input("Mesa / Pulseira / Comanda:", placeholder="Ex: Comanda 12")
            dict_produtos = {f"{p[1]} (R$ {p[3]:.2f})": p[0] for p in lista_produtos}
            
            if not dict_produtos:
                st.info("Nenhum item encontrado nesta categoria.")
            else:
                produto_selecionado = st.selectbox("Item do Cardápio:", list(dict_produtos.keys()))
                quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1)
                botao_enviar = st.form_submit_button("🔥 Enviar Pedido", type="primary", use_container_width=True)
                
                if botao_enviar:
                    if mesa.strip() == "":
                        st.error("Informe a mesa ou pulseira.")
                    else:
                        p_id = dict_produtos[produto_selecionado]
                        horario_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)",
                            (mesa.strip(), p_id, quantidade, horario_atual)
                        )
                        conn.commit()
                        st.success("✅ Pedido enviado!")
                        st.rerun()

# --- 2. ABA DA COZINHA ---
with aba_cozinha:
    st.subheader("🍳 Cozinha")
    placeholders = ",".join("?" for _ in CATEGORIAS_COZINHA)
    query_cz = f"""
        SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status, p.horario 
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({placeholders})
        ORDER BY p.id DESC
    """
    cursor.execute(query_cz, CATEGORIAS_COZINHA)
    pedidos_cozinha = cursor.fetchall()
    
    if not pedidos_cozinha:
        st.success("🎉 Tudo pronto por aqui!")
    else:
        for p_id, p_mesa, pr_nome, p_qtd, p_status, p_horario_completo in pedidos_cozinha:
            cor_status = "🔴 Pendente" if p_status == "Pendente" else "🟡 Preparando"
            hora_exibicao = p_horario_completo[11:19] if (p_horario_completo and len(p_horario_completo) > 10) else p_horario_completo
            with st.container(border=True):
                st.markdown(f"**{p_mesa}** — *{hora_exibicao}*")
                st.markdown(f"### {p_qtd}x {pr_nome}")
                st.text(f"Status: {cor_status}")
                if p_status == "Pendente":
                    if st.button("🚚 Prontificar", key=f"pronto_cz_{p_id}", use_container_width=True):
                        cursor.execute("UPDATE pedidos SET status = 'Entregue' WHERE id = ?", (p_id,))
                        conn.commit()
                        st.rerun()

# --- 3. ABA DO BAR ---
with aba_bar:
    st.subheader("🍹 Bar")
    placeholders = ",".join("?" for _ in CATEGORIAS_BAR)
    query_br = f"""
        SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status, p.horario 
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({placeholders})
        ORDER BY p.id DESC
    """
    cursor.execute(query_br, CATEGORIAS_BAR)
    pedidos_bar = cursor.fetchall()
    
    if not pedidos_bar:
        st.success("🎉 Tudo pronto por aqui!")
    else:
        for p_id, p_mesa, pr_nome, p_qtd, p_status, p_horario_completo in pedidos_bar:
            cor_status = "🔴 Pendente" if p_status == "Pendente" else "🟡 Preparando"
            hora_exibicao = p_horario_completo[11:19] if (p_horario_completo and len(p_horario_completo) > 10) else p_horario_completo
            with st.container(border=True):
                st.markdown(f"**{p_mesa}** — *{hora_exibicao}*")
                st.markdown(f"### {p_qtd}x {pr_nome}")
                st.text(f"Status: {cor_status}")
                if p_status == "Pendente":
                    if st.button("🚚 Prontificar", key=f"pronto_br_{p_id}", use_container_width=True):
                        cursor.execute("UPDATE pedidos SET status = 'Entregue' WHERE id = ?", (p_id,))
                        conn.commit()
                        st.rerun()

# --- 4. ABA: CONTAS ABERTAS ---
with aba_comandas:
    st.subheader("🎟️ Contas Abertas")
    query_comandas = """
        SELECT p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as total_item
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        WHERE p.status != 'Finalizado (Pago)'
        ORDER BY p.mesa, pr.nome
    """
    cursor.execute(query_comandas)
    itens_consumidos = cursor.fetchall()
    
    if not itens_consumidos:
        st.info("Nenhuma comanda ativa.")
    else:
        df_consumo = pd.DataFrame(itens_consumidos, columns=["Identificador", "Produto", "Quantidade", "Preço Unitário (R$)", "Total Item (R$)"])
        comandas_abertas = df_consumo["Identificador"].unique()
        
        for comanda in comandas_abertas:
            df_filtrado = df_consumo[df_consumo["Identificador"] == comanda]
            subtotal = df_filtrado["Total Item (R$)"].sum()
            taxa_calculada = subtotal * 0.10
            total_geral = subtotal + taxa_calculada
            
            with st.container(border=True):
                st.markdown(f"### 🎫 {comanda}")
                st.dataframe(df_filtrado[["Produto", "Quantidade", "Total Item (R$)"]], hide_index=True, use_container_width=True)
                st.write(f"🔹 **Subtotal:** R$ {subtotal:.2f}")
                st.write(f"🔸 **Serviço (10%):** R$ {taxa_calculada:.2f}")
                st.markdown(f"#### 💰 Total: **R$ {total_geral:.2f}**")
                st.write("---")
                st.warning("❓ **O cliente aceitou pagar a taxa de 10%?**")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"🟢 Sim", key=f"pago_10_{comanda}", use_container_width=True):
                        cursor.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_servico = 0.10 WHERE mesa = ? AND status != 'Finalizado (Pago)'", (comanda,))
                        conn.commit()
                        st.success("Fechado com taxa!")
                        st.rerun()
                with c2:
                    if st.button(f"🔴 Não", key=f"pago_sem_{comanda}", use_container_width=True):
                        cursor.execute("UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_servico = 0.0 WHERE mesa = ? AND status != 'Finalizado (Pago)'", (comanda,))
                        conn.commit()
                        st.success("Fechado sem taxa!")
                        st.rerun()

# --- 5. RELATÓRIO SEPARADO POR DIA E MÊS ---
with aba_relatorio:
    st.subheader("📊 Relatório de Vendas")
    query_vendas = """
        SELECT pr.nome, pr.categoria, p.quantidade, pr.preco, (p.quantidade * pr.preco) as total_item, p.horario, p.taxa_servico
