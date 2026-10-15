
"""
APP.PY - Ponto de Entrada Principal, Roteador Multi-Tenant e Persistência de Sessão
Mantém a aba gerencial oculta quando um garçom está autenticado.
Integrado com views/garcom_login.py, views/caixa.py e views/gerencia.py.
"""

import os
import sys
import logging

import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CONFIGURAÇÃO INICIAL
# ---------------------------------------------------------

raiz_projeto = os.path.dirname(os.path.abspath(__file__))

if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

from core.database import inicializar_banco, ob_cx
from views.garcom_login import renderizar_terminal_garcom
from views.caixa import renderizar_fechamento_caixa
from views.gerencia import renderizar_painel_gerencial


# Não exibir detalhes internos do banco para os usuários.
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Sistema de Vendas Multi-Tenant",
    layout="centered"
)

# Inicializa o banco de dados.
inicializar_banco()


# ---------------------------------------------------------
# FUNÇÕES AUXILIARES DE VALIDAÇÃO
# ---------------------------------------------------------

def converter_inteiro(valor, padrao=None):
    """Converte um valor para inteiro sem interromper a aplicação."""
    try:
        resultado = int(valor)

        if resultado <= 0:
            return padrao

        return resultado

    except (ValueError, TypeError):
        return padrao


def validar_sessao_url(empresa_id, token):
    """
    Verifica se a empresa e a credencial recebidas pela URL
    correspondem a um registro válido no banco de dados.

    Observação: este método mantém a compatibilidade com o
    modelo atual de autenticação. Não substitui um token de
    sessão aleatório armazenado e validado no servidor.
    """
    if empresa_id is None or not token:
        return False

    conn = None

    try:
        conn = ob_cx()

        if conn is None:
            return False

        with conn.cursor() as cur:
            cur.execute("SET search_path TO public;")

            cur.execute(
                """
                SELECT 1
                FROM usuarios
                WHERE empresa_id = %s
                  AND senha = %s
                LIMIT 1;
                """,
                (empresa_id, token)
            )

            return cur.fetchone() is not None

    except Exception:
        logger.exception("Erro ao validar a sessão pela URL.")
        return False

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ---------------------------------------------------------
# RECUPERAÇÃO DA SESSÃO VIA URL
# ---------------------------------------------------------

params = st.query_params

token_empresa = params.get("empresa_id")
token_senha = params.get("auth_token")
aba_salva = params.get("aba_ativa", "0")

empresa_id_url = converter_inteiro(token_empresa)

try:
    indice_aba_url = int(aba_salva)

    if indice_aba_url not in (0, 1, 2):
        indice_aba_url = 0

except (ValueError, TypeError):
    indice_aba_url = 0


# Valida a URL antes de utilizá-la para inicializar uma sessão.
logado_inicial = validar_sessao_url(
    empresa_id_url,
    token_senha
)


# ---------------------------------------------------------
# INICIALIZAÇÃO DOS ESTADOS DA SESSÃO
# ---------------------------------------------------------

estados_obrigatorios = {
    "logado": logado_inicial,
    "operador_atual": None,
    "empresa_id_atual": empresa_id_url if logado_inicial else None,
    "senha_master_empresa": token_senha if logado_inicial else "",
    "carrinho": [],
    "indice_aba_atual": indice_aba_url,
}

for chave, valor_padrao in estados_obrigatorios.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor_padrao


# Se os parâmetros de autenticação forem inválidos, não os
# manter como credenciais utilizáveis na URL.
if (
    (token_empresa or token_senha)
    and not logado_inicial
    and not st.session_state.logado
):
    st.query_params.clear()


