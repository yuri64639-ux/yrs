import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Painel Gerencial", layout="centered")
ADMIN = "admin123"

if "ok_g" not in st.session_state: st.session_state["ok_g"] = False
if not st.session_state["ok_g"]:
    with st.form("f_adm"):
        st.subheader("🔒 Acesso Restrito da Gerência")
        if st.form_submit_button("🔓 Liberar") and st.text_input("Senha Master:", type="password") == ADMIN:
            st.session_state["ok_g"] = True; st.rerun()
    st.stop()

if st.button("🔒 Bloquear Painel"): st.session_state["ok_g"] = False; st.rerun()

def ob_cx():
    c = st.secrets["connections"]["postgresql"]
    return psycopg2.connect(c["url"]) if "url" in c else psycopg2.connect(host=c.get("host"), port=c.get("port", 5432), database=c.get("database"), user=c.get("username"), password=c.get("password"), sslmode="require")

conn = ob_cx()
cats = ["Drinks", "Cervejas", "Sem Álcool", "Porções", "Pratos Principais", "Sobremesas"]
df_est = pd.read_sql("SELECT id, item, quantidade FROM public.estoque ORDER BY item", conn)
df_prods = pd.read_sql("SELECT id, nome FROM public.produtos ORDER BY nome", conn)

subtabs = st.tabs(["📦 Estoque", "❌ Cancelamentos", "🛠️ Cadastro", "🔬 Receitas (Até 4 Itens)", "📊 Relatórios", "🗑️ Excluir"])

