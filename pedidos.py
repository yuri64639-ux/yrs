import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

st.set_page_config(page_title="Frente de Caixa & Pedidos", layout="wide")

def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def upgrade_db_silencioso():
    conn = init_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pedidos_realizados (
                    id SERIAL PRIMARY KEY,
                    produto_nome VARCHAR(255) NOT NULL,
                    quantidade_pedida INT NOT NULL,
                    valor_total NUMERIC(10,2) NOT NULL,
                    taxa_inclusa BOOLEAN NOT NULL DEFAULT FALSE,
                    mesa_numero VARCHAR(50) DEFAULT 'Balcão',
                    comanda_codigo VARCHAR(100) DEFAULT 'Não Informado',
                    forma_pagamento VARCHAR(50) DEFAULT 'Mesa Aberta',
                    garcao_nome VARCHAR(255) DEFAULT 'Sistema',
                    status_conta VARCHAR(50) DEFAULT 'Aberta',
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            try:
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS total NUMERIC(10, 2) NOT NULL DEFAULT 0.00;")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS metodo_pagamento VARCHAR(50) NOT NULL DEFAULT 'Não Informado';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS status_conta VARCHAR(50) DEFAULT 'Aberta';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS mesa_numero VARCHAR(50) DEFAULT 'Balcão';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS comanda_codigo VARCHAR(100) DEFAULT 'Não Informado';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS forma_pagamento VARCHAR(50) DEFAULT 'Dinheiro';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS garcao_nome VARCHAR(255) DEFAULT 'Sistema';")
            except:
                pass
            conn.commit()
        conn.close()

upgrade_db_silencioso()

if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}
if "produtos_cache" not in st.session_state:
    st.session_state.produtos_cache = []
if "ultimo_carregamento_produtos" not in st.session_state:
    st.session_state.ultimo_carregamento_produtos = 0.0
if "gerente_autenticado" not in st.session_state:
    st.session_state.gerente_autenticado = False

if "garcao" in st.query_params:
    st.session_state.usuario_autenticado = True
    st.session_state.garcao_atual = st.query_params["garcao"]
else:
    if "usuario_autenticado" not in st.session_state:
        st.session_state.usuario_autenticado = False
    if "garcao_atual" not in st.session_state:
        st.session_state.garcao_atual = ""

