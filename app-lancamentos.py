from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

# Configuração mobile
st.set_page_config(page_title="Sistema Mobile - Gestão", layout="centered")

# --- CONTROLE DE ACESSO ---
SENHA_CORRETA = "orla123"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔑 Acesso ao Sistema")
    senha_digitada = st.text_input("Digite a senha do estabelecimento:", type="password")
    if st.button("Entrar", type="primary", use_container_width=True):
        if senha_digitada == SENHA_CORRETA:
            st.session_state["autenticado"] = True
            st.success("Acesso liberado!")
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# --- BANCO DE DADOS ---
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

# Atualização em tempo real (5s)
st.fragment(run_every=5)

CATEGORIAS_BAR = ["Bebidas", "Drinks"]
CATEGORIAS_COZINHA = ["Porções", "Pratos Principais", "Sobremesas"]
TODAS_CATEGORIAS = CATEGORIAS_BAR + CATEGORIAS_COZINHA

st.title("📱 Gestão Bar & Restaurante")
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
            mesa = st.text_input("Mesa / Pulseira / Comanda:", placeholder="Ex: Pulseira 12")
            dict_produtos = {f"{p[1]} (R$ {p[3]:.2f})": p[0] for p in lista_produtos}
            produto_selecionado = st.selectbox("Item do Cardápio:", list(dict_produtos.keys()))
            quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1)

            if st.form_submit_button("🔥 Enviar Pedido", type="primary", use_container_width=True):
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

# --- FUNÇÃO REUTILIZÁVEL DE PREPARO ---
def renderizar_tela_preparo(categorias_alvo, titulo_tela):
    st.subheader(titulo_tela)
    placeholders = ",".join("?" for _ in categorias_alvo)
    query = f"""
        SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status, p.horario 
        FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id
        WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({placeholders})
        ORDER BY p.id DESC
    """
    cursor.execute(query, categorias_alvo)
    pedidos_ativos = cursor.fetchall()

    if not pedidos_ativos:
        st.success("🎉 Tudo pronto por aqui!")
    else:
        for p_id, p_mesa, pr_nome, p_qtd, p_status, p_horario in pedidos_ativos:
            cor_status = "🔴 Pendente" if p_status == "Pendente" else "🟡 Preparando"
            hora = p_horario[11:19] if (p_horario and len(p_horario) > 10) else p_horario
            
            with st.container(border=True):
                st.markdown(f"**{p_mesa}** — *{hora}*")
                st.markdown(f"### {p_qtd}x {pr_nome}")
                st.text(f"Status: {cor_status}")

                if p_status == "Pendente":
                    if st.button("👨‍🍳 Preparar", key=f"prep_{titulo_tela}_{p_id}", use_container_width=True):
                        cursor.execute("UPDATE pedidos SET status = 'Preparando' WHERE id = ?", (p_id,))
                        conn.commit()
                        st.rerun()
                elif p_status == "Preparando":
                    if st.button("🚚 Prontificar", key=f"pronto_{titulo_tela}_{p_id}", use_container_width=True):
                        cursor.execute("UPDATE pedidos SET status = 'Entregue' WHERE id = ?", (p_id,))
                        conn.commit()
                        st.rerun()

with aba_cozinha:
    renderizar_tela_preparo(CATEGORIAS_COZINHA, "🍳 Cozinha")

with aba_bar:
    renderizar_tela_preparo(CATEGORIAS_BAR, "🍹 Bar")

# --- 4. ABA: CONTAS ABERTAS ---
with aba_comandas:
    st.subheader("🎟️ Contas Abertas")
    cursor.execute("""
        SELECT p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as total_item
        FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id
        WHERE p.status != 'Finalizado (Pago)' ORDER BY p.mesa, pr.nome
    """)
    itens = cursor.fetchall()

    if not itens:
        st.info("Nenhuma comanda ativa.")
    else:
        df = pd.DataFrame(itens, columns=["Mesa", "Produto", "Qtd", "Preco", "Total"])
        for comanda in df["Mesa"].unique():
            df_m = df[df["Mesa"] == comanda]
            with st.container(border=True):
                st.markdown(f"### 🎫 {comanda} — Total: **R$ {df_m['Total'].sum():.2f}**")
                st.dataframe(df_m[["Produto", "Qtd", "Total"]], hide_index=True, use_container_width=True)
                if st.button(f"💵 Fechar Conta ({comanda})", key=f"f_{comanda}", use_container_width=True):
                    cursor.execute("UPDATE pedidos SET status = 'Finalizado (Pago)' WHERE mesa = ? AND status != 'Finalizado (Pago)'", (comanda,))
                    conn.commit()
                    st.success("Conta fechada!")
                    st.rerun()

# --- 5. RELATÓRIO DE VENDAS ---
with aba_relatorio:
    st.subheader("📊 Relatório de Vendas")
    cursor.execute("""
        SELECT pr.nome, p.quantidade, (p.quantidade * pr.preco) as total, p.horario
        FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'
    """)
    vendas = cursor.fetchall()

    if not vendas:
        st.info("ℹ️ Nenhuma venda finalizada ainda.")
    else:
        df_v = pd.DataFrame(vendas, columns=["Produto", "Qtd", "Total", "Horario"])
        df_v["Dia"] = pd.to_datetime(df_v["Horario"]).dt.strftime("%d/%m/%Y")
        
        dia_sel = st.selectbox("Selecione o Dia:", sorted(df_v["Dia"].unique(), reverse=True))
        df_f = df_v[df_v["Dia"] == dia_sel]
        
        st.metric("Faturamento do Dia", f"R$ {df_f['Total'].sum():.2f}")
        st.markdown("#### Itens Vendidos")
        st.dataframe(df_f.groupby("Produto")[["Qtd", "Total"]].sum().reset_index(), hide_

# --- 6. ABA DE GERÊNCIA (CARDÁPIO) ---
with aba_gerencia:
    st.subheader("⚙️ Gerenciar Cardápio")
    with st.form("cad_prod", clear_on_submit=True):
        n = st.text_input("Nome do Produto:")
        c = st.selectbox("Categoria:", TODAS_CATEGORIAS)
        p = st.number_input("Preço (R$):", min_value=0.0, format="%.2f", step=0.50)
        
        if st.form_submit_button("💾 Salvar Produto", type="primary", use_container_width=True):
            if n.strip() != "" and p > 0:
                try:
                    cursor.execute("INSERT INTO produtos (nome, categoria, preco) VALUES (?, ?, ?)", (n.strip(), c, p))
                    conn.commit()
                    st.success("Produto cadastrado!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Produto já existe.")

    st.write("---")
    cursor.execute("SELECT id, nome, categoria, preco FROM produtos ORDER BY categoria, nome")
    prods = cursor.fetchall()
    if prods:
        st.dataframe(pd.DataFrame(prods, columns=["ID", "Nome", "Categoria", "Preço"]), hide_index=True, use_container_width=True)
        
        # Remoção rápida
        dict_del = {f"{item[1]} ({item[2]})": item[0] for item in prods}
        item_del = st.selectbox("🗑️ Remover item do cardápio:", ["Selecione..."] + list(dict_del.keys()))
        if item_del != "Selecione..." and st.button("❌ Confirmar Exclusão", use_container_width=True):
            cursor.execute("DELETE FROM produtos WHERE id = ?", (dict_del[item_del],))
            conn.commit()
            st.success("Item removido!")
            st.rerun()
