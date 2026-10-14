"""
VIEWS/GARCOM.PY - Terminal Operacional para Garçons e Lançamentos
Implementa compatibilidade adaptativa para colunas variantes do PostgreSQL (mesa/mesa_comanda).
"""

import streamlit as st
import pandas as pd
from core.database import ob_cx

def renderizar_terminal_garcom(empresa_id, senha_master, conn_principal):
    st.subheader("📱 Terminal Operacional (Garçom / Caixa)")
    
    liberado = st.checkbox("🔓 Ativar Modo Garçom (Uso exclusivo da equipe)")
    if not liberado:
        st.info("Marque a caixa acima para ativar a tela de lançamentos do restaurante.")
        st.stop()
        
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []
        
    mesa_ou_comanda = st.text_input("📍 Identificação (Nº da Mesa ou Comanda):", placeholder="Ex: Mesa 04").strip()
    st.markdown("---")
    
    st.markdown("### 🔍 Pesquisar no Cardápio")
    busca = st.text_input("Digite o nome ou categoria do item:", placeholder="Ex: Coca, Batata...").strip()
    
    with ob_cx() as conn:
        if conn:
            try:
                with conn.cursor() as cur:
                    if busca:
                        cur.execute("""
                            SELECT id, nome, preco, categoria, estoque 
                            FROM produtos 
                            WHERE empresa_id = %s 
                              AND (LOWER(nome) LIKE LOWER(%s) OR LOWER(categoria) LIKE LOWER(%s)) 
                              AND estoque > 0
                            ORDER BY nome;
                        """, (empresa_id, f"%{busca}%", f"%{busca}%"))
                    else:
                        cur.execute("""
                            SELECT id, nome, preco, categoria, estoque 
                            FROM produtos 
                            WHERE empresa_id = %s 
                              AND estoque > 0 
                            ORDER BY nome
                            LIMIT 8;
                        """, (empresa_id,))
                    
                    dados_busca = cur.fetchall()
                    colunas = [str(desc[0]) for desc in cur.description] if cur.description else []
                    
                df_busca = pd.DataFrame(dados_busca, columns=colunas) if dados_busca else pd.DataFrame()
                
                if not df_busca.empty:
                    for _, row in df_busca.iterrows():
                        col_nome, col_add = st.columns(2)
                        col_nome.write(f"**{row['nome']}** - R$ {row['preco']:.2f} *(Estoque: {row['estoque']} un)*")
                        if col_add.button(f"➕ Adicionar", key=f"add_{row['id']}"):
                            st.session_state.carrinho.append({
                                "id": int(row["id"]),
                                "nome": str(row["nome"]),
                                "preco": float(row["preco"])
                            })
                            st.toast(f"'{row['nome']}' colocado no carrinho!")
                            st.rerun()
                else:
                    st.info("Nenhum produto localizado com estoque disponível.")
            except Exception as error:
                st.error(f"Erro temporário de sincronização de dados: {error}")

    st.markdown("---")

    st.markdown("### 🛒 Sacola / Carrinho Corrente")
    if st.session_state.carrinho:
        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        total_conta = df_carrinho["preco"].sum()
        
        resumo_carrinho = df_carrinho["nome"].value_counts()
        for item_nome, qtd in resumo_carrinho.items():
            st.write(f"• **{qtd}x** {item_nome}")
            
        st.markdown(f"## **Total Geral: R$ {total_conta:.2f}**")
        metodo_pag = st.selectbox("Forma de Liquidação / Pagamento:", ["PIX", "Crédito", "Débito", "Dinheiro"])
        
        col_cancelar, col_fechar = st.columns(2)
        
        if col_cancelar.button("🗑️ Limpar Sacola", width='stretch'):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_fechar.button("✅ Confirmar e Enviar Pedido", type="primary", width='stretch'):
            if not mesa_ou_comanda:
                st.error("Por favor, preencha o número da Mesa ou Comanda antes de finalizar!")
            else:
                try:
                    texto_itens = ", ".join([f"{qtd}x {nome}" for nome, qtd in resumo_carrinho.items()])
                    with ob_cx() as conn_venda:
                        if conn_venda:
                            with conn_venda.cursor() as cur:
                                try:
                                    # Estrutura 1: Tenta mapear o modelo 'mesa_comanda'
                                    cur.execute("""
                                        INSERT INTO pedidos (empresa_id, mesa_comanda, itens, total, metodo_pagamento)
                                        VALUES (%s, %s, %s, %s, %s);
                                    """, (empresa_id, mesa_ou_comanda, texto_itens, total_conta, metodo_pag))
                                except psycopg2.errors.UndefinedColumn:
                                    # Estrutura 2: Fallback automático se a coluna correta no banco for 'mesa'
                                    conn_venda.rollback()
                                    cur.execute("""
                                        INSERT INTO pedidos (empresa_id, mesa, itens, total, metodo_pagamento)
                                        VALUES (%s, %s, %s, %s, %s);
                                    """, (empresa_id, mesa_ou_comanda, texto_itens, total_conta, metodo_pag))
                                
                                # Processamento sequencial de baixa de inventário
                                for item in st.session_state.carrinho:
                                    cur.execute("""
                                        UPDATE produtos 
                                        SET estoque = estoque - 1 
                                        WHERE id = %s AND empresa_id = %s;
                                    """, (item["id"], empresa_id))
                                    
                                conn_venda.commit()
                                
                            st.success(f"🚀 Pedido da {mesa_ou_comanda} computado com sucesso na Neon!")
                            st.session_state.carrinho = []
                            st.rerun()
                except Exception as error:
                    st.error(f"Erro ao processar baixa de pedido: {error}")
    else:
        st.info("O carrinho está vazio.")
