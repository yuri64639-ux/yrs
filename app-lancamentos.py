import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração otimizada para telas verticais de celular
st.set_page_config(page_title="Sistema Mobile - Bar", layout="centered")

# --- BANCO DE DADOS (CONCURRÊNCIA ATIVADA) ---
def conectar_banco():
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
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    """)
    conn.commit()
    return conn

conn = conectar_banco()
cursor = conn.cursor()

# Atualização automática em tempo real a cada 5 segundos
st.fragment(run_every=5)

# Mapeamento de quais categorias pertencem ao BAR e quais pertencem à COZINHA
CATEGORIAS_BAR = ["Bebidas", "Drinks"]
CATEGORIAS_COZINHA = ["Porções", "Pratos Principais", "Sobremesas"]

# --- INTERFACE MOBILE ---
st.title("📱 Gestão Orla Bar")

aba_garcom, aba_cozinha, aba_bar, aba_comandas, aba_gerencia = st.tabs([
    "🏃‍♂️ Lançar", 
    "🍳 Cozinha", 
    "🍹 Bar",
    "🎟️ Contas",
    "⚙️ Cardápio"
])

# --- 1. ABA DO GARÇOM (LANÇAMENTO VERTICAL) ---
with aba_garcom:
    st.subheader("📋 Novo Pedido")
    
    cursor.execute("SELECT DISTINCT categoria FROM produtos ORDER BY categoria")
    categorias_disponiveis = [c[0] for c in cursor.fetchall() if c[0]]
    
    # CORRIGIDO: Agora a variável está escrita corretamente em português
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
            mesa = st.text_input("Mesa / Pulseira / Comanda:", placeholder="Ex: Pulseira 12")
            
            dict_produtos = {f"{p[1]} (R$ {p[3]:.2f})": p[0] for p in lista_produtos}
            produto_selecionado = st.selectbox("Item do Cardápio:", list(dict_produtos.keys()))
            
            quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1)
                
            botao_enviar = st.form_submit_button("🔥 Enviar Pedido", type="primary", use_container_width=True)
            
            if botao_enviar:
                if mesa.strip() == "":
                    st.error("Informe a mesa ou pulseira.")
                else:
                    p_id = dict_produtos[produto_selecionado]
                    horario_atual = datetime.now().strftime("%H:%M:%S")
                    
                    cursor.execute(
                        "INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)",
                        (mesa.strip(), p_id, quantidade, horario_atual)
                    )
                    conn.commit()
                    st.success("✅ Pedido enviado!")
                    st.rerun()

# --- FUNCIONALIDADE REUTILIZÁVEL PARA TELAS DE PREPARO (BAR E COZINHA) ---
def renderizar_tela_preparo(categorias_alvo, titulo_tela):
    st.subheader(titulo_tela)
    
    if not categorias_alvo:
        return
        
    placeholders = ",".join("?" for _ in categorias_alvo)
    query = f"""
        SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status, p.horario 
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({placeholders})
        ORDER BY p.id DESC
    """
    cursor.execute(query, categorias_alvo)
    pedidos_ativos = cursor.fetchall()
    
    if not pedidos_ativos:
        st.success("🎉 Tudo pronto por aqui!")
    else:
        for p_id, p_mesa, pr_nome, p_qtd, p_status, p_hora in pedidos_ativos:
            cor_status = "🔴 Pendente" if p_status == "Pendente" else "🟡 Preparando"
                
            with st.container(border=True):
                st.markdown(f"**{p_mesa}** — *{p_hora}*")
                st.markdown(f"### {p_qtd}x {pr_nome}")
                st.text(f"Status: {cor_status}")
                
                if p_status == "Pendente":
                    if st.button("🚚 Prontificar", key=f"pronto_{titulo_tela}_{p_id}", use_container_width=True):
                        cursor.execute("UPDATE pedidos SET status = 'Entregue' WHERE id = ?", (p_id,))
                        conn.commit()
                        st.rerun()

# --- 2. ABA DA COZINHA (APENAS COMIDAS) ---
with aba_cozinha:
    renderizar_tela_preparo(CATEGORIAS_COZINHA, "🍳 Cozinha (Porções e Pratos)")

# --- 3. ABA DO BAR (APENAS DRINKS E BEBIDAS) ---
with aba_bar:
    renderizar_tela_preparo(CATEGORIAS_BAR, "🍹 Bar (Drinks e Bebidas)")

# --- 4. ABA: COMANDAS / PULSEIRAS ABERTAS ---
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
            valor_total_comanda = df_filtrado["Total Item (R$)"].sum()
            
            with st.container(border=True):
                st.markdown(f"### 🎫 {comanda}")
                st.markdown(f"#### Total: **R$ {valor_total_comanda:.2f}**")
                
                st.dataframe(df_filtrado[["Produto", "Quantidade", "Total Item (R$)"]], hide_index=True, use_container_width=True)
                
                if st.button(f"💵 Fechar Conta ({comanda})", key=f"fechar_{comanda}", use_container_width=True):
                    cursor.execute("UPDATE pedidos SET status = 'Finalizado (Pago)' WHERE mesa = ? AND status != 'Finalizado (Pago)'", (comanda,))
                    conn.commit()
                    st.success("Conta fechada com sucesso!")
                    st.rerun()

# --- 5. ABA DE CADASTRO DE PRODUTOS ---
with aba_gerencia:
    st.subheader("⚙️ Configurar Cardápio")
    
    novo_nome = st.text_input("Nome do Item:")
    nova_categoria = st.selectbox("Categoria correspondente:", CATEGORIAS_BAR + CATEGORIAS_COZINHA)
    novo_preco = st.number_input("Preço (R$):", min_value=0.0, value=0.0, step=0.50, format="%.2f")
    
    if st.button("💾 Salvar Produto", type="primary", use_container_width=True):
        if novo_nome.strip() == "" or novo_preco <= 0:
            st.error("Preencha nome e preço válidos.")
        else:
            try:
                cursor.execute("INSERT INTO produtos (nome, categoria, preco) VALUES (?, ?, ?)", (novo_nome.strip(), nova_categoria, novo_preco))
                conn.commit()
                st.success("Cadastrado com sucesso!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Este produto já existe no banco.")


            
