import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Configuração da página do Streamlit para o Caixa/Pedidos
st.set_page_config(page_title="Frente de Caixa & Pedidos", layout="wide")

# Conexão segura e direta com o Banco de Dados Neon na nuvem
def init_connection():
    try:
        return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    except Exception as e:
        st.error(f"Erro ao conectar ao banco Neon: {e}")
        return None

# Atualização estrutural para incluir as tabelas relacionais necessárias
def upgrade_db_pedidos():
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
                    forma_pagamento VARCHAR(50) DEFAULT 'Dinheiro',
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            try:
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS mesa_numero VARCHAR(50) DEFAULT 'Balcão';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS comanda_codigo VARCHAR(100) DEFAULT 'Não Informado';")
                cur.execute("ALTER TABLE pedidos_realizados ADD COLUMN IF NOT EXISTS forma_pagamento VARCHAR(50) DEFAULT 'Dinheiro';")
            except:
                pass
            conn.commit()
        conn.close()

upgrade_db_pedidos()

# Inicializa a memória do carrinho de compras se não existir
if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}

# CHECAGEM OCULTA: Monitora em segundo plano e alerta o garçom sobre itens acabando
@st.fragment(run_every="1s")
def checar_alertas_estoque_oculto():
    conn = init_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT nome, quantidade_atual FROM insumos WHERE quantidade_atual <= 2.000 ORDER BY nome;")
            itens_criticos = cur.fetchall()
        conn.close()
        if itens_criticos:
            for item in itens_criticos:
                st.error(f"⚠️ **ATENÇÃO GARÇOM:** O insumo **{item['nome']}** está acabando no estoque! (Restam apenas {float(item['quantidade_atual']):.3f} Kg/L)")

st.title("🛒 Frente de Caixa: Lançamento de Vendas")
st.caption("Frente de caixa com carrinho múltiplo e revisão prévia unificada")

checar_alertas_estoque_oculto()
st.markdown("---")

st.subheader("👤 Identificação do Atendimento")
col_mesa, col_comanda, col_pagamento = st.columns(3)
with col_mesa:
    input_mesa = st.text_input("🪑 Número da Mesa:", value="Balcão")
with col_comanda:
    input_comanda = st.text_input("📋 Código da Comanda:", value="Não Informado")
with col_pagamento:
    opcao_pagamento = st.selectbox("Forma de Pagamento:", ["Dinheiro", "Pix", "Crédito", "Débito"])

st.markdown("---")
st.subheader("🔍 Encontrar Itens do Cardápio")
busca_termo = st.text_input("🔍 Buscar Produto no Cardápio (Lupa):", placeholder="Ex: Batata Frita")

conn = init_connection()
produtos_filtrados = []
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if busca_termo:
            cur.execute("SELECT id, nome, preco FROM produtos WHERE nome ILIKE %s ORDER BY nome;", (f"%{busca_termo}%",))
        else:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
        produtos_filtrados = cur.fetchall()
    conn.close()
if not produtos_filtrados:
    st.warning("Nenhum produto encontrado no cardápio.")
else:
    st.markdown("### Produtos Disponíveis")
    for prod in produtos_filtrados:
        col_n, col_p, col_q, col_b = st.columns([0.4, 0.2, 0.2, 0.2])
        p_base = float(prod['preco'])
        
        with col_n:
            st.markdown(f"**{prod['nome']}**")
        with col_p:
            st.markdown(f"R$ {p_base:.2f}")
        with col_q:
            qtd_p = st.number_input("Quantidade", min_value=1, value=1, key=f"caixa_qtd_{prod['id']}")
        with col_b:
            if st.button("➕ Adicionar à Seleção", key=f"add_cart_{prod['id']}", use_container_width=True):
                # Guarda as informações do produto selecionado no carrinho temporário
                p_id = str(prod['id'])
                if p_id in st.session_state.carrinho:
                    st.session_state.carrinho[p_id]["qtd"] += qtd_p
                else:
                    st.session_state.carrinho[p_id] = {"nome": prod['nome'], "preco": p_base, "qtd": qtd_p, "id_real": prod['id']}
                st.toast(f"Adicionado: {qtd_p}x {prod['nome']}")

st.markdown("---")
st.subheader("📋 Conferir Seleção de Itens (Carrinho)")

