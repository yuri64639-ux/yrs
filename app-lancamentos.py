from datetime import datetime
import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Sistema de Vendas", layout="centered")
st.markdown("<style>.stButton>button { width: 100%; height: 3rem; }</style>", unsafe_allow_html=True)
PASS = "orla123"

if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    with st.form("login_form"):
        st.subheader("📱 Acesso ao Sistema")
        if st.form_submit_button("Entrar", type="primary") and st.text_input("Senha:", type="password") == PASS:
            st.session_state.logado = True; st.rerun()
    st.stop()

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    if "url" in c: return psycopg2.connect(c["url"])
    return psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

conn = ob_cx()
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

cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
tabs = st.tabs(["🚀 Lançar Pedidos", "💵 Contas"])

# --- ABA 0: LANÇAMENTO COM LUPA EM PRIMEIRO LUGAR (ÍNDICE 0 CORRIGIDO) ---
with tabs[0]:
    st.subheader("📝 Montar Comanda / Pedido")
    
    m = st.text_input("Mesa / Comanda:", value=st.session_state.get("mesa_atual", ""), key="mesa_global_input")
    st.session_state["mesa_atual"] = m
    
    st.markdown("---")
    st.markdown("**1. Adicione os itens ao pedido:**")
    
    # LUPA DE PESQUISA EM PRIMEIRO LUGAR (Filtra conforme o garçom digita)
    busca_nome = st.text_input("🔍 Digite o nome do produto (Ex: caipirinha, picanha, batata):", key="lupa_busca_topo").strip()
    
    if busca_nome:
        prods_filtrados = pd.read_sql("SELECT id, nome, preco, categoria FROM public.produtos WHERE LOWER(nome) LIKE LOWER(%s) ORDER BY nome", conn, params=[f"%{busca_nome}%"])
    else:
        cat_sel = st.selectbox("Ou selecione uma Categoria para listar:", cats)
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
                    "id": int(item_escolhido['id']),
                    "nome": item_escolhido['nome'],
                    "categoria": item_escolhido['categoria'],
                    "qtd": int(q),
                    "preco": float(item_escolhido['preco'])
                })
                st.success(f"'{q}x {item_escolhido['nome']}' adicionado ao rascunho!")
                st.rerun()
    else:
        st.warning("Nenhum item encontrado. Continue digitando ou verifique o nome.")
    if st.session_state.carrinho:
        st.markdown("---")
        st.markdown(f"📋 **Resumo do Pedido Atual (Mesa: {m}):**")
        
        total_carrinho = 0.0
        for idx_c, item in enumerate(st.session_state.carrinho):
            sub_item = item['qtd'] * item['preco']
            total_carrinho += sub_item
            col_txt, col_btn = st.columns([4, 1])
            col_txt.write(f"▪️ **{item['qtd']}x** {item['nome']} [{item['categoria']}] — R$ {sub_item:.2f}")
            if col_btn.button("🗑️ Remover", key=f"rem_{idx_c}"):
                st.session_state.carrinho.pop(idx_c)
                st.rerun()
                
        st.markdown(f"### 🧾 Total Parcial: R$ {total_carrinho:.2f}")
        
        col_cancelar, col_enviar = st.columns(2)
        if col_cancelar.button("❌ Limpar Todo o Rascunho"):
            st.session_state.carrinho = []
            st.rerun()
            
        if col_enviar.button("🔥 LANÇAR COMANDA COMPLETA", type="primary"):
            pedidos_finais = []
            estoque_geral_ok = True
            
            for item in st.session_state.carrinho:
                rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.item, e.quantidade FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn, params=[item['id']])
                for _, r_ins in rec.iterrows():
                    qtd_necessaria = (float(r_ins['qtd_insumo']) / 1000.0) * item['qtd']
                    if r_ins['quantidade'] < qtd_necessaria:
                        st.error(f"🚨 Estoque insuficiente de '{r_ins['item']}' para fazer '{item['nome']}'!")
                        estoque_geral_ok = False
                if estoque_geral_ok:
                    pedidos_finais.append((item['id'], item['qtd']))
            
            if estoque_geral_ok and pedidos_finais:
                with ob_cx() as c_massa, c_massa.cursor() as cur_trans:
                    cur_trans.execute("SET search_path TO public;")
                    for pid, qtd in pedidos_finais:
                        cur_trans.execute("INSERT INTO public.pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (m.strip(), pid, qtd, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        rec = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", conn, params=[pid])
                        for _, r_ins in rec.iterrows():
                            qtd_convertida = float((float(r_ins['qtd_insumo']) / 1000.0) * qtd)
                            cur_trans.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (qtd_convertida, int(r_ins['insumo_id'])))
                    c_massa.commit()
                st.success(f"✅ Sucesso! Comanda da mesa {m.strip()} enviada!")
                st.session_state.carrinho = []
                st.rerun()

# --- CONTAS (ÍNDICE 1 CORRIGIDO) ---
with tabs[1]:
    st.subheader("🎟️ Contas Abertas")
    peds = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as sub FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    if peds.empty: st.info("Nenhuma comanda aberta.")
    else:
        for m_aberta in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m_aberta]; sub = float(itens['sub'].sum())
            with st.expander(f"📋 Mesa {m_aberta} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): st.write(f"▪️ {i['quantidade']}x {i['nome']} (R$ {i['sub']:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa de Serviço (10%)", value=True, key=f"t_{m_aberta}") else 0.0
                st.markdown(f"### Total Final: R$ {sub + tx:.2f}")
                pago_opcao = st.radio("O cliente pagou a conta?", ["Sim", "Não"], key=f"pago_{m_aberta}", horizontal=True)
                if st.button(f"💵 Fechar Conta {m_aberta}", key=f"b_{m_aberta}"):
                    status_final = 'Finalizado (Pago)' if pago_opcao == "Sim" else 'Fechado (Não Pago)'
                    with ob_cx() as c_fechar, c_fechar.cursor() as cur_fechar:
                        cur_fechar.execute("SET search_path TO public;")
                        cur_fechar.execute("UPDATE public.pedidos SET status = %s, taxa_paga = %s, pago = %s WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (status_final, 1 if tx > 0 else 0, pago_opcao, m_aberta))
                        c_fechar.commit()
                    st.success(f"Conta da mesa {m_aberta} fechada!"); st.rerun()
