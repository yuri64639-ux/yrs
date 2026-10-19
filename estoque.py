import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configuração de Logs do Sistema
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Config:
    PAGE_TITLE = "ERP Gastronômico - Backoffice & Engenharia de Menu"
    LOW_STOCK_THRESHOLD = 2.000  # Limite crítico em Kg ou Litros

class DatabaseManager:
    @staticmethod
    def get_connection():
        try:
            return psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
        except Exception as e:
            logging.error(f"Falha de conexão com a instância Neon: {e}")
            st.error("🚨 Falha na comunicação com o servidor de dados central. Verifique as credenciais.")
            return None

    @classmethod
    def execute_migration(cls):
        conn = cls.get_connection()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                # Esquema de Banco de Dados Relacional Correto e Normalizado
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS insumos (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(255) UNIQUE NOT NULL,
                        quantidade_atual NUMERIC(10,3) NOT NULL DEFAULT 100.000
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
                # Garante integridade de migrações antigas sem perda de dados
                cur.execute("ALTER TABLE insumos ADD COLUMN IF NOT EXISTS quantidade_atual NUMERIC(10,3) NOT NULL DEFAULT 100.000;")
                conn.commit()
                logging.info("Migração de esquema SQL executada com sucesso.")
        except Exception as e:
            logging.critical(f"Erro crítico durante a execução do DDL: {e}")
        finally:
            conn.close()

# Executa barreira de migração de dados antes da renderização da UI
st.set_page_config(page_title=Config.PAGE_TITLE, layout="wide", initial_sidebar_state="expanded")
DatabaseManager.execute_migration()

# --- COMPONENTE COMPARTILHADO: MONITOR REAL-TIME DE ATIVOS ---
@st.fragment(run_every="1s")
def render_dashboard_estoque():
    st.subheader("📊 Indicadores de Volume de Estoque Bruto")
    conn = DatabaseManager.get_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT nome, quantidade_atual FROM insumos ORDER BY nome;")
            items = cur.fetchall()
        conn.close()
        
        if items:
            cols = st.columns(min(len(items), 5))
            for idx, item in enumerate(items):
                qtd = float(item['quantidade_atual'])
                # Alerta visual corporativo dinâmico baseado em criticidade
                label_status = "🔴 Crítico" if qtd <= Config.LOW_STOCK_THRESHOLD else "🟢 Normal"
                with cols[idx % 5]:
                    st.metric(
                        label=f"{item['nome']} ({label_status})",
                        value=f"{qtd:.3f} Unidades",
                        delta=f"{qtd - Config.LOW_STOCK_THRESHOLD:.3f} acima do limite" if qtd > Config.LOW_STOCK_THRESHOLD else "Abaixo da Margem de Segurança",
                        delta_color="normal" if qtd > Config.LOW_STOCK_THRESHOLD else "inverse"
                    )
        else:
            st.info("Nenhum ativo de insumo registrado no almoxarifado.")

# Renderização da Interface Administrativa Principal
st.title("💼 Enterprise Resource Planning (ERP) - Inteligência Operacional")
render_dashboard_estoque()
st.markdown("---")

menu_tabs = st.tabs(["📥 Entrada de Insumos (Lote)", "🏗️ Engenharia de Fichas Técnicas", "📋 Auditoria e Controle de Cardápio"])

# ABA 1: INGESTÃO DE MATÉRIA-PRIMA EM MASSA
with menu_tabs[0]:
    st.header("📥 Ingestão de Matéria-Prima em Lote")
    st.markdown("Utilize esta interface para cadastrar novos insumos comerciais por linha. O estoque base é parametrizado em **Quilos (Kg)** ou **Litros (L)**.")
    
    txt_carga = st.text_area(
        "Massa de Dados para Importação (Um insumo por linha):",
        placeholder="Exemplo:\nQueijo Muçarela\nPeito de Frango\nÓleo de Soja",
        height=180,
        key="erp_txt_ingestao"
    )
    
    if st.button("Executar Carga em Massa", type="primary", use_container_width=True):
        if txt_carga.strip():
            ativos_linhas = [linha.strip() for list_item in txt_carga.split("\n") if (linha := list_item.strip())]
            db_conn = DatabaseManager.get_connection()
            if db_conn:
                novos_ativos = 0
                try:
                    with db_conn.cursor() as cur:
                        for item_nome in ativos_linhas:
                            cur.execute("INSERT INTO insumos (nome) VALUES (%s) ON CONFLICT DO NOTHING;", (item_nome,))
                            if cur.rowcount > 0:
                                novos_ativos += 1
                        db_conn.commit()
                    st.success(f"Carga finalizada com sucesso. Incorporados {novos_ativos} novos ativos ao inventário.")
                    time.sleep(1)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Erro operacional durante a carga: {ex}")
                finally:
                    db_conn.close()
        else:
            st.warning("Validação Recusada: O campo de entrada de dados textual está vazio.")
# ABA 2: ENGENHARIA DE PRODUTOS E MATRIZ DE COMPOSIÇÃO (FICHAS TÉCNICAS)
with menu_tabs[1]:
    st.header("🏗️ Engenharia de Fichas Técnicas")
    
    db_conn = DatabaseManager.get_connection()
    lista_ativos_insumos = []
    if db_conn:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome FROM insumos ORDER BY nome;")
            lista_ativos_insumos = cur.fetchall()
        db_conn.close()
        
    opcoes_obrigatorias = [item["nome"] for item in lista_ativos_insumos] if lista_ativos_insumos else ["- Cadastre insumos primeiro -"]
    opcoes_opcionais = ["- Nenhum -"] + ([item["nome"] for item in lista_ativos_insumos] if lista_insumos else [])
    mapeamento_insumos = {item["nome"]: item["id"] for item in lista_ativos_insumos}
    
    c_dados1, c_dados2 = st.columns(2)
    with c_dados1:
        input_nome_sku = st.text_input("Nome Comercial do Produto (SKU):", key="erp_nome_sku")
    with c_dados2:
        input_preco_sku = st.number_input("Preço de Venda Comercial (R$):", min_value=0.00, step=1.00, format="%.2f", key="erp_preco_sku")
        
    st.markdown("---")
    st.subheader("📋 Matriz de Formulação (Limite de 1 a 6 Insumos por SKU)")
    componentes_ficha = []
    
    # Grid Simétrico de Formulação Comercial (3 Linhas x 2 Colunas)
    for index_row in range(3):
        col_esq, col_dir = st.columns(2)
        
        idx_esq = index_row * 2
        with col_esq:
            st.markdown(f"**Componente Operacional {idx_esq + 1}**")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sel_ins_l = st.selectbox(f"Insumo Ativo {idx_esq + 1}", options=opcoes_obrigatorias if idx_esq == 0 else opcoes_opcionais, key=f"matriz_ins_{idx_esq}")
            with sc2:
                qtd_ins_l = st.number_input(f"Consumo Proporcional {idx_esq + 1}", min_value=0.01, value=100.00, step=10.00, key=f"matriz_qtd_{idx_esq}")
            with sc3:
                uni_ins_l = st.selectbox(f"Unidade de Medida {idx_esq + 1}", options=["g", "ml"], key=f"matriz_uni_{idx_esq}")
            
            if sel_ins_l not in ["- Nenhum -", "- Cadastre insumos primeiro -"]:
                componentes_ficha.append({"insumo_id": mapeamento_insumos[sel_ins_l], "quantidade": qtd_ins_l, "unidade": uni_ins_l})
                
        idx_dir = (index_row * 2) + 1
        with col_dir:
            st.markdown(f"**Componente Operacional {idx_dir + 1}**")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sel_ins_r = st.selectbox(f"Insumo Ativo {idx_dir + 1} (Opcional)", options=opcoes_opcionais, key=f"matriz_ins_{idx_dir}")
            with sc2:
                qtd_ins_r = st.number_input(f"Consumo Proporcional {idx_dir + 1}", min_value=0.01, value=100.00, step=10.00, key=f"matriz_qtd_{idx_dir}")
            with sc3:
                uni_ins_r = st.selectbox(f"Unidade de Medida {idx_dir + 1}", options=["g", "ml"], key=f"matriz_uni_{idx_dir}")
            
            if sel_ins_r not in ["- Nenhum -"]:
                componentes_ficha.append({"insumo_id": mapeamento_insumos[sel_ins_r], "quantidade": qtd_ins_r, "unidade": uni_ins_r})

    st.markdown("")
    if st.button("Homologar Engenharia de Produto", type="primary", use_container_width=True):
        ids_validacao = [comp["insumo_id"] for comp in componentes_ficha]
        
        if not lista_ativos_insumos:
            st.error("Validação Recusada: Banco de dados de insumos vazio. Realize a importação na Aba 1.")
        elif not componentes_ficha:
            st.error("Validação Recusada: Selecione ao menos 1 insumo válido para compor a receita.")
        elif len(set(ids_validacao)) < len(componentes_ficha):
            st.error("Validação Recusada: Foram detectados insumos duplicados na mesma matriz. Escolha itens distintos.")
        elif not input_nome_sku.strip():
            st.error("Validação Recusada: O identificador SKU do produto não pode ser nulo.")
        elif input_preco_sku <= 0:
            st.error("Validação Recusada: O preço comercial do SKU deve ser superior a zero.")
        else:
            db_conn = DatabaseManager.get_connection()
            if db_conn:
                try:
                    with db_conn.cursor() as cur:
                        cur.execute("INSERT INTO produtos (nome, preco) VALUES (%s, %s) RETURNING id;", (input_nome_sku.strip(), input_preco_sku))
                        id_gerado_produto = cur.fetchone()[0]
                        
                        for item_associado in componentes_ficha:
                            cur.execute(
                                "INSERT INTO ficha_tecnica (produto_id, insumo_id, quantidade, unidade) VALUES (%s, %s, %s, %s);",
                                (id_gerado_produto, item_associado["insumo_id"], item_associado["quantidade"], item_associado["unidade"])
                            )
                        db_conn.commit()
                    st.success(f"Sucesso: SKU '{input_nome_sku}' homologado com {len(componentes_ficha)} amarrações operacionais.")
                    time.sleep(1)
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro durante a transação relacional: {err}")
                finally:
                    db_conn.close()

# ABA 3: AUDITORIA E EXCLUSÃO SELETIVA EM LOTE DO CARDÁPIO
with menu_tabs[2]:
    st.header("📋 Auditoria e Controle de Cardápio")
    st.markdown("Abaixo estão listados todos os SKUs comercializados. Selecione múltiplos itens para exclusão imediata em lote do servidor central.")
    
    db_conn = DatabaseManager.get_connection()
    if db_conn:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, preco FROM produtos ORDER BY nome;")
            todos_skus = cur.fetchall()
            
            if not todos_skus:
                st.info("Nenhum produto cadastrado no catálogo comercial até o momento.")
            else:
                fila_exclusao_lote = []
                
                # Renderizador Avançado de Tabela com Checkboxes Alinhados
                for sku in todos_skus:
                    c_check, c_expand = st.columns([0.04, 0.96])
                    with c_check:
                        marcado = st.checkbox("", key=f"chk_auditoria_{sku['id']}")
                        if marcado:
                            fila_exclusao_lote.append(sku['id'])
                    with c_expand:
                        with st.expander(f"🍽️ {sku['nome']} — Preço de Venda: R$ {sku['preco']:.2f}"):
                            cur.execute("""
                                SELECT f.quantidade, f.unidade, i.nome as insumo_nome 
                                FROM ficha_tecnica f
                                JOIN insumos i ON f.insumo_id = i.id
                                WHERE f.produto_id = %s;
                            """, (sku['id'],))
                            elementos_receita = cur.fetchall()
                            
                            st.write("**Detalhamento de Engenharia de Custo (Ficha Técnica):**")
                            for component in elementos_receita:
                                equivalencia_estoque = float(component['quantidade']) / 1000.0
                                unidade_estoque_global = "Kg" if component['unidade'] == "g" else "L"
                                st.markdown(f"- **{component['insumo_nome']}**: {float(component['quantidade']):.1f}{component['unidade']} *(Baixa calculada por porção: **{equivalencia_estoque:.3f} {unidade_estoque_global}**)*")
                
                st.markdown("---")
                if fila_exclusao_lote:
                    total_selecionados = len(fila_exclusao_lote)
                    if st.button(f"🗑️ Expurgar {total_selecionados} SKU(s) Selecionado(s)", type="primary", use_container_width=True):
                        try:
                            with db_conn.cursor() as cur:
                                # Processamento massivo de exclusão via ARRAY PostgreSQL
                                cur.execute("DELETE FROM produtos WHERE id = ANY(%s);", (fila_exclusao_lote,))
                                db_conn.commit()
                            st.success(f"Auditoria Concluída: {total_selecionados} SKUs removidos do ecossistema.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as err:
                            st.error(f"Falha na deleção em lote do banco: {err}")
                else:
                    st.button("🗑️ Expurgar Selecionados", disabled=True, use_container_width=True, key="btn_expurgo_disabled")
        db_conn.close()