# ---------------------------------------------------------
# OCULTAÇÃO DOS MENUS NATIVOS DO STREAMLIT
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        #MainMenu,
        .stAppDeployButton {
            visibility: hidden !important;
            display: none !important;
        }

        header [data-testid="stToolbar"] {
            display: none !important;
        }

        [data-testid="collapsedControl"] {
            display: none !important;
        }

        header {
            background-color: transparent !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# FLUXO DE AUTENTICAÇÃO DO ESTABELECIMENTO
# ---------------------------------------------------------

if not st.session_state.logado:

    aba_acesso = st.radio(
        "Selecione uma opção:",
        [
            "Fazer Login",
            "Cadastrar Nova Empresa (Criar Conta)"
        ],
        horizontal=True
    )

    # -----------------------------------------------------
    # CADASTRO DE NOVA EMPRESA
    # -----------------------------------------------------

    if aba_acesso == "Cadastrar Nova Empresa (Criar Conta)":

        with st.form("cadastro_empresa_form"):

            st.subheader("🏢 Cadastrar Empresa no Sistema")

            nova_empresa = st.text_input(
                "Nome do seu Estabelecimento / Empresa:"
            ).strip()

            adm_usuario = st.text_input(
                "Usuário Administrador (ex: admin):"
            ).strip()

            adm_senha = st.text_input(
                "Defina a Senha do Administrador:",
                type="password"
            ).strip()

            if st.form_submit_button(
                "Criar Minha Conta",
                type="primary"
            ):

                if not (
                    nova_empresa
                    and adm_usuario
                    and adm_senha
                ):
                    st.error(
                        "Todos os campos do formulário são obrigatórios."
                    )

                else:
                    conn = None

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

                                cur.execute(
                                    """
                                    INSERT INTO empresas (nome_empresa)
                                    VALUES (%s)
                                    RETURNING id;
                                    """,
                                    (nova_empresa,)
                                )

                                id_da_empresa = cur.fetchone()[0]

                                cur.execute(
                                    """
                                    INSERT INTO usuarios
                                        (empresa_id, usuario, senha)
                                    VALUES (%s, %s, %s);
                                    """,
                                    (
                                        id_da_empresa,
                                        adm_usuario,
                                        adm_senha
                                    )
                                )

                            conn.commit()

                            st.success(
                                f"🎉 Empresa '{nova_empresa}' criada "
                                "com sucesso! Mude para a aba de login."
                            )

                    except Exception:
                        if conn is not None:
                            try:
                                conn.rollback()
                            except Exception:
                                pass

                        logger.exception(
                            "Erro durante o cadastro da empresa."
                        )

                        st.error(
                            "Não foi possível cadastrar a empresa. "
                            "Verifique os dados e a conexão com o banco."
                        )

                    finally:
                        if conn is not None:
                            try:
                                conn.close()
                            except Exception:
                                pass

    # -----------------------------------------------------
    # LOGIN DA EMPRESA
    # -----------------------------------------------------

    else:

        with st.form("login_form"):

            st.subheader(
                "📱 Login do Estabelecimento (Empresa)"
            )

            conn = None

            try:
                conn = ob_cx()

                dados_empresas = []

                if conn is not None:
                    with conn.cursor() as cur:

                        cur.execute(
                            "SET search_path TO public;"
                        )

                        cur.execute(
                            """
                            SELECT id, nome_empresa
                            FROM empresas
                            ORDER BY nome_empresa;
                            """
                        )

                        dados_empresas = cur.fetchall()

            except Exception:
                logger.exception(
                    "Erro ao consultar as empresas cadastradas."
                )

                st.error(
                    "Falha ao consultar as empresas. "
                    "Verifique a conexão com o banco."
                )

            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

            dict_empresas = {
                row[1]: row[0]
                for row in dados_empresas
            } if dados_empresas else {}

            if dict_empresas:

                empresa_selecionada = st.selectbox(
                    "Selecione sua Empresa:",
                    list(dict_empresas.keys())
                )

                user_input = st.text_input(
                    "Usuário Master da Empresa:"
                )

                senha_input = st.text_input(
                    "Senha Master:",
                    type="password"
                )

                if st.form_submit_button(
                    "Liberar Terminal",
                    type="primary"
                ):

                    id_empresa_login = dict_empresas[
                        empresa_selecionada
                    ]

                    conn_login = None
                    resultado = None

                    try:
                        conn_login = ob_cx()

                        if conn_login is not None:
                            with conn_login.cursor() as cur:

                                cur.execute(
                                    "SET search_path TO public;"
                                )

                                cur.execute(
                                    """
                                    SELECT empresa_id, senha
                                    FROM usuarios
                                    WHERE empresa_id = %s
                                      AND LOWER(usuario) = LOWER(%s)
                                      AND senha = %s
                                    LIMIT 1;
                                    """,
                                    (
                                        id_empresa_login,
                                        user_input.strip(),
                                        senha_input.strip()
                                    )
                                )

                                resultado = cur.fetchone()

                    except Exception:
                        logger.exception(
                            "Erro durante a autenticação da empresa."
                        )

                        st.error(
                            "Não foi possível realizar o login. "
                            "Verifique a conexão com o banco."
                        )

                    finally:
                        if conn_login is not None:
                            try:
                                conn_login.close()
                            except Exception:
                                pass

                    if resultado:

                        st.session_state.logado = True

                        st.session_state.empresa_id_atual = int(
                            resultado[0]
                        )

                        st.session_state.senha_master_empresa = str(
                            resultado[1]
                        )

                        # Mantém o comportamento original de recuperação
                        # da sessão via URL.
                        st.query_params["empresa_id"] = str(
                            resultado[0]
                        )

                        st.query_params["auth_token"] = str(
                            resultado[1]
                        )

                        st.query_params["aba_ativa"] = "0"

                        st.rerun()

                    elif resultado is None:
                        # Diferencia credenciais incorretas de falhas
                        # de conexão através da mensagem genérica.
                        st.error(
                            "Credenciais incorretas ou falha "
                            "na autenticação. Tente novamente."
                        )

            else:
                st.info(
                    "Nenhuma empresa cadastrada no sistema "
                    "ou o banco de dados está indisponível."
                )

    st.stop()


# ---------------------------------------------------------
# VALIDAÇÃO DO ESTADO DE AUTENTICAÇÃO
# ---------------------------------------------------------

if (
    st.session_state.empresa_id_atual is None
    or not st.session_state.senha_master_empresa
):
    st.session_state.logado = False
    st.session_state.operador_atual = None
    st.session_state.empresa_id_atual = None
    st.session_state.senha_master_empresa = ""

    st.query_params.clear()
    st.rerun()


# ---------------------------------------------------------
# CONTROLE DINÂMICO DAS ABAS
# ---------------------------------------------------------

conn_global = None

try:
    conn_global = ob_cx()

    if conn_global is None:
        st.error(
            "Não foi possível conectar ao banco de dados. "
            "Recarregue a página ou tente novamente mais tarde."
        )
        st.stop()

    # -----------------------------------------------------
    # GARÇOM AUTENTICADO
    # Oculta a aba gerencial e mantém terminal e caixa.
    # -----------------------------------------------------

    if st.session_state.operador_atual is not None:

        lista_abas = [
            "🚀 Terminal do Garçom (Lançar)",
            "🧾 Fechamento de Conta (Caixa)"
        ]

        abas_renderizadas = st.tabs(lista_abas)

        with abas_renderizadas[0]:

            st.query_params["aba_ativa"] = "1"

            renderizar_terminal_garcom(
                st.session_state.empresa_id_atual,
                st.session_state.senha_master_empresa,
                conn_global
            )

        with abas_renderizadas[1]:

            st.query_params["aba_ativa"] = "2"

            renderizar_fechamento_caixa(
                st.session_state.empresa_id_atual,
                st.session_state.senha_master_empresa,
                conn_global
            )

    # -----------------------------------------------------
    # ADMINISTRADOR / MASTER DA EMPRESA
    # Exibe as três abas.
    # -----------------------------------------------------

    else:

        lista_abas = [
            "⚙️ Painel de Controle Gerencial",
            "🚀 Terminal do Garçom (Lançar)",
            "🧾 Fechamento de Conta (Caixa)"
        ]

        abas_renderizadas = st.tabs(lista_abas)

        with abas_renderizadas[0]:

            renderizar_painel_gerencial(
                st.session_state.empresa_id_atual,
                conn_global
            )

            st.markdown("---")

            if st.button(
                "🔒 Bloquear Terminal da Empresa por Completo",
                type="primary",
                width="stretch",
                key="lock_terminal_global"
            ):

                st.session_state.logado = False
                st.session_state.empresa_id_atual = None
                st.session_state.senha_master_empresa = ""
                st.session_state.operador_atual = None

                st.session_state.carrinho = []
                st.session_state.indice_aba_atual = 0

                st.query_params.clear()

                st.rerun()

        with abas_renderizadas[1]:

            st.query_params["aba_ativa"] = "1"

            renderizar_terminal_garcom(
                st.session_state.empresa_id_atual,
                st.session_state.senha_master_empresa,
                conn_global
            )

        with abas_renderizadas[2]:

            st.query_params["aba_ativa"] = "2"

            renderizar_fechamento_caixa(
                st.session_state.empresa_id_atual,
                st.session_state.senha_master_empresa,
                conn_global
            )

except Exception:
    logger.exception(
        "Erro ao renderizar as telas do sistema."
    )

    st.error(
        "Ocorreu um erro ao carregar o sistema. "
        "Verifique a conexão e os registros do servidor."
    )

finally:
    if conn_global is not None:
        try:
            conn_global.close()
        except Exception:
            pass
