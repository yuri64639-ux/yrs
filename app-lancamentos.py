import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time

# 1. CONFIGURAÇÃO INICIAL CONFIGURADA PARA CELULAR
st.set_page_config(
    page_title="Cria Bar - Multi-Garçom", 
    layout="centered",               
    initial_sidebar_state="collapsed" 
)

# Injeta a atualização automática de 5 segundos no app usando fragmentos nativos
if "contador_refresh" not in st.session_state:
    st.session_state.contador_refresh = 0

# Estilização CSS para o celular
st.markdown("""
    <style>
        .stButton>button { width: 100% !important; height: 48px !important; font-size: 16px !important; }
        .stTabs [data-baseweb="tab"] { font-size: 14px !important; padding: 8px 10px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DO BANCO DE DADOS (Agora com a coluna 'garcom')
def iniciar_banco():
    conexao = sqlite3.connect("restaurante_financeiro.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT, tipo TEXT, categoria TEXT, valor REAL, descricao TEXT, garcom TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, categoria TEXT, preco REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome_item TEXT UNIQUE, quantidade REAL, unidade_medida TEXT, quantidade_minima REAL
        )
    """)
    conexao.commit()
    conexao.close()

iniciar_banco()

# 3. IDENTIFICAÇÃO DO USUÁRIO (Obrigatório para os Garçons)
st.title("📱 Cria Bar Coletivo")

nome_garcom = st.text_input("👤 Nome do Garçom / Operador", value="Balcão").strip()

if not nome_garcom:
    st.warning("⚠️ Por favor, digite seu nome para liberar os lançamentos.")
    st.stop()

# Abas do aplicativo
aba_fin, aba_card, aba_est = st.tabs(["💰 Lançar Caixa", "📋 Cardápio", "📦 Estoque"])

# --- ABA 1: GESTÃO FINANCEIRA ---
with aba_fin:
    st.subheader("Novo Lançamento")
    with st.form("form_financeiro_mobile", clear_on_submit=True):
        data_mov = st.date_input("Data", datetime.now())
        tipo_mov = st.selectbox("Tipo de Operação", ["Receita (Entrada)", "Despesa (Saída)"])
        valor_mov = st.number_input("Valor (R$)", min_value=0.01, step=1.00, format="%.2f")
        
        if "Receita" in tipo_mov:
            categoria_mov = st.selectbox("Categoria", ["Salão / Mesas", "Delivery", "Balcão", "Eventos"])
        else:
            categoria_mov = st.selectbox("Categoria", ["Insumos", "Bebidas", "Funcionários", "Estrutura", "Marketing"])
            
        descricao_mov = st.text_input("Descrição / Notas")
        botao_salvar = st.form_submit_button("Confirmar Lançamento")
        
        if botao_salvar:
            tipo_limpo = "Receita" if "Receita" in tipo_mov else "Despesa"
            conexao = sqlite3.connect("restaurante_financeiro.db")
            cursor = conexao.cursor()
            cursor.execute("""
                INSERT INTO lancamentos (data, tipo, categoria, valor, descricao, garcom) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(data_mov), tipo_limpo, categoria_mov, valor_mov, descricao_mov, nome_garcom))
            conexao.commit()
            conexao.close()
            st.success(f"Lançamento registrado por {nome_garcom}!")
            st.rerun()

    st.markdown("---")
    
    # TRECHO AUTO-ATUALIZÁVEL (Painel de Resumo)
    st.subheader("Resumo do Caixa (Sincronizado)")
    
    # Criamos um fragmento isolado que recarrega os dados dinamicamente
    @st.fragment(run_every=5)
    def renderizar_dados_atualizados():
        conexao = sqlite3.connect("restaurante_financeiro.db")
        df_fin = pd.read_sql_query("SELECT data, tipo, valor, garcom FROM lancamentos ORDER BY id DESC LIMIT 10", conexao)
        conexao.close()
        
        if not df_fin.empty:
            total_rec = df_fin[df_fin["tipo"] == "Receita"]["valor"].sum()
            st.caption(f"🔄 Última sincronização automática em tempo real: {datetime.now().strftime('%H:%M:%S')}")
            
            # Tabela adaptada para rolar no celular mostrando o garçom responsável
            df_formatado = df_fin.rename(columns={"data":"Data", "tipo":"Tipo", "valor":"R$", "garcom":"Por"})
            st.dataframe(df_formatado, use_container_width=True, hide_index=True)
        else:
            st.info("Aguardando os primeiros lançamentos dos garçons...")

    renderizar_dados_atualizados()

# --- ABA 2: GERENCIAR CARDÁPIO ---
with aba_card:
    st.subheader("Cadastrar Item e Preço")
    with st.form("form_cardapio_mobile", clear_on_submit=True):
        nome_prod = st.text_input("Nome do Produto").strip()
        cat_prod = st.selectbox("Categoria", ["Pratos", "Bebidas", "Porções", "Sobremesas"])
        preco_prod = st.number_input("Preço de Venda (R$)", min_value=0.00, step=0.50, format="%.2f")
        
        botao_prod = st.form_submit_button("Adicionar ao Cardápio")
        if botao_prod and nome_prod != "":
            try:
                conexao = sqlite3.connect("restaurante_financeiro.db")
                cursor = conexao.cursor()
                cursor.execute("INSERT INTO produtos (nome, categoria, preco) VALUES (?, ?, ?)", (nome_prod, cat_prod, preco_prod))
                conexao.commit()
                conexao.close()
                st.success(f"'{nome_prod}' adicionado!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Item já existente!")

    st.markdown("---")
    conexao = sqlite3.connect("restaurante_financeiro.db")
    df_prod = pd.read_sql_query("SELECT nome, preco FROM produtos ORDER BY nome", conexao)
    conexao.close()
    if not df_prod.empty:
        st.dataframe(df_prod.rename(columns={"nome":"Item", "preco":"Preço (R$)"}), use_container_width=True)

# --- ABA 3: CONTROLE DE ESTOQUE ---
with aba_est:
    st.subheader("Cadastro de Estoque")
    with st.form("form_estoque_mobile", clear_on_submit=True):
        item_est = st.text_input("Nome do Insumo").strip()
        unidade_est = st.selectbox("Unidade", ["un", "kg", "L", "pct"])
        qtd_inicial = st.number_input("Estoque Atual", min_value=0.0, step=1.0)
        qtd_minima = st.number_input("Aviso Mínimo", min_value=0.0, step=1.0)
        
        botao_est = st.form_submit_button("Salvar Insumo")
        if botao_est and item_est != "":
            try:
                conexao = sqlite3.connect("restaurante_financeiro.db")
                cursor = conexao.cursor()
                cursor.execute("INSERT INTO estoque (nome_item, quantidade, unidade_medida, quantidade_minima) VALUES (?, ?, ?, ?)", 
                               (item_est, qtd_inicial, unidade_est, qtd_minima))
                conexao.commit()
                conexao.close()
                st.success(f"'{item_est}' monitorado!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Item já monitorado!")

    st.markdown("---")
    st.subheader("Lista de Insumos")
    conexao = sqlite3.connect("restaurante_financeiro.db")
    df_estoque = pd.read_sql_query("SELECT nome_item, quantidade, quantidade_minima FROM estoque", conexao)
    conexao.close()
    
    if not df_estoque.empty:
        df_estoque['Sinal'] = df_estoque.apply(lambda r: "🚨" if r['quantidade'] <= r['quantidade_minima'] else "✅", axis=1)
        st.dataframe(df_estoque.rename(columns={"nome_item":"Item", "quantidade":"Qtd"}), use_container_width=True)

