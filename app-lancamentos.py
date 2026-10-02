import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO INICIAL CONFIGURADA PARA CELULAR
st.set_page_config(
    page_title="Cria Bar Mobile", 
    layout="centered",               # Mantém o conteúdo centralizado e estreito
    initial_sidebar_state="collapsed" # Esconde o menu lateral por padrão no celular
)

# Estilização CSS para melhorar o visual no celular (botões e espaçamento touch)
st.markdown("""
    <style>
        /* Aumenta os botões para facilitar o toque no celular */
        .stButton>button {
            width: 100% !important;
            height: 48px !important;
            font-size: 16px !important;
        }
        /* Ajusta o espaçamento das abas em telas pequenas */
        .stTabs [data-baseweb="tab"] {
            font-size: 14px !important;
            padding: 8px 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 2. INICIALIZAÇÃO DO BANCO DE DADOS
def iniciar_banco():
    conexao = sqlite3.connect("restaurante_financeiro.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT, tipo TEXT, categoria TEXT, valor REAL, descricao TEXT
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

# 3. INTERFACE PRINCIPAL
st.title("📱 Cria Bar Pocket")
st.markdown("Gestão rápida para o seu restaurante na palma da mão.")

# Abas compactas ideais para telas de smartphones
aba_fin, aba_card, aba_est = st.tabs(["💰 Caixa", "📋 Cardápio", "📦 Estoque"])

# --- ABA 1: GESTÃO FINANCEIRA ---
with aba_fin:
    st.subheader("Novo Lançamento")
    with st.form("form_financeiro_mobile", clear_on_submit=True):
        # Campos empilhados verticalmente para telas verticais de celular
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
            cursor.execute("INSERT INTO lancamentos (data, tipo, categoria, valor, descricao) VALUES (?, ?, ?, ?, ?)", 
                           (str(data_mov), tipo_limpo, categoria_mov, valor_mov, descricao_mov))
            conexao.commit()
            conexao.close()
            st.success("Lançamento salvo!")
            st.rerun()

    st.markdown("---")
    st.subheader("Resumo Financeiro")
    conexao = sqlite3.connect("restaurante_financeiro.db")
    df_fin = pd.read_sql_query("SELECT * FROM lancamentos ORDER BY data DESC LIMIT 20", conexao)
    conexao.close()
    
    if not df_fin.empty:
        total_rec = df_fin[df_fin["tipo"] == "Receita"]["valor"].sum()
        total_des = df_fin[df_fin["tipo"] == "Despesa"]["valor"].sum()
        saldo = total_rec - total_des
        
        # Cards de métrica simplificados
        st.metric("Saldo do Período", f"R$ {saldo:.2f}", delta=f"R$ {total_rec:.2f} Entradas")
        
        # Exibição adaptada para celular (rolagem horizontal nativa do Streamlit)
        st.dataframe(df_fin.rename(columns={"data":"Data", "tipo":"Tipo", "valor":"Valor (R$)"})[["Data", "Tipo", "Valor (R$)"]], use_container_width=True)
    else:
        st.info("Nenhum registro encontrado.")

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
    df_estoque = pd.read_sql_query("SELECT nome_item, quantidade, unidade_medida, quantidade_minima FROM estoque", conexao)
    conexao.close()
    
    if not df_estoque.empty:
        # Coluna visual simples indicando alerta
        df_estoque['Alerta'] = df_estoque.apply(lambda r: "🚨" if r['quantidade'] <= r['quantidade_minima'] else "✅", axis=1)
        st.dataframe(df_estoque.rename(columns={"nome_item":"Item", "quantidade":"Qtd", "Alerta":"Sinal"}), use_container_width=True)
