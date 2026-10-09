import os
import sys
import streamlit as st
import pandas as pd
import warnings

# Força o Python a procurar arquivos .py na mesma pasta deste script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importações locais do banco de dados de forma segura
from core_db import ob_cx, inicializar_banco

# Inicialização de estados globais essenciais para o fluxo do app
if "logado" not in st.session_state:
    st.session_state.logado = False
if "empresa_id_atual" not in st.session_state:
    st.session_state.empresa_id_atual = None
if "senha_master_empresa" not in st.session_state:
    st.session_state.senha_master_empresa = ""
if "garcom_logado" not in st.session_state:
    st.session_state.garcom_logado = False
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

def render_login_cadastro():
    """Gerencia as telas de autenticação e criação de conta multi-tenant."""
    conn = ob_cx()
    aba_acesso = st.radio("Selecione uma opção:", ["Fazer Login", "Cadastrar Nova Empresa (Criar Conta)"], horizontal=True)
    
    if aba_acesso == "Cadastrar Nova Empresa (Criar Conta)":
        with st.form("cadastro_empresa_form"):
            st.subheader("🏢 Cadastrar Empresa no Sistema")
            nova_empresa = st.text_input("Nome do seu Estabelecimento / Empresa:").strip()
            adm_usuario = st.text_input("Usuário Administrador (ex: admin):").strip()
            adm_senha = st.text_input("Defina a Senha do Administrador:", type="password").strip()
            if st.form_submit_button("Criar Minha Conta", type="primary") and nova_empresa and adm_usuario and adm_senha:
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; INSERT INTO empresas (nome_empresa) VALUES (%s) RETURNING id;", (nova_empresa,))
                        id_da_empresa = cur.fetchone()[0]
                        cur.execute("INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (id_da_empresa, adm_usuario, adm_senha))
                        c.commit()
                    st.success(f"🎉 Empresa '{nova_empresa}' criada com sucesso! Mude para a aba de login.")
                except Exception as e: 
                    st.error(f"Erro no cadastro: {e}")
    else:
        with st.form("login_form"):
            st.subheader("📱 Login do Estabelecimento (Empresa)")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df_lista_empresas = pd.read_sql("SELECT id, nome_empresa FROM empresas ORDER BY nome_empresa", conn)
                
            dict_empresas = {row["nome_empresa"]: row["id"] for _, row in df_lista_empresas.iterrows()} if not df_lista_empresas.empty else {}
            if dict_empresas:
                empresa_selecionada = st.selectbox("Selecione sua Empresa:", list(dict_empresas.keys()))
                user_input = st.text_input("Usuário Master da Empresa:")
                senha_input = st.text_input("Senha Master:", type="password")
                if st.form_submit_button("Liberar Terminal", type="primary"):
                    id_empresa_login = dict_empresas[empresa_selecionada]
                    with ob_cx() as c, c.cursor() as cur:
                        cur.execute("SET search_path TO public; SELECT empresa_id, senha FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (id_empresa_login, user_input.strip(), senha_input.strip()))
                        resultado = cur.fetchone()
                    if resultado:
                        st.session_state.logado = True
                        st.session_state.empresa_id_atual = int(resultado[0])
                        st.session_state.senha_master_empresa = str(resultado[1])
                        st.rerun()
                    else: 
                        st.error("Credenciais da empresa incorretas!")
            else: 
                st.info("Nenhuma empresa cadastrada ainda.")
    conn.close()
    st.stop()

def render_painel_gerencial(emp_id, cats=None):
    """Renderiza o painel gerencial administrativo protegido por senha."""
    permitir_render_gerencial = False
    
    if st.button("🔒 Bloquear Terminal da Empresa por Completo", type="primary", use_container_width=True):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.garcom_logado = False
        st.session_state.carrinho = []
        st.rerun()
        
    st.markdown("---")
    st.subheader("🔑 Autenticação Gerencial Requerida")
    senha_gerencial_digitada = st.text_input("Insira a Senha Master para desbloquear as funções de Gerência:", type="password")
    
    if senha_gerencial_digitada == st.session_state.senha_master_empresa:
        permitir_render_gerencial = True
        st.success("🔓 Acesso Gerencial Liberado!")
    elif senha_gerencial_digitada != "":
        st.error("🔒 Senha Gerencial Incorreta!")

    if permitir_render_gerencial:
        st.markdown("---")
        menu_gerencial = st.selectbox("Selecione o Módulo Gerencial:", ["Painel de Vendas & Caixa", "Estoque & Insumos", "Produtos & Ficha Técnica"])

        if menu_gerencial == "Painel de Vendas & Caixa":
            st.subheader("📊 Relatório de Pedidos do Estabelecimento")
            with ob_cx() as c:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    df_pedidos = pd.read_sql(f"SELECT p.id, p.mesa, prod.nome, p.quantidade, p.status, p.horario, p.garcom, p.modo_pagamento, p.pago, prod.preco FROM pedidos p JOIN produtos prod ON p.produto_id = prod.id WHERE p.empresa_id = {emp_id} ORDER BY p.id DESC", c)
            
            if not df_pedidos.empty:
                df_pedidos["Total (R$)"] = df_pedidos["quantidade"] * df_pedidos["preco"]
                st.dataframe(df_pedidos[["id", "mesa", "nome", "quantidade", "Total (R$)", "status", "horario", "garcom", "pago", "modo_pagamento"]], use_container_width=True)
                
                st.subheader("🧾 Fechamento de Conta")
                mesas_ativas = df_pedidos[df_pedidos["pago"] == "Não"]["mesa"].unique()
                
                if len(mesas_ativas) > 0:
                    mesa_fechar = st.selectbox("Mesa para Fechamento:", mesas_ativas)
                    df_mesa = df_pedidos[(df_pedidos["mesa"] == mesa_fechar) & (df_pedidos["pago"] == "Não")]
                    
                    st.markdown(f"#### 📋 Consumo Atual - {mesa_fechar}:")
                    for _, row in df_mesa.iterrows():
                        st.text(f"• {int(row['quantidade'])}x {row['nome']} — R$ {row['Total (R$)']:.2f} ({row['horario']})")
                    
                    subtotal = df_mesa["Total (R$)"].sum()
                    taxa_servico = subtotal * 0.10
                    total_geral = subtotal + taxa_servico
                    
                    st.write("---")
                    st.metric("Subtotal", f"R$ {subtotal:.2f}")
                    st.metric("Taxa de Serviço (10%)", f"R$ {taxa_servico:.2f}")
                    st.markdown(f"### **Total Geral: R$ {total_geral:.2f}**")
                    
                    forma_pag = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX"])
                    if st.button("Confirmar Pagamento e Baixar Conta", type="primary"):
                        with ob_cx() as c, c.cursor() as cur:
                            cur.execute("UPDATE pedidos SET pago = 'Sim', modo_pagamento = %s, status = 'Entregue' WHERE empresa_id = %s AND mesa = %s AND pago = 'Não'", (forma_pag, emp_id, mesa_fechar))
                            c.commit()
                        st.success(f"Conta da {mesa_fechar} baixada com sucesso!")
                        st.rerun()
                else: 
                    st.info("Nenhum pedido pendente de pagamento.")
            else: 
                st.info("Nenhum pedido realizado ainda.")

        elif menu_gerencial == "Estoque & Insumos":
            st.subheader("🥦 Controle de Insumos / Estoque")
            with st.form("add_estoque"):
                novo_insumo = st.text_input("Nome do Insumo (ex: Limão, Rum, Batata):").strip()
                qtd_inicial = st.number_input("Quantidade Inicial:", min_value=0.0, step=0.1)
                if st.form_submit_button("Salvar Insumo"):
                    if novo_insumo:
                        st.success(f"Insumo '{novo_insumo}' registrado com sucesso com quantidade de {qtd_inicial}!")
                    else:
                        st.error("Insira um nome válido para o insumo.")
                        
        elif menu_gerencial == "Produtos & Ficha Técnica":
            st.subheader("🍳 Gerenciamento de Produtos & Ficha Técnica")
            st.info("Módulo de engenharia de cardápio e associação de insumos.")
def render_painel_operacional(emp_id):
    """Módulo padrão de lançamento de pedidos na mesa."""
    st.title("🍽️ Terminal de Lançamento de Pedidos")
    
    with ob_cx() as c:
        try:
            df_produtos = pd.read_sql(f"SELECT id, nome, preco FROM produtos WHERE empresa_id = {emp_id} ORDER BY nome", c)
        except Exception:
            df_produtos = pd.DataFrame(columns=["id", "nome", "preco"])
            
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Novo Lançamento")
        mesa = st.text_input("Número/Identificação da Mesa (ex: Mesa 04):").strip()
        
        if not df_produtos.empty:
            dict_produtos = {row["nome"]: (row["id"], row["preco"]) for _, row in df_produtos.iterrows()}
            prod_selecionado = st.selectbox("Selecione o Produto:", list(dict_produtos.keys()))
            qtd = st.number_input("Quantidade:", min_value=1, value=1, step=1)
            garcom = st.text_input("Nome do Atendente/Garçom:").strip()
            
            if st.button("➕ Adicionar ao Pedido", use_container_width=True):
                if mesa and garcom:
                    p_id, preco = dict_produtos[prod_selecionado]
                    item_pedido = {
                        "produto_id": p_id,
                        "nome": prod_selecionado,
                        "quantidade": qtd,
                        "mesa": mesa,
                        "garcom": garcom,
                        "preco": preco
                    }
                    st.session_state.carrinho.append(item_pedido)
                    st.toast(f"{qtd}x {prod_selecionado} adicionado!", icon="🛒")
                else:
                    st.warning("Preencha a Mesa e o Garçom antes de adicionar!")
        else:
            st.info("Nenhum produto cadastrado no sistema para esta empresa.")
            
    with col2:
        st.subheader("🛒 Itens Prontos para Envio")
        if st.session_state.carrinho:
            df_car = pd.DataFrame(st.session_state.carrinho)
            df_car["Subtotal"] = df_car["quantidade"] * df_car["preco"]
            st.dataframe(df_car[["mesa", "nome", "quantidade", "Subtotal", "garcom"]], use_container_width=True)
            
            c1, c2 = st.columns(2)
            if c1.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.carrinho = []
                st.rerun()
                
            if c2.button("🚀 Confirmar e Enviar para Cozinha/Bar", type="primary", use_container_width=True):
                try:
                    with ob_cx() as c, c.cursor() as cur:
                        for item in st.session_state.carrinho:
                            cur.execute(
                                """INSERT INTO pedidos (empresa_id, mesa, produto_id, quantidade, status, garcom, pago) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                (emp_id, item["mesa"], item["produto_id"], item["quantidade"], "Pendente", item["garcom"], "Não")
                            )
                        c.commit()
                    st.success("✅ Todos os pedidos foram enviados com sucesso!")
                    st.session_state.carrinho = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar pedidos: {e}")
        else:
            st.info("Nenhum item na fila de lançamento.")

# =====================================================================
# ROTEADOR DE FLUXO DA APLICAÇÃO (Interface principal)
# =====================================================================
if not st.session_state.logado:
    render_login_cadastro()
else:
    aba_modulo = st.sidebar.selectbox("Módulos do Sistema:", ["Frente de Lançamentos", "Painel Administrativo"])
    
    if st.sidebar.button("🔒 Desconectar Sessão", use_container_width=True):
        st.session_state.logado = False
        st.session_state.empresa_id_atual = None
        st.session_state.senha_master_empresa = ""
        st.session_state.garcom_logado = False
        st.session_state.carrinho = []
        st.rerun()
        
    if aba_modulo == "Frente de Lançamentos":
        render_painel_operacional(st.session_state.empresa_id_atual)
    else:
        render_painel_gerencial(st.session_state.empresa_id_atual)
