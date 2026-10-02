from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sistema Mobile", layout="centered")

# --- LOGIN SIMPLES ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.subheader("🔑 Acesso ao Sistema")
    if st.text_input("Senha:", type="password") == "orla123" and st.button("Entrar", type="primary", use_container_width=True):
        st.session_state["logado"] = True
        st.rerun()
    st.stop()

# --- BANCO DE DADOS ---
conn = sqlite3.connect("sistema_restaurante.db", check_same_thread=False, timeout=20)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL);
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT);
""")
conn.commit()

st.fragment(run_every=5)
CATEGORIAS = ["Bebidas", "Drinks", "Porções", "Pratos Principais", "Sobremesas"]

st.title("📱 Gestão Bar & Restaurante")
aba_garcom, aba_cozinha, aba_bar, aba_comandas, aba_relatorio, aba_gerencia = st.tabs([
    "🏃‍♂️ Lançar", "🍳 Cozinha", "🍹 Bar", "🎟️ Contas", "📊 Relatório", "⚙️ Cardápio"
])

# --- 1. LANÇAR PEDIDO ---
with aba_garcom:
    st.subheader("📋 Novo Pedido")
    cursor.execute("SELECT id, nome, preco FROM produtos ORDER BY nome")
    produtos = cursor.fetchall()
    
    if not produtos:
        st.warning("Cadastre os produtos na aba 'Cardápio' primeiro.")
    else:
        with st.form("form_pedido", clear_on_submit=True):
            mesa = st.text_input("Mesa / Comanda:")
            dict_p = {f"{p[1]} (R$ {p[2]:.2f})": p[0] for p in produtos}
            prod_sel = st.selectbox("Item:", list(dict_p.keys()))
            qtd = st.number_input("Quantidade:", min_value=1, value=1)
            
            if st.form_submit_button("🔥 Enviar", type="primary", use_container_width=True) and mesa.strip():
                cursor.execute("INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (?, ?, ?, ?)",
                               (mesa.strip(), dict_p[prod_sel], qtd, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Pedido enviado!")
                st.rerun()

# --- TELA DE PREPARO (COZINHA / BAR) ---
def tela_preparo(cats, titulo):
    st.subheader(titulo)
    cursor.execute(f"SELECT p.id, p.mesa, pr.nome, p.quantidade, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)' AND pr.categoria IN ({','.join('?'*len(cats))}) ORDER BY p.id DESC", cats)
    for p_id, mesa, nome, qtd, status in cursor.fetchall():
        with st.container(border=True):
            st.markdown(f"**{mesa}** -> ### {qtd}x {nome}")
            btn_txt = "👨‍🍳 Preparar" if status == "Pendente" else "🚚 Prontificar"
            novo_status = "Preparando" if status == "Pendente" else "Entregue"
            if st.button(btn_txt, key=f"b_{p_id}_{titulo}", use_container_width=True):
                cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, p_id))
                conn.commit()
                st.rerun()

with aba_cozinha: tela_preparo(["Porções", "Pratos Principais", "Sobremesas"], "🍳 Cozinha")
with aba_bar: tela_preparo(["Bebidas", "Drinks"], "🍹 Bar")

# --- 4. CONTAS ABERTAS ---
with aba_comandas:
    st.subheader("🎟️ Contas Abertas")
    df = pd.read_sql_query("SELECT p.mesa, pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status != 'Finalizado (Pago)'", conn)
    
    if df.empty:
        st.info("Nenhuma comanda ativa.")
    else:
        for comanda, dados in df.groupby("mesa"):
            with st.container(border=True):
                st.markdown(f"### 🎫 {comanda} — Total: **R$ {dados['Total'].sum():.2f}**")
                st.dataframe(dados[["Produto", "Qtd", "Total"]], hide_index=True, use_container_width=True)
                if st.button(f"💵 Fechar Conta", key=f"f_{comanda}", use_container_width=True):
                    cursor.execute("UPDATE pedidos SET status = 'Finalizado (Pago)' WHERE mesa = ?", (comanda,))
                    conn.commit()
                    st.rerun()

# --- 5. RELATÓRIO DE VENDAS ---
with aba_relatorio:
    st.subheader("📊 Relatório do Dia")
    df_v = pd.read_sql_query("SELECT pr.nome as Produto, p.quantidade as Qtd, (p.quantidade * pr.preco) as Total, p.horario FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.status = 'Finalizado (Pago)'", conn)
    
    if df_v.empty:
        st.info("Nenhuma venda realizada ainda.")
    else:
        df_v["Dia"] = pd.to_datetime(df_v["horario"]).dt.strftime("%d/%m/%Y")
        dia_sel = st.selectbox("Escolha o Dia:", sorted(df_v["Dia"].unique(), reverse=True))
        df_f = df_v[df_v["Dia"] == dia_sel]
        
        st.metric("Faturamento", f"R$ {df_f['Total'].sum():.2f}")
        # Correção definitiva da agregação do Pandas
        resumo = df_f.groupby("Produto", as_index=False)[["Qtd", "Total"]].sum()
        st.dataframe(resumo, hide_index=True, use_container_width=True)

# --- 6. GERENCIAR CARDÁPIO ---
with aba_gerencia:
    st.subheader("⚙️ Cardápio")
    with st.form("cad"):
        n = st.text_input("Nome:")
        c = st.selectbox("Categoria:", CATEGORIAS)
        p = st.number_input("Preço (R$):", min_value=0.0, step=0.5)
        if st.form_submit_button("💾 Salvar", use_container_width=True) and n.strip() and p > 0:
            try:
                cursor.execute("INSERT INTO produtos (nome, categoria, preco) VALUES (?, ?, ?)", (n.strip(), c, p))
                conn.commit()
                st.rerun()
            except sqlite3.IntegrityError: st.error("Produto já existe.")
            
    df_p = pd.read_sql_query("SELECT id, nome as Nome, categoria as Categoria, preco as Preço FROM produtos ORDER BY categoria, nome", conn)
    if not df_p.empty:
        st.dataframe(df_p, hide_index=True, use_container_width=True)
        item_del = st.selectbox("🗑️ Remover do cardápio:", ["Selecione..."] + df_p["Nome"].tolist())
        if item_del != "Selecione..." and st.button("❌ Confirmar Exclusão", use_container_width=True):
            cursor.execute("DELETE FROM produtos WHERE nome = ?", (item_del,))
            conn.commit()
            st.rerun()
