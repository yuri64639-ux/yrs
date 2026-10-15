
"""
VIEWS/GERENCIA.PY - Painel de Controle e Gestão Protegido por Senha Master
Mantém as abas de estoque, cadastro individual, importação em massa
e relatórios financeiros, com validação e isolamento por empresa.
"""

import csv
import logging
from decimal import Decimal, InvalidOperation
from io import StringIO

import pandas as pd
import streamlit as st

from core.database import ob_cx
from views.relatorios import renderizar_abas_financeiras

logger = logging.getLogger(__name__)


def renderizar_painel_gerencial(empresa_id, senha_master, conn_principal):
    st.title("⚙️ Painel de Controle Gerencial")
    st.markdown(f"Estabelecimento Ativo: **ID {empresa_id}**")
    st.markdown("---")

    # -----------------------------------------------------
    # AUTENTICAÇÃO ADMINISTRATIVA
    # -----------------------------------------------------
    st.subheader("🔑 Autenticação Administrativa")

    senha_digitada = st.text_input(
        "Insira a Senha Master do Estabelecimento para liberar "
        "as ferramentas de gestão:",
        type="password",
        placeholder="Senha Master",
        key="senha_protecao_gerencial_input"
    )

    if not senha_digitada:
        st.info(
            "🔒 Conteúdo restrito. Insira a senha master "
            "para acessar as ferramentas de gestão."
        )
        return

    if senha_digitada != senha_master:
        st.error(
            "❌ Senha Master incorreta! Acesso negado "
            "às ferramentas de auditoria e inventário."
        )
        return

    st.success(
        "🔓 Autenticação efetuada com sucesso! "
        "Painel de controle liberado."
    )
    st.markdown("---")

    # -----------------------------------------------------
    # ABAS GERENCIAIS
    # -----------------------------------------------------
    aba_est, aba_cad, aba_massa, aba_financeira = st.tabs([
        "📦 Estoque Atual",
        "📝 Cadastro Individual",
        "🍔 Importação em Massa",
        "📊 Relatórios & Faturamento"
    ])

    # -----------------------------------------------------
    # 1. ESTOQUE ATUAL
    # -----------------------------------------------------
    with aba_est:
        st.subheader("📦 Itens Cadastrados no Estoque")

        conn = None

        try:
            conn = ob_cx()

            if conn is None:
                st.error("Banco de dados indisponível.")
            else:
                with conn.cursor() as cur:
                    cur.execute("SET search_path TO public;")

                    cur.execute(
                        """
                        SELECT id, nome, preco, categoria, estoque
                        FROM produtos
                        WHERE empresa_id = %s
                        ORDER BY nome;
                        """,
                        (empresa_id,)
                    )

                    dados = cur.fetchall()

                    colunas = [
                        str(desc[0])
                        for desc in cur.description
                    ] if cur.description else []

                if dados:
                    df = pd.DataFrame(dados, columns=colunas)

                    df.columns = [
                        "ID",
                        "Nome do Item",
                        "Preço (R$)",
                        "Categoria",
                        "Estoque Atual"
                    ]

                    st.dataframe(
                        df,
                        width="stretch",
                        hide_index=True
                    )
                else:
                    st.info(
                        "Nenhum item localizado no estoque desta empresa."
                    )

        except Exception:
            logger.exception(
                "Erro ao consultar o estoque da empresa %s.",
                empresa_id
            )
            st.error(
                "Não foi possível carregar o estoque. "
                "Verifique a conexão com o banco."
            )

        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # -----------------------------------------------------
    # 2. CADASTRO INDIVIDUAL
    # -----------------------------------------------------
    with aba_cad:
        st.subheader("🛒 Adicionar Item ao Cardápio")

        with st.form(
            "form_cadastro_produto",
            clear_on_submit=True
        ):
            nome_prod = st.text_input(
                "Nome do Produto / Ingrediente:"
            ).strip()

            preco_prod = st.number_input(
                "Preço de Venda (R$):",
                min_value=0.0,
                step=0.50,
                format="%.2f"
            )

            cat_prod = st.selectbox(
                "Categoria:",
                [
                    "Bebidas",
                    "Comidas / Lanches",
                    "Sobremesas",
                    "Ingredientes / Adicionais"
                ]
            )

            est_prod = st.number_input(
                "Estoque Inicial (Unidades):",
                min_value=0,
                value=10,
                step=1
            )

            salvar_produto = st.form_submit_button(
                "Salvar no Cardápio",
                type="primary"
            )

            if salvar_produto:
                if not nome_prod:
                    st.error(
                        "Insira um nome válido para o produto."
                    )

                elif not Decimal(str(preco_prod)).is_finite():
                    st.error("O preço informado é inválido.")

                else:
                    conn = None

                    try:
                        conn = ob_cx()

                        if conn is None:
                            st.error(
                                "Banco de dados indisponível."
                            )
                        else:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "SET search_path TO public;"
                                )

                                cur.execute(
                                    """
                                    INSERT INTO produtos (
                                        empresa_id,
                                        nome,
                                        preco,
                                        categoria,
                                        estoque
                                    )
                                    VALUES (%s, %s, %s, %s, %s);
                                    """,
                                    (
                                        empresa_id,
                                        nome_prod,
                                        Decimal(str(preco_prod)),
                                        cat_prod,
                                        int(est_prod)
                                    )
                                )

                            conn.commit()

                            st.success(
                                f"🎉 '{nome_prod}' adicionado com sucesso!"
                            )
                            st.rerun()

                    except Exception:
                        if conn is not None:
                            try:
                                conn.rollback()
                            except Exception:
                                pass

                        logger.exception(
                            "Erro ao cadastrar produto na empresa %s.",
                            empresa_id
                        )

                        st.error(
                            "Não foi possível salvar o produto. "
                            "Verifique os dados e tente novamente."
                        )

                    finally:
                        if conn is not None:
                            try:
                                conn.close()
                            except Exception:
                                pass

    # -----------------------------------------------------
    # 3. IMPORTAÇÃO EM MASSA
    # -----------------------------------------------------
    with aba_massa:
        st.subheader("🍔 Cadastro de Cardápio em Lote")

        st.caption(
            "Formato: Nome do Produto, Categoria, Preço, Estoque"
        )

        st.code(
            "Nome do Produto, Categoria, Preço, Estoque",
            language="text"
        )

        texto_produtos = st.text_area(
            "Cole os itens aqui (um por linha):",
            height=250,
            placeholder=(
                "Exemplo:\n"
                "Coca-Cola Lata, Bebidas, 6.50, 50\n"
                "X-Salada Especial, Comidas / Lanches, 22.00, 30"
            ),
            key="texto_importacao_produtos"
        )

        if st.button(
            "🔥 Importar Lista Completa",
            type="primary",
            width="stretch",
            key="btn_importar_produtos"
        ):
            if not texto_produtos.strip():
                st.warning("O campo de texto está vazio.")

            else:
                produtos_validos = []
                erros_linhas = []

                # Valida todas as linhas antes de iniciar
                # a gravação no banco de dados.
                leitor = csv.reader(
                    StringIO(texto_produtos),
                    skipinitialspace=True
                )

                for numero_linha, partes in enumerate(
                    leitor,
                    start=1
                ):
                    if not partes or not any(
                        campo.strip() for campo in partes
                    ):
                        continue

                    if len(partes) != 4:
                        erros_linhas.append(
                            f"Linha {numero_linha}: "
                            "informe nome, categoria, preço e estoque."
                        )
                        continue

                    nome, categoria, preco_texto, estoque_texto = [
                        parte.strip()
                        for parte in partes
                    ]

                    if not nome or not categoria:
                        erros_linhas.append(
                            f"Linha {numero_linha}: "
                            "nome e categoria são obrigatórios."
                        )
                        continue

                    try:
                        # Aceita preços como 6.50 ou 6,50.
                        # A vírgula decimal deve estar entre aspas
                        # no CSV para não ser confundida com separador.
                        preco_normalizado = preco_texto.replace(
                            ",", "."
                        )

                        preco = Decimal(preco_normalizado)

                        if not preco.is_finite() or preco < 0:
                            raise InvalidOperation

                        estoque = int(estoque_texto)

                        if estoque < 0:
                            raise ValueError

                    except (
                        InvalidOperation,
                        ValueError,
                        TypeError
                    ):
                        erros_linhas.append(
                            f"Linha {numero_linha}: "
                            "preço ou estoque inválido."
                        )
                        continue

                    produtos_validos.append(
                        (
                            empresa_id,
                            nome,
                            categoria,
                            preco,
                            estoque
                        )
                    )

                if erros_linhas:
                    st.warning(
                        f"{len(erros_linhas)} linha(s) inválida(s). "
                        "As linhas válidas serão importadas."
                    )

                    for erro in erros_linhas[:20]:
                        st.write(f"- {erro}")

                    if len(erros_linhas) > 20:
                        st.caption(
                            f"E mais {len(erros_linhas) - 20} "
                            "erro(s) não exibido(s)."
                        )

                if not produtos_validos:
                    st.error(
                        "Nenhum produto válido encontrado para importar."
                    )

                else:
                    conn = None

                    try:
                        conn = ob_cx()

                        if conn is None:
                            st.error(
                                "Banco de dados indisponível."
                            )
                        else:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "SET search_path TO public;"
                                )

                                cur.executemany(
                                    """
                                    INSERT INTO produtos (
                                        empresa_id,
                                        nome,
                                        categoria,
                                        preco,
                                        estoque
                                    )
                                    VALUES (%s, %s, %s, %s, %s);
                                    """,
                                    produtos_validos
                                )

                            # Confirma todas as inserções juntas.
                            conn.commit()

                            st.success(
                                f"🚀 {len(produtos_validos)} produto(s) "
                                "importado(s) com sucesso!"
                            )

                            st.rerun()

                    except Exception:
                        if conn is not None:
                            try:
                                conn.rollback()
                            except Exception:
                                pass

                        logger.exception(
                            "Erro na importação em massa da empresa %s.",
                            empresa_id
                        )

                        st.error(
                            "A importação falhou. "
                            "As alterações desta operação foram "
                            "revertidas. Verifique o banco de dados."
                        )

                    finally:
                        if conn is not None:
                            try:
                                conn.close()
                            except Exception:
                                pass

    # -----------------------------------------------------
    # 4. RELATÓRIOS FINANCEIROS
    # -----------------------------------------------------
    with aba_financeira:
        renderizar_abas_financeiras(
            empresa_id,
            senha_master
        )