if not st.session_state.usuario_autenticado:
    lista_garcons_db = ["Gerente"]
    conn = init_connection()
    if conn:
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT nome FROM cadastros_garcons ORDER BY nome;")
                lista_garcons_db += [row[0] for row in cur.fetchall()]
            except:
                pass
        conn.close()

    st.container()
    col_l1, col_l2, col_l3 = st.columns([0.1, 0.8, 0.1])
    with col_l2:
        st.markdown("<h2 style='text-align: center;'>🔐 Login Operador</h2>", unsafe_allow_html=True)
        nome_input = st.selectbox("Selecione seu Nome:", options=lista_garcons_db)
        senha_input = st.text_input("Sua Senha / Código Operacional:", type="password")
        
        if st.button("Entrar no Sistema", type="primary", use_container_width=True):
            if nome_input == "Gerente" and senha_input == "admin":
                st.session_state.usuario_autenticado = True
                st.session_state.garcao_atual = nome_input
                st.query_params["garcao"] = nome_input
                st.success("Acesso Gerencial Autorizado!")
                time.sleep(0.3)
                st.rerun()
            else:
                conn = init_connection()
                autenticado_db = False
                if conn:
                    with conn.cursor() as cur:
                        try:
                            cur.execute("SELECT nome FROM cadastros_garcons WHERE nome = %s AND codigo_operacional = %s;", (nome_input, senha_input.strip()))
                            if cur.fetchone():
                                autenticado_db = True
                        except:
                            pass
                    conn.close()
                
                if autenticado_db:
                    st.session_state.usuario_autenticado = True
                    st.session_state.garcao_atual = nome_input
                    st.query_params["garcao"] = nome_input
                    st.success(f"Bem-vindo, {nome_input}!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("Senha Incorreta para o garçom selecionado!")
    st.stop()
tempo_atual = time.time()
if not st.session_state.produtos_cache or (tempo_atual - st.session_state.ultimo_carregamento_produtos > 30):
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
            st.session_state.produtos_cache = cur.fetchall()
        conn.close()
        st.session_state.ultimo_carregamento_produtos = tempo_atual

col_titulo, col_logout = st.columns([0.7, 0.3])
with col_titulo:
    st.title("🛒 Caixa & Salão")
with col_logout:
    st.markdown(f"👤 **{st.session_state.garcao_atual}**")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario_autenticado = False
        st.session_state.garcao_atual = ""
        st.session_state.carrinho = {}
        st.session_state.gerente_autenticado = False
        st.query_params.clear()
        st.rerun()

st.markdown("---")
tabs = st.tabs(["🛍️ Lançar Pedidos", "🗂️ Mesas Abertas", "🔐 Gerência"])

with tabs[0]:
    st.subheader("👤 Identificação do Atendimento")
    col_mesa, col_comanda = st.columns(2)
    with col_mesa:
        input_mesa = st.text_input("🪑 Número da Mesa:", placeholder="Ex: Mesa 04")
    with col_comanda:
        input_comanda = st.text_input("📋 Código da Comanda:", placeholder="Ex: 1042")

    st.markdown("---")
    st.subheader("🔍 Encontrar Itens")
    busca_termo = st.text_input("🔍 Buscar Produto (Lupa):", placeholder="Ex: Batata Frita")

    produtos_filtrados = [p for p in st.session_state.produtos_cache if busca_termo.lower() in p['nome'].lower()] if busca_termo else []

    if busca_termo and not produtos_filtrados:
        st.warning("Nenhum produto encontrado no cardápio.")
    else:
        for prod in produtos_filtrados:
            col_n, col_p, col_q, col_b = st.columns([0.4, 0.2, 0.2, 0.2])
            p_base = float(prod['preco'])
            with col_n:
                st.markdown(f"**{prod['nome']}**")
            with col_p:
                st.markdown(f"R\\\\$ {p_base:.2f}")
            with col_q:
                qtd_p = st.number_input("Quantidade", min_value=1, value=1, key=f"caixa_qtd_{prod['id']}")
            with col_b:
                if st.button("➕ Selecionar Item", key=f"add_cart_{prod['id']}", use_container_width=True):
                    p_id = str(prod['id'])
                    if p_id in st.session_state.carrinho:
                        st.session_state.carrinho[p_id]["qtd"] += qtd_p
                    else:
                        st.session_state.carrinho[p_id] = {"nome": prod['nome'], "preco": p_base, "qtd": qtd_p, "id_real": prod['id']}
                    st.toast(f"Adicionado: {qtd_p}x {prod['nome']}")

    st.markdown("---")
    st.subheader("📋 Conferir Seleção Atual (Carrinho)")

    if not st.session_state.carrinho:
        st.info("Nenhum item selecionado na bandeja temporária.")
    else:
        st.markdown(f"**Destino:** {input_mesa.strip()} | **Comanda:** {input_comanda.strip()}")
        total_geral_carrinho = 0.0
        itens_remover = []
        
        for k, item in st.session_state.carrinho.items():
            col_c_nome, col_c_qtd, col_c_sub, col_c_del = st.columns([0.4, 0.2, 0.2, 0.2])
            sub_total_item = item["preco"] * item["qtd"]
            total_geral_carrinho += sub_total_item
            with col_c_nome:
                st.write(f"• **{item['nome']}** (R\\\\$ {item['preco']:.2f})")
            with col_c_qtd:
                st.write(f"{item['qtd']} un")
            with col_c_sub:
                st.write(f"R\\\\$ {sub_total_item:.2f}")
            with col_c_del:
                if st.button("Tirar", key=f"del_item_cart_{k}", use_container_width=True):
                    itens_remover.append(k)
                    
        for k in itens_remover:
            del st.session_state.carrinho[k]
            st.rerun()
            
        st.markdown(f"### Total Acumulado do Pedido: R\\\\$ {total_geral_carrinho:.2f}")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("✅ Confirmar e Enviar Pedido", type="primary", use_container_width=True):
                if not input_mesa.strip() or input_mesa.strip().lower() in ["balcão", ""]:
                    st.error("🚨 LANÇAMENTO RECUSADO: Você deve informar o número da Mesa.")
                elif not input_comanda.strip() or input_comanda.strip().lower() in ["não informado", ""]:
                    st.error("🚨 LANÇAMENTO RECUSADO: O código da Comanda é obrigatório.")
                else:
                    conn = init_connection()
                    if conn:
                        try:
                            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                                erro_estoque = False
                                ids_produtos = [item['id_real'] for item in st.session_state.carrinho.values()]
                                
                                cur.execute("""
                                    SELECT f.produto_id, f.insumo_id, f.quantidade, i.nome, i.quantidade_atual 
                                    FROM ficha_tecnica f 
                                    JOIN insumos i ON f.insumo_id = i.id 
                                    WHERE f.produto_id = ANY(%s);
                                """, (ids_produtos,))
                                todas_fichas = cur.fetchall()
                                
                                mapa_fichas = {}
                                for row in todas_fichas:
                                    if row['produto_id'] not in mapa_fichas:
                                        mapa_fichas[row['produto_id']] = []
                                    mapa_fichas[row['produto_id']].append(row)
                                
                                for item in st.session_state.carrinho.values():
                                    ficha = mapa_fichas.get(item['id_real'], [])
                                    for f_item in ficha:
                                        consumo_necessario = (float(f_item['quantidade']) / 1000.0) * item['qtd']
                                        if float(f_item['quantidade_atual']) < consumo_necessario:
                                            st.error(f"Estoque Insuficiente de '{f_item['nome']}'!")
                                            erro_estoque = True
                                
                                if not erro_estoque:
                                    for item in st.session_state.carrinho.values():
                                        ficha = mapa_fichas.get(item['id_real'], [])
                                        for f_item in ficha:
                                            consumo = (float(f_item['quantidade']) / 1000.0) * item['qtd']
                                            cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual - %s WHERE id = %s;", (consumo, f_item['insumo_id']))
                                        
                                        valor_venda_item = item["preco"] * item["qtd"]
                                        cur.execute("""
                                            INSERT INTO pedidos_realizados (produto_nome, quantidade_pedida, valor_total, total, forma_pagamento, metodo_pagamento, taxa_inclusa, mesa_numero, comanda_codigo, status_conta, garcao_nome) 
                                            VALUES (%s, %s, %s, %s, 'Mesa Aberta', 'Mesa Aberta', FALSE, %s, %s, 'Aberta', %s);
                                        """, (item['nome'], item['qtd'], valor_venda_item, valor_venda_item, input_mesa.strip(), input_comanda.strip(), st.session_state.garcao_atual))
                                    
                                    conn.commit()
                                    st.session_state.carrinho = {}
                                    st.success("Comanda enviada com sucesso!")
                                    time.sleep(0.4)
                                    st.rerun()
                        except Exception as err:
                            st.error(f"Erro de transação no banco: {err}")
                        finally:
                            conn.close()
        with col_c2:
            if st.button("🗑️ Limpar Toda a Bandeja", use_container_width=True):
                st.session_state.carrinho = {}
                st.rerun()
with tabs[1]:
    st.subheader("🗂️ Painel de Acompanhamento de Mesas Ativas")
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT DISTINCT mesa_numero FROM pedidos_realizados WHERE status_conta = 'Aberta' ORDER BY mesa_numero;")
            mesas_abertas = cur.fetchall()
            if not mesas_abertas:
                st.info("Nenhuma mesa com consumo aberto no momento.")
            else:
                for m in mesas_abertas:
                    with st.expander(f"🪑 {m['mesa_numero']} (Toque para Carregar Conta)"):
                        cur.execute("""
                            SELECT produto_nome, comanda_codigo, garcao_nome, SUM(quantidade_pedida) as total_qtd, SUM(valor_total) as total_financeiro 
                            FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta' GROUP BY produto_nome, comanda_codigo, garcao_nome ORDER BY produto_nome;
                        """, (m['mesa_numero'],))
                        itens_mesa = cur.fetchall()
                        if itens_mesa:
                            subtotal_mesa = sum(float(it['total_financeiro']) for it in itens_mesa)
                            comanda_ref = itens_mesa[0]['comanda_codigo']
                            st.markdown(f"**Identificador Comanda:** `{comanda_ref}` | **Total: R\\\\$ {subtotal_mesa:.2f}**")
                            st.markdown("---")
                            for it in itens_mesa:
                                st.markdown(f"- **{it['total_qtd']}x** {it['produto_nome']} — R\\\\$ {float(it['total_financeiro']):.2f} *(Por: {it['garcao_nome']})*")
        conn.close()

with tabs[2]:
    if not st.session_state.gerente_autenticado:
        st.subheader("🔐 Módulo de Gestão Restrito ao Administrador")
        senha_gerencia = st.text_input("Insira a credencial master:", type="password", key="senha_master_gerencia")
        if st.button("Liberar Painel", type="primary", use_container_width=True):
            if senha_gerencia == "admin":
                st.session_state.gerente_autenticado = True
                st.success("Módulo de Auditoria Liberado!")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("Acesso Recusado: Senha Incorreta!")
    else:
        st.subheader("🚀 Operações Especiais de Caixa")
        if st.button("🔒 Trancar Painel Administrativo", use_container_width=True):
            st.session_state.gerente_autenticado = False
            st.rerun()
            
        g_tab1, g_tab2, g_tab3 = st.tabs(["💰 Fechar Conta", "❌ Cancelar Lançamento", "🔄 Transferir de Mesa"])
        
        conn = init_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT DISTINCT mesa_numero FROM pedidos_realizados WHERE status_conta = 'Aberta' ORDER BY mesa_numero;")
                    lista_mesas_gerencia = [r['mesa_numero'] for r in cur.fetchall()]
                    
                    with g_tab1:
                        if not lista_mesas_gerencia:
                            st.info("Não há comandas abertas para faturamento no salão.")
                        else:
                            mesa_fechar = st.selectbox("Selecione a Mesa para Encerrar:", options=lista_mesas_gerencia, key="sel_fechar_m")
                            cur.execute("SELECT id, produto_nome, quantidade_pedida, valor_total FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_fechar,))
                            itens_f = cur.fetchall()
                            
                            sub_f = sum(float(i['valor_total']) for i in itens_f)
                            st.write(f"**Consumo dos Produtos:** R\\\\$ {sub_f:.2f}")
                            
                            aplicar_10 = st.checkbox("Incluir Taxa de Serviço Opcional (10%)", value=True, key="chk_taxa_10_gerencia")
                            forma_p = st.selectbox("Método de Recebimento:", ["Dinheiro", "Pix", "Crédito", "Débito"], key="sel_forma_p_gerencia")
                            
                            multiplicador = 1.10 if aplicar_10 else 1.0
                            valor_final_f = sub_f * multiplicador
                            st.markdown(f"### Total Final do Caixa: R\\\\$ {valor_final_f:.2f}")
                            
                            if st.button("Confirmar Encerramento", type="primary", use_container_width=True):
                                ids_fechar = [item['id'] for item in itens_f]
                                cur.execute("""
                                    UPDATE pedidos_realizados 
                                    SET status_conta = 'Fechada', forma_pagamento = %s, metodo_pagamento = %s, valor_total = valor_total * %s, total = valor_total * %s, taxa_inclusa = %s 
                                    WHERE id = ANY(%s);
                                """, (forma_p, forma_p, multiplicador, multiplicador, aplicar_10, ids_fechar))
                                conn.commit()
                                st.success(f"Conta fechada e registrada sob o método: {forma_p}!")
                                time.sleep(0.4)
                                st.rerun()
                                
                    with g_tab2:
                        if not lista_mesas_gerencia:
                            st.info("Nenhum ativo disponível para estorno.")
                        else:
                            mesa_estorno = st.selectbox("Selecione a Mesa:", options=lista_mesas_gerencia, key="sel_estorno_m")
                            cur.execute("SELECT id, produto_nome, quantidade_pedida FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_estorno,))
                            itens_estornar = cur.fetchall()
                            
                            opcoes_estorno = {f"{i['quantidade_pedida']}x {i['produto_nome']} (ID Ref: {i['id']})": i for i in itens_estornar}
                            if not opcoes_estorno:
                                st.info("Nenhum item em aberto nesta comanda.")
                            else:
                                item_sel_estorno = st.selectbox("Escolha o Lançamento Incorreto:", options=list(opcoes_estorno.keys()))
                                obj_estorno = opcoes_estorno[item_sel_estorno]
                                
                                if st.button("❌ Estornar Item e Reabastecer Estoque", type="primary", use_container_width=True):
                                    cur.execute("""
                                        SELECT f.insumo_id, f.quantidade 
                                        FROM ficha_tecnica f 
                                        JOIN produtos p ON f.produto_id = p.id 
                                        WHERE p.nome = %s LIMIT 6;
                                    """, (obj_estorno['produto_nome'],))
                                    ficha_estorno = cur.fetchall()
                                    
                                    for f_e in ficha_estorno:
                                        devolucao = (float(f_e['quantidade']) / 1000.0) * int(obj_estorno['quantidade_pedida'])
                                        cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual + %s WHERE id = %s;", (devolucao, f_e['insumo_id']))
                                        
                                    cur.execute("DELETE FROM pedidos_realizados WHERE id = %s;", (obj_estorno['id'],))
                                    conn.commit()
                                    st.success("Transação desfeita e inventário estornado!")
                                    time.sleep(0.4)
                                    st.rerun()
                                    
                    with g_tab3:
                        if not lista_mesas_gerencia:
                            st.info("Nenhum ativo disponível para transferência.")
                        else:
                            mesa_origem = st.selectbox("Mesa de Origem:", options=lista_mesas_gerencia, key="sel_trans_origem")
                            cur.execute("SELECT id, produto_nome, quantidade_pedida FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_origem,))
                            itens_trans = cur.fetchall()
                            
                            opcoes_trans = {f"{i['quantidade_pedida']}x {i['produto_nome']} (ID Ref: {i['id']})": i for i in itens_trans}
                            if not opcoes_trans:
                                st.info("Nenhum item ativo nesta comanda.")
                            else:
                                item_sel_trans = st.selectbox("Item a transferir:", options=list(opcoes_trans.keys()))
                                obj_trans = opcoes_trans[item_sel_trans]
                                mesa_destino = st.text_input("Número da Nova Mesa de Destino:")
                                
                                if st.button("🔄 Confirmar Transferência", type="primary", use_container_width=True):
                                    if not mesa_destino.strip():
                                        st.error("Erro: Identifique o destino.")
                                    else:
                                        cur.execute("UPDATE pedidos_realizados SET mesa_numero = %s WHERE id = %s;", (mesa_destino.strip(), obj_trans['id']))
                                        conn.commit()
                                        st.success(f"Item transferido de forma permanente para a {mesa_destino}!")
                                        time.sleep(0.5)
