import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
from banco import init_db

st.set_page_config(page_title="Barbearia Prime", layout="centered")
init_db()

for k, v in [("aut", False), ("usr", ""), ("car", [])]:
    if k not in st.session_state: st.session_state[k] = v

st.markdown("<style>#MainMenu, .stAppDeployButton {visibility: hidden; display: none;} header [data-testid='stToolbar'] {display: none;} .stButton>button {width: 100%; height: 3rem;}</style>", unsafe_allow_html=True)

if not st.session_state.aut:
    with st.form("l_f"):
        st.subheader("💈 Identificação do Profissional")
        u = st.text_input("Barbeiro:").strip()
        p = st.text_input("Senha:", type="password").strip()
        if st.form_submit_button("Entrar", type="primary") and u and p:
            with sqlite3.connect("barber.db") as conn:
                cur = conn.cursor()
                cur.execute("SELECT nome FROM barbeiros WHERE LOWER(nome) = ? AND senha = ?", (u.lower(), p))
                res = cur.fetchone()
            if res:
                st.session_state.aut, st.session_state.usr = True, res[0]
                st.rerun()
            else: st.error("Incorreto.")
    st.stop()

if st.sidebar.button("🔒 Sair", type="primary"):
    st.session_state.aut, st.session_state.usr, st.session_state.car = False, "", []
    st.rerun()

t_op, t_ger = st.tabs(["📱 Terminal do Barbeiro", "⚙️ Painel Admin"])

with t_op:
    op = st.radio("Ação:", ["➕ Atendimento", "📅 Agendar", "🧾 Caixa"], horizontal=True)
    with sqlite3.connect("barber.db") as conn:
        df_s = pd.read_sql("SELECT id, nome, preco FROM servicos ORDER BY nome", conn)
        df_b = pd.read_sql("SELECT nome FROM barbeiros ORDER BY nome", conn)

    if op == "➕ Atendimento":
        cli = st.text_input("Cliente / Cadeira:", value="Cadeira 01").strip()
        if df_s.empty: st.warning("Nenhum serviço cadastrado.")
        else:
            bus = st.text_input("🔍 Filtrar:").strip()
            if bus: df_s = df_s[df_s['nome'].str.contains(bus, case=False, na=False)]
            d_s = {f"{r['nome']} - R$ {r['preco']:.2f}": (r['id'], r['nome'], r['preco']) for _, r in df_s.iterrows()}
            if d_s:
                sel = st.selectbox("Serviço:", list(d_s.keys()))
                if st.button("➕ Adicionar"):
                    st.session_state.car.append({"id": d_s[sel][0], "nome": d_s[sel][1], "preco": d_s[sel][2]})
                    st.toast("Adicionado!")
            if st.session_state.car:
                for i in st.session_state.car: st.write(f"▪ {i['nome']} — R$ {i['preco']:.2f}")
                if st.button("🚀 Enviar ao Caixa", type="primary") and cli:
                    dt = datetime.now().strftime("%Y-%m-%d")
                    with sqlite3.connect("barber.db") as conn:
                        for i in st.session_state.car: conn.cursor().execute("INSERT INTO comandas (cliente, servico_id, barbeiro, valor, data) VALUES (?, ?, ?, ?, ?)", (cli, i['id'], st.session_state.usr, i['preco'], dt))
                        conn.commit()
                    st.success("Enviado!"); st.session_state.car = []; st.rerun()

    elif op == "📅 Agendar":
        st.subheader("📅 Marcar na Agenda")
        c_nome = st.text_input("Nome do Cliente:").strip()
        b_agenda = st.selectbox("Barbeiro:", df_b['nome'].tolist())
        s_agenda = st.selectbox("Serviço:", df_s['nome'].tolist() if not df_s.empty else ["Nenhum"])
        col_d, col_h = st.columns(2)
        d_sel = col_d.date_input("Data:", min_value=date.today())
        h_sel = col_h.time_input("Horário:", value=time(9, 0))
        if st.button("💾 Confirmar Agendamento", type="primary") and c_nome and s_agenda != "Nenhum":
            d_str, h_str = d_sel.strftime("%Y-%m-%d"), h_sel.strftime("%H:%M")
            with sqlite3.connect("barber.db") as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM agenda WHERE barbeiro = ? AND data = ? AND horario = ? AND status = 'Agendado'", (b_agenda, d_str, h_str))
                if cur.fetchone(): st.error("❌ Conflito de horário!")
                else:
                    cur.execute("SELECT id FROM servicos WHERE nome = ?", (s_agenda,))
                    s_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO agenda (cliente, servico_id, barbeiro, data, horario) VALUES (?, ?, ?, ?, ?)", (c_nome, s_id, b_agenda, d_str, h_str))
                    conn.commit(); st.success("🎉 Agendado!"); st.rerun()

    elif op == "🧾 Caixa":
        with sqlite3.connect("barber.db") as conn:
            df_a = pd.read_sql("SELECT c.id, c.cliente, s.nome as servico, c.valor FROM comandas c JOIN servicos s ON c.servico_id = s.id WHERE c.status = 'Aberto'", conn)
            df_age = pd.read_sql("SELECT a.id, a.cliente, s.nome as servico, s.preco, a.barbeiro, a.data, a.horario FROM agenda a JOIN servicos s ON a.servico_id = s.id WHERE a.status = 'Agendado' ORDER BY a.data, a.horario", conn)
        if not df_age.empty:
            st.markdown("### 📅 Clientes Agendados")
            for _, r_a in df_age.iterrows():
                col_t, col_bx = st.columns([3, 1])
                col_t.write(f"⏰ **{r_a['horario']}** ({r_a['data']}) — **{r_a['cliente']}** c/ {r_a['barbeiro']}")
                if col_bx.button("Abrir", key=f"ab_{r_a['id']}"):
                    with sqlite3.connect("barber.db") as conn:
                        conn.cursor().execute("INSERT INTO comandas (cliente, servico_id, barbeiro, valor, data) VALUES (?, ?, ?, ?, ?)", (r_a['cliente'], r_a['id'], r_a['barbeiro'], r_a['preco'], r_a['data']))
                        conn.cursor().execute("UPDATE agenda SET status = 'Atendido' WHERE id = ?", (r_a['id'],))
                        conn.commit()
                    st.success("Comanda aberta!"); st.rerun()
        st.markdown("---")
        if df_a.empty: st.info("Nenhuma comanda aberta.")
        else:
            c_sel = st.selectbox("Cliente em Cadeira:", sorted(list(set(df_a['cliente'].tolist()))))
            df_c = df_a[df_a['cliente'] == c_sel]
            st.markdown(f"### Total: R$ {sum(r['valor'] for _, r in df_c.iterrows()):.2f}")
            p_com = st.checkbox("Pagar comissão (50%)?", value=True)
            if st.button("💰 Finalizar Conta", type="primary", use_container_width=True):
                with sqlite3.connect("barber.db") as conn:
                    conn.cursor().execute("UPDATE comandas SET status = 'Finalizado', comissao = ? WHERE cliente = ? AND status = 'Aberto'", (1 if p_com else 0, c_sel))
                    conn.commit()
                st.success("Pago!"); st.rerun()

