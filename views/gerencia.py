"""
VIEWS/GERENCIA.PY - Painel de Controle e Gestão Protegido por Senha Master
Garante proteção de dados nas abas de inventário, cargas em massa e auditoria financeira.
"""

import streamlit as st
import pandas as pd
import psycopg2
from core.database import ob_cx
from views.relatorios import renderizar_abas_financeiras

def renderizar_painel_gerencial(empresa_id, senha_master, conn_principal):
    st.title("⚙️ Painel de Controle Gerencial")
    st.markdown(f"Estabelecimento Ativo: **ID {empresa_id}**")
    st.markdown("---")
    
    # --- BARREIRA DE SEGURANÇA INTERNA ---
    st.subheader("🔑 Autenticação Administrativa")
    senha_digitada = st.text_input(
        "Insira a Senha Master do Estabelecimento para liberar as ferramentas de gestão:", 
        type="password", 
        placeholder="Senha Master"
    )
    
    if not senha_digitada:
        st.info("🔒 Insira a sua senha para visualizar o estoque, cadastros e relatórios.")
        st.stop()
        
    if senha_digitada != senha_master:
        st.error("❌ Senha Master incorreta! Acesso negada às ferramentas de auditoria e inventário.")
        st.stop()
        
    # --- SEÇÃO LIBERADA APENAS COM SENHA VÁLIDA ---
    st.success("🔓 Autenticação efetuada com sucesso! Painel de controle liberado.")
    
    aba_est, aba_cad, aba_massa, aba_financeira = st.tabs([
        "📦 Estoque Atual",
        "📝 Cadastro Individual", 
        "🍔 Importação em Massa", 
        "📊 Relatórios & Faturamento"
    ])
    
    # --- 1. VISUALIZAÇÃO DE ESTOQUE ---
    with aba_est:
        st.subheader("📦 Itens Cadastrados no Estoque")
        try:
            with ob_cx() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nome, preco, category, estoque FROM produtos WHERE empresa_id = %s ORDER BY nome;", 
                    (empresa_id,)
                )
                dados = cur.fetchall()
                colunas = [str(desc[0]) for desc in cur.description] if cur.description else []
                
            df = pd.DataFrame(dados, columns=colunas) if dados else pd.DataFrame()
            if not df.empty:
                df.columns = ["ID", "Nome do Item", "Preço (R$)", "Categoria", "Estoque Atual"]
                st.dataframe(df, width='stretch', hide_index=True)
            else: 
                st.info("Nenhum item localizado no estoque desta empresa.")
        except Exception as error: 
            st.error(f"Erro ao carregar cardápio e estoque: {error}")
    
    # --- 2. CADASTRO INDIVIDUAL ---
    with aba_cad:
        st.subheader("🛒 Adicionar Item ao Cardápio")
        with st.form("form_cadastro_produto", clear_on_submit=True):
            nome_prod = st.text_input("Nome do Produto / Ingrediente:").strip()
            preco_prod = st.number_input("Preço de Venda (R$):", min_value=0.0, step=0.50, format="%.2f")
            cat_prod = st.selectbox("Categoria:", ["Bebidas", "Comidas / Lanches", "Sobremesas", "Ingredientes / Adicionais"])
            est_prod = st.number_input("Estoque Inicial (Unidades):", min_value=0, value=10, step=1)
            
            if st.form_submit_button("Salvar no Cardápio", type="primary"):
                if not nome_prod:
                    st.error("Insira um nome válido para o produto.")
                else:
                    try:
                        with ob_cx() as conn, conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO produtos (empresa_id, nome, preco, categoria, estoque) 
                                VALUES (%s, %s, %s, %s, %s);
                                """, 
                                (empresa_id, nome_prod, preco_prod, cat_prod, est_prod)
                            )
                            conn.commit()
                        st.success(f"🎉 '{nome_prod}' adicionado com sucesso!")
                        st.rerun()
                    except Exception as error: 
                        st.error(f"Erro ao salvar produto: {error}")

    # --- 3. CADASTRO EM MASSA ---
    with aba_massa:
        st.subheader("🍔 Cadastro de Cardápio em Lote")
        st.code("Nome do Produto, Categoria, Preço, Estoque", language="text")
        texto_produtos = st.text_area(
            "Cole os itens aqui (um por linha):", 
            height=150, 
            placeholder="Exemplo:\nCoca-Cola Lata, Bebidas, 6.50, 50\nX-Salada Especial, Comidas / Lanches, 22.00, 30"
        )
        
        if st.button("🔥 Importar Lista Completa", type="primary", width='stretch'):
            if not texto_produtos.strip():
                st.warning("O campo de texto está vazio.")
            else:
                linhas = texto_produtos.strip().split("\n")
                itens_gravados = 0
                try:
                    with ob_cx() as conn, conn.cursor() as cur:
                        for linha in linhas:
                            partes = [p.strip() for p in linha.split(",")]
                            if len(partes) == 4:
                                try:
                                    cur.execute(
                                        """
                                        INSERT INTO produtos (empresa_id, nome, categoria, preco, estoque) 
                                        VALUES (%s, %s, %s, %s, %s);
                                        """, 
                                        (empresa_id, partes[0], partes[1], float(partes[2]), int(partes[3]))
                                    )
                                    itens_gravados += 1
                                except ValueError:
                                    continue
                        conn.commit()
                        
                    if itens_gravados > 0:
                        st.success(f"🚀 Sucesso! {itens_gravados} produtos importados e vinculados!")
                        st.rerun()
                    else:
                        st.error("Nenhuma linha estava no formato correto solicitado.")
                except Exception as error: 
                    st.error(f"Erro estrutural na importação em lote: {error}")

    # --- 4. RELATÓRIOS FINANCEIROS ACESSADOS COM SEGURANÇA ---
    with aba_financeira:
        renderizar_abas_financeiras(empresa_id, senha_master)
