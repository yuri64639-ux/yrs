import psycopg2
import streamlit as st

def ob_cx():
    """Gerencia a conexão dinâmica com o Banco de Dados PostgreSQL baseado nos secrets do Streamlit."""
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

def inicializar_banco():
    """Executa as DDLs e garante o ecossistema relacional e multi-tenant isolado."""
    conn = ob_cx()
    with conn.cursor() as cur:
        cur.execute("SET search_path TO public;")
        cur.execute("CREATE TABLE IF NOT EXISTS empresas (id SERIAL PRIMARY KEY, nome_empresa TEXT UNIQUE NOT NULL, data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT, senha TEXT);")
        cur.execute("CREATE TABLE IF NOT EXISTS estoque (id SERIAL PRIMARY KEY, item TEXT, quantidade REAL);")
        cur.execute("CREATE TABLE IF NOT EXISTS produtos (id SERIAL PRIMARY KEY, nome TEXT, categoria TEXT, preco REAL);")
        cur.execute("CREATE TABLE IF NOT EXISTS receitas (id SERIAL PRIMARY KEY, produto_id INTEGER, insumo_id INTEGER, qtd_insumo REAL);")
        cur.execute("CREATE TABLE IF NOT EXISTS pedidos (id SERIAL PRIMARY KEY, mesa TEXT, produto_id INTEGER, quantidade INTEGER, status TEXT DEFAULT 'Pendente', horario TEXT, taxa_paga INTEGER DEFAULT 1, pago TEXT DEFAULT 'Não', garcom TEXT, modo_pagamento TEXT);")
        
        # Adição segura de colunas e chaves estrangeiras
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE estoque ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE produtos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE receitas ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        cur.execute("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;")
        conn.commit()
        
        # Remoção de constraints globais legadas
        try: cur.execute("ALTER TABLE produtos DROP CONSTRAINT IF EXISTS produtos_nome_key CASCADE;")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE estoque DROP CONSTRAINT IF EXISTS estoque_item_key CASCADE;")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_usuario_key CASCADE;")
        except: conn.rollback()
        conn.commit()
        
        # Criação de chaves únicas compostas por Tenant (empresa_id)
        try: cur.execute("ALTER TABLE usuarios ADD CONSTRAINT unique_empresa_usuario UNIQUE(empresa_id, usuario);")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE estoque ADD CONSTRAINT unique_empresa_item UNIQUE(empresa_id, item);")
        except: conn.rollback()
        try: cur.execute("ALTER TABLE produtos ADD CONSTRAINT unique_empresa_produto UNIQUE(empresa_id, nome);")
        except: conn.rollback()
    conn.commit()
    conn.close()
