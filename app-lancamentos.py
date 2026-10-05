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

df_prods = pd.read_sql("SELECT id, nome, preco FROM public.produtos ORDER BY nome", conn)
tabs = st.tabs(["🚀 Lançamento em Massa", "💵 Contas"])

# --- LANÇAMENTO EM MASSA (INDEX 0) ---
with tabs[0]:
    st.subheader("📝 Lançar Múltiplos Pedidos")
    st.info("💡 Insira a comanda, o produto e a quantidade. Clique na linha de baixo para lançar mais itens juntos.")
    
    if not df_prods.empty:
        lista_itens_cardapio = sorted(list(df_prods['nome']))
        
        # Cria a estrutura padrão da planilha de lançamentos
        df_novo_pedido = pd.DataFrame([{"Mesa / Comanda": "", "Produto": lista_itens_cardapio, "Quantidade": 1}])
        grid_pedidos = st.data_editor(df_novo_pedido, num_rows="dynamic", use_container_width=True, key="grid_ped", column_config={
            "Produto": st.column_config.SelectboxColumn(options=lista_itens_cardapio),
            "Quantidade": st.column_config.NumberColumn(min_value=1, step=1)
        })
        
        if st.button("🔥 Enviar Todos os Pedidos", type="primary"):
            pedidos_validos = []
            estoque_ok = True
            mapa_produtos = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
            
            # 1. Validação prévia de estoque para TODAS as linhas da planilha
            for _, row in grid_pedidos.iterrows():
                mesa = str(row["Mesa / Comanda"]).strip()
                prod_nome = row["Produto"]
                qtd = int(row["Quantidade"])
                
                if mesa and prod_nome in mapa_produtos and qtd > 0:
                    pid = mapa_produtos[prod_nome]
                    rec = pd.read_sql("SELECT r.insumo_id, r.qtd_insumo, e.item, e.quantidade FROM public.receitas r JOIN public.estoque e ON r.insumo_id = e.id WHERE r.produto_id = %s", conn, params=[pid])
                    
                    for _, r in rec.iterrows():
                        qtd_necessaria = (float(r['qtd_insumo']) / 1000.0) * qtd
                        if r['quantidade'] < qtd_necessaria:
                            st.error(f"🚨 Estoque insuficiente de '{r['item']}' para fazer o item '{prod_nome}' na comanda {mesa}!")
                            estoque_ok = False
                    
                    if estoque_ok:
                        pedidos_validos.append((mesa, pid, qtd, prod_nome))
            
            # 2. Se todo o estoque estiver validado, processa a gravação de uma só vez
            if estoque_ok and pedidos_validos:
                with ob_cx() as c_trans, c_trans.cursor() as cur_trans:
                    cur_trans.execute("SET search_path TO public;")
                    for mesa, pid, qtd, prod_nome in pedidos_validos:
                        cur_trans.execute("INSERT INTO public.pedidos (mesa, produto_id, quantidade, horario) VALUES (%s, %s, %s, %s)", (mesa, pid, qtd, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
                        # Carrega os insumos novamente para dar a baixa na transação ativa
                        rec = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", conn, params=[pid])
                        for _, r in rec.iterrows():
                            qtd_convertida = float((float(r['qtd_insumo']) / 1000.0) * qtd)
                            cur_trans.execute("UPDATE public.estoque SET quantidade = quantidade - %s WHERE id = %s", (qtd_convertida, int(r['insumo_id'])))
                    c_trans.commit()
                st.success(f"✅ Sucesso! {len(pedidos_validos)} pedidos lançados e estoque atualizado.")
                st.rerun()
    else:
        st.warning("Nenhum produto cadastrado no cardápio. Cadastre os itens na gerência primeiro.")
# --- CONTAS (INDEX 1) ---
with tabs[1]:
    st.subheader("🎟️ Contas Abertas")
    peds = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, pr.preco, (p.quantidade * pr.preco) as sub FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", conn)
    if peds.empty: st.info("Nenhuma comanda aberta.")
    else:
        for m in sorted(list(set(peds['mesa'].tolist()))):
            itens = peds[peds['mesa'] == m]; sub = float(itens['sub'].sum())
            with st.expander(f"📋 Mesa {m} ➔ R$ {sub:.2f}"):
                for _, i in itens.iterrows(): st.write(f"▪️ {i['quantidade']}x {i['nome']} (R$ {i['sub']:.2f})")
                tx = sub * 0.10 if st.checkbox("Taxa de Serviço (10%)", value=True, key=f"t_{m}") else 0.0
                st.markdown(f"### Total Final: R$ {sub + tx:.2f}")
                pago_opcao = st.radio("O cliente pagou a conta?", ["Sim", "Não"], key=f"pago_{m}", horizontal=True)
                if st.button(f"💵 Fechar Conta {m}", key=f"b_{m}"):
                    status_final = 'Finalizado (Pago)' if pago_opcao == "Sim" else 'Fechado (Não Pago)'
                    with ob_cx() as c_fechar, c_fechar.cursor() as cur_fechar:
                        cur_fechar.execute("SET search_path TO public;")
                        cur_fechar.execute("UPDATE public.pedidos SET status = %s, taxa_paga = %s, pago = %s WHERE mesa = %s AND status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)')", (status_final, 1 if tx > 0 else 0, pago_opcao, m))
                        c_fechar.commit()
                    st.success(f"Conta da mesa {m} fechada!"); st.rerun()
