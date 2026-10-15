
"""
VIEWS/GARCOM_LOGIN.PY
Gerenciamento de login e identificação da equipe.
Mantém a integração com o sistema de pedidos.
"""

import logging
import streamlit as st

from core.database import ob_cx
from views.garcom_pedidos import renderizar_sistema_pedidos

logger = logging.getLogger(__name__)


def renderizar_terminal_garcom(empresa_id, senha_master, conn_principal):
    st.subheader("📱 Terminal de Lançamentos do Garçom")

    # Inicialização do estado do operador.
    if "operador_atual" not in st.session_state:
        st.session_state.operador_atual = None

    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    # -----------------------------------------------------
    # LOGIN INDIVIDUAL
    # -----------------------------------------------------
    if st.session_state.operador_atual is None:
        st.info(
            "🔒 Identificação obrigatória: efetue o login "
            "para liberar as comandas."
        )

        with st.form(
            "form_login_operador_garcom",
            clear_on_submit=True
        ):
            user_garcom = st.text_input(
                "Usuário / Nome do Garçom:"
            ).strip()

            senha_garcom = st.text_input(
                "Senha de Acesso:",
                type="password"
            ).strip()

            col_cad, col_ent = st.columns(2)

            botao_entrar = col_ent.form_submit_button(
                "Entrar no Sistema",
                type="primary",
                width="stretch"
            )

            botao_cadastrar = col_cad.form_submit_button(
                "💼 Cadastrar Minha Conta",
                type="secondary",
                width="stretch"
            )

            # ---------------------------------------------
            # AUTENTICAR
            # ---------------------------------------------
            if botao_entrar:
                if not user_garcom or not senha_garcom:
                    st.error(
                        "Informe o usuário e a senha para continuar."
                    )
                else:
                    conn = None

                    try:
                        conn = ob_cx()

                        if conn is None:
                            st.error(
                                "Banco de dados indisponível. "
                                "Tente novamente."
                            )
                        else:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "SET search_path TO public;"
                                )

                                cur.execute(
                                    """
                                    SELECT usuario
                                    FROM usuarios
                                    WHERE empresa_id = %s
                                      AND LOWER(usuario) = LOWER(%s)
                                      AND senha = %s
                                    LIMIT 1;
                                    """,
                                    (
                                        empresa_id,
                                        user_garcom,
                                        senha_garcom
                                    )
                                )

                                res_login = cur.fetchone()

                            if res_login:
                                st.session_state.operador_atual = (
                                    str(res_login[0]).upper()
                                )

                                st.session_state.carrinho = []

                                st.success(
                                    "Login realizado com sucesso!"
                                )
                                st.rerun()
                            else:
                                st.error(
                                    "Usuário ou senha incorretos."
                                )

                    except Exception:
                        logger.exception(
                            "Falha durante o login do operador."
                        )
                        st.error(
                            "Não foi possível realizar o login. "
                            "Verifique a conexão e tente novamente."
                        )

                    finally:
                        if conn is not None:
                            try:
                                conn.close()
                            except Exception:
                                pass

            # ---------------------------------------------
            # CADASTRAR GARÇOM
            # ---------------------------------------------
            elif botao_cadastrar:
                if not user_garcom or not senha_garcom:
                    st.error(
                        "Informe o usuário e a senha para cadastrar."
                    )
                else:
                    conn = None

                    try:
                        conn = ob_cx()

                        if conn is None:
                            st.error(
                                "Banco de dados indisponível. "
                                "Tente novamente."
                            )
                        else:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "SET search_path TO public;"
                                )

                                # Verifica duplicidade ignorando
                                # diferenças entre maiúsculas e minúsculas.
                                cur.execute(
                                    """
                                    SELECT 1
                                    FROM usuarios
                                    WHERE empresa_id = %s
                                      AND LOWER(usuario) = LOWER(%s)
                                    LIMIT 1;
                                    """,
                                    (empresa_id, user_garcom)
                                )

                                usuario_existe = cur.fetchone()

                                if usuario_existe:
                                    st.error(
                                        "Esse usuário já existe "
                                        "nesta empresa."
                                    )
                                else:
                                    cur.execute(
                                        """
                                        INSERT INTO usuarios
                                            (empresa_id, usuario, senha)
                                        VALUES (%s, %s, %s);
                                        """,
                                        (
                                            empresa_id,
                                            user_garcom,
                                            senha_garcom
                                        )
                                    )

                                    conn.commit()

                                    st.success(
                                        f"Garçom '{user_garcom}' "
                                        "cadastrado com sucesso. "
                                        "Faça login para continuar."
                                    )

                    except Exception:
                        if conn is not None:
                            try:
                                conn.rollback()
                            except Exception:
                                pass

                        logger.exception(
                            "Falha durante o cadastro do operador."
                        )

                        st.error(
                            "Não foi possível cadastrar o usuário. "
                            "Verifique os dados e tente novamente."
                        )

                    finally:
                        if conn is not None:
                            try:
                                conn.close()
                            except Exception:
                                pass

        # Impede que os pedidos apareçam sem login.
        st.stop()

    # -----------------------------------------------------
    # INTERFACE OPERACIONAL
    # -----------------------------------------------------
    col_user_info, col_btn_logout = st.columns(2)

    col_user_info.markdown(
        f"👤 Atendente ativo: "
        f"**{st.session_state.operador_atual}**"
    )

    if col_btn_logout.button(
        "🔒 Sair / Trocar Atendente",
        width="stretch"
    ):
        st.session_state.operador_atual = None
        st.session_state.carrinho = []
        st.rerun()

    st.markdown("---")

    # Mantém a assinatura e a integração originais.
    renderizar_sistema_pedidos(
        empresa_id,
        senha_master,
        conn_principal
    )

