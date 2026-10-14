# ==============================================================================
# VIEWS/GERENCIA.PY - INTERFACE DO PAINEL ADMINISTRATIVO COM SENHA
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx

def renderizar_painel_gerencial(empresa_id, senha_master):
    st.title("⚙️ Painel de Controle Gerencial")
    
    # Campo de validação antes de liberar o painel
    senha_digitada = st.text_input("🔑 Digite a Senha Master para acessar a Gerência:", type="password")
    
    if not senha_digitada:
        st.info("Insira a senha master do estabelecimento para liberar as informações financeiras e de estoque.")
        st.stop()
        
    if senha_digitada != senha_master:
        st.error("❌ Senha Master incorreta! Acesso negado.")
        st.stop()
        
    # Se a senha estiver correta, exibe o conteúdo original:
    st.success("🔓 Acesso Gerencial Autorizado.")
    
    aba_cad, aba_rel = st.tabs(["📝 Cadastrar & Estoque", "📊 Faturamento e Relatórios"])
    
    with aba_cad:
        st.subheader("🛒 Cadastro de Itens no Cardápio")
        with st.form("form_cadastro_produto", clear_on_submit=True):
            nome_prod = st.text_input("Nome do Produto / Ingrediente:").strip()
            preco_prod = st.number_input("Preço de Venda (R$):", min_value=0.0, step=0.50, format="%.2f")
            cat_prod = st.selectbox("Categoria:", ["Bebidas", "Comidas / Lanches", "Sobremesas", "Ingredientes / Adicionais"])
            est_prod = st.number_input("Estoque Inicial (Unidades/Qtd):", min_value=0, value=10, step=1)
            
            if st.form_submit_button("Salvar no Cardápio", type="primary"):
                if nome_prod:
                    try:
                        with ob_cx() as conn, conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO produtos (empresa_id, nome, preco, categoria, estoque)
                                VALUES (%s, %s, %s, %s, %s);
                            """, (empresa_id, nome_prod, preco_prod, cat_prod, est_prod))
                            conn.commit()
                        st.success(f"🎉 '{nome_prod}' adicionado ao cardápio com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    st.warning("Preencha o nome do produto.")
        
        st.subheader("📦 Itens Cadastrados Atualmente")
        with ob_cx() as conn:
            if conn:
                df = pd.read_sql("SELECT id, nome, preco, categoria, estoque FROM produtos WHERE empresa_id = %s ORDER BY nome", conn, params=(empresa_id,))
                if not df.empty:
                    df.columns = ["ID", "Nome do Item", "Preço (R$)", "Categoria", "Estoque Atual"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum item cadastrado no cardápio ainda.")

    with aba_rel:
        st.subheader("📈 Controle Financeiro e Vendas")
        with ob_cx() as conn:
            if conn:
                df_pedidos = pd.read_sql("SELECT total, metodo_pagamento, data_pedido FROM pedidos WHERE empresa_id = %s ORDER BY data_pedido DESC", conn, params=(empresa_id,))
                if not df_pedidos.empty:
                    faturamento_total = df_pedidos["total"].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("💵 Faturamento Bruto", f"R$ {faturamento_total:,.2f}")
                    
                    pix_total = df_pedidos[df_pedidos["metodo_pagamento"] == "PIX"]["total"].sum()
                    cartao_total = df_pedidos[df_pedidos["metodo_pagamento"].isin(["Crédito", "Débito"])]["total"].sum()
                    
                    c2.metric("⚡ Total via PIX", f"R$ {pix_total:,.2f}")
                    c3.metric("💳 Total via Cartão", f"R$ {cartao_total:,.2f}")
                    
                    st.markdown("### Histórico Recente de Caixa")
                    st.dataframe(df_pedidos, use_container_width=True)
                else:
                    st.info("Nenhuma venda computada neste turno até o momento.")
