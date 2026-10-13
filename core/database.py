# ==============================================================================
# CORE/DATABASE.PY - GERENCIAMENTO DO BANCO DE DADOS POSTGRESQL
# ==============================================================================
import streamlit as st
import psycopg2

def ob_cx():
    """Retorna uma conexão limpa com o PostgreSQL usando st.secrets."""
    try:
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            port=st.secrets["postgres"]["port"]
        )
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def inicializar_banco():
    """Garante de forma resiliente que as tabelas base do ecossistema existam."""
    conn = ob_cx()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO public;")
                
                # Tabela de Empresas (Multi-Tenant)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS empresas (
                        id SERIAL PRIMARY KEY,
                        nome_empresa VARCHAR(255) NOT NULL UNIQUE
                    );
                """)
                
                # Tabela de Usuários / Administradores
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY,
                        empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
                        usuario VARCHAR(100) NOT NULL,
                        senha VARCHAR(255) NOT NULL
                    );
                """)
                conn.commit()
        except Exception as e:
            print(f"Erro crítico ao rodar DDLs de inicialização: {e}")
        finally:
            conn.close()
