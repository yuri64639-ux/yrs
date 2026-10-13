# ==============================================================================
# VIEWS/GARCOM.PY - TERMINAL DE OPERAÇÃO DO GARÇOM E SALÃO
# ==============================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
from core.database import ob_cx

def f_login_garcom(emp_id, senha_master):
    st.subheader("👤 Identificação do Garçom")
    with st.form("l_garcom"):
        g_in = st.text_input("Usuário do Garçom:")
        s_in = st.text_input("Senha:", type="password")
        if st.form_submit_button("Entrar", type="primary"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public; SELECT usuario FROM usuarios WHERE empresa_id = %s AND LOWER(usuario) = LOWER(%s) AND senha = %s", (emp_id, g_in.strip().lower(), s_in.strip()))
                res = cur.fetchone()
            if res:
                st.session_state.garcom_logado = True
                st.session_state.usuario_atual = str(res[0])
                st.rerun()
            else: st.error("Incorreto!")
                
    with st.expander("Cadastrar Novo Garçom"):
        with st.form("cad_g"):
            ng = st.text_input("Nome Garçom:")
            sg = st.text_input("Senha Garçom:", type="password")
            sm = st.text_input("Senha Master Empresa:", type="password")
            if st.form_submit_button("Confirmar") and ng and sg and sm == senha_master:
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public; INSERT INTO usuarios (empresa_id, usuario, senha) VALUES (%s, %s, %s);", (emp_id, ng.strip(), sg.strip()))
                    c.commit()
                st.success("Salvo!")

def f_lancar_pedido(emp_id, conn):
    df_pv = pd.read_sql("SELECT id, nome, preco FROM produtos WHERE empresa_id = %s ORDER BY nome", conn, params=[emp_id])
    if df_pv.empty:
        st.info("Sem produtos.")
        return
    mesa = st.text_input("Mesa/Comanda:", value="Mesa 01")
    lupa = st.text_input("🔍 Buscar Produto:").strip()
    df_f = df_pv[df_pv['nome'].str.contains(lupa, case=False)] if lupa else df_pv
    p_map = {f"{r['nome']} - R$ {r['preco']:.2f}": (r['id'], r['nome']) for _, r in df_f.iterrows()}
    
    if p_map:
        p_sel = st.selectbox("Item:", list(p_map.keys()))
        qtd = st.number_input("Qtd:", min_value=1, value=1)
        if st.button("➕ Adicionar", use_container_width=True):
            id_prod, nome_prod = p_map[p_sel]
            st.session_state.carrinho.append({"id": int(id_prod), "nome": str(nome_prod), "qtd": int(qtd)})
            
    if st.session_state.carrinho:
        st.markdown("---")
        for i in st.session_state.carrinho: st.write(f"▪ *{i['qtd']}x* - {i['nome']}")
        if st.button("🚀 Enviar Pedido", type="primary", use_container_width=True):
            h = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                for i in st.session_state.carrinho:
                    cur.execute("INSERT INTO pedidos (empresa_id, mesa, produto_id, quantidade, status, horario, garcom, pago) VALUES (%s, %s, %s, %s, 'Pendente', %s, %s, 'Não')", (emp_id, mesa.strip(), int(i['id']), int(i['qtd']), h, st.session_state.usuario_atual))
                    rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM receitas WHERE empresa_id = %s AND produto_id = %s", c, params=[emp_id, int(i['id'])])
                    for _, r in rc.iterrows(): 
                        cur.execute("UPDATE estoque SET quantidade = quantidade - %s WHERE empresa_id = %s AND id = %s", (((float(r['qtd_insumo']) / 1000.0) * int(i['qtd'])), emp_id, int(r['insumo_id'])))
                c.commit()
            st.session_state.carrinho = []
            st.rerun()

def f_fechar_mesa(emp_id, conn):
    p_at = pd.read_sql("SELECT p.id, p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status FROM pedidos p JOIN produtos pr ON p.produto_id = pr.id WHERE p.empresa_id = %s AND p.status IN ('Pendente', 'Confirmado') ORDER BY p.mesa", conn, params=[emp_id])
    if p_at.empty:
        st.info("Sem comandas abertas.")
        return
    l_b = st.text_input("🔍 Buscar Mesa:").strip()
    df_m = p_at[p_at['mesa'].str.contains(l_b, case=False)] if l_b else p_at
    if not df_m.empty:
        m_ver = st.selectbox("Selecione a Mesa:", sorted(list(set(df_m['mesa'].tolist()))))
        df_mf = p_at[p_at['mesa'] == m_ver]
        if 'Pendente' in df_mf['status'].tolist() and st.button("✅ Confirmar Todos"):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public; UPDATE pedidos SET status = 'Confirmado' WHERE empresa_id = %s AND mesa = %s AND status = 'Pendente'", (emp_id, m_ver))
                c.commit()
            st.rerun()
        sub = float(df_mf['subtotal'].sum())
        st.metric("Total Consumo", f"R$ {sub:.2f}")
        
        f_pag = st.selectbox("Forma de Pagamento:", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"])
        if st.button("💰 Fechar Mesa", type="primary", use_container_width=True):
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public; UPDATE pedidos SET status = 'Finalizado (Pago)', pago = 'Sim', modo_pagamento = %s WHERE empresa_id = %s AND mesa = %s", (f_pag, emp_id, m_ver))
                c.commit()
            st.rerun()

def renderizar_terminal_garcom(emp_id, senha_master):
    if "garcom_logado" not in st.session_state: st.session_state.garcom_logado = False
    if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = ""
    if "carrinho" not in st.session_state: st.session_state.carrinho = []
    
    if not st.session_state.garcom_logado:
        f_login_garcom(emp_id, senha_master)
        return
        
    st.subheader(f"📋 Operador: {st.session_state.usuario_atual.upper()}")
    if st.button("🔒 Sair do Terminal", use_container_width=True):
        st.session_state.garcom_logado = False
        st.session_state.usuario_atual = ""
        st.session_state.carrinho = []
        st.rerun()
        
    conn = ob_cx()
    if conn is None: return
    
    op = st.radio("Ação:", ["➕ Lançar Pedido", "🧾 Fechar Mesas"], horizontal=True)
    if op == "➕ Lançar Pedido": f_lancar_pedido(emp_id, conn)
    elif op == "🧾 Fechar Mesas": f_fechar_mesa(emp_id, conn)
    conn.close()
