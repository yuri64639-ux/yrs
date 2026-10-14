import streamlit as st
import pandas as pd
from core.database import ob_cx

def renderizar_painel_gerencial(empresa_id, senha_master, conn_principal):
    st.title("⚙️ Painel de Controle Gerencial")
    st.write(f"Empresa ativa: **ID {empresa_id}**")
    
    aba_cad, aba_massa, aba_rel = st.tabs(["📝 Individual", "🍔 Em Massa", "📊 Relatórios & Reset"])
    
    with aba_cad:
        st.subheader("🛒 Cadastro de Itens")
        with st.form("form_cadastro_produto", clear_on_submit=True):
            nome_prod = st.text_input("Nome do Produto / Ingrediente:").strip()
            preco_prod = st.number_input("Preço de Venda (R$):", min_value=0.0, step=0.50, format="%.2f")
            cat_prod = st.selectbox("Categoria:", ["Bebidas", "Comidas / Lanches", "Sobremesas", "Ingredientes / Adicionais"])
            est_prod = st.number_input("Estoque Inicial:", min_value=0, value=10)
            
            if st.form_submit_button("Salvar no Cardápio", type="primary") and nome_prod:
                try:
                    with ob_cx() as conn, conn.cursor() as cur:
                        cur.execute("INSERT INTO produtos (empresa_id, nome, preco, categoria, estoque) VALUES (%s,%s,%s,%s,%s);", (empresa_id, nome_prod, preco_prod, cat_prod, est_prod))
                        conn.commit()
                    st.success(f"🎉 '{nome_prod}' adicionado!")
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
        
        st.subheader("📦 Cardápio Atual")
        with ob_cx() as conn:
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id, nome, preco, categoria, estoque FROM produtos WHERE empresa_id = %s ORDER BY nome", (empresa_id,))
                        dados = cur.fetchall()
                        colunas = [desc[0] for desc in cur.description] if cur.description else []
                    df = pd.DataFrame(dados, columns=colunas) if dados else pd.DataFrame()
                    if not df.empty:
                        df.columns = ["ID", "Nome", "Preço", "Categoria", "Estoque"]
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else: st.info("Nenhum item cadastrado.")
                except Exception as e: st.error(f"Erro: {e}")

    with aba_massa:
        st.subheader("🍔 Cadastro Rápido em Lote")
        st.code("Nome, Categoria, Preço, Estoque", language="text")
        texto_produtos = st.text_area("Cole os produtos (um por linha):", height=150, placeholder="Ex:\nCoca-Cola Lata, Bebidas, 6.50, 50\nX-Salada, Comidas / Lanches, 22.00, 30")
        
        if st.button("🔥 Importar Lista", type="primary", use_container_width=True) and texto_produtos.strip():
            linhas = texto_produtos.strip().split("\n")
            itens_gravados = 0
            with ob_cx() as conn:
                if conn:
                    try:
                        with conn.cursor() as cur:
                            for linha in linhas:
                                if "," in linha and len(partes := linha.split(",")) == 4:
                                    try:
                                        cur.execute("INSERT INTO produtos (empresa_id, nome, preco, categoria, estoque) VALUES (%s,%s,%s,%s,%s);", (empresa_id, partes[0].strip(), float(partes[2]), partes[1].strip(), int(partes[3])))
                                        itens_gravados += 1
                                    except: pass
                            conn.commit()
                        if itens_gravados > 0:
                            st.success(f"🚀 Sucesso! {itens_gravados} produtos vinculados!")
                            st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

    with aba_rel:
        st.subheader("📈 Controle Financeiro")
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
                        c1, c2, c3 = st.columns(3)
                        c1.metric("💵 Faturamento", f"R$ {df_pedidos['total'].sum():,.2f}")
                        c2.metric("⚡ PIX", f"R$ {df_pedidos[df_pedidos['metodo_pagamento'] == 'PIX']['total'].sum():,.2f}")
                        c3.metric("💳 Cartão", f"R$ {df_pedidos[df_pedidos['metodo_pagamento'].isin(['Crédito', 'Débito'])]['total'].sum():,.2f}")
                        st.dataframe(df_pedidos, use_container_width=True, hide_index=True)
                    else: st.info("Nenhuma venda computada.")
                except Exception as e: st.error(f"Erro: {e}")

        st.markdown("---")
        st.subheader("🚨 Zona de Perigo")
        with st.expander("⚠️ Opções de Reset de Dados"):
            acao = st.selectbox("O que deseja apagar?", ["Selecione...", "Zerar Estoque", "Apagar Cardápio", "Limpar Faturamento"])
            if acao != "Selecione...":
                senha_conf = st.text_input("🔑 Senha Master para autorizar:", type="password")
                if st.button("💥 Confirmar Exclusão", type="primary") and senha_conf.strip() == str(senha_master).strip():
                    try:
                        with ob_cx() as conn, conn.cursor() as cur:
                            if acao == "Zerar Estoque": cur.execute("UPDATE produtos SET estoque = 0 WHERE empresa_id = %s;", (empresa_id,))
                            elif acao == "Apagar Cardápio": cur.execute("DELETE FROM produtos WHERE empresa_id = %s;", (empresa_id,))
                            elif acao == "Limpar Faturamento": cur.execute("DELETE FROM pedidos WHERE empresa_id = %s;", (empresa_id,))
                            conn.commit()
                        st.success("🎉 Dados redefinidos!")
                        st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")
