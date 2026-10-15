"""
VIEWS/GARCOM.PY - Módulo de Identificação da Equipe e Balcão de Caixa
Gerencia logins de múltiplos operadores, controle de acesso e fechamento de comandas.
"""

import streamlit as st
import pandas as pd
import psycopg2
from core.database import ob_cx
from views.garcom_pedidos import renderizar_sistema_pedidos

def renderizar_terminal_garcom(empresa_id, senha_master, conn_principal):
    st.subheader("📱 Terminal de Lançamentos do Atendente")
    
    # --- SISTEMA DE LOGIN INDIVIDUAL PARA MÚLTIPLOS GARÇONS ---
    if "operador_atual" not in st.session_state:
        st.session_state.operador_atual = None

    if st.session_state.operador_atual is None:
        st.info("🔒 Identificação Obrigatória: Efetue o login para liberar as comandas.")
        
        with st.form("form_login_operador_garcom", clear_on_submit=True):
            user_garcom = st.text_input("Usuário / Nome do Garçom:").strip()
            senha_garcom = st.text_input("Senha de Acesso:", type="password").strip()
            
            col_cad, col_ent = st.columns(2)
            botao_entrar = col_ent.form_submit_button("Entrar no Sistema", type="primary", width="stretch")
            botao_cadastrar = col_cad.form_submit_button("💼 Cadastrar Minha Conta", type="secondary", width="stretch")
            
            if botao_entrar and user_garcom and senha_garcom:
                try:
                    with ob_cx() as conn, conn.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            SELECT usuario FROM usuarios 
                            WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s;
                        """, (empresa_id, user_garcom, senha_garcom))
                        res_login = cur.fetchone()
                        
                    if res_login:
                        st.session_state.operador_atual = str(res_login[0]).upper()
                        st.success(f"Bem-vindo, {st.session_state.operador_atual}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha de garçom incorretos!")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")
                    
            elif botao_cadastrar and user_garcom and senha_garcom:
                try:
                    with ob_cx() as conn, conn.cursor() as cur:
                        cur.execute("SET search_path TO public;")
                        cur.execute("""
                            INSERT INTO usuarios (empresa_id, usuario, senha) 
                            VALUES (%s, %s, %s);
                        """, (empresa_id, user_garcom, senha_garcom))
                        conn.commit()
                    st.success(f"🎉 Garçom '{user_garcom}' cadastrado! Digite os dados novamente para Entrar.")
                except Exception as e:
                    st.error("Erro: Esse nome de usuário já está em uso na empresa.")
        st.stop()

    # --- RENDERIZAÇÃO DA INTERFACE APÓS AUTENTICAÇÃO ---
    col_user_info, col_btn_logout = st.columns(2)
    col_user_info.markdown(f"👤 Atendente Ativo: **{st.session_state.operador_atual}**")
    if col_btn_logout.button("🔒 Sair / Trocar Atendente", width="stretch", key="btn_logout_atendente_garcom"):
        st.session_state.operador_atual = None
        st.session_state.carrinho = []
        st.rerun()

    st.markdown("---")
    
    # Chama o módulo de montagem do pedido contido no segundo arquivo separado
    renderizar_sistema_pedidos(empresa_id, senha_master, conn_principal)

def renderizar_fechamento_caixa(empresa_id, senha_master, conn_principal):
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
                st.error(f"Erro ao ler comandas: {e}")
                return

    if not lista_mesas:
        st.info("Não há nenhuma mesa ou comanda com consumption em aberto no momento.")
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
"""
VIEWS/GARCOM_PEDIDOS.PY - Interface de Montagem de Pedidos e Baixa de Insumos
Processa as pesquisas de cardápio, carrinho corrente e o cálculo fracionado de insumos (L/Kg).
"""

import streamlit as st
import pandas as pd
import psycopg2
from core.database import ob_cx

def renderizar_sistema_pedidos(empresa_id, senha_master, conn_principal):
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []
        
    mesa_ou_comanda = st.text_input("📍 Identificação (Nº da Mesa ou Comanda):", placeholder="Ex: Mesa 04", key="input_mesa_lancamento").strip()
    st.markdown("---")
    
    st.markdown("### 🔍 Pesquisar no Cardápio")
    busca = st.text_input("Digite o nome ou categoria do item:", placeholder="Ex: Coca, Batata...", key="input_busca_cardapio").strip()
    
    with ob_cx() as conn:
        if conn:
            try:
                with conn.cursor() as cur:
                    if busca:
                        cur.execute("""
                            SELECT id, nome, preco, categoria 
                            FROM produtos 
                            WHERE empresa_id = %s 
                              AND (LOWER(nome) LIKE LOWER(%s) OR LOWER(categoria) LIKE LOWER(%s))
                            ORDER BY nome;
                        """, (empresa_id, f"%{busca}%", f"%{busca}%"))
                    else:
                        cur.execute("""
                            SELECT id, nome, preco, categoria 
                            FROM produtos 
                            WHERE empresa_id = %s 
                            ORDER BY nome
                            LIMIT 8;
                        """, (empresa_id,))
                    
                    dados_busca = cur.fetchall()
                    colunas = [str(desc[0]) for desc in cur.description] if cur.description else []
                    
                df_busca = pd.DataFrame(dados_busca, columns=colunas) if dados_busca else pd.DataFrame()
                
                if not df_busca.empty:
                    for _, row in df_busca.iterrows():
                        col_nome, col_add = st.columns(2)
                        col_nome.write(f"**{row['nome']}** - R$ {row['preco']:.2f}")
                        if col_add.button(f"➕ Adicionar", key=f"add_{row['id']}"):
                            st.session_state.carrinho.append({
                                "id": int(row["id"]),
                                "nome": str(row["nome"]),
                                "preco": float(row["preco"])
                            })
                            st.toast(f"'{row['nome']}' colocado no carrinho!")
                            st.rerun()
                else:
                    st.info("Nenhum produto localizado no cardápio.")
            except Exception as error:
                st.error(f"Erro temporário de sincronização de dados: {error}")

    st.markdown("---")

    st.markdown("### 🛒 Sacola / Itens Pendentes")
    if st.session_state.carrinho:
        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        total_conta = df_carrinho["preco"].sum()
        
        resumo_carrinho = df_carrinho["nome"].value_counts()
        for item_nome, qtd in resumo_carrinho.items():
            st.write(f"• **{qtd}x** {item_nome}")
            
        st.markdown(f"## **Subtotal: R$ {total_conta:.2f}**")
        
        col_cancelar, col_enviar = st.columns(2)
        if col_cancelar.button("🗑️ Limpar Sacola", width='stretch', key="btn_limpar_sacola"):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_enviar.button("🚀 Confirmar e Lançar Pedido", type="primary", width='stretch', key="btn_enviar_pedido"):
            if not mesa_ou_comanda:
                st.error("Por favor, preencha o número da Mesa ou Comanda antes de lançar!")
            else:
                try:
                    texto_itens = ", ".join([f"{qtd}x {nome}" for nome, qtd in resumo_carrinho.items()])
                    with ob_cx() as conn_venda, conn_venda.cursor() as cur:
                        try:
                            cur.execute("""
                                INSERT INTO pedidos (empresa_id, mesa, itens, total, metodo_pagamento, garcom)
                                VALUES (%s, %s, %s, %s, 'Pendente', %s);
                            """, (empresa_id, mesa_ou_comanda, texto_itens, total_conta, st.session_state.operador_atual))
                        except (psycopg2.errors.UndefinedColumn, psycopg2.errors.InFailedSqlTransaction):
                            conn_venda.rollback()
                            try:
                                cur.execute("""
                                    INSERT INTO pedidos (empresa_id, mesa_comanda, itens, total, metodo_pagamento, garcom)
                                    VALUES (%s, %s, %s, %s, 'Pendente', %s);
                                """, (empresa_id, mesa_ou_comanda, texto_itens, total_conta, st.session_state.operador_atual))
                            except (psycopg2.errors.UndefinedColumn, psycopg2.errors.InFailedSqlTransaction):
                                conn_venda.rollback()
                                for item in st.session_state.carrinho:
                                    try:
                                        cur.execute("""
                                            INSERT INTO pedidos (empresa_id, mesa, produto_id, quantidade, status, garcom)
                                            VALUES (%s, %s, %s, 1, 'Pendente', %s);
                                        """, (empresa_id, mesa_ou_comanda, item["id"], st.session_state.operador_atual))
                                    except:
                                        conn_venda.rollback()
                                        cur.execute("""
                                            INSERT INTO pedidos (empresa_id, comanda, produto_id, quantidade, status, garcom)
                                            VALUES (%s, %s, %s, 1, 'Pendente', %s);
                                        """, (empresa_id, mesa_ou_comanda, item["id"], st.session_state.operador_atual))

                        # --- LOGÍSTICA DE DEBITO POR SUPRIMENTO FRACIONADO (L/KG) ---
                        for item in st.session_state.carrinho:
                            cur.execute("""
                                SELECT insumo_id, qtd_insumo 
                                FROM receitas 
                                WHERE empresa_id = %s AND produto_id = %s;
                            """, (empresa_id, item["id"]))
                            ingredientes_ficha = cur.fetchall()
                            
                            for insumo_id, qtd_insumo in ingredientes_ficha:
                                qtd_convertida = float(qtd_insumo) / 1000.0
                                cur.execute("""
                                    UPDATE estoque 
                                    SET quantidade = quantidade - %s 
                                    WHERE id = %s AND empresa_id = %s;
                                """, (qtd_convertida, insumo_id, empresa_id))
                        conn_venda.commit()
                        
                    st.success(f"🚀 Pedido da {mesa_ou_comanda} computado pelo garçom {st.session_state.operador_atual}!")
                    st.session_state.carrinho = []
                    st.rerun()
                except Exception as error:
                    st.error(f"Erro ao salvar pedido: {error}")
    else:
        st.info("Nenhum item na sacola.")