with t_ger:
    if st.text_input("Senha Admin:", type="password") != "1234": st.warning("Insira a senha.")
    else:
        g_tab = st.tabs(["🛠️ Catálogo", "👥 Equipe", "📊 Relatório"])
        with g_tab:
            txt = st.text_area("Formato: Nome, Preço", placeholder="Corte, 40.0")
            if st.button("🔥 Salvar") and txt.strip():
                with sqlite3.connect("barber.db") as conn:
                    for l in txt.strip().split("\n"):
                        if "," in l:
                            p = l.split(",")
                            try: conn.cursor().execute("INSERT INTO servicos (nome, preco) VALUES (?, ?) ON CONFLICT(nome) DO UPDATE SET preco=EXCLUDED.preco", (p[0].strip(), float(p[1].strip())))
                            except: pass
                    conn.commit()
                st.success("Salvo!"); st.rerun()
        with g_tab:
            with st.form("c_b"):
                nb, sb = st.text_input("Nome:").strip(), st.text_input("Senha:", type="password").strip()
                if st.form_submit_button("Registrar") and nb and sb:
                    try:
                        with sqlite3.connect("barber.db") as conn: conn.cursor().execute("INSERT INTO barbeiros (nome, senha) VALUES (?, ?)", (nb, sb)); conn.commit()
                        st.success("Registrado!")
                    except: st.error("Erro ou já existe.")
        with g_tab:
            with sqlite3.connect("barber.db") as conn: df_f = pd.read_sql("SELECT c.cliente, s.nome as servico, c.barbeiro, c.valor, c.comissao, c.data FROM comandas c JOIN servicos s ON c.servico_id = s.id WHERE c.status = 'Finalizado'", conn)
            if df_f.empty: st.info("Sem registros.")
            else:
                dt_s = st.selectbox("📅 Dia:", sorted(list(set(df_f['data'].tolist())), reverse=True))
                filt = df_f[df_f['data'] == dt_s]
                bruto = float(filt['valor'].sum())
                comis = float(filt[filt['comissao'] == 1]['valor'].sum() * 0.5)
                st.metric("💰 Bruto", f"R$ {bruto:.2f}")
                st.metric("💈 Comissões", f"R$ {comis:.2f}")
                st.metric("📈 Casa", f"R$ {bruto-comis:.2f}")
                st.dataframe(filt, use_container_width=True, hide_index=True)
