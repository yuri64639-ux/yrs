from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

# CONFIGURAÇÃO ÚNICA DA PÁGINA
st.set_page_config(page_title="Sistema de Vendas", layout="centered")

# 🙈 OCULTAR BARRA SUPERIOR COMPLETA (MENU, SHARE, 3 PONTINHOS, GITHUB E RODAPÉ)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stActionButton"] {display: none !important;}
    [data-testid="stAppToolbar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# 🎨 DESIGN PROFISSIONAL DO MENU LATERAL E BOTÕES (CSS)
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1E1E24; }
    [data-testid="stSidebar"] .st-emotion-cache-1768qis, [data-testid="stSidebar"] p {
        color: #FFFFFF !important; font-size: 16px !important; font-weight: 500;
    }
    [data-testid="stSidebarNavActiveItem"] {
        background-color: #007BFF !important; border-radius: 8px !important; padding: 6px 12px !important;
    }
    [data-testid="stSidebarNavActiveItem"] p { color: #FFFFFF !important; font-weight: bold !important; }
    [data-testid="stSidebarNavItems"] li:hover { background-color: #2D2D35; border-radius: 8px; }
    .stButton>button { width: 100%; height: 3rem; }
</style>
""", unsafe_allow_html=True)

PASS = "orla123"

if "logado" not in st.session_state:
    st.session_state.logado = False

# FORMULÁRIO DE LOGIN CORRIGIDO
if not st.session_state.logado:
    with st.form("login_form"):
        st.subheader("📱 Acesso ao Sistema")
        senha_input = st.text_input("Senha:", type="password")
        botao_entrar = st.form_submit_button("Entrar", type="primary")
        
        if botao_entrar:
            if senha_input == PASS:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
    st.stop()

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c:
        return psycopg2.connect(c["url"])
    return psycopg2.connect(
        host=c.get("host"), 
        port=c.get("port", 5432), 
        database=c.get("database"), 
        user=c.get("username"), 
        password=c.get("password"), 
        sslmode="require"
    )

conn = ob_cx()

# INICIALIZAÇÃO DO BANCO DE DADOS
with conn.cursor() as cur:
    cur.execute("SET search_path TO public;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.estoque (id SERIAL PRIMARY KEY, item TEXT UNIQUE, quantidade REAL);
        CREATE TABLE IF NOT EXISTS public.produtos (id SERIAL PRIMARY KEY, nome TEXT UNIQUE, categoria TEXT, preco REAL);
        CREATE TABLE IF NOT EXISTS public.receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL, UNIQUE(produto_id, insumo_id));
        CREATE TABLE IF NOT EXISTS public.pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Sim');
    """)
    conn.commit()

if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

# EXIBE ÚLTIMA MESA MODIFICADA
df_ultima_mesa = pd.read_sql("SELECT mesa FROM public.pedidos WHERE status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY id DESC LIMIT 1", conn)
if not df_ultima_mesa.empty:
    st.info(f"📌 **Última mesa modificada:** Comanda {df_ultima_mesa['mesa'].iloc[0]}")

cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs(["🚀 Lançar Pedidos", "💵 Contas"])

with tabs[0]:
    st.subheader("📝 Montar Comanda / Pedido")
    
    # 🔢 CAMPO DE MESA DEFINIDO COMO PRIMEIRO ITEM DA INTERFACE
    m = st.text_input("Mesa / Comanda:", value=st.session_state.get("mesa_atual", ""), key="mesa_global_input")
    st.session_state["mesa_atual"] = m
    
    # Busca de produtos vem logo na sequência
    busca_nome = st.text_input("🔍 Digite o nome do produto:", key="lupa_busca_topo_absoluto").strip()
    
    st.markdown("---")
    st.markdown("**Ajuste e adicione o item encontrado:**")
    
    if busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE LOWER(nome) LIKE LOWER(%s) ORDER BY nome", conn, params=[f"%{busca_nome}%"])
    else:
        cat_sel = st.selectbox("Ou liste os itens escolhendo a Categoria:", cats)
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE categoria = %s ORDER BY nome", conn, params=[cat_sel])
        
    if not prods_filtrados.empty:
        dp = {f"{r['nome']} ({r['categoria']}) - R$ {r['preco']:.2f}": r for _, r in prods_filtrados.iterrows()}
        ps = st.selectbox("Confirmar Item selecionado:", list(dp.keys()))
        q = st.number_input("Quantidade:", min_value=1, value=1)
        
        if st.button("➕ Adicionar ao Pedido"):
            if not m.strip():
                st.error("Por favor, digite o número da Mesa / Comanda antes de adicionar itens!")
            else:
                item_escolhido = dp[ps]
                st.session_state.carrinho.append({
                    "id": int(item_escolhido["id"]),
                    "nome": item_escolhido["nome"],
                    "categoria": item_escolhido["categoria"],
                    "qtd": int(q),
                    "preco": float(item_escolhido["preco"])
                })
                st.success(f"{q}x {item_escolhido['nome']} adicionado ao rascunho!")
                st.rerun()
    else:
        st.warning("Nenhum item encontrado. Continue digitando ou escolha outra categoria.")

    # RENDERIZAÇÃO E LOGICA DO CARRINHO (RASCUNHO)
    if st.session_state.carrinho:
        st.markdown("---")
        st.markdown(f"📋 **Resumo do Pedido Atual (Mesa: {m}):**")
        total_carrinho = 0.0
        
        for idx_c, item in enumerate(list(st.session_state.carrinho)):
            sub_item = item["qtd"] * item["preco"]
            total_carrinho += sub_item
            col_txt, col_btn = st.columns([4, 1])
            col_txt.write(f"▪️ **{item['qtd']}x** {item['nome']} — R$ {sub_item:.2f}")
            
            if col_btn.button("🗑️ Remover", key=f"rem_{idx_c}"):
                st.session_state.carrinho.pop(idx_c)
                st.rerun()
                
        st.markdown(f"### 🧾 Total Parcial: R$ {total_carrinho:.2f}")
        col_cancelar, col_enviar = st.columns(2)
        
        if col_cancelar.button("❌ Limpar Todo o Rascunho"):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_enviar.button("🔥 LANÇAR COMANDA COMPLETA", type="primary"):
            estoque_geral_ok = True
            itens_para_baixar = []
            
            # Validação prévia de todo o estoque do carrinho
            for item in st.session_state.carrinho:
                rec = pd.read_sql("""
                    SELECT r.insumo_id, r.qtd_insumo, e.item, e.quantidade 
                    FROM public.receitas r 
                    JOIN public.estoque e ON r.insumo_id = e.id 
                    WHERE r.produto_id = %s
                """, conn, params=[item["id"]])
                
                for _, r_ins in rec.iterrows():
                    qtd_necessaria = (float(r_ins["qtd_insumo"]) / 1000.0) * item["qtd"]
                    if r_ins["quantidade"] < qtd_necessaria:
                        st.error(f"🚨 Estoque insuficiente de **{r_ins['item']}** para fazer {item['nome']}! (Disponível: {r_ins['quantidade']:.2f}, Necessário: {qtd_necessaria:.2f})")
                        estoque_geral_ok = False
                    else:
                        itens_para_baixar.append((qtd_necessaria, r_ins["insumo_id"]))

            # Executa transações apenas se o estoque total estiver OK
            if estoque_geral_ok:
                try:
                    with conn.cursor() as cur:
                        horario_atual = datetime.now().strftime("%H:%M")
                        for item in st.session_state.carrinho:
                            cur.execute("""
                                INSERT INTO public.pedidos (mesa, produto_id, quantidade, status, horario) 
                                VALUES (%s, %s, %s, 'Pendente', %s)
                            """, (m, item["id"], item["qtd"], horario_atual))
                        
                        for qtd, insumo_id in itens_para_baixar:
                            cur.execute("""
                                UPDATE public.estoque 
                                SET quantidade = quantidade - %s 
                                WHERE id = %s
                            """, (qtd, insumo_id))
                            
                    conn.commit()
                    st.session_state.carrinho = []
                    st.success("🚀 Pedido lançado com sucesso e estoque atualizado!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Erro ao salvar pedido: {e}")
