import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuração da página do Streamlit
st.set_page_config(page_title="Gestão de Cardápio & Insumos", layout="wide")

# Conexão com o Banco de Dados Neon (PostgreSQL)
def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro ao conectar ao banco Neon: {e}")
        return None

# Criação das tabelas caso não existam
def init_db():
    conn = init_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS insumos (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE NOT NULL,
                    preco NUMERIC(10, 2) NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ficha_tecnica (
                    id SERIAL PRIMARY KEY,
                    produto_id INT REFERENCES produtos(id) ON DELETE CASCADE,
                    insumo_id INT REFERENCES insumos(id) ON DELETE CASCADE,
                    quantidade NUMERIC(10, 2) NOT NULL,
                    unidade VARCHAR(10) NOT NULL
                );
            """)
            conn.commit()
        conn.close()

# Inicializa o banco de dados Neon na primeira execução
init_db()

st.title("🍳 Sistema de Gestão de Cardápio e Fichas Técnicas")
st.caption("Rodando via GitHub, Streamlit Community Cloud e Banco Neon (PostgreSQL)")

tabs = st.tabs(["1. Cadastrar Insumos (Massa)", "2. Cadastrar Produtos & Ficha Técnica", "3. Visualizar e Gerenciar Cardápio"])

# ABA 1: CADASTRO EM MASSA
with tabs[0]:
    st.header("📦 Cadastro de Insumos em Massa")
    st.info("O sistema assume estoque central em Quilogramas (Kg) ou Litros (L).")
    
    insumos_texto = st.text_area(
        "Digite ou cole os insumos (um por linha):",
        placeholder="Massa Espaguete\nManjericão\nAlho\nManteiga",
        height=200
    )
    
    if st.button("Cadastrar Insumos no Banco Neon", type="primary"):
        if insumos_texto.strip():
            linhas = [linha.strip() for linha in insumos_texto.split("\n") if linha.strip()]
            conn = init_connection()
            if conn:
                novos = 0
                with conn.cursor() as cur:
                    for insumo in linhas:
                        try:
                            cur.execute("INSERT INTO insumos (nome) VALUES (%s) ON CONFLICT DO NOTHING;", (insumo,))
                            if cur.rowcount > 0:
                                novos += 1
                        except:
                            pass
                    conn.commit()
                conn.close()
                st.success(f"Processamento concluído! {novos} novos insumos adicionados.")
                st.rerun()
        else:
            st.warning("Por favor, digite ao menos um insumo.")
# ABA 2: CADASTRO DE PRODUTO COM ATÉ 6 ASSOCIAÇÕES
with tabs[1]:
    st.header("🍔 Cadastrar Produto Comercial")
    
    conn = init_connection()
    lista_insumos = []
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome FROM insumos ORDER BY nome;")
            lista_insumos = cur.fetchall()
        conn.close()
        
    opcoes_select_obrigatorio = [item["nome"] for item in lista_insumos] if lista_insumos else ["- Cadastre insumos primeiro -"]
    opcoes_select_opcional = ["- Nenhum -"] + ([item["nome"] for item in lista_insumos] if lista_insumos else [])
    insumo_opcoes = {item["nome"]: item["id"] for item in lista_insumos}
    
    col1, col2 = st.columns(2)
    with col1:
        nome_produto = st.text_input("Nome do Prato / Bebida do Cardápio:")
    with col2:
        preco_produto = st.number_input("Preço de Venda (R$):", min_value=0.0, step=0.50, format="%.2f")
        
    st.markdown("---")
    st.subheader("📋 Ficha Técnica: Associe de 1 a no máximo 6 insumos (g ou ml)")
    dados_associacao = []
    
    for i in range(3):
        c_left, c_right = st.columns(2)
        
        idx_l = i * 2
        with c_left:
            st.markdown(f"**Insumo {idx_l + 1}**")
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                if idx_l == 0:
                    ins_sel_l = st.selectbox("Selecione o item 1 (Obrigatório)", options=opcoes_select_obrigatorio, key=f"ins_{idx_l}")
                else:
                    ins_sel_l = st.selectbox(f"Selecione o item {idx_l + 1} (Opcional)", options=opcoes_select_opcional, key=f"ins_{idx_l}")
            with sub_col2:
                qtd_sel_l = st.number_input(f"Qtd {idx_l + 1}", min_value=0.01, value=100.0, step=10.0, key=f"qtd_{idx_l}")
            with sub_col3:
                uni_sel_l = st.selectbox(f"Unidade {idx_l + 1}", options=["g", "ml"], key=f"uni_{idx_l}")
            
            if ins_sel_l not in ["- Nenhum -", "- Cadastre insumos primeiro -"]:
                dados_associacao.append({"insumo_id": insumo_opcoes[ins_sel_l], "quantidade": qtd_sel_l, "unidade": uni_sel_l, "nome": ins_sel_l})
            
        idx_r = (i * 2) + 1
        with c_right:
            st.markdown(f"**Insumo {idx_r + 1}**")
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                ins_sel_r = st.selectbox(f"Selecione o item {idx_r + 1} (Opcional)", options=opcoes_select_opcional, key=f"ins_{idx_r}")
            with sub_col2:
                qtd_sel_r = st.number_input(f"Qtd {idx_r + 1}", min_value=0.01, value=100.0, step=10.0, key=f"qtd_{idx_r}")
            with sub_col3:
                uni_sel_r = st.selectbox(f"Unidade {idx_r + 1}", options=["g", "ml"], key=f"uni_{idx_r}")
            
            if ins_sel_r not in ["- Nenhum -", "- Cadastre insumos primeiro -"]:
                dados_associacao.append({"insumo_id": insumo_opcoes[ins_sel_r], "quantidade": qtd_sel_r, "unidade": uni_sel_r, "nome": ins_sel_r})

    st.markdown("")
    if st.button("Salvar Produto e Ficha Técnica", type="primary"):
        if not lista_insumos:
            st.error("Erro: Cadastre insumos brutos primeiro na Aba 1.")
        elif not dados_associacao:
            st.error("Erro: Selecione pelo menos 1 insumo válido para a ficha técnica.")
        else:
            ids_utilizados = [d["insumo_id"] for d in dados_associacao]
            if len(set(ids_utilizados)) < len(dados_associacao):
                st.error("Erro: Você repetiu o mesmo insumo em campos diferentes.")
            elif not nome_produto.strip():
                st.error("Erro: O nome do produto comercial não pode estar vazio.")
            elif preco_produto <= 0:
                st.error("Erro: O preço deve ser maior que zero.")
            else:
                conn = init_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO produtos (nome, preco) VALUES (%s, %s) RETURNING id;", (nome_produto.strip(), preco_produto))
                            produto_id = cur.fetchone()
                            for dado in dados_associacao:
                                cur.execute("INSERT INTO ficha_tecnica (produto_id, insumo_id, quantidade, unidade) VALUES (%s, %s, %s, %s);", (produto_id, dado["insumo_id"], dado["quantidade"], dado["unidade"]))
                            conn.commit()
                        st.success(f"Sucesso! Produto '{nome_produto}' salvo no Neon.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Erro ao salvar no banco de dados: {err}")
                    finally:
                        conn.close()

# ABA 3: VISUALIZAR E DELETAR MULTIPLOS PRODUTOS
with tabs[2]:
    st.header("📖 Gerenciamento do Cardápio")
    
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
            todos_produtos = cur.fetchall()
            
            if not todos_produtos:
                st.info("Nenhum produto cadastrado no sistema até o momento.")
            else:
                st.warning("Marque as caixas abaixo para selecionar múltiplos produtos e apagá-los de uma só vez.")
                produtos_para_deletar = []
                
                for prod in todos_produtos:
                    col_check, col_content = st.columns([0.05, 0.95])
                    with col_check:
                        selecionado = st.checkbox("", key=f"del_{prod['id']}")
                        if selecionado:
                            produtos_para_deletar.append(prod['id'])
                            
                    with col_content:
                        with st.expander(f"🍽️ {prod['nome']} — R$ {prod['preco']:.2f}"):
                            cur.execute("""
                                SELECT f.quantidade, f.unidade, i.nome as insumo_nome 
                                FROM ficha_tecnica f
                                JOIN insumos i ON f.insumo_id = i.id
                                WHERE f.produto_id = %s;
                            """, (prod['id'],))
                            itens_ficha = cur.fetchall()
                            
                            st.write("**Composição da Receita (Ficha Técnica):**")
                            for item in itens_ficha:
                                baixa_estoque = float(item['quantidade']) / 1000.0
                                unidade_estoque = "Kg" if item['unidade'] == "g" else "L"
                                st.markdown(f"- **{item['insumo_nome']}**: {float(item['quantidade']):.1f}{item['unidade']} *(Baixa: **{baixa_estoque:.3f} {unidade_estoque}** no estoque)*")
                
                st.markdown("---")
                if produtos_para_deletar:
                    qtd_selecionada = len(produtos_para_deletar)
                    if st.button(f"🗑️ Deletar {qtd_selecionada} Produto(s) Selecionado(s)", type="primary"):
                        try:
                            with conn.cursor() as cur:
                                cur.execute("DELETE FROM produtos WHERE id = ANY(%s);", (produtos_para_deletar,))
                                conn.commit()
                            st.success(f"{qtd_selecionada} produto(s) removido(s) com sucesso!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Erro ao remover produtos: {err}")
                else:
                    st.button("🗑️ Deletar Selecionados", disabled=True)
        conn.close()
