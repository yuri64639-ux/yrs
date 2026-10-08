import sqlite3

def init_db():
    """Inicializa as tabelas do banco de dados isolado da marinote club."""
    # Alterado o nome do banco de dados para marinote_club.db
    with sqlite3.connect('marinote_club.db') as conn:
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
        
        # Verifica se o administrador Artur já existe
        cur.execute("SELECT COUNT(*) FROM barbeiros WHERE LOWER(nome) = 'artur'")
        if cur.fetchone()[0] == 0:
            # Remove qualquer resquício antigo do usuário Admin se o banco já existir
            cur.execute("DELETE FROM barbeiros WHERE LOWER(nome) = 'admin'")
            
            # Cria Artur como o administrador e barbeiro principal do sistema (Senha: 1234)
            cur.execute("INSERT INTO barbeiros (nome, senha) VALUES ('Artur', '1234')")
            
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("Banco de dados 'marinote_club.db' inicializado com sucesso!")
