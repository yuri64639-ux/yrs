from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

# Configuração otimizada para telas verticais de celular
st.set_page_config(page_title="Sistema Mobile - Orla Bar", layout="centered")

# --- CONTROLE DE ACESSO (SENHA) ---
SENHA_CORRETA = "orla123"  # <-- Mude a senha do seu bar aqui se quiser

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔑 Acesso ao Sistema Orla Bar")
    senha_digitada = st.text_input(
        "Digite a senha do estabelecimento:", type="password"
    )
    if st.button("Entrar", type="primary", use_container_width=True):
        if senha_digitada == SENHA_CORRETA:
            st.session_state["autenticado"] = True
            st.success("Acesso liberado!")
            st.rerun()
        else:
            st.error("Senha incorreta. Tente novamente.")
    st.stop()  # Interrompe o código aqui se não estiver logado


# --- BANCO DE DADOS (CONCURRÊNCIA ATIVADA) ---
def conectar_banco():
    conn = sqlite3.connect(
        "sistema_restaurante.db", check_same_thread=False, timeout=20
    )
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

# Categorias do estabelecimento
CATEGORIAS_BAR = ["Bebidas", "Drinks"]
CATEGORIAS_COZINHA = ["Porções", "Pratos Principais", "Sobremesas"]

# --- INTERFACE MOBILE ---
st.title("📱 Gestão Orla Bar")
aba_garcom, aba_cozinha, aba_bar, aba_comandas, aba_relatorio, aba_gerencia = (
    st.tabs([
        "🏃‍♂️ Lançar",
        "🍳 Cozinha",
        "🍹 Bar",
        "🎟️ Contas",
        "📊 Relatório",
        "⚙️ Cardápio",
    ])
)

# --- 1. ABA DO GARÇOM ---
with aba_garcom:
    st.subheader("📋 Novo Pedido")

    cursor.execute(
        "SELECT DISTINCT categoria FROM produtos ORDER BY categoria"
    )
    categorias_disponiveis = [c[0] for c in cursor.fetchall() if c[0]]

    if not categorias_disponiveis:
        st.warning("⚠️ Cadastre os produtos na aba 'Cardápio' primeiro.")
    else:
        filtro_categorias = ["Todas"] + categorias_disponiveis
        categoria_selecionada = st.selectbox("📂 Categoria:", filtro_categorias)

        if categoria_selecionada == "Todas":
            cursor.execute(
                "SELECT id, nome, categoria, preco FROM produtos ORDER BY categoria, nome"
            )
        else:
            cursor.execute(
                "SELECT id, nome, categoria, preco FROM produtos WHERE categoria = ? ORDER BY nome",
                (categoria_selecionada,),
            )

        lista_produtos = cursor.fetchall()

        with st.form("form_pedido", clear_on_submit=True):
            mesa = st.text_input(
                "Mesa / Pulseira / Comanda:", placeholder="Ex: Pulseira 12"
            )

            # Correção do mapeamento estrutural do dicionário {Nome formatado: id_produto}
            dict_produtos = {
                f"{p[1]} (R$ {p[3]:.2f})": p[0] for p in lista_produtos
            }
            produto_selecionado = st.selectbox(
                "Item do Cardápio:", list(dict_produtos.keys())
            )
            quantidade = st.number_input(
                "Quantidade:", min_value=1, value=1, step=1
            )

            botao_enviar = st.form_submit_button(
                "🔥 Enviar Pedido", type="primary", use_container_width=True
            )

            if botao_enviar:
                if mesa.strip() == "":
                    st.error("Informe a mesa ou pulseira.")
                elif not produto_selecionado:
                    st.error("Selecione um produto.")
                else:
                    p_id = dict_produtos[produto_selecionado]
                    horario_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute(
                        "INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)",
                        (mesa.strip(), p_id, quantidade, horario_atual),
                    )
                    conn.commit()
                    st.success("✅ Pedido enviado!")
                    st.rerun()


# --- REUTILIZÁVEL PARA TELAS DE PREPARO ---
def renderizar_tela_preparo(categorias_alvo, titulo_tela):
    st.subheader(titulo_tela)
    if not categorias_alvo:
        st.info("Nenhuma categoria configurada.")
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
        for (
            p_id,
            p_mesa,
            pr_nome,
            p_qtd,
            p_status,
            p_horario_completo,
        ) in pedidos_ativos:
            cor_status = "🔴 Pendente" if p_status == "Pendente" else "🟡 Preparando"
            hora_exibicao = (
                p_horario_completo[11:19]
                if (p_horario_completo and len(p_horario_completo) > 10)
                else p_horario_completo
            )

            with st.container(border=True):
                st.markdown(f"**{p_mesa}** — *{hora_exibicao}*")
                st.markdown(f"### {p_qtd}x {pr_nome}")
                st.text(f"Status: {cor_status}")

                if p_status == "Pendente":
                    if st.button(
                        "👨‍🍳 Preparar",
                        key=f"prep_{titulo_tela}_{p_id}",
                        use_container_width=True,
                    ):
                        cursor.execute(
                            "UPDATE pedidos SET status = 'Preparando' WHERE id = ?",
                            (p_id,),
                        )
                        conn.commit()
                        st.rerun()
                elif p_status == "Preparando":
                    if st.button(
                        "🚚 Prontificar",
                        key=f"pronto_{titulo_tela}_{p_id}",
                        use_container_width=True,
                    ):
                        cursor.execute(
                            "UPDATE pedidos SET status = 'Entregue' WHERE id = ?",
                            (p_id,),
                        )
                        conn.commit()
                        st.rerun()


with aba_cozinha:
    renderizar_tela_preparo(CATEGORIAS_COZINHA, "🍳 Cozinha")

with aba_bar:
    renderizar_tela_preparo(CATEGORIAS_BAR, "🍹 Bar")

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
        df_consumo = pd.DataFrame(
            itens_consumidos,
            columns=[
                "Identificador",
                "Produto",
                "Quantidade",
                "Preço Unitário (R$)",
                "Total Item (R$)",
            ],
        )
        comandas_abertas = df_consumo["Identificador"].unique()

        for comanda in comandas_abertas:
            df_filtrado = df_consumo[df_consumo["Identificador"] == comanda]
            valor_total_comanda = df_filtrado["Total Item (R$)"].sum()

            with st.container(border=True):
                st.markdown(f"### 🎫 {comanda}")
                st.markdown(f"#### Total: **R$ {valor_total_comanda:.2f}**")

                st.dataframe(
                    df_filtrado[["Produto", "Quantidade", "Total Item (R$)"]],
                    hide_index=True,
                    use_container_width=True,
                )

                if st.button(
                    f"💵 Fechar Conta ({comanda})",
                    key=f"fechar_{comanda}",
                    use_container_width=True,
                ):
                    cursor.execute(
                        "UPDATE pedidos SET status = 'Finalizado (Pago)' WHERE mesa = ? AND status != 'Finalizado (Pago)'",
                        (comanda,),
                    )
                    conn.commit()
                    st.success("Conta fechada com sucesso!")
                    st.rerun()

# --- 5. RELATÓRIO SEPARADO POR DIA E MÊS ---
with aba_relatorio:
    st.subheader("📊 Relatório de Vendas")

    query_vendas = """
        SELECT pr.nome, pr.categoria, p.quantidade, pr.preco, (p.quantidade * pr.preco) as total_item, p.horario
        FROM pedidos p
        JOIN produtos pr ON p.produto_id = pr.id
        WHERE p.status = 'Finalizado (Pago)'
    """
    cursor.execute(query_vendas)
    vendas_realizadas = cursor.fetchall()

