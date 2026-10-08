import sqlite3

def init_db():
    with sqlite3.connect("barber.db") as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, preco REAL)")
        cur.execute("CREATE TABLE IF NOT EXISTS barbeiros (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, senha TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS comandas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, servico_id INTEGER, barbeiro TEXT, valor REAL, status TEXT DEFAULT 'Aberto', comissao INTEGER DEFAULT 1, data TEXT)")
        # Tabela para agendamentos de dia e horário
        cur.execute("CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, servico_id INTEGER, barbeiro TEXT, data TEXT, horario TEXT, status TEXT DEFAULT 'Agendado')")
        cur.execute("SELECT COUNT(*) FROM barbeiros")
        if cur.fetchone() == 0:
            cur.execute("INSERT INTO barbeiros (nome, senha) VALUES ('Admin', '1234')")
        conn.commit()
