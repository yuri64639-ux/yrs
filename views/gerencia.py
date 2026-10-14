# ==============================================================================
# VIEWS/GERENCIA.PY - INTERFACE ADMINISTRATIVA (CADASTRO EM MASSA VINCULADO)
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx

def renderizar_painel_gerencial(empresa_id, senha_master, conn_principal):
    st.title("⚙️ Painel de Controle Gerencial")
    st.write(f"Empresa ativa no terminal: **ID {empresa_id}**")
    
    aba_cad, aba_massa, aba_rel = st.tabs([
        "📝 Cadastro Individual", 
        "🍔 Cadastro em Massa (Copiar e Colar)", 
        "📊 Faturamento e Relatórios"
    ])
    
    # --- 1. CADASTRO INDIVIDUAL ---
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
                        colunas = [desc for desc in cur.description] if cur.description else []
                        
                    df = pd.DataFrame(dados, columns=colunas) if dados else pd.DataFrame()
                    
                    if not df.empty:
                        df.columns = ["ID", "Nome do Item", "Preço (R$)", "Categoria", "Estoque Atual"]
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum item cadastrado no cardápio ainda.")
                except Exception as e:
                    st.error(f"Erro ao carregar cardápio: {e}")

    # --- 2. NOVO: CADASTRO EM MASSA (COPIAR E COLAR) ---
    with aba_massa:
        st.subheader("🍔 Cadastro de Cardápio Rápido em Lote")
        st.write("Cole a sua lista de produtos abaixo seguindo o formato exato separado por vírgulas:")
        st.code("Nome do Produto, Categoria, Preço, Estoque Inicial", language="text")
        st.caption("Categorias aceitas: Bebidas, Comidas / Lanches, Sobremesas, Ingredientes / Adicionais")
        
        texto_produtos = st.text_area(
            "Cole os produtos (um por linha):",
            height=200,
            placeholder="Exemplo:\nCoca-Cola Lata, Bebidas, 6.50, 50\nX-Salada Especial, Comidas / Lanches, 22.00, 30\nPudim de Leite, Sobremesas, 8.00, 15"
        )
        
        if st.button("🔥 Importar e Vincular Lista Completa", type="primary", use_container_width=True):
            if texto_produtos.strip():
                linhas = texto_produtos.strip().split("\n")
                itens_gravados = 0
                erros = 0
                
                with ob_cx() as conn:
                    if conn:
                        try:
                            with conn.cursor() as cur:
                                for linha in linhas:
                                    if "," in linha:
                                        partes = linha.split(",")
                                        if len(partes) == 4:
                                            nome_m = partes[0].strip()
                                            cat_m = partes[1].strip()
                                            preco_m = partes[2].strip()
                                            est_m = partes[3].strip()
                                            
                                            try:
                                                preco_float = float(preco_m)
                                                estoque_int = int(est_m)
                                                
                                                cur.execute("""
                                                    INSERT INTO produtos (empresa_id, nome, preco, categoria, estoque)
                                                    VALUES (%s, %s, %s, %s, %s);
                                                """, (empresa_id, nome_m, preco_float, cat_m, estoque_int))
                                                itens_gravados += 1
                                            except ValueError:
                                                erros += 1
                                conn.commit()
                            
                            if itens_gravados > 0:
                                st.success(f"🚀 Sucesso! {itens_gravados} produtos foram processados e vinculados à sua empresa na Neon!")
                                if erros > 0:
                                    st.warning(f"⚠️ {erros} linhas continham erros de formatação e foram puladas.")
                                st.rerun()
                            else:
                                st.error("❌ Nenhum produto pôde ser cadastrado. Verifique se usou as vírgulas corretamente.")
                        except Exception as e:
                            st.error(f"Erro no lote do banco: {e}")
            else:
                st.warning("O campo de texto está vazio.")

    # --- 3. RELATÓRIOS FINANCEIROS ---
    with aba_rel:
        st.subheader("📈 Controle Financeiro e Vendas")
        with ob_cx() as conn:
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT total, metodo_pagamento, data_pedido FROM pedidos WHERE empresa_id = %s ORDER BY data_pedido DESC", (empresa_id,))
                        dados_pedidos = cur.fetchall()
                        colunas_pedidos = [desc for desc in cur.description] if cur.description else []
                        
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
