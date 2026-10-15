
"""
VIEWS/RELATORIOS.PY - Controle Financeiro e Auditoria
Mantém relatórios de vendas e ações administrativas protegidas.
"""

import logging

import pandas as pd
import streamlit as st

from core.database import ob_cx

logger = logging.getLogger(__name__)


def renderizar_abas_financeiras(empresa_id, senha_master):
    st.subheader("📈 Controle Financeiro do Turno")

    # -----------------------------------------------------
    # RELATÓRIOS FINANCEIROS
    # -----------------------------------------------------
    conn = None

    try:
        conn = ob_cx()

        if conn is None:
            st.error(
                "Banco de dados indisponível. "
                "Não foi possível carregar os relatórios."
            )
        else:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO public;")

                cur.execute(
                    """
                    SELECT total, metodo_pagamento, data_pedido
                    FROM pedidos
                    WHERE empresa_id = %s
                    ORDER BY data_pedido DESC;
                    """,
                    (empresa_id,)
                )

                dados_pedidos = cur.fetchall()

                colunas_pedidos = [
                    str(desc[0])
                    for desc in cur.description
                ] if cur.description else []

            df_pedidos = pd.DataFrame(
                dados_pedidos,
                columns=colunas_pedidos
            ) if dados_pedidos else pd.DataFrame(
                columns=[
                    "total",
                    "metodo_pagamento",
                    "data_pedido"
                ]
            )

            if not df_pedidos.empty:
                df_pedidos["total"] = pd.to_numeric(
                    df_pedidos["total"],
                    errors="coerce"
                ).fillna(0)

                df_pedidos["metodo_pagamento"] = (
                    df_pedidos["metodo_pagamento"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

                faturamento_bruto = df_pedidos["total"].sum()

                recebido_pix = df_pedidos.loc[
                    df_pedidos["metodo_pagamento"].str.upper() == "PIX",
                    "total"
                ].sum()

                recebido_cartao = df_pedidos.loc[
                    df_pedidos["metodo_pagamento"].str.casefold().isin(
                        ["crédito", "débito"]
                    ),
                    "total"
                ].sum()

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "💵 Faturamento Bruto",
                    f"R$ {faturamento_bruto:,.2f}"
                )

                c2.metric(
                    "⚡ Recebido via PIX",
                    f"R$ {recebido_pix:,.2f}"
                )

                c3.metric(
                    "💳 Recebido via Cartão",
                    f"R$ {recebido_cartao:,.2f}"
                )

                st.markdown("### 📋 Histórico Recente de Vendas")

                st.dataframe(
                    df_pedidos,
                    width="stretch",
                    hide_index=True
                )

            else:
                st.info(
                    "Nenhum pedido computado no sistema "
                    "até o momento."
                )

    except Exception:
        logger.exception(
            "Erro ao carregar relatórios da empresa %s.",
            empresa_id
        )

        st.error(
            "Erro ao carregar os relatórios financeiros. "
            "Verifique a conexão com o banco."
        )

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # -----------------------------------------------------
    # ZONA DE PERIGO
    # -----------------------------------------------------
    st.markdown("---")
    st.subheader("🚨 Zona de Perigo (Ações Irreversíveis)")

    with st.expander("⚠️ Opções de Reset de Dados"):
        acao = st.selectbox(
            "Selecione o módulo que deseja apagar:",
            [
                "Selecione uma opção...",
                "Zerar Estoque de Itens",
                "Excluir Todo o Cardápio",
                "Limpar Histórico de Caixa"
            ],
            key="acao_reset_relatorios"
        )

        if acao != "Selecione uma opção...":
            st.warning(
                f"Você está prestes a executar: **{acao}**."
            )

            senha_conf = st.text_input(
                "🔑 Digite a Senha Master para autorizar:",
                type="password",
                key="senha_confirmacao_reset"
            )

            confirmar = st.checkbox(
                "Confirmo que compreendo que esta ação pode ser irreversível.",
                key="confirmacao_reset_relatorios"
            )

            if st.button(
                "💥 Confirmar e Executar Exclusão",
                type="primary",
                width="stretch",
                key="btn_confirmar_reset_relatorios"
            ):
                if not senha_conf:
                    st.error(
                        "Digite a senha master para continuar."
                    )

                elif senha_conf.strip() != str(senha_master).strip():
                    st.error(
                        "❌ Senha Master incorreta! "
                        "Operação bloqueada."
                    )

                elif not confirmar:
                    st.error(
                        "Marque a confirmação antes de executar."
                    )

                elif not empresa_id:
                    st.error(
                        "Empresa não identificada. "
                        "Operação cancelada."
                    )

                else:
                    conn_reset = None

                    try:
                        conn_reset = ob_cx()

                        if conn_reset is None:
                            st.error(
                                "Banco de dados indisponível. "
                                "Nenhuma alteração foi confirmada."
                            )
                        else:
                            with conn_reset.cursor() as cur:
                                cur.execute(
                                    "SET search_path TO public;"
                                )

                                if acao == "Zerar Estoque de Itens":
                                    cur.execute(
                                        """
                                        UPDATE produtos
                                        SET estoque = 0
                                        WHERE empresa_id = %s;
                                        """,
                                        (empresa_id,)
                                    )

                                elif acao == "Excluir Todo o Cardápio":
                                    cur.execute(
                                        """
                                        DELETE FROM produtos
                                        WHERE empresa_id = %s;
                                        """,
                                        (empresa_id,)
                                    )

                                elif acao == "Limpar Histórico de Caixa":
                                    cur.execute(
                                        """
                                        DELETE FROM pedidos
                                        WHERE empresa_id = %s;
                                        """,
                                        (empresa_id,)
                                    )

                                else:
                                    st.error(
                                        "Ação não reconhecida."
                                    )
                                    st.stop()

                                registros_afetados = cur.rowcount

                            conn_reset.commit()

                            st.success(
                                "🎉 Operação concluída com sucesso. "
                                f"Registros afetados: {registros_afetados}."
                            )

                            st.rerun()

                    except Exception:
                        if conn_reset is not None:
                            try:
                                conn_reset.rollback()
                            except Exception:
                                pass

                        logger.exception(
                            "Erro durante o reset de dados da empresa %s.",
                            empresa_id
                        )

                        st.error(
                            "Não foi possível concluir a operação. "
                            "A transação foi revertida quando possível."
                        )

                    finally:
                        if conn_reset is not None:
                            try:
                                conn_reset.close()
                            except Exception:
                                pass
