import sqlite3

def init_db():
    """Inicializa as tabelas do banco de dados isolado da marinote club."""
    with sqlite3.connect("barber.db") as conn:
        cur = conn.cursor()
        # Tabela para o catálogo de serviços
        cur.execute("""
            CREATE TABLE IF NOT EXISTS servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nome TEXT UNIQUE, 
                preco REAL
            )
        """)
        # Tabela para controle da equipe de barbeiros
        cur.execute("""
            CREATE TABLE IF NOT EXISTS barbeiros (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nome TEXT UNIQUE, 
                senha TEXT
            )
        """)
        # Tabela para comandas de atendimento em andamento e finalizadas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comandas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                cliente TEXT, 
                servico_id INTEGER, 
                barbeiro TEXT, 
                valor REAL, 
                status TEXT DEFAULT 'Aberto', 
                comissao INTEGER DEFAULT 1, 
                data TEXT
            )
        """)
        # Tabela para o autoagendamento de data e horário do cliente
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                cliente TEXT, 
                servico_id INTEGER, 
                barbeiro TEXT, 
                data TEXT, 
                horario TEXT, 
                status TEXT DEFAULT 'Agendado'
            )
        """)
        
        # Garante a criação do usuário Admin padrão caso o banco seja novo
        cur.execute("SELECT COUNT(*) FROM barbeiros")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO barbeiros (nome, senha) VALUES ('Admin', '1234')")
        conn.commit()
