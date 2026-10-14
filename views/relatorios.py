# ==============================================================================
# VIEWS/RELATORIOS.PY - PARTE 2: FINANCEIRO (CORREÇÃO DE TEXTO DAS COLUNAS)
# ==============================================================================
import streamlit as st
import pandas as pd
from core.database import ob_cx

def renderizar_abas_financeiras(empresa_id, senha_master):
    st.subheader("📈 Controle Financeiro do Turno")
    try:
        with ob_cx() as conn, conn.cursor() as cur:
            cur.execute("SELECT total, metodo_pagamento, data_pedido FROM pedidos WHERE empresa_id = %s ORDER BY data_pedido DESC;", (empresa_id,))
            dados_pedidos = cur.fetchall()
            # CORREÇÃO DEFINITIVA: Extrai estritamente o elemento [0] de texto puro da tupla
            colunas_pedidos = [str(desc[0]) for desc in cur.description] if cur.description else []
        
        df_pedidos = pd.DataFrame(dados_pedidos, columns=colunas_pedidos) if dados_pedidos else pd.DataFrame()
        
        if not df_pedidos.empty:
            df_pedidos["total"] = pd.to_numeric(df_pedidos["total"])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💵 Faturamento Bruto", f"R$ {df_pedidos['total'].sum():,.2f}")
            c2.metric("⚡ Recebido via PIX", f"R$ {df_pedidos[df_pedidos['metodo_pagamento'] == 'PIX']['total'].sum():,.2f}")
            c3.metric("💳 Recebido via Cartão", f"R$ {df_pedidos[df_pedidos['metodo_pagamento'].isin(['Crédito', 'Débito'])]['total'].sum():,.2f}")
            
            st.markdown("### 📋 Histórico Recente de Vendas")
            st.dataframe(df_pedidos, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum pedido computado no sistema até o momento.")
    except Exception as e:
        st.error(f"Erro ao carregar relatórios: {e}")

    # --- ZONA DE PERIGO PROTEGIDA ---
    st.markdown("---")
    st.subheader("🚨 Zona de Perigo (Ações Irreversíveis)")
    
    with st.expander("⚠️ Opções de Reset de Dados"):
        acao = st.selectbox(
            "Selecione o módulo que deseja apagar:", 
            ["Selecione uma opção...", "Zerar Estoque de Itens", "Excluir Todo o Cardápio", "Limpar Histórico de Caixa"]
        )
        
        if acao != "Selecione uma opção...":
            st.warning(f"Você está prestes a executar: **{acao}**.")
            senha_conf = st.text_input("🔑 Digite a Senha Master para autorizar:", type="password")
            
            if st.button("💥 Confirmar e Executar Exclusão", type="primary", use_container_width=True):
                if senha_conf.strip() == str(senha_master).strip():
                    try:
                        with ob_cx() as conn, conn.cursor() as cur:
                            if acao == "Zerar Estoque de Itens":
                                cur.execute("UPDATE produtos SET estoque = 0 WHERE empresa_id = %s;", (empresa_id,))
                            elif acao == "Excluir Todo o Cardápio":
                                cur.execute("DELETE FROM produtos WHERE empresa_id = %s;", (empresa_id,))
                            elif acao == "Limpar Histórico de Caixa":
                                cur.execute("DELETE FROM pedidos WHERE empresa_id = %s;", (empresa_id,))
                            conn.commit()
                        st.success("🎉 Dados redefinidos com sucesso!")
                        st.rerun()
                    except Exception as e: st.error(f"Falha ao limpar registros: {e}")
                else:
                    st.error("❌ Senha Master incorreta! Operação bloqueada.")
