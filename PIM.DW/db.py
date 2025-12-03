import sqlite3

DB_NAME = "academico_ia.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabelas básicas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS materias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL,
            materia_id INTEGER NOT NULL,
            np1 REAL,
            np2 REAL,
            media REAL,
            FOREIGN KEY (aluno_id) REFERENCES alunos(id),
            FOREIGN KEY (materia_id) REFERENCES materias(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS faltas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL,
            materia_id INTEGER NOT NULL,
            total_faltas INTEGER DEFAULT 0,
            limite_faltas INTEGER DEFAULT 25,
            FOREIGN KEY (aluno_id) REFERENCES alunos(id),
            FOREIGN KEY (materia_id) REFERENCES materias(id)
        )
    """)

    # Dados de exemplo apenas se não tiver nada
    cur.execute("SELECT COUNT(*) FROM alunos")
    qtd_alunos = cur.fetchone()[0]

    if qtd_alunos == 0:
        cur.execute("INSERT INTO alunos (nome, email) VALUES (?, ?)",
                    ("Aluno Exemplo", "aluno@example.com"))
        aluno_id = cur.lastrowid

        materias = ["Algoritmos", "Banco de Dados", "Cálculo", "Programação Web"]
        materia_ids = []
        for nome in materias:
            cur.execute("INSERT INTO materias (nome) VALUES (?)", (nome,))
            materia_ids.append(cur.lastrowid)

        # Notas exemplo
        notas_exemplo = [
            (aluno_id, materia_ids[0], 6.5, 8.0),
            (aluno_id, materia_ids[1], 5.0, 4.0),
            (aluno_id, materia_ids[2], 7.0, 6.0),
            (aluno_id, materia_ids[3], 8.5, 9.0),
        ]
        for aluno, materia, np1, np2 in notas_exemplo:
            media = round((np1 + np2) / 2, 2)
            cur.execute("""
                INSERT INTO notas (aluno_id, materia_id, np1, np2, media)
                VALUES (?, ?, ?, ?, ?)
            """, (aluno, materia, np1, np2, media))

        # Faltas exemplo
        faltas_exemplo = [
            (aluno_id, materia_ids[0], 12, 25),
            (aluno_id, materia_ids[1], 5, 25),
            (aluno_id, materia_ids[2], 24, 25),
            (aluno_id, materia_ids[3], 2, 25),
        ]
        for aluno, materia, total, limite in faltas_exemplo:
            cur.execute("""
                INSERT INTO faltas (aluno_id, materia_id, total_faltas, limite_faltas)
                VALUES (?, ?, ?, ?)
            """, (aluno, materia, total, limite))

    conn.commit()
    conn.close()
