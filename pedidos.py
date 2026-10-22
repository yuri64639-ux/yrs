import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Configuração e injeção de CSS responsivo focado em telas de celulares e maquininhas
st.set_page_config(page_title="Caixa Mobile", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* OCULTA TOTALMENTE OS ELEMENTOS PADRÃO DO STREAMLIT (Estrela, Lápis, Share, 3 Pontinhos) */
    header, [data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    .stDeployButton {
        display: none !important;
        visibility: hidden !important;
    }

    /* Compactação total para telas pequenas (evita rolagens horizontais) */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    h1 { font-size: 1.6rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.3rem !important; margin-top: 0.5rem !important; }
    h3 { font-size: 1.1rem !important; margin-top: 0.5rem !important; }
    
    /* Remove espaçamentos exagerados e força preenchimento completo no celular */
    [data-testid="column"] { padding: 0.2rem 0rem !important; width: 100% !important; min-width: 100% !important; }
    div.stButton > button { margin-top: 5px !important; font-size: 1rem !important; padding: 0.5rem !important; }
    div[data-testid="stForm"] { padding: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
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
                    total NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                    taxa_inclusa BOOLEAN NOT NULL DEFAULT FALSE,
                    mesa_numero VARCHAR(50) DEFAULT 'Balcão',
                    comanda_codigo VARCHAR(100) DEFAULT 'Não Informado',
                    forma_pagamento VARCHAR(50) DEFAULT 'Mesa Aberta',
                    metodo_pagamento VARCHAR(50) DEFAULT 'Não Informado',
                    garcao_nome VARCHAR(255) DEFAULT 'Sistema',
                    status_conta VARCHAR(50) DEFAULT 'Aberta',
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        conn.close()

upgrade_db_silencioso()
# --- INICIALIZAÇÃO DE MEMÓRIA E ESTADOS ---
if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}
if "produtos_cache" not in st.session_state:
    st.session_state.produtos_cache = []
if "ultimo_carregamento_produtos" not in st.session_state:
    st.session_state.ultimo_carregamento_produtos = 0.0
if "gerente_autenticado" not in st.session_state:
    st.session_state.gerente_autenticado = False
if "input_mesa_salva" not in st.session_state:
    st.session_state.input_mesa_salva = ""
if "input_comanda_salva" not in st.session_state:
    st.session_state.input_comanda_salva = ""

# Sistema Anti-F5 para manter o operador logado no smartphone
if "garcao" in st.query_params:
    st.session_state.usuario_autenticado = True
    st.session_state.garcao_atual = st.query_params["garcao"]
else:
    if "usuario_autenticado" not in st.session_state:
        st.session_state.usuario_autenticado = False
    if "garcao_atual" not in st.session_state:
        st.session_state.garcao_atual = ""

# --- FLUXO DE LOGIN DINÂMICO ADAPTADO PARA CELULAR ---
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

    st.markdown("<h2 style='text-align: center;'>🔐 Login Operador</h2>", unsafe_allow_html=True)
    nome_input = st.selectbox("Selecione seu Nome:", options=lista_garcons_db)
    senha_input = st.text_input("Senha / Código Operacional:", type="password")
    
    if st.button("Entrar no Sistema", type="primary", use_container_width=True):
        if nome_input == "Gerente" and senha_input == "admin":
            st.session_state.usuario_autenticado = True
            st.session_state.garcao_atual = nome_input
            st.query_params["garcao"] = nome_input
            st.success("Acesso Autorizado!")
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
                st.error("Senha Incorreta!")
    st.stop()

# Renovação automática do cache de produtos (30 segundos)
tempo_atual = time.time()
if not st.session_state.produtos_cache or (tempo_atual - st.session_state.ultimo_carregamento_produtos > 30):
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
            st.session_state.produtos_cache = cur.fetchall()
        conn.close()
        st.session_state.ultimo_carregamento_produtos = tempo_atual

# Cabeçalho compacto para celular
st.markdown(f"👤 Operador: **{st.session_state.garcao_atual}**")

st.markdown("---")
# Criação das Abas em formato amigável para telas touch screen
tabs = st.tabs(["🛍️ Lançar", "🗂️ Mesas", "🔐 ADM"])
# --- ABA 1: OPERAÇÃO DE LANÇAMENTO VERTICALIZADO ---
with tabs[0]:
    st.markdown("### 👤 Atendimento")
    input_mesa = st.text_input("🪑 Número da Mesa:", value=st.session_state.input_mesa_salva, placeholder="Ex: 04", key="input_mesa_real")
    st.session_state.input_mesa_salva = input_mesa
    
    input_comanda = st.text_input("📋 Código da Comanda:", value=st.session_state.input_comanda_salva, placeholder="Ex: 1042", key="input_comanda_real")
    st.session_state.input_comanda_salva = input_comanda

    st.markdown("---")
    st.markdown("### 🔍 Cardápio")
    busca_termo = st.text_input("🔎 Pesquisar Item:", placeholder="Digite o nome do produto...")

    produtos_filtrados = [p for p in st.session_state.produtos_cache if busca_termo.lower() in p['nome'].lower()] if busca_termo else st.session_state.produtos_cache

    if not produtos_filtrados:
        st.warning("Produto não encontrado.")
    else:
        for prod in produtos_filtrados:
            p_base = float(prod['preco'])
            with st.container(border=True):
                st.markdown(f"**{prod['nome']}**")
                st.markdown(f"Preço: `R$ {p_base:.2f}`")
                
                col_m_qtd, col_m_btn = st.columns([0.4, 0.6])
                with col_m_qtd:
                    qtd_p = st.number_input("Qtd", min_value=1, value=1, key=f"caixa_qtd_{prod['id']}", label_visibility="collapsed")
                with col_m_btn:
                    if st.button("➕ Adicionar", key=f"add_cart_{prod['id']}", use_container_width=True, type="secondary"):
                        p_id = str(prod['id'])
                        if p_id in st.session_state.carrinho:
                            st.session_state.carrinho[p_id]["qtd"] += qtd_p
                        else:
                            st.session_state.carrinho[p_id] = {"nome": prod['nome'], "preco": p_base, "qtd": qtd_p, "id_real": prod['id']}
                        st.toast(f"Adicionado: {qtd_p}x {prod['nome']}")

    st.markdown("---")
    st.markdown("### 📋 Seu Carrinho Atual")

    if not st.session_state.carrinho:
        st.info("Carrinho vazio.")
    else:
        st.caption(f"Mesa: {input_mesa.strip()} | Comanda: {input_comanda.strip()}")
        total_geral_carrinho = 0.0
        itens_remover = []
        
        for k, item in st.session_state.carrinho.items():
            sub_total_item = item["preco"] * item["qtd"]
            total_geral_carrinho += sub_total_item
            
            with st.container(border=True):
                col_c_txt, col_c_del = st.columns([0.8, 0.2])
                with col_c_txt:
                    st.markdown(f"**{item['nome']}**")
                    st.caption(f"{item['qtd']} un x R\$ {item['preco']:.2f} = **R\$ {sub_total_item:.2f}**")
                with col_c_del:
                    if st.button("❌", key=f"del_item_cart_{k}", use_container_width=True):
                        itens_remover.append(k)
                        
        for k in itens_remover:
            del st.session_state.carrinho[k]
            st.rerun()
            
        st.markdown(f"#### 💰 Total Acumulado: **R\$ {total_geral_carrinho:.2f}**")
        
        if st.button("✅ Enviar Pedido", type="primary", use_container_width=True):
            if not input_mesa.strip():
                st.error("Informe a Mesa!")
            elif not input_comanda.strip():
                st.error("Informe a Comanda!")
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
                                        st.error(f"Sem estoque: {f_item['nome']}")
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
                                st.session_state.input_mesa_salva = ""
                                st.session_state.input_comanda_salva = ""
                                st.success("Pedido Enviado!")
                                time.sleep(0.4)
                                st.rerun()
                    except Exception as err:
                        st.error(f"Erro no banco: {err}")
                    finally:
                        conn.close()
                        
        if st.button("🗑️ Limpar Carrinho", key="btn_limpar_bandeja_master", type="secondary", use_container_width=True):
            st.session_state.carrinho = {}
            st.rerun()
# --- ABA 2: MONITOR DE MESAS - TOTALMENTE EMPILHADO ---
with tabs[1]:
    st.markdown("### 🗂️ Consumo no Salão")
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT DISTINCT mesa_numero FROM pedidos_realizados WHERE status_conta = 'Aberta' ORDER BY mesa_numero;")
            mesas_abertas = cur.fetchall()
            if not mesas_abertas:
                st.info("Nenhuma mesa aberta no momento.")
            else:
                for m in mesas_abertas:
                    with st.expander(f"🪑 {m['mesa_numero']}"):
                        cur.execute("""
                            SELECT produto_nome, comanda_codigo, garcao_nome, SUM(quantidade_pedida) as total_qtd, SUM(valor_total) as total_financeiro 
                            FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta' GROUP BY produto_nome, comanda_codigo, garcao_nome ORDER BY produto_nome;
                        """, (m['mesa_numero'],))
                        itens_mesa = cur.fetchall()
                        if itens_mesa:
                            subtotal_mesa = sum(float(it['total_financeiro']) for it in itens_mesa)
                            st.markdown(f"**Identificador Comanda:** `{itens_mesa[0]['comanda_codigo']}`")
                            st.markdown(f"**Total Acumulado:** `R$ {subtotal_mesa:.2f}`")
                            st.markdown("---")
                            for it in itens_mesa:
                                st.markdown(f"• **{it['total_qtd']}x** {it['produto_nome']} — `R$ {float(it['total_financeiro']):.2f}`")
        conn.close()
# --- ABA 3: GERÊNCIA E AUDITORIA PARA DISPOSITIVOS MÓVEIS ---
with tabs[2]:
    if not st.session_state.gerente_autenticado:
        st.markdown("### 🔐 Painel Master Gerencial")
        senha_gerencia = st.text_input("Credencial Master:", type="password", key="senha_master_gerencia")
        if st.button("Liberar Painel", type="primary", use_container_width=True):
            if senha_gerencia == "admin":
                st.session_state.gerente_autenticado = True
                st.success("Módulo Liberado!")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("Senha Incorreta!")
    else:
        st.markdown("### 🚀 Operações Especiais")
        if st.button("🔒 Trancar Painel ADM", use_container_width=True):
            st.session_state.gerente_autenticado = False
            st.rerun()
        
        opcao_adm = st.radio("Selecione a ação:", ["💰 Fechar", "❌ Cancelar", "🔄 Transferir"], horizontal=True)
        
        conn = init_connection()
        if conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT DISTINCT mesa_numero FROM pedidos_realizados WHERE status_conta = 'Aberta' ORDER BY mesa_numero;")
                lista_mesas_gerencia = [r['mesa_numero'] for r in cur.fetchall()]
                
                if opcao_adm == "💰 Fechar":
                    if not lista_mesas_gerencia:
                        st.info("Nenhuma comanda para faturamento.")
                    else:
                        mesa_fechar = st.selectbox("Selecione a Mesa para Encerrar:", options=lista_mesas_gerencia, key="sel_fechar_m")
                        cur.execute("SELECT id, produto_nome, quantidade_pedida, valor_total FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_fechar,))
                        itens_f = cur.fetchall()
                        
                        sub_f = sum(float(i['valor_total']) for i in itens_f)
                        st.write(f"Consumo Original: R$ {sub_f:.2f}")
                        
                        aplicar_10 = st.checkbox("Incluir Taxa de 10%", value=True, key="chk_taxa_10_gerencia")
                        forma_p = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Pix", "Crédito", "Débito"], key="sel_forma_p_gerencia")
                        
                        fator_multiplicador = 1.10 if aplicar_10 else 1.00
                        valor_final_f = sub_f * fator_multiplicador
                        st.markdown(f"### Total Final: **R$ {valor_final_f:.2f}**")
                        
                        if st.button("🖨️ Registrar Baixa e Fechar", type="primary", use_container_width=True):
                            ids_fechar = [item['id'] for item in itens_f]
                            cur.execute("""
                                UPDATE pedidos_realizados 
                                SET status_conta = 'Fechada', 
                                    forma_pagamento = %s, 
                                    total = valor_total * %s,
                                    valor_total = valor_total * %s, 
                                    taxa_inclusa = %s 
                                WHERE id = ANY(%s);
                            """, (forma_p, fator_multiplicador, fator_multiplicador, aplicar_10, ids_fechar))
                            conn.commit()
                            st.success("Conta Encerrada com Sucesso!")
                            time.sleep(0.4)
                            st.rerun()

                elif opcao_adm == "❌ Cancelar":
                    if not lista_mesas_gerencia:
                        st.info("Nenhum item aberto para estorno.")
                    else:
                        mesa_estorno = st.selectbox("Selecione a Mesa:", options=lista_mesas_gerencia, key="sel_estorno_m")
                        cur.execute("SELECT id, produto_nome, quantidade_pedida FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_estorno,))
                        itens_estornar = cur.fetchall()
                        
                        opcoes_estorno = {f"{i['quantidade_pedida']}x {i['produto_nome']}": i for i in itens_estornar}
                        if not opcoes_estorno:
                            st.info("Mesa sem itens ativos.")
                        else:
                            item_sel_estorno = st.selectbox("Escolha o Item Incorreto:", options=list(opcoes_estorno.keys()))
                            obj_estorno = opcoes_estorno[item_sel_estorno]
                            
                            if st.button("❌ Remover e Devolver Insumo", type="primary", use_container_width=True):
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
                                st.success("Lançamento Desfeito!")
                                time.sleep(0.4)
                                st.rerun()

                elif opcao_adm == "🔄 Transferir":
                    if not lista_mesas_gerencia:
                        st.info("Nenhum item ativo para transferência.")
                    else:
                        mesa_origem = st.selectbox("Mesa de Origem:", options=lista_mesas_gerencia, key="sel_trans_origem")
                        cur.execute("SELECT id, produto_nome, quantidade_pedida FROM pedidos_realizados WHERE mesa_numero = %s AND status_conta = 'Aberta';", (mesa_origem,))
                        itens_trans = cur.fetchall()
                        
                        opcoes_trans = {f"{i['quantidade_pedida']}x {i['produto_nome']}": i for i in itens_trans}
                        if not opcoes_trans:
                            st.info("Sem itens para transferir.")
                        else:
                            item_sel_trans = st.selectbox("Escolha o Item a Mudar:", options=list(opcoes_trans.keys()))
                            obj_trans = opcoes_trans[item_sel_trans]
                            mesa_destino = st.text_input("Nova Mesa Destino (Número):")
                            
                            if st.button("🔄 Confirmar Transferência", type="primary", use_container_width=True):
                                if not mesa_destino.strip():
                                    st.error("Informe a mesa di destino!")
                                else:
                                    cur.execute("UPDATE pedidos_realizados SET mesa_numero = %s WHERE id = %s;", (mesa_destino.strip(), obj_trans['id']))
                                    conn.commit()
                                    st.success("Item Transferido de Mesa!")
                                    time.sleep(0.5)
                                    st.rerun()
            conn.close()

# --- ULTIMO ELEMENTO DO APP: BOTÃO DE SAIR NO RODAPÉ ---
st.markdown("---")
if st.button("🚪 Desconectar Sistema", type="secondary", use_container_width=True, key="btn_sair_rodape_final"):
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