"""
VIEWS/GARCOM_PEDIDOS.PY
Interface de vendas, pesquisa de cardápio e lançamento de pedidos.
"""

import logging
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from core.database import ob_cx

logger = logging.getLogger(__name__)


def renderizar_sistema_pedidos(
    empresa_id,
    senha_master,
    conn_principal
):
    # -----------------------------------------------------
    # INICIALIZAÇÃO
    # -----------------------------------------------------
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    if "operador_atual" not in st.session_state:
        st.session_state.operador_atual = None

    mesa_ou_comanda = st.text_input(
        "📍 Identificação (Nº da Mesa ou Comanda):",
        placeholder="Ex: Mesa 04",
        key="input_mesa_lancamento"
    ).strip()

    st.markdown("---")
    st.markdown("### 🔍 Pesquisar no Cardápio")

    busca = st.text_input(
        "Digite o nome ou categoria do item:",
        placeholder="Ex: Coca, Batata...",
        key="input_busca_cardapio"
    ).strip()

    # -----------------------------------------------------
    # PESQUISA DE PRODUTOS
    # -----------------------------------------------------
    conn = None
    dados_busca = []

    try:
        conn = ob_cx()

        if conn is None:
            st.error(
                "Não foi possível conectar ao banco de dados."
            )
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "SET search_path TO public;"
                )

                if busca:
                    cur.execute(
                        """
                        SELECT id, nome, preco, categoria
                        FROM produtos
                        WHERE empresa_id = %s
                          AND (
                              LOWER(nome) LIKE LOWER(%s)
                              OR LOWER(COALESCE(categoria, ''))
                                 LIKE LOWER(%s)
                          )
                        ORDER BY nome;
                        """,
                        (
                            empresa_id,
                            f"%{busca}%",
                            f"%{busca}%"
                        )
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, nome, preco, categoria
                        FROM produtos
                        WHERE empresa_id = %s
                        ORDER BY nome
                        LIMIT 8;
                        """,
                        (empresa_id,)
                    )

                dados_busca = cur.fetchall()

            df_busca = pd.DataFrame(
                dados_busca,
                columns=["id", "nome", "preco", "categoria"]
            )

            if df_busca.empty:
                st.info(
                    "Nenhum produto localizado no cardápio."
                )
            else:
                for _, row in df_busca.iterrows():
                    col_nome, col_add = st.columns(2)

                    try:
                        preco = Decimal(str(row["preco"]))

                        if not preco.is_finite() or preco < 0:
                            raise InvalidOperation

                    except (InvalidOperation, ValueError, TypeError):
                        logger.error(
                            "Preço inválido no produto ID %s.",
                            row["id"]
                        )
                        col_nome.write(
                            f"**{row['nome']}** — preço indisponível"
                        )
                        continue

                    col_nome.write(
                        f"**{row['nome']}** — R$ {preco:.2f}"
                    )

                    if col_add.button(
                        "➕ Adicionar",
                        key=f"add_{row['id']}"
                    ):
                        st.session_state.carrinho.append(
                            {
                                "id": int(row["id"]),
                                "nome": str(row["nome"]),
                                "preco": str(preco)
                            }
                        )

                        st.toast(
                            f"'{row['nome']}' colocado no carrinho!"
                        )
                        st.rerun()

    except Exception:
        logger.exception(
            "Erro durante a pesquisa do cardápio."
        )
        st.error(
            "Não foi possível carregar os produtos. "
            "Verifique a conexão e tente novamente."
        )

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    # -----------------------------------------------------
    # CARRINHO
    # -----------------------------------------------------
    st.markdown("---")
    st.markdown("### 🛒 Sacola / Itens Pendentes")

    carrinho = st.session_state.carrinho

    if not carrinho:
        st.info("A sacola de itens pendentes está vazia.")
        return

    try:
        total_conta = sum(
            (
                Decimal(str(item["preco"]))
                for item in carrinho
            ),
            Decimal("0.00")
        )

        resumo_carrinho = {}

        for item in carrinho:
            nome = str(item["nome"])
            resumo_carrinho[nome] = (
                resumo_carrinho.get(nome, 0) + 1
            )

    except (InvalidOperation, ValueError, TypeError, KeyError):
        logger.exception(
            "O carrinho contém dados inválidos."
        )
        st.error(
            "Há um item inválido no carrinho. "
            "Limpe a sacola e adicione os produtos novamente."
        )
        return

    for item_nome, qtd in resumo_carrinho.items():
        st.write(f"• **{qtd}x** {item_nome}")

    st.markdown(
        f"## **Subtotal: R$ {total_conta:.2f}**"
    )

    col_cancelar, col_enviar = st.columns(2)

    # -----------------------------------------------------
    # LIMPAR CARRINHO
    # -----------------------------------------------------
    if col_cancelar.button(
        "🗑️ Limpar Sacola",
        width="stretch",
        key="btn_limpar_sacola"
    ):
        st.session_state.carrinho = []
        st.rerun()

    # -----------------------------------------------------
    # CONFIRMAR E LANÇAR PEDIDO
    # -----------------------------------------------------
    if col_enviar.button(
        "🚀 Confirmar e Lançar Pedido",
        type="primary",
        width="stretch",
        key="btn_enviar_pedido"
    ):
        if not mesa_ou_comanda:
            st.error(
                "Preencha o número da mesa ou da comanda "
                "antes de lançar o pedido."
            )
            return

        if not st.session_state.operador_atual:
            st.error(
                "Faça login como garçom antes de lançar o pedido."
            )
            return

        if not empresa_id:
            st.error(
                "Empresa não identificada. Faça login novamente."
            )
            return

        # Revalida os preços no banco para evitar confiar
        # apenas nos valores guardados no estado da sessão.
        conn_venda = None

        try:
            conn_venda = ob_cx()

            if conn_venda is None:
                st.error(
                    "Banco de dados indisponível. "
                    "O pedido não foi lançado."
                )
                return

            ids_produtos = [
                int(item["id"])
                for item in carrinho
            ]

            with conn_venda.cursor() as cur:
                cur.execute(
                    "SET search_path TO public;"
                )

                cur.execute(
                    """
                    SELECT id, nome, preco
                    FROM produtos
                    WHERE empresa_id = %s
                      AND id = ANY(%s);
                    """,
                    (empresa_id, ids_produtos)
                )

                produtos_banco = {
                    int(row[0]): {
                        "nome": str(row[1]),
                        "preco": Decimal(str(row[2]))
                    }
                    for row in cur.fetchall()
                }

                # Verifica se todos os produtos ainda existem
                # e pertencem à empresa autenticada.
                if any(
                    produto_id not in produtos_banco
                    for produto_id in ids_produtos
                ):
                    st.error(
                        "Um ou mais produtos não estão mais "
                        "disponíveis. Atualize o cardápio."
                    )
                    return

                total_validado = Decimal("0.00")
                quantidades = {}

                for item in carrinho:
                    produto_id = int(item["id"])
                    produto = produtos_banco[produto_id]
                    preco_atual = produto["preco"]

                    if (
                        not preco_atual.is_finite()
                        or preco_atual < 0
                    ):
                        raise ValueError(
                            "Foi encontrado um preço inválido."
                        )

                    total_validado += preco_atual

                    if produto_id not in quantidades:
                        quantidades[produto_id] = {
                            "nome": produto["nome"],
                            "quantidade": 0
                        }

                    quantidades[produto_id]["quantidade"] += 1

                texto_itens = ", ".join(
                    f"{dados['quantidade']}x {dados['nome']}"
                    for dados in quantidades.values()
                )

                cur.execute(
                    """
                    INSERT INTO pedidos (
                        empresa_id,
                        mesa,
                        itens,
                        total,
                        metodo_pagamento,
                        garcom
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        empresa_id,
                        mesa_ou_comanda,
                        texto_itens,
                        total_validado,
                        "Pendente",
                        st.session_state.operador_atual
                    )
                )

            conn_venda.commit()

            st.session_state.carrinho = []

            st.success(
                "🎉 Pedido lançado com sucesso no banco de dados!"
            )
            st.rerun()

        except Exception:
            if conn_venda is not None:
                try:
                    conn_venda.rollback()
                except Exception:
                    pass

            logger.exception(
                "Erro ao processar o lançamento do pedido."
            )

            st.error(
                "Não foi possível salvar o pedido. "
                "Nenhum lançamento foi confirmado. "
                "Verifique a conexão e tente novamente."
            )

        finally:
            if conn_venda is not None:
                try:
                    conn_venda.close()
                except Exception:
                    pass
 