if not st.session_state.carrinho:
    st.info("Nenhum item selecionado até o momento. Use os botões acima para montar o pedido.")
else:
    # Exibe o espelho do pedido estruturado na tela
    st.markdown(f"**Destino:** {input_mesa.strip()} | **Identificador:** {input_comanda.strip()} | **Pagamento:** {opcao_pagamento}")
    
    total_geral_carrinho = 0.0
    itens_remover = []
    
    for k, item in st.session_state.carrinho.items():
        c_item_nome, c_item_preco, c_item_qtd, c_item_sub, c_item_del = st.columns([0.3, 0.2, 0.15, 0.2, 0.15])
        sub_total_item = item["preco"] * item["qtd"]
        total_geral_carrinho += sub_total_item
        
        with c_item_nome:
            st.write(f"• **{item['nome']}**")
        with c_item_preco:
            st.write(f"R$ {item['preco']:.2f} cada")
        with c_item_qtd:
            st.write(f"{item['qtd']} un")
        with c_item_sub:
            st.write(f"Subtotal: R$ {sub_total_item:.2f}")
        with c_item_del:
            if st.button("❌ Tirar", key=f"del_item_cart_{k}"):
                itens_remover.append(k)
                
    # Remove itens que o usuário escolheu retirar antes de confirmar
    for k in itens_remover:
        del st.session_state.carrinho[k]
        st.rerun()
        
    st.markdown(f"### Total do Pedido: R$ {total_geral_carrinho:.2f}")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("✅ Confirmar e Enviar Pedido", type="primary", use_container_width=True):
            conn = init_connection()
            if conn:
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        erro_estoque_geral = False
                        
                        # 1. Primeira varredura: Garante que há estoque para toda a lista conjunta
                        for k, item in st.session_state.carrinho.items():
                            cur.execute("SELECT f.insumo_id, f.quantidade, i.nome, i.quantidade_atual FROM ficha_tecnica f JOIN insumos i ON f.insumo_id = i.id WHERE f.produto_id = %s;", (item['id_real'],))
                            ficha = cur.fetchall()
                            
                            for f_item in ficha:
                                consumo_necessario = (float(f_item['quantidade']) / 1000.0) * item['qtd']
                                if float(f_item['quantidade_atual']) < consumo_necessario:
                                    st.error(f"Estoque Insuficiente! O item '{f_item['nome']}' precisa de {consumo_necessario:.3f} Kg/L, mas possui apenas {float(f_item['quantidade_atual']):.3f}.")
                                    erro_estoque_geral = True
                        
                        # 2. Segunda varredura: Se tudo estiver OK, processa as baixas e grava as linhas
                        if not erro_estoque_geral:
                            for k, item in st.session_state.carrinho.items():
                                cur.execute("SELECT f.insumo_id, f.quantidade FROM ficha_tecnica f WHERE f.produto_id = %s;", (item['id_real'],))
                                ficha = cur.fetchall()
                                
                                # Executa a baixa
                                for f_item in ficha:
                                    consumo = (float(f_item['quantidade']) / 1000.0) * item['qtd']
                                    cur.execute("UPDATE insumos SET quantidade_atual = quantidade_atual - %s WHERE id = %s;", (consumo, f_item['insumo_id']))
                                
                                # Grava a linha do pedido (Sem a taxa de 10%)
                                valor_venda_item = item["preco"] * item["qtd"]
                                cur.execute("""
                                    INSERT INTO pedidos_realizados (produto_nome, quantidade_pedida, valor_total, taxa_inclusa, mesa_numero, comanda_codigo, forma_pagamento) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                                """, (item['nome'], item['qtd'], valor_venda_item, False, input_mesa.strip(), input_comanda.strip(), opcao_pagamento))
                            
                            conn.commit()
                            st.session_state.carrinho = {}  # Limpa o carrinho após a transação
                            st.success("Lote de pedidos enviado com sucesso e estoque atualizado!")
                            time.sleep(1)
                            st.rerun()
                except Exception as err:
                    st.error(f"Erro no processamento em lote do banco: {err}")
                finally:
                    conn.close()
                    
    with col_c2:
        if st.button("🗑️ Limpar Toda a Seleção", use_container_width=True):
            st.session_state.carrinho = {}
            st.success("Seleção esvaziada!")
            time.sleep(0.5)
            st.rerun()
