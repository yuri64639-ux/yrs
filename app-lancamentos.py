from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

# Configuração da página e estilo dos botões mobile
st.set_page_config(page_title="Gestão de Restaurante", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)

PASS, ADMIN = "orla123", "admin123"

# --- SISTEMA DE LOGIN SEGURO ---
if "logado" not in st.session_state: 
    st.session_state.logado = False

if not st.session_state.logado:
    with st.form("login_form"):
        st.subheader("🔑 Acesso ao Sistema")
        senha_input = st.text_input("Senha de Acesso:", type="password")
        if st.form_submit_button("Entrar", type="primary") and senha_input == PASS:
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- CONEXÃO DIRETA COM O BANCO DE DADOS EM NUVEM (POSTGRESQL) ---
def obter_conexao():
    credenciais = st.secrets["connections"]["postgresql"]
    return psycopg2.connect(
        host=credenciais["host"],
        port=credenciais["port"],
        database=credenciais["database"],
        user=credenciais["username"],
        password=credenciais["password"]
    )

# Estabelece a conexão e cria o cursor
conn_raw = obter_conexao()

# Inicialização das tabelas na nuvem
with conn_raw.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id SERIAL PRIMARY KEY, item TEXT UNIQUE, quantidade REAL
        );
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL, insumo_id INTEGER, qtd_insumo REAL
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1
        );
    """)
    conn_raw.commit()

# Verificação visual de Estoque Baixo
crit = pd.read_sql("SELECT item, quantidade FROM estoque WHERE quantidade <= 200", conn_raw)
if not crit.empty:
    lista_crit = [f"{row['item']} ({row['quantidade']:.0f})" for _, row in crit.iterrows()]
    st.error("⚠️ Estoque Baixo: " + ", ".join(lista_crit))

st.title("📱 Gestão de Restaurante")

# Criação das abas do sistema
tabs = st.tabs(["🍸 Drinks", "🍺 Cervejas", "🥤 Sem Álcool", "🍟 Entradas", "🍽️ Principais", "🍰 Sobremesas", "💵 Contas", "⚙️ Gerência"])

# --- FUNÇÃO DE LANÇAMENTO DE PEDIDOS ---
def lançar_pedido_aba(idx_tab, categoria_nome, legenda):
    with tabs[idx_tab]:
        # Carrega os produtos da categoria usando pandas
        query_prod = "SELECT id, nome, preco, insumo_id, qtd_insumo FROM produtos WHERE categoria = %s ORDER BY nome"
        prods = pd.read_sql(query_prod, conn_raw, params=[categoria_nome])
        
        with st.form(f"f_ped_{categoria_nome}", clear_on_submit=True):
            st.subheader(legenda)
            m = st.text_input("Mesa / Comanda:", key=f"m_{categoria_nome}")
            
            if not prods.empty:
                dp = {f"{row['nome']} (R$ {row['preco']:.2f})": row for _, row in prods.iterrows()}
                ps = st.selectbox("Escolha o Item:", list(dp.keys()), key=f"ps_{categoria_nome}")
                q = st.number_input("Quantidade:", min_value=1, value=1, key=f"q_{categoria_nome}")
                
                if st.form_submit_button("🚀 Enviar Pedido", type="primary") and m.strip():
                    item_selecionado = dp[ps]
                    pid = int(item_selecionado['id'])
                    iid = item_selecionado['insumo_id']
                    qins = item_selecionado['qtd_insumo']
                    
                    pode_vender = True
                    if iid and not pd.isna(iid):
                        query_est = "SELECT quantidade FROM estoque WHERE id = %s"
                        res = pd.read_sql(query_est, conn_raw, params=[int(iid)])
                        if not res.empty and res.iloc[0]['quantidade'] < (qins * q):
                            st.error(f"Estoque insuficiente. Restam apenas {res.iloc[0]['quantidade']:.0f}g/ml/un")
                            pode_vender = False
                    
                    if pode_vender:
                        with obter_conexao() as c_insert:
                            with c_insert.cursor() as cur_ins:
                                cur_ins.execute(
                                    "INSERT INTO pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)",
                                    (m.strip(), pid, q, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                )
                                if iid and not pd.isna(iid):
                                    cur_ins.execute(
                                        "UPDATE estoque SET quantidade = quantidade - %s WHERE id = %s",
                                        ((qins * q), int(iid))
                                    )
                                c_insert.commit()
                        st.success("Pedido enviado com sucesso!")
                        st.rerun()
            else:
                st.warning(f"Nenhum item cadastrado em '{categoria_nome}'.")

# Execução das abas de vendas rápidas
lançar_pedido_aba(0, "Drinks", "🍸 Lançar Drinks")
lançar_pedido_aba(1, "Cervejas", "🍺 Lançar Cervejas")
lançar_pedido_aba(2, "Sem Álcool", "🥤 Lançar Sem Álcool")
lançar_pedido_aba(3, "Porções", "🍟 Lançar Entradas / Porções")
lançar_pedido_aba(4, "Pratos Principais", "🍽️ Lançar Pratos Principais")
lançar_pedido_aba(5, "Sobremesas", "🍰 Lançar Sobremesas")
# --- CONTAS (FECHAMENTO DE COMANDAS) ---
with tabs[6]:
    query_contas = """
        SELECT p.id as ped_id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, pr.insumo_id, pr.qtd_insumo
        FROM pedidos p 
        JOIN produtos pr ON p.produto_id = pr.id 
        WHERE p.status != 'Finalizado (Pago)'
    """
    peds = pd.read_sql(query_contas, conn_raw)
    
    if peds.empty: 
        st.info("Nenhuma comanda aberta no momento.")
    else:
        for m in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m]
            sub = float(itens['subtotal'].sum())
            
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): 
                    st.write(f"▪️ {i['quantidade']}x {i['nome']} (R$ {i['subtotal']:.2f})")
                
                tx = sub * 0.10 if st.checkbox("Taxa de Serviço (10%)", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total Final: R$ {sub + tx:.2f}")
                
                if st.button(f"💵 Fechar Mesa {m}", key=f"btn_f_{m}"):
                    with obter_conexao() as c_update:
                        with c_update.cursor() as cur_upd:
                            cur_upd.execute(
                                "UPDATE pedidos SET status = 'Finalizado (Pago)', taxa_paga = %s WHERE mesa = %s AND status != 'Finalizado (Pago)'",
                                (1 if tx > 0 else 0, m)
                            )
                            c_update.commit()
                    st.rerun()

# --- PASTA DA GERÊNCIA PROTEGIDA ---
with tabs[7]:
    if "ok_gerencia" not in st.session_state: 
        st.session_state["ok_gerencia"] = False
        
    if not st.session_state["ok_gerencia"]:
        with st.form("f_adm_geral"):
            st.subheader("🔒 Acesso Restrito da Gerência")
            senha_adm = st.text_input("Digite a Senha Master:", type="password")
            if st.form_submit_button("🔓 Liberar Painel") and senha_adm == ADMIN:
                st.session_state["ok_gerencia"] = True
                st.rerun()
    else:
        if st.button("🔒 Bloquear Painel Geral", type="secondary"):
            st.session_state["ok_gerencia"] = False
            st.rerun()
            
        st.markdown("---")
        
        # 1. RELATÓRIO DE VENDAS DIÁRIAS
        with st.expander("📊 Abrir Relatório de Vendas", expanded=False):
            query_relatorio = """
                SELECT pr.nome, p.quantidade, (p.quantidade * pr.preco) as total_item, p.horario, p.taxa_paga 
                FROM pedidos p 
                JOIN produtos pr ON p.produto_id = pr.id 
                WHERE p.status = 'Finalizado (Pago)'
            """
            vds = pd.read_sql(query_relatorio, conn_raw)
            
            if vds.empty: 
                st.info("Nenhuma venda finalizada encontrada no histórico.")
            else:
                vds['dia_formatado'] = vds['horario'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y") if x else "-")
                dias = sorted(list(set(vds['dia_formatado'].tolist())), reverse=True)
                sel = st.selectbox("Filtrar Dia:", dias)
                
                v_dia = vds[vds['dia_formatado'] == sel]
                p_tot = float(v_dia['total_item'].sum())
                t_tot = float(v_dia[v_dia['taxa_paga'] == 1]['total_item'].sum() * 0.10)
                
                st.metric("📦 Total em Produtos", f"R$ {p_tot:.2f}")
                st.metric("💰 Total em Taxas (10%)", f"R$ {t_tot:.2f}")
                st.metric("💵 Faturamento Geral do Dia", f"R$ {p_tot + t_tot:.2f}")
                
                st.markdown("**Resumo de itens vendidos no dia:**")
                for nome_item in set(v_dia['nome'].tolist()):
                    total_qtd = v_dia[v_dia['nome'] == nome_item]['quantidade'].sum()
                    st.write(f"▪️ **{nome_item}**: {int(total_qtd)} un")

        # 2. CONTROLE E ABASTECIMENTO DE ESTOQUE
        with st.expander("📦 Abrir Controle de Estoque", expanded=False):
            with st.form("f_e_gerencia", clear_on_submit=True):
                ni = st.text_input("Nome do Novo Insumo (Ex: Gelo, Batata, Rum):")
                qi = st.number_input("Quantidade Inicial:", min_value=0.0, step=100.0)
                if st.form_submit_button("📥 Adicionar / Atualizar Estoque"):
                    if ni.strip():
                        with obter_conexao() as c_est:
                            with c_est.cursor() as cur_est:
                                cur_est.execute("""
                                    INSERT INTO estoque (item, quantity) VALUES (%s, %s) if False else INSERT INTO estoque (item, quantidade) VALUES (%s, %s)
                                    ON CONFLICT(item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade
                                """, (ni.strip(), qi))
                                c_est.commit()
                        st.success(f"Insumo '{ni}' atualizado!")
                        st.rerun()
                        
            est_atual = pd.read_sql("SELECT item, quantidade FROM estoque ORDER BY item", conn_raw)
            if not est_atual.empty:
                for _, row in est_atual.iterrows(): 
                    st.write(f"📦 **{row['item']}**: {row['quantidade']:.0f} (g/ml/un)")

        # 3. CANCELAR PEDIDOS ATIVOS E DEVOLVER INSUMOS
        with st.expander("❌ Abrir Cancelar Pedidos Ativos", expanded=False):
            if not peds.empty:
                for _, row in peds.iterrows():
                    if st.button(f"❌ Cancelar Mesa {row['mesa']}: {row['quantidade']}x {row['nome']}", key=f"c_{row['ped_id']}"):
                        with obter_conexao() as c_del:
                            with c_del.cursor() as cur_del:
                                if row['insumo_id'] and not pd.isna(row['insumo_id']):
                                    devolucao = float(row['quantidade'] * row['qtd_insumo'])
                                    cur_del.execute(
                                        "UPDATE estoque SET quantidade = quantidade + %s WHERE id = %s",
                                        (devolucao, int(row['insumo_id']))
                                    )
                                cur_del.execute("DELETE FROM pedidos WHERE id = %s", (int(row['ped_id']),))
                                c_del.commit()
                        st.rerun()
            else: 
                st.info("Não há nenhum pedido ativo para cancelamento rápido.")

        # 4. CONFIGURAÇÃO DO CARDÁPIO
        with st.expander("🍽️ Abrir Configuração do Cardápio", expanded=False):
            est_cadastro = pd.read_sql("SELECT id, item FROM estoque ORDER BY item", conn_raw)
            ins = {row['item']: row['id'] for _, row in est_cadastro.iterrows()} if not est_cadastro.empty else {}
            
            with st.form("f_add_produto", clear_on_submit=True):
                st.subheader("➕ Cadastrar Novo Produto")
                nome_p = st.text_input("Nome Comercial do Produto:")
                cat_p = st.selectbox("Categoria do Menu:", ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"])
                preco_p = st.number_input("Preço de Venda Praticado (R$):", min_value=0.0, format="%.2f", step=1.0)
                
                vincular_insumo = st.checkbox("Este produto desconta insumo do estoque ao ser vendido?")
                insumo_sel = None
                qtd_ins_p = 0.0
                
                if vincular_insumo and ins:
                    insumo_sel = st.selectbox("Selecione qual insumo ele gasta:", list(ins.keys()))
                    qtd_ins_p = st.number_input("Quantidade g/ml/un gasta por venda única:", min_value=0.01, step=1.0)
                elif vincular_insumo and not ins:
                    st.warning("Cadastre primeiro um insumo na aba 'Controle de Estoque' acima para poder fazer o vínculo.")
                
                if st.form_submit_button("💾 Salvar no Cardápio"):
                    if nome_p.strip():
                        iid_p = int(ins[insumo_sel]) if (vincular_insumo and insumo_sel) else None
                        with obter_conexao() as c_prod:
                            with c_prod.cursor() as cur_prod:
                                cur_prod.execute("""
                                    INSERT INTO produtos (nome, categoria, preco, insumo_id, qtd_insumo) 
                                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT(nome) DO UPDATE 
                                    SET categoria = EXCLUDED.categoria, preco = EXCLUDED.preco, insumo_id = EXCLUDED.insumo_id, qtd_insumo = EXCLUDED.qtd_insumo
                                """, (nome_p.strip(), cat_p, preco_p, iid_p, float(qtd_ins_p)))
                                c_prod.commit()
                        st.success(f"O item '{nome_p}' foi configurado com sucesso!")
                        st.rerun()

conn_raw.close()
