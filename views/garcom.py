# ==============================================================================
# VIEWS/GARCOM.PY - INTERFACE DO TERMINAL DE PEDIDOS
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx

def renderizar_terminal_garcom(empresa_id, senha_master):
    st.subheader("📱 Terminal Operacional (Garçom / Caixa)")
    
    # Inicializa o carrinho na sessão do Streamlit se não existir
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []
        
    # --- Identificação do Pedido ---
    mesa_ou_comanda = st.text_input("📍 Identificação (Nº da Mesa ou Comanda):", placeholder="Ex: Mesa 04").strip()
    
    st.markdown("---")
    
    # --- Lupa de Busca e Seleção de Itens ---
    st.markdown("### 🔍 Pesquisar no Cardápio")
    busca = st.text_input("Digite o nome ou categoria do item:", placeholder="Ex: Coca, Batata...").strip()
    
    with ob_cx() as conn:
        if conn:
            if busca:
                df_busca = pd.read_sql("SELECT id, nome, preco, categoria, estoque FROM produtos WHERE empresa_id = %s AND (LOWER(nome) LIKE LOWER(%s) OR LOWER(categoria) LIKE LOWER(%s)) AND estoque > 0", conn, params=(empresa_id, f"%{busca}%", f"%{busca}%"))
            else:
                df_busca = pd.read_sql("SELECT id, nome, preco, categoria, estoque FROM produtos WHERE empresa_id = %s AND estoque > 0 LIMIT 8", conn, params=(empresa_id,))
            
            if not df_busca.empty:
                for _, row in df_busca.iterrows():
                    col_nome, col_add = st.columns([3, 1])
                    col_nome.write(f"**{row['nome']}** - R$ {row['preco']:.2f} *(Estoque: {row['estoque']} un)*")
                    if col_add.button(f"➕ Adicionar", key=f"add_{row['id']}"):
                        st.session_state.carrinho.append({
                            "id": row["id"],
                            "nome": row["nome"],
                            "preco": float(row["preco"])
                        })
                        st.toast(f"'{row['nome']}' colocado no carrinho!")
                        st.rerun()
            else:
                st.info("Nenhum produto localizado ou estoque zerado.")

    st.markdown("---")

    # --- Carrinho Corrente e Fechamento ---
    st.markdown("### 🛒 Sacola / Carrinho Corrente")
    if st.session_state.carrinho:
        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        total_conta = df_carrinho["preco"].sum()
        
        # Agrupa itens repetidos visualmente para o garçom
        resumo_carrinho = df_carrinho["nome"].value_counts()
        for item_nome, qtd in resumo_carrinho.items():
            st.write(f"• **{qtd}x** {item_nome}")
            
        st.markdown(f"## **Total Geral: R$ {total_conta:.2f}**")
        
        # Modos de Pagamento Originais
        metodo_pag = st.selectbox("Forma de Liquidação / Pagamento:", ["PIX", "Crédito", "Débito", "Dinheiro"])
        
        col_cancelar, col_fechar = st.columns(2)
        
        if col_cancelar.button("🗑️ Limpar Sacola", use_container_width=True):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_fechar.button("✅ Confirmar e Enviar Pedido", type="primary", use_container_width=True):
            if not mesa_ou_comanda:
                st.error("Por favor, preencha o número da Mesa ou Comanda antes de fechar!")
            else:
                try:
                    texto_itens = ", ".join([f"{qtd}x {nome}" for nome, qtd in resumo_carrinho.items()])
                    
                    with ob_cx() as conn, conn.cursor() as cur:
                        # 1. Salva o faturamento líquido e dados na tabela de pedidos
                        cur.execute("""
                            INSERT INTO pedidos (empresa_id, mesa_comanda, itens, total, metodo_pagamento)
                            VALUES (%s, %s, %s, %s, %s);
                        """, (empresa_id, mesa_ou_comanda, texto_itens, total_conta, metodo_pag))
                        
                        # 2. Atualiza a baixa automática de estoque de cada item comprado
                        for item in st.session_state.carrinho:
                            cur.execute("UPDATE produtos SET estoque = estoque - 1 WHERE id = %s", (item["id"],))
                            
                        conn.commit()
                        
                    st.success(f"🚀 Pedido da {mesa_ou_comanda} computado com sucesso na Neon!")
                    st.session_state.carrinho = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar baixa de pedido: {e}")
    else:
        st.info("O carrinho está vazio. Adicione itens acima.")
