"""
VIEWS/CAIXA.PY - Módulo do Balcão de Atendimento, Extratos e Fechamento de Caixa
Centraliza o faturamento, seleção de meios de pagamento e finalização de comandas abertas.
"""

import streamlit as st
import pandas as pd
import psycopg2
from core.database import ob_cx

def renderizar_fechamento_caixa(empresa_id, senha_master, conn_principal):
    """Módulo exclusivo para fechamento, consulta de consumo e recebimento financeiro."""
    st.subheader("🧾 Balcão de Atendimento e Caixa")
    
    with ob_cx() as conn:
        if conn:
            try:
                cur = conn.cursor()
                try:
                    cur.execute("SELECT DISTINCT mesa_comanda FROM pedidos WHERE empresa_id = %s AND metodo_pagamento = 'Pendente' ORDER BY mesa_comanda;", (empresa_id,))
                    lista_mesas = [row[0] for row in cur.fetchall()]
                except:
                    conn.rollback()
                    try:
                        cur.execute("SELECT DISTINCT mesa FROM pedidos WHERE empresa_id = %s AND metodo_pagamento = 'Pendente' ORDER BY mesa;", (empresa_id,))
                        lista_mesas = [row[0] for row in cur.fetchall()]
                    except:
                        conn.rollback()
                        cur.execute("SELECT DISTINCT mesa FROM pedidos WHERE empresa_id = %s AND status = 'Pendente' ORDER BY mesa;", (empresa_id,))
                        lista_mesas = [row[0] for row in cur.fetchall()]
            except Exception as e:
                st.error(f"Erro ao ler comandas ativas: {e}")
                return

    if not lista_mesas:
        st.info("Não há nenhuma mesa ou comanda com consumo em aberto no momento.")
        return
        
    mesa_selecionada = st.selectbox("Selecione a Mesa para calcular o fechamento:", lista_mesas, key="sb_mesa_fechamento_caixa")
    
    with ob_cx() as conn:
        try:
            df_comanda = pd.read_sql("""
                SELECT id, itens, total FROM pedidos 
                WHERE empresa_id = %s AND (mesa_comanda = %s OR mesa = %s) AND metodo_pagamento = 'Pendente';
            """, conn, params=[empresa_id, mesa_selecionada, mesa_selecionada])
        except:
            try:
                # Mapeamento dinâmico alternativo para leitura relacional por ID do produto
                df_comanda = pd.read_sql("""
                    SELECT p.id, pr.nome as itens, pr.preco as total 
                    FROM pedidos p
                    JOIN produtos pr ON p.produto_id = pr.id
                    WHERE p.empresa_id = %s AND (p.mesa = %s) AND p.status = 'Pendente';
                """, conn, params=[empresa_id, mesa_selecionada])
            except:
                df_comanda = pd.DataFrame()

    if not df_comanda.empty:
        st.markdown(f"#### 📝 Extrato de Consumo: **{mesa_selecionada}**")
        total_comanda = df_comanda["total"].sum()
        
        for _, row in df_comanda.iterrows():
            st.write(f"• {row['itens']} (Subtotal: R$ {row['total']:.2f})")
            
        st.markdown(f"## **Total da Conta: R$ {total_comanda:.2f}**")
        metodo_pag = st.selectbox("Forma de Liquidação / Recebimento:", ["PIX", "Crédito", "Débito", "Dinheiro"], key="caixa_forma_pagamento_select")
        
        if st.button("💰 Finalizar e Receber Pagamento", type="primary", width='stretch', key="btn_processar_fechamento_final"):
            try:
                with ob_cx() as conn_caixa, conn_caixa.cursor() as cur:
                    try:
                        cur.execute("""
                            UPDATE pedidos 
                            SET metodo_pagamento = %s 
                            WHERE empresa_id = %s AND mesa_comanda = %s AND metodo_pagamento = 'Pendente';
                        """, (metodo_pag, empresa_id, mesa_selecionada))
                    except psycopg2.errors.UndefinedColumn:
                        conn_caixa.rollback()
                        try:
                            cur.execute("""
                                UPDATE pedidos 
                                SET metodo_pagamento = %s 
                                WHERE empresa_id = %s AND mesa = %s AND metodo_pagamento = 'Pendente';
                            """, (metodo_pag, empresa_id, mesa_selecionada))
                        except:
                            conn_caixa.rollback()
                            cur.execute("""
                                UPDATE pedidos 
                                SET status = 'Finalizado (Pago)', modo_pagamento = %s 
                                WHERE empresa_id = %s AND mesa = %s AND status = 'Pendente';
                            """, (metodo_pag, empresa_id, mesa_selecionada))
                        
                    conn_caixa.commit()
                st.success(f"✅ Conta da {mesa_selecionada} encerrada com sucesso via {metodo_pag}!")
                st.rerun()
            except Exception as error:
                st.error(f"Erro ao dar baixa no caixa: {error}")
