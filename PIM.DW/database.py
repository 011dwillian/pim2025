# database.py
import sqlite3
import os

DB_FILE = "sistema_academico.db"

def conectar():
    return sqlite3.connect(DB_FILE)

def inicializar_banco():
    """Cria todas as tabelas necessárias e insere dados de exemplo se necessário."""
    conn = conectar()
    c = conn.cursor()

    # Alunos
    c.execute("""
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nascimento TEXT,
        ra TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        email TEXT
    )
    """)

    # Professores
    c.execute("""
    CREATE TABLE IF NOT EXISTS professores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        disciplina TEXT
    )
    """)

    # Disciplinas
    c.execute("""
    CREATE TABLE IF NOT EXISTS disciplinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        semestre TEXT,
        professor_id INTEGER,
        FOREIGN KEY(professor_id) REFERENCES professores(id)
    )
    """)

    # Notas
    c.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        disciplina_id INTEGER,
        nota REAL,
        FOREIGN KEY(aluno_id) REFERENCES alunos(id),
        FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id)
    )
    """)

    # Frequência
    c.execute("""
    CREATE TABLE IF NOT EXISTS frequencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        disciplina_id INTEGER,
        presencas INTEGER DEFAULT 0,
        faltas INTEGER DEFAULT 0,
        FOREIGN KEY(aluno_id) REFERENCES alunos(id),
        FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id)
    )
    """)

    # Cronograma
    c.execute("""
    CREATE TABLE IF NOT EXISTS cronograma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disciplina_id INTEGER,
        conteudo TEXT,
        data TEXT,
        FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id)
    )
    """)

    # Chat
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente_tipo TEXT,
        remetente_id INTEGER,
        destinatario_tipo TEXT,
        destinatario_id INTEGER,
        mensagem TEXT,
        data TEXT
    )
    """)

    # IA histórico (opcional)
    c.execute("""
    CREATE TABLE IF NOT EXISTS ia_historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        data TEXT,
        resumo TEXT
    )
    """)

    conn.commit()

    # Inserir dados iniciais se tabelas vazias
    # Professor exemplo
    c.execute("SELECT COUNT(*) FROM professores")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO professores (nome, email, senha, disciplina) VALUES (?, ?, ?, ?)",
            ("Carlos Andrade", "carlos@unip.edu.br", "12345", "Engenharia de Software")
        )

    # Aluno exemplo
    c.execute("SELECT COUNT(*) FROM alunos")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO alunos (nome, data_nascimento, ra, senha, email) VALUES (?, ?, ?, ?, ?)",
            ("Maria Oliveira", "2002-03-15", "A1B2C3D", "12345", "maria.aluno@unip.edu.br")
        )

    # Disciplina exemplo (assume professor id 1)
    c.execute("SELECT COUNT(*) FROM disciplinas")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO disciplinas (nome, semestre, professor_id) VALUES (?, ?, ?)",
            ("Engenharia de Software", "2025/1", 1)
        )

    # Notas e frequencia exemplos (aluno id 1, disciplina id 1)
    c.execute("SELECT COUNT(*) FROM notas")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO notas (aluno_id, disciplina_id, nota) VALUES (?, ?, ?)", (1, 1, 8.5))
    c.execute("SELECT COUNT(*) FROM frequencia")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO frequencia (aluno_id, disciplina_id, presencas, faltas) VALUES (?, ?, ?, ?)", (1, 1, 12, 2))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_banco()
    print("Banco inicializado")
