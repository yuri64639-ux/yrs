# ==============================================================================
# VIEWS/GERENCIA.PY - PARTE 1: CADASTROS (PRODUTOS E EM MASSA)
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx
from views.relatorios import renderizar_abas_financeiras  # Importa a parte 2

def renderizar_painel_gerencial(empresa_id, senha_master, conn_principal):
    st.title("⚙️ Painel de Controle Gerencial")
    st.markdown(f"Estabelecimento Ativo: **ID {empresa_id}**")
    st.markdown("---")
    
    aba_cad, aba_massa, aba_financeira = st.tabs([
        "📝 Cadastro Individual", 
        "🍔 Importação em Massa", 
        "📊 Relatórios & Zona de Perigo"
    ])
    
    # --- 1. CADASTRO INDIVIDUAL ---
    with aba_cad:
        st.subheader("🛒 Adicionar Item ao Cardápio")
        with st.form("form_cadastro_produto", clear_on_submit=True):
            nome_prod = st.text_input("Nome do Produto / Ingrediente:").strip()
            preco_prod = st.number_input("Preço de Venda (R$):", min_value=0.0, step=0.50, format="%.2f")
            cat_prod = st.selectbox("Categoria:", ["Bebidas", "Comidas / Lanches", "Sobremesas", "Ingredientes / Adicionais"])
            est_prod = st.number_input("Estoque Inicial (Unidades):", min_value=0, value=10, step=1)
            
            if st.form_submit_button("Salvar no Cardápio", type="primary") and nome_prod:
                try:
                    with ob_cx() as conn, conn.cursor() as cur:
                        cur.execute("INSERT INTO produtos (empresa_id, nome, preco, categoria, estoque) VALUES (%s,%s,%s,%s,%s);", (empresa_id, nome_prod, preco_prod, cat_prod, est_prod))
                        conn.commit()
                    st.success(f"🎉 '{nome_prod}' adicionado!")
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
        
        st.markdown("---")
        st.subheader("📦 Itens Cadastrados no Estoque")
        try:
            with ob_cx() as conn, conn.cursor() as cur:
                cur.execute("SELECT id, nome, preco, categoria, estoque FROM produtos WHERE empresa_id = %s ORDER BY nome;", (empresa_id,))
                dados = cur.fetchall()
                colunas = [desc[0] for desc in cur.description] if cur.description else []
            df = pd.DataFrame(dados, columns=colunas) if dados else pd.DataFrame()
            if not df.empty:
                df.columns = ["ID", "Nome do Item", "Preço (R$)", "Categoria", "Estoque Atual"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: st.info("Nenhum item localizado no cardápio.")
        except Exception as e: st.error(f"Erro ao carregar cardápio: {e}")

    # --- 2. CADASTRO EM MASSA ---
    with aba_massa:
        st.subheader("🍔 Cadastro de Cardápio em Lote")
        st.code("Nome do Produto, Categoria, Preço, Estoque", language="text")
        texto_produtos = st.text_area("Cole os itens aqui (um por linha):", height=150, placeholder="Exemplo:\nCoca-Cola Lata, Bebidas, 6.50, 50\nX-Salada Especial, Comidas / Lanches, 22.00, 30")
        
        if st.button("🔥 Importar Lista Completa", type="primary", use_container_width=True) and texto_produtos.strip():
            linhas = texto_produtos.strip().split("\n")
            itens_gravados = 0
            try:
                with ob_cx() as conn, conn.cursor() as cur:
                    for linha in linhas:
                        if "," in linha and len(partes := [p.strip() for p in linha.split(",")]) == 4:
                            try:
                                cur.execute("INSERT INTO produtos (empresa_id, nome, categoria, preco, estoque) VALUES (%s,%s,%s,%s,%s);", (empresa_id, partes[0], partes[1], float(partes[2]), int(partes[3])))
                                itens_gravados += 1
                            except: continue
                    conn.commit()
                if itens_gravados > 0:
                    st.success(f"🚀 Sucesso! {itens_gravados} produtos vinculados!")
                    st.rerun()
            except Exception as e: st.error(f"Erro na importação: {e}")

    # --- 3. ACESSA A SEGUNDA PARTE (FINANCEIRO E RESET) ---
    with aba_financeira:
        renderizar_abas_financeiras(empresa_id, senha_master)