# --- ESTOQUE (INDEX 0) ---
with subtabs[0]:
    st.subheader("📦 Estoque Atual (Exibido em Litros / Kg / Unidades)")
    df_est_visual = df_est.copy()
    if not df_est_visual.empty: df_est_visual.columns = ["ID", "Insumo", "Quantidade Atual (L / Kg)"]
    st.dataframe(df_est_visual, use_container_width=True, hide_index=True)
    with st.expander("➕ Alimentar Estoque"):
        with st.form("f_ins", clear_on_submit=True):
            n_i = st.text_input("Insumo:")
            q_i = st.number_input("Qtd Inteira (Litros, Quilos ou Un):", min_value=0.0, value=1.0, step=1.0)
            if st.form_submit_button("Salvar") and n_i.strip():
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    cur.execute("INSERT INTO public.estoque (item, quantidade) VALUES (%s, %s) ON CONFLICT (item) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (n_i.strip(), q_i))
                    c.commit()
                st.success("Estoque atualizado!"); st.rerun()

# --- CANCELAMENTOS (INDEX 1) ---
with subtabs[1]:
    st.subheader("❌ Cancelar Itens e Devolver ao Estoque")
    p_ab = pd.read_sql("SELECT p.id, p.mesa, pr.nome, p.quantidade, p.produto_id FROM public.pedidos p JOIN public.produtos pr ON p.produto_id = pr.id WHERE p.status NOT IN ('Finalizado (Pago)', 'Fechado (Não Pago)') ORDER BY p.mesa", conn)
    if p_ab.empty: st.info("Nenhuma comanda aberta para cancelamento.")
    else:
        m_sel = st.selectbox("Selecione a Mesa:", sorted(list(set(p_ab['mesa'].tolist()))))
        for _, it in p_ab[p_ab['mesa'] == m_sel].iterrows():
            col1, col2 = st.columns(2)
            col1.write(f"▪ *{it['quantidade']}x* {it['nome']}")
            if col2.button("Deletar", key=f"cn_{it['id']}"):
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    rc = pd.read_sql("SELECT insumo_id, qtd_insumo FROM public.receitas WHERE produto_id = %s", c, params=[int(it['produto_id'])])
                    for _, r in rc.iterrows(): 
                        cur.execute("UPDATE public.estoque SET quantidade = quantidade + %s WHERE id = %s", ((float(r['qtd_insumo']) / 1000.0) * int(it['quantidade']), int(r['insumo_id'])))
                    cur.execute("DELETE FROM public.pedidos WHERE id = %s", (int(it['id']),))
                    c.commit()
                st.success("Item removido!"); st.rerun()

# --- CADASTRO (INDEX 2) ---
with subtabs[2]:
    st.subheader("🍔 Criar Produto")
    with st.form("f_prod", clear_on_submit=True):
        n_p = st.text_input("Nome:")
        c_p = st.selectbox("Categoria:", cats)
        p_p = st.number_input("Preço de Venda:", min_value=0.0, value=15.0)
        if st.form_submit_button("Gravar") and n_p.strip():
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("INSERT INTO public.produtos (nome, categoria, preco) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (n_p.strip(), c_p, p_p))
                c.commit()
            st.success("Produto gravado!"); st.rerun()
# --- RECEITAS ATUALIZADAS PARA ATÉ 4 INSUMOS (INDEX 3 COIGIDO) ---
with subtabs[3]:
    st.subheader("🔬 Montar Ficha Técnica (De 1 até 4 Insumos Simultâneos)")
    st.info("💡 Escolha o produto e defina de 1 a 4 ingredientes informando o gasto em ml ou gramas.")
    if not df_prods.empty and not df_est.empty:
        lista_prods = [r['nome'] for _, r in df_prods.iterrows()]
        lista_insumos = ["---"] + [r['item'] for _, r in df_est.iterrows()]
        d_p = {r['nome']: r['id'] for _, r in df_prods.iterrows()}
        d_i = {r['item']: r['id'] for _, r in df_est.iterrows()}
        
        with st.form("f_vinc_multi_4", clear_on_submit=True):
            p_sel = d_p[st.selectbox("Selecione o Produto:", lista_prods)]
            st.markdown("---")
            
            # Linha do Insumo 1
            col1, col2 = st.columns(2)
            i1 = col1.selectbox("Ingrediente 1:", lista_insumos, key="i1")
            q1 = col2.number_input("Qtd gasta 1 (ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q1")
            
            # Linha do Insumo 2
            col3, col4 = st.columns(2)
            i2 = col3.selectbox("Ingrediente 2 (Opcional):", lista_insumos, key="i2")
            q2 = col4.number_input("Qtd gasta 2 (ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q2")
            
            # Linha do Insumo 3
            col5, col6 = st.columns(2)
            i3 = col5.selectbox("Ingrediente 3 (Opcional):", lista_insumos, key="i3")
            q3 = col6.number_input("Qtd gasta 3 (ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q3")
            
            # NOVA LINHA: Insumo 4 adicionado conforme pedido
            col7, col8 = st.columns(2)
            i4 = col7.selectbox("Ingrediente 4 (Opcional):", lista_insumos, key="i4")
            q4 = col8.number_input("Qtd gasta 4 (ml ou g):", min_value=0.0, value=0.0, step=5.0, key="q4")
            
            if st.form_submit_button("🔥 Gravar Receita Completa"):
                vinc_salvos = 0
                with ob_cx() as c, c.cursor() as cur:
                    cur.execute("SET search_path TO public;")
                    if i1 != "---" and q1 > 0:
                        cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i1], q1))
                        vinc_salvos += 1
                    if i2 != "---" and q2 > 0:
                        cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i2], q2))
                        vinc_salvos += 1
                    if i3 != "---" and q3 > 0:
                        cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i3], q3))
                        vinc_salvos += 1
                    if i4 != "---" and q4 > 0:
                        cur.execute("INSERT INTO public.receitas (produto_id, insumo_id, qtd_insumo) VALUES (%s, %s, %s) ON CONFLICT (produto_id, insumo_id) DO UPDATE SET qtd_insumo = EXCLUDED.qtd_insumo", (p_sel, d_i[i4], q4))
                        vinc_salvos += 1
                    c.commit()
                if vinc_salvos > 0:
                    st.success(f"Sucesso! {vinc_salvos} ingrediente(s) configurados."); st.rerun()
                else: st.error("Preencha ao menos um ingrediente válido.")
    else: st.warning("Cadastre produtos e insumos primeiro.")

