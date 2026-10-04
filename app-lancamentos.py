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
    
    # Se você configurou a URL de conexão direta (Altamente recomendado para o Neon)
    if "url" in credenciais:
        return psycopg2.connect(credenciais["url"])
        
    # Fallback estruturado caso decida usar campos separados
    return psycopg2.connect(
        host=credenciais.get("host"),
        port=credenciais.get("port", 5432),
        database=credenciais.get("database"),
        user=credenciais.get("username"),
        password=credenciais.get("password"),
        sslmode="require"
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
            relatorio_df = pd.read_sql(query_relatorio, conn_raw)
            if not relatorio_df.empty:
                st.dataframe(relatorio_df)
                total_faturado = relatorio_df['total_item'].sum()
                st.metric("Total Faturado", f"R$ {total_faturado:.2f}")
            else:
                st.info("Nenhuma venda finalizada encontrada.")
