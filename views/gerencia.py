# ==============================================================================
# VIEWS/GERENCIA.PY - INTERFACE DO PAINEL ADMINISTRATIVO (TRANSAÇÕES BLINDADAS)
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx  # Importação local segura

def renderizar_painel_gerencial(empresa_id, senha_master, conn_principal):
    st.title("⚙️ Painel de Controle Gerencial")
    st.write(f"Empresa ativa no terminal: **ID {empresa_id}**")
    
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    st.warning("Preencha o nome do produto.")
        
        st.subheader("📦 Itens Cadastrados Atualmente")
        with ob_cx() as conn:
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id, nome, preco, categoria, estoque FROM produtos WHERE empresa_id = %s ORDER BY nome", (empresa_id,))
                        dados = cur.fetchall()
                        colunas = [desc[0] for desc in cur.description] if cur.description else []
                        
                    df = pd.DataFrame(dados, columns=colunas) if dados else pd.DataFrame()
                    
                    if not df.empty:
                        df.columns = ["ID", "Nome do Item", "Preço (R$)", "Categoria", "Estoque Atual"]
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum item cadastrado no cardápio ainda.")
                except Exception as e:
                    st.error(f"Erro ao carregar cardápio: {e}")

    with aba_rel:
        st.subheader("📈 Controle Financeiro e Vendas")
        with ob_cx() as conn:
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT total, metodo_pagamento, data_pedido FROM pedidos WHERE empresa_id = %s ORDER BY data_pedido DESC", (empresa_id,))
                        dados_pedidos = cur.fetchall()
                        colunas_pedidos = [desc[0] for desc in cur.description] if cur.description else []
                        
                    df_pedidos = pd.DataFrame(dados_pedidos, columns=colunas_pedidos) if dados_pedidos else pd.DataFrame()
                    
                    if not df_pedidos.empty:
                        df_pedidos["total"] = pd.to_numeric(df_pedidos["total"])
                        faturamento_total = df_pedidos["total"].sum()
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("💵 Faturamento Bruto", f"R$ {faturamento_total:,.2f}")
                        
                        pix_total = df_pedidos[df_pedidos["metodo_pagamento"] == "PIX"]["total"].sum()
                        cartao_total = df_pedidos[df_pedidos["metodo_pagamento"].isin(["Crédito", "Débito"])]["total"].sum()
                        
                        c2.metric("⚡ Total via PIX", f"R$ {pix_total:,.2f}")
                        c3.metric("💳 Total via Cartão", f"R$ {cartao_total:,.2f}")
                        
                        st.markdown("### Histórico Recente de Caixa")
                        st.dataframe(df_pedidos, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma venda computada neste turno até o momento.")
                except Exception as e:
                    st.error(f"Erro ao carregar relatórios: {e}")