# --- 📊 RELATÓRIOS (INDEX 4) ---
with subtabs[4]:
    st.subheader("📊 Resumo Financeiro Detalhado")
    vendas_df = pd.read_sql("""
        SELECT p.mesa, pr.nome as produto, p.quantidade, pr.preco, (p.quantidade * pr.preco) as subtotal, p.status, p.taxa_paga, p.horario 
        FROM public.pedidos p 
        JOIN public.produtos pr ON p.produto_id = pr.id 
        WHERE p.status IN ('Finalizado (Pago)', 'Fechado (Não Pago)')
        ORDER BY p.horario DESC
    """, conn)
    
    if vendas_df.empty: st.info("Nenhuma comanda foi finalizada no sistema até o momento.")
    else:
        empresa_total, garcons_total, pendente_total = 0.0, 0.0, 0.0
        for mesa_id, grupo in vendas_df.groupby('mesa'):
            sub_mesa = float(grupo['subtotal'].sum())
            status_mesa = grupo['status'].iloc[0]
            taxa_marcada = int(grupo['taxa_paga'].iloc[0]) == 1
            if status_mesa == 'Finalizado (Pago)':
                empresa_total += sub_mesa
                if taxa_marcada: garcons_total += (sub_mesa * 0.10)
            else: pendente_total += sub_mesa
        
        col_emp, col_garc, col_pen = st.columns(3)
        col_emp.metric("💰 Faturamento Líquido (Empresa)", f"R$ {empresa_total:.2f}")
        col_garc.metric("🍹 Caixinha Acumulada (10%)", f"R$ {garcons_total:.2f}")
        col_pen.metric("⚠️ Total Perdido (Não Pago)", f"R$ {pendente_total:.2f}")
        st.markdown(f"**📈 Caixa Bruto Total Movimentado: R$ {empresa_total + garcons_total:.2f}**")
        
        visual_vendas = vendas_df.copy()
        visual_vendas['taxa_paga'] = visual_vendas['taxa_paga'].map({1: "Inclusa (10%)", 0: "Isenta"})
        visual_vendas.columns = ["Mesa/Comanda", "Item Vendido", "Quantidade", "Preço Un. (R$)", "Subtotal (R$)", "Situação", "Taxa", "Data/Horário"]
        st.dataframe(visual_vendas, use_container_width=True, hide_index=True)

# --- EXCLUIR (INDEX 5) ---
with subtabs[5]:
    st.subheader("🗑 Excluir do Menu/Estoque")
    if not df_prods.empty:
        p_ex = st.selectbox("Remover do Cardápio:", ["---"] + list(df_prods['nome']))
        if p_ex != "---" and st.button("❌ Deletar Produto"):
            id_p = int(df_prods[df_prods['nome'] == p_ex]['id'].values[0])
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("DELETE FROM public.receitas WHERE produto_id = %s", (id_p,))
                cur.execute("DELETE FROM public.produtos WHERE id = %s", (id_p,))
                c.commit()
            st.success("Removido!"); st.rerun()
    st.markdown("---")
    if not df_est.empty:
        i_ex = st.selectbox("Remover do Estoque:", ["---"] + list(df_est['item']))
        if i_ex != "---" and st.button("❌ Deletar Insumo"):
            id_i = int(df_est[df_est['item'] == i_ex]['id'].values[0])
            with ob_cx() as c, c.cursor() as cur:
                cur.execute("SET search_path TO public;")
                cur.execute("DELETE FROM public.receitas WHERE insumo_id = %s", (id_i,))
                cur.execute("DELETE FROM public.estoque WHERE id = %s", (id_i,))
                c.commit()
            st.success("Insumo removido!"); st.rerun()
