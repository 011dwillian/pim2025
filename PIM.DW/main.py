# main_complete_v4_modified_v4.py
# UNIP - Sistema Acadêmico Colaborativo (Updated with SUB note, Substitution Logic, Color Coding, and corrected Freq. calculation to 35 classes, Financeiro, and Interactive IA Chat)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3, os, datetime, re, threading
from html.parser import HTMLParser

DB_FILE = "sistema_academico.db"

MAIN_BG = "#001f3f"
INNER_BG = "#cfeeff"
UNIP_YELLOW = "#FFD700"
BTN_BG = "#00509e"
BTN_FG = "#FFFFFF"
FONT_LABEL = ("Arial", 10, "bold")

# --- Novas Constantes de Cores ---
NOTE_COLOR_RED = '#B00020'      # <= 6.9 (Vermelho)
NOTE_COLOR_YELLOW = '#FFC107'   # 7.0 (Amarelo)
NOTE_COLOR_GREEN = '#007E33'    # >= 8.0 (Verde)

FREQ_COLOR_RED = '#B00020'      # <= 74.9% (Vermelho)
FREQ_COLOR_YELLOW = '#FFC107'   # 75.0% a 79.9% (Amarelo)
FREQ_COLOR_GREEN = '#007E33'    # >= 80.0% (Verde)
# ---------------------------------

# --- Novas Constantes Financeiras ---
FINANCIAL_MONTHLY_FEE = 581.75
FINANCE_COLOR_PAID_OK = '#007E33'  # Green for Paid on time (Concluído)
FINANCE_COLOR_PENDING = '#FF8C00'  # Orange for Pending/Current (Pendente)
FINANCE_COLOR_OVERDUE = '#B00020'  # Red for Overdue/Paid Late (Atraso/Não Pagou)
PAYMENT_METHODS = ["DEBITO", "CREDITO", "PIX"]
# ------------------------------------

UNIVERSAL_DISCIPLINES = [
    "Engenharia de Software Ágil",
    "Algoritmo e Estrutura de Dados em Python",
    "Programação Estruturada em C",
    "Analise e Projeto de Sistemas"
]

INITIAL_STUDENTS = [
    ("David Willian", "A123456"),
    ("Guilherme Mendonça", "B123456"),
    ("Walisson Pereira", "C123456"),
    ("Thomas Lopes", "D123456"),
    ("Vinicius Hisashi", "E123456"),
]

INITIAL_PROFESSORS = [
    ("Airton", "Engenharia de Software Ágil"),
    ("Ageu", "Algoritmo e Estrutura de Dados em Python"),
    ("Ivan", "Programação Estruturada em C"),
    ("Glauco", "Analise e Projeto de Sistemas"),
]

COORD_EMAIL = "coordenadorads@unip.edu.br"
COORD_PASS = "1234567"

# CORREÇÕES APLICADAS: Ajuste para atender à regra de 35 Aulas e limite de 25% (padrão)
SEMESTER_TOTAL_CLASSES = 35 # Aulas totais no semestre por disciplina
MAX_ALLOWED_ABSENCES = 9 # Máximo de faltas permitido (25% de 35 = 8.75. Arredondado para 9 faltas)
MIN_PASS_GRADE = 7.0
# A porcentagem mínima de aprovação é de (35 - 9) / 35 = 74.28% (75% é o padrão)
MIN_PASS_FREQUENCY = (SEMESTER_TOTAL_CLASSES - MAX_ALLOWED_ABSENCES) / SEMESTER_TOTAL_CLASSES * 100 

class DBWatcher:
    def __init__(self):
        self._v = 0
        self._lock = threading.Lock()
    def bump(self):
        with self._lock:
            self._v += 1
    def value(self):
        with self._lock:
            return self._v

db_watcher = DBWatcher()

def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    created = not os.path.exists(DB_FILE)
    conn = connect_db(); c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nasc TEXT,
        ra TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        email TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS professores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        disciplina TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS disciplinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        disciplina_id INTEGER NOT NULL,
        UNIQUE(aluno_id, disciplina_id)
    );
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        disciplina_id INTEGER NOT NULL,
        np1 REAL,
        np2 REAL,
        sub REAL, -- Adicionado campo SUB para prova substitutiva
        UNIQUE(aluno_id, disciplina_id)
    );
    CREATE TABLE IF NOT EXISTS frequencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        disciplina_id INTEGER NOT NULL,
        presencas INTEGER DEFAULT 0,
        faltas INTEGER DEFAULT 0,
        UNIQUE(aluno_id, disciplina_id)
    );
    CREATE TABLE IF NOT EXISTS cronogramas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disciplina_id INTEGER NOT NULL,
        modulo_index INTEGER NOT NULL,
        titulo TEXT,
        subtemas TEXT,
        marcado INTEGER DEFAULT 0,
        marcado_em TEXT
    );
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente_type TEXT,
        remetente_email TEXT,
        destinatario_type TEXT,
        destinatario_email TEXT,
        mensagem TEXT,
        data TEXT
    );
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT,
        tipo TEXT
    );
    CREATE TABLE IF NOT EXISTS motivos_exclusao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT UNIQUE,
        descricao TEXT
    );
    CREATE TABLE IF NOT EXISTS ia_historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        data TEXT,
        resumo TEXT
    );
    CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER NOT NULL,
        mes TEXT NOT NULL, -- e.g., 'JAN', 'FEV', 'MAR'
        ano INTEGER NOT NULL,
        valor REAL NOT NULL,
        status TEXT NOT NULL, -- 'PENDENTE', 'PAGO', 'ATRASO', 'PAGO_ATRASO'
        forma_pagamento TEXT, -- 'DEBITO', 'CREDITO', 'PIX'
        data_pagamento TEXT, -- ISO format (Data e hora do pagamento)
        data_lancamento TEXT, -- When coord registered
        UNIQUE(aluno_id, mes, ano)
    );
    """)
    # Check if 'sub' column exists, if not, add it (for existing databases)
    c.execute("PRAGMA table_info(notas)")
    columns = [info[1] for info in c.fetchall()]
    if 'sub' not in columns:
        c.execute("ALTER TABLE notas ADD COLUMN sub REAL")
    
    # motivos defaults and disciplines
    c.execute("INSERT OR IGNORE INTO motivos_exclusao (chave, descricao) VALUES (?, ?)", ("transferencia", "Aluno transferido de campus"))
    c.execute("INSERT OR IGNORE INTO motivos_exclusao (chave, descricao) VALUES (?, ?)", ("trancamento", "Aluno trancou o curso"))
    c.execute("INSERT OR IGNORE INTO motivos_exclusao (chave, descricao) VALUES (?, ?)", ("pendencia_financeira", "Aluno em débito com o financeiro há mais de 6 meses"))
    for d in UNIVERSAL_DISCIPLINES:
        c.execute("INSERT OR IGNORE INTO disciplinas (nome) VALUES (?)", (d,))
    # ensure coordinator user
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (COORD_EMAIL, COORD_PASS, "coordenador"))
    conn.commit(); conn.close()
    return created

def seed_initial_data():
    conn = connect_db(); c = conn.cursor()
    # students
    for nome, ra in INITIAL_STUDENTS:
        email = f"{nome.split()[0].lower()}@unip.edu.br"
        c.execute("SELECT id FROM alunos WHERE ra=?", (ra,))
        if not c.fetchone():
            c.execute("INSERT INTO alunos (nome, data_nasc, ra, senha, email) VALUES (?, ?, ?, ?, ?)", (nome, "10/07/2000", ra, "12345", email))
            aid = c.lastrowid
            c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (email, "12345", "aluno"))
            # matriculate in the 4 universal disciplines only
            for dname in UNIVERSAL_DISCIPLINES:
                c.execute("SELECT id FROM disciplinas WHERE nome=?", (dname,))
                dr = c.fetchone()
                if dr:
                    did = dr["id"]
                    c.execute("INSERT OR IGNORE INTO matriculas (aluno_id, disciplina_id) VALUES (?, ?)", (aid, did))
                    # Adicionado 'sub' no insert inicial
                    c.execute("INSERT OR IGNORE INTO notas (aluno_id, disciplina_id, np1, np2, sub) VALUES (?, ?, ?, ?, ?)", (aid, did, None, None, None))
                    c.execute("INSERT OR IGNORE INTO frequencia (aluno_id, disciplina_id, presencas, faltas) VALUES (?, ?, ?, ?)", (aid, did, 0, 0))
        
            # Seed financial data for the current year
            MONTHS = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
            CURRENT_YEAR = datetime.date.today().year
            
            for month in MONTHS:
                c.execute("INSERT OR IGNORE INTO financeiro (aluno_id, mes, ano, valor, status) VALUES (?, ?, ?, ?, ?)", 
                          (aid, month, CURRENT_YEAR, FINANCIAL_MONTHLY_FEE, "PENDENTE"))
                          
    # professors
    for nome, materia in INITIAL_PROFESSORS:
        email = f"{nome.split()[0].lower()}@unip.edu.br"
        c.execute("SELECT id FROM professores WHERE email=?", (email,))
        if not c.fetchone():
            # ensure discipline exists
            c.execute("INSERT OR IGNORE INTO professores (nome, email, senha, disciplina) VALUES (?, ?, ?, ?)", (nome, email, "12345", materia))
            c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (email, "12345", "professor"))
            # create 5 modules for this discipline if not existing
            c.execute("SELECT id FROM disciplinas WHERE nome=?", (materia,))
            dr = c.fetchone()
            if dr:
                did = dr["id"]
                c.execute("SELECT COUNT(*) as cnt FROM cronogramas WHERE disciplina_id=?", (did,))
                if c.fetchone()["cnt"] == 0:
                    # create modules with subtopics (5 modules)
                    modules = [
                        ("Introdução e conceitos gerais", "Conceitos;História;Aplicações"),
                        ("Tópicos fundamentais", "Tema 1;Tema 2;Tema 3"),
                        ("Práticas e exercícios", "Exemplo 1;Exemplo 2;Exemplo 3"),
                        ("Avaliações e estudos de caso", "Caso 1;Caso 2"),
                        ("Revisão e aprofundamento", "Revisão;Exercícios extra")
                    ]
                    for idx, (titulo, subs) in enumerate(modules, start=1):
                        c.execute("INSERT INTO cronogramas (disciplina_id, modulo_index, titulo, subtemas, marcado, marcado_em) VALUES (?, ?, ?, ?, ?, ?)",
                                  (did, idx, titulo, subs, 0, None))
    conn.commit(); conn.close()

# Validation helpers
def validar_ra(ra): return bool(re.fullmatch(r"[A-Za-z0-9]{7}", ra))
def validar_email_unip(email): return isinstance(email, str) and email.endswith("@unip.edu.br")
def validar_senha5(senha): return senha.isdigit() and len(senha) == 5
def calc_media(np1, np2, sub):
    """
    Calcula a média final. Se a média (NP1+NP2)/2 for < MIN_PASS_GRADE (7.0)
    e houver nota SUB, SUB substitui a menor nota entre NP1 e NP2.
    """
    # 1. Obter notas iniciais válidas (NP1 e NP2)
    initial_vals = [v for v in (np1, np2) if v is not None]
    if not initial_vals: return None
   
    # 2. Calcular Média Inicial (para checagem de substituição)
    if len(initial_vals) == 2:
        initial_media = sum(initial_vals) / 2
    else:
        # Se apenas uma nota, a média é a nota (consistente com a lógica anterior)
        initial_media = initial_vals[0]
        
    final_media = initial_media
    
    # 3. Aplicar Regra SUB
    if sub is not None and sub > 0.0:
        
        # O aluno é elegível para substituição se a média de (NP1+NP2)/2 for < 7.0 (ou se uma nota estiver faltando)
        is_eligible = initial_media < MIN_PASS_GRADE
        
        if is_eligible and len(initial_vals) == 2:
            # SUB substitui a menor nota entre NP1 e NP2
            if np1 <= np2:
                final_media = (sub + np2) / 2
            else:
                final_media = (np1 + sub) / 2
        
        elif is_eligible and len(initial_vals) == 1:
            # Se apenas uma nota, SUB substitui a nota faltante (a ser substituída)
            # Para manter a média por 2, a nota faltante é considerada a ser substituída
            final_media = (initial_vals[0] + sub) / 2
            
        elif len(initial_vals) == 0:
            # Se apenas SUB for fornecida (NP1=NP2=None). A média é apenas SUB.
            final_media = sub
            
    return round(final_media, 2)

def calc_freq_percent(faltas):
    presencas = max(0, SEMESTER_TOTAL_CLASSES - faltas)
    pct = (presencas / SEMESTER_TOTAL_CLASSES) * 100
    return round(pct, 2)

def get_grade_color_tag(media):
    if media is None: return ''
    if media <= 6.9: return 'red'
    if media == 7.0: return 'yellow'
    if media >= 8.0: return 'green'
    return 'default' # 7.1 to 7.9, no specific color requested

def get_freq_color_tag(pct):
    # Regras solicitadas:
    # 75% a 79.9% = Amarelo
    # 80% ou mais = Verde
    # 74% ou menos = Vermelho
    
    # A aprovação é 74.28% (MIN_PASS_FREQUENCY)
    
    if pct < MIN_PASS_FREQUENCY: return 'red' # Abaixo do mínimo (74.28%)
    if MIN_PASS_FREQUENCY <= pct < 80.0: return 'yellow'
    if pct >= 80.0: return 'green'
    return 'default'

def center(win):
    win.update_idletasks()
    w = win.winfo_width(); h = win.winfo_height()
    ws = win.winfo_screenwidth(); hs = win.winfo_screenheight()
    x = (ws // 2) - (w // 2); y = (hs // 2) - (h // 2)
    win.geometry(f"+{x}+{y}")

class SimpleHTMLtoText(HTMLParser):
    """Converts a simplified HTML/Markdown-like output to plain text with formatting."""
    def __init__(self):
        super().__init__()
        self.output = []
        self.tag_stack = []
        self.bold_active = False

    def handle_data(self, data):
        data = data.strip()
        if data:
            if self.bold_active:
                self.output.append(f'**{data}**')
            else:
                self.output.append(data)

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        if tag == 'h2': self.output.append("\n\n" + "="*40 + "\n")
        elif tag == 'h3': self.output.append("\n" + "-"*20 + "\n")
        elif tag == 'p' or tag == 'li': self.output.append("\n")
        elif tag == 'b': self.bold_active = True
        elif tag == 'br': self.output.append("\n")

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        if tag == 'h2': self.output.append("\n" + "="*40 + "\n")
        elif tag == 'h3': self.output.append("\n" + "-"*20 + "\n")
        elif tag == 'li': self.output.append("") # Items in list
        elif tag == 'p': self.output.append("\n")
        elif tag == 'b': self.bold_active = False
        
    def get_text(self):
        # Join and clean up extra spaces/newlines, but preserve structure
        text = "".join(self.output)
        text = re.sub(r'(\n{2,})', r'\n\n', text) # Consolidate multiple newlines
        text = text.strip()
        return text

class App:
    def __init__(self, root):
        self.root = root
        root.title("UNIP - Sistema Acadêmico")
        root.configure(bg=MAIN_BG)
        header = tk.Frame(root, bg=MAIN_BG); header.pack(fill='x', pady=8)
        logo = tk.Canvas(header, width=220, height=64, bg=MAIN_BG, highlightthickness=0); logo.pack()
        logo.create_rectangle(10,10,210,54, fill=UNIP_YELLOW, outline=UNIP_YELLOW)
        logo.create_text(110,32, text="UNIP", font=("Arial",24,"bold"), fill="#002040")
        tk.Label(header, text="Sistema Acadêmico Colaborativo", bg=MAIN_BG, fg=UNIP_YELLOW, font=("Arial",12)).pack()
        tk.Label(header, text="Curso: Análise e Desenvolvimento (Noturno) - Campus Anchieta - 2º Semestre", bg=MAIN_BG, fg="#CCCCCC", font=("Arial",9)).pack()

        btn_frame = tk.Frame(root, bg=MAIN_BG); btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="ALUNO", width=30, height=2, bg=BTN_BG, fg=BTN_FG, command=self.open_aluno_login).pack(pady=6)
        tk.Button(btn_frame, text="PROFESSOR", width=30, height=2, bg=BTN_BG, fg=BTN_FG, command=self.open_prof_login).pack(pady=6)
        tk.Button(btn_frame, text="COORDENADOR", width=30, height=2, bg=BTN_BG, fg=BTN_FG, command=self.open_coord_login).pack(pady=6)
        tk.Label(root, text="Credenciais iniciais: alunos/profs = primeiroNome@unip.edu.br / 12345 | coord = coordenadorads@unip.edu.br / 1234567", bg=MAIN_BG, fg="#CCCCCC", font=("Arial",8)).pack(side='bottom', pady=6)
        self.current_user = None

    def logout(self):
        """Reseta o usuário atual e fecha todas as janelas secundárias."""
        self.current_user = None
        for win in self.root.winfo_children():
            if isinstance(win, tk.Toplevel):
                win.destroy()
        
    def open_aluno_login(self):
        win = tk.Toplevel(self.root); win.title("Login - Aluno"); win.configure(bg=MAIN_BG)
        card = tk.Frame(win, bg=INNER_BG, padx=20, pady=20); card.pack(padx=24, pady=24)
        tk.Label(card, text="LOGIN - ALUNO", font=FONT_LABEL, bg=INNER_BG).pack(pady=(2,8))
        _, e_ra = framed_label_entry(card, "RA (7 dígitos)", width=30, center_label=True); _.pack(pady=6)
        _, e_senha = framed_label_entry(card, "SENHA (5 dígitos)", width=30, center_label=True); _.pack(pady=6)
        btn_frame = tk.Frame(card, bg=INNER_BG); btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Entrar", bg=BTN_BG, fg=BTN_FG, width=12, command=lambda: self.login_aluno(e_ra.get().strip(), e_senha.get().strip(), win)).pack(side='left', padx=6)
        tk.Button(btn_frame, text="Cadastrar", bg="#4CAF50", fg='white', width=12, command=lambda: [win.destroy(), self.open_aluno_cadastro()]).pack(side='left', padx=6)
        center(win)

    def login_aluno(self, ra, senha, win):
        if not ra or not senha:
            messagebox.showerror("Erro", "Preencha RA e senha."); return
        conn = connect_db(); c = conn.cursor(); c.execute("SELECT * FROM alunos WHERE ra=? AND senha=?", (ra, senha)); r = c.fetchone(); conn.close()
        if r:
            self.current_user = {"type":"aluno", "id": r["id"], "email": r["email"], "nome": r["nome"]}
            win.destroy(); self.open_aluno_dashboard() # Chama o novo dashboard
        else:
            messagebox.showerror("Erro", "RA ou senha inválidos.")

    def open_prof_login(self):
        win = tk.Toplevel(self.root); win.title("Login - Professor"); win.configure(bg=MAIN_BG)
        card = tk.Frame(win, bg=INNER_BG, padx=20, pady=20); card.pack(padx=24, pady=24)
        tk.Label(card, text="LOGIN - PROFESSOR", font=FONT_LABEL, bg=INNER_BG).pack(pady=(2,8))
        _, e_email = framed_label_entry(card, "E-MAIL INSTITUCIONAL (@unip.edu.br)", width=40, center_label=True); _.pack(pady=6)
        _, e_senha = framed_label_entry(card, "SENHA (5 dígitos)", width=30, center_label=True); _.pack(pady=6)
        btn_frame = tk.Frame(card, bg=INNER_BG); btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Entrar", bg=BTN_BG, fg=BTN_FG, width=12, command=lambda: self.login_prof(e_email.get().strip(), e_senha.get().strip(), win)).pack(side='left', padx=6)
        tk.Button(btn_frame, text="Cadastrar", bg="#4CAF50", fg='white', width=12, command=lambda: [win.destroy(), self.open_prof_cadastro()]).pack(side='left', padx=6)
        center(win)

    def login_prof(self, email, senha, win):
        if not email or not senha:
            messagebox.showerror("Erro", "Preencha e-mail e senha."); return
        conn = connect_db(); c = conn.cursor(); c.execute("SELECT * FROM professores WHERE email=? AND senha=?", (email, senha)); r = c.fetchone(); conn.close()
        if r:
            self.current_user = {"type":"professor", "id": r["id"], "email": r["email"], "nome": r["nome"], "disciplina": r["disciplina"]}
            win.destroy(); self.open_prof_dashboard()
        else:
            messagebox.showerror("Erro", "E-mail ou senha inválidos.")

    def open_coord_login(self):
        win = tk.Toplevel(self.root); win.title("Login - Coordenador"); win.configure(bg=MAIN_BG)
        card = tk.Frame(win, bg=INNER_BG, padx=20, pady=20); card.pack(padx=24, pady=24)
        tk.Label(card, text="LOGIN - COORDENADOR", font=FONT_LABEL, bg=INNER_BG).pack(pady=(2,8))
        _, e_email = framed_label_entry(card, "E-MAIL DO COORDENADOR", width=40, center_label=True); _.pack(pady=6)
        e_email.insert(0, COORD_EMAIL)
        _, e_senha = framed_label_entry(card, "SENHA", width=30, center_label=True); _.pack(pady=6)
        tk.Button(card, text="Entrar", bg=BTN_BG, fg=BTN_FG, width=12, command=lambda: self.login_coord(e_email.get().strip(), e_senha.get().strip(), win)).pack(pady=8)
        center(win)

    def login_coord(self, email, senha, win):
        if email == COORD_EMAIL and senha == COORD_PASS:
            self.current_user = {"type":"coordenador", "email": email}
            win.destroy(); self.open_coord_dashboard()
        else:
            messagebox.showerror("Erro", "Credenciais do coordenador incorretas.")

    def open_aluno_cadastro(self):
        win = tk.Toplevel(self.root); win.title("Cadastro - Aluno"); win.configure(bg=MAIN_BG)
        card = tk.Frame(win, bg=INNER_BG, padx=18, pady=18); card.pack(padx=24, pady=24)
        tk.Label(card, text="CADASTRO DE ALUNO", font=FONT_LABEL, bg=INNER_BG).pack(pady=(2,8))
        form = tk.Frame(card, bg=INNER_BG); form.pack(pady=6)
        tk.Label(form, text="NOME COMPLETO", font=FONT_LABEL, bg=INNER_BG).grid(row=0, column=0, pady=(6,2))
        e_nome = tk.Entry(form, width=50); e_nome.grid(row=1, column=0, pady=(0,8))
        tk.Label(form, text="DATA DE NASCIMENTO (DD/MM/AAAA)", font=FONT_LABEL, bg=INNER_BG).grid(row=2, column=0, pady=(6,2))
        e_data = tk.Entry(form, width=20); e_data.grid(row=3, column=0, pady=(0,8))
        tk.Label(form, text="RA (7 dígitos)", font=FONT_LABEL, bg=INNER_BG).grid(row=4, column=0, pady=(6,2))
        e_ra = tk.Entry(form, width=20); e_ra.grid(row=5, column=0, pady=(0,8))
        tk.Label(form, text="E-MAIL INSTITUCIONAL (@unip.edu.br)", font=FONT_LABEL, bg=INNER_BG).grid(row=6, column=0, pady=(6,2))
        e_email = tk.Entry(form, width=50); e_email.grid(row=7, column=0, pady=(0,8))
        tk.Label(form, text="SENHA (5 dígitos)", font=FONT_LABEL, bg=INNER_BG).grid(row=8, column=0, pady=(6,2))
        e_senha = tk.Entry(form, width=20, show="*"); e_senha.grid(row=9, column=0, pady=(0,8))
        def on_date_key(event):
            s = "".join(ch for ch in e_data.get() if ch.isdigit())
            if len(s) > 8: s = s[:8]
            out = ""
            if len(s) >= 2:
                out += s[:2]
                if len(s) >= 4:
                    out += "/" + s[2:4]
                    if len(s) > 4:
                        out += "/" + s[4:8]
                    else:
                        out += "/" + s[2:]
            else:
                out = s
            e_data.delete(0, 'end'); e_data.insert(0, out)
        e_data.bind("<KeyRelease>", on_date_key)
        
        def salvar():
            nome = e_nome.get().strip(); data = e_data.get().strip(); ra = e_ra.get().strip(); email = e_email.get().strip(); senha = e_senha.get().strip()
            if not nome or not data or not ra or not email or not senha:
                messagebox.showerror("Erro", "Preencha todos os campos."); return
            if not validar_ra(ra):
                messagebox.showerror("Erro", "RA inválido. Deve conter 7 caracteres alfanuméricos."); return
            if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
                messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA."); return
            if not validar_email_unip(email):
                messagebox.showerror("Erro", "E-mail deve terminar com @unip.edu.br"); return
            if not validar_senha5(senha):
                messagebox.showerror("Erro", "Senha deve ter 5 dígitos numéricos."); return
            conn = connect_db(); c = conn.cursor()
            try:
                c.execute("INSERT INTO alunos (nome, data_nasc, ra, senha, email) VALUES (?, ?, ?, ?, ?)", (nome, data, ra, senha, email))
                aid = c.lastrowid
                c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (email, senha, "aluno"))
                
                # Matriculate in all universal disciplines
                for dname in UNIVERSAL_DISCIPLINES:
                    c.execute("SELECT id FROM disciplinas WHERE nome=?", (dname,))
                    dr = c.fetchone()
                    if dr:
                        did = dr["id"]
                        c.execute("INSERT OR IGNORE INTO matriculas (aluno_id, disciplina_id) VALUES (?, ?)", (aid, did))
                        c.execute("INSERT OR IGNORE INTO notas (aluno_id, disciplina_id, np1, np2, sub) VALUES (?, ?, ?, ?, ?)", (aid, did, None, None, None))
                        c.execute("INSERT OR IGNORE INTO frequencia (aluno_id, disciplina_id, presencas, faltas) VALUES (?, ?, ?, ?)", (aid, did, 0, 0))
                
                # Seed financial data for the current year
                MONTHS = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
                CURRENT_YEAR = datetime.date.today().year
                for month in MONTHS:
                    c.execute("INSERT OR IGNORE INTO financeiro (aluno_id, mes, ano, valor, status) VALUES (?, ?, ?, ?, ?)", 
                            (aid, month, CURRENT_YEAR, FINANCIAL_MONTHLY_FEE, "PENDENTE"))
                            
                conn.commit(); conn.close(); db_watcher.bump();
                messagebox.showinfo("Sucesso", "Aluno cadastrado. Use seu RA e senha para login."); win.destroy()
            except sqlite3.IntegrityError as e:
                conn.close(); messagebox.showerror("Erro", f"RA ou E-mail já cadastrado. ({e})")
        tk.Button(card, text="Salvar", bg="#4CAF50", fg='white', width=16, command=salvar).pack(pady=8)
        center(win)

    def open_prof_cadastro(self):
        win = tk.Toplevel(self.root); win.title("Cadastro - Professor"); win.configure(bg=MAIN_BG)
        card = tk.Frame(win, bg=INNER_BG, padx=18, pady=18); card.pack(padx=24, pady=24)
        tk.Label(card, text="CADASTRO DE PROFESSOR", font=FONT_LABEL, bg=INNER_BG).pack(pady=(2,8))
        form = tk.Frame(card, bg=INNER_BG); form.pack(pady=6)
        tk.Label(form, text="NOME COMPLETO", font=FONT_LABEL, bg=INNER_BG).grid(row=0, column=0, pady=(6,2))
        e_nome = tk.Entry(form, width=50); e_nome.grid(row=1, column=0, pady=(0,8))
        tk.Label(form, text="E-MAIL INSTITUCIONAL (@unip.edu.br)", font=FONT_LABEL, bg=INNER_BG).grid(row=2, column=0, pady=(6,2))
        e_email = tk.Entry(form, width=50); e_email.grid(row=3, column=0, pady=(0,8))
        tk.Label(form, text="SENHA (5 dígitos)", font=FONT_LABEL, bg=INNER_BG).grid(row=4, column=0, pady=(6,2))
        e_senha = tk.Entry(form, width=20, show="*"); e_senha.grid(row=5, column=0, pady=(0,8))
        tk.Label(form, text="DISCIPLINA PRINCIPAL", font=FONT_LABEL, bg=INNER_BG).grid(row=6, column=0, pady=(6,2))
        cb = ttk.Combobox(form, values=UNIVERSAL_DISCIPLINES, state='readonly', width=47); cb.grid(row=7, column=0, pady=(0,8))
        if UNIVERSAL_DISCIPLINES: cb.current(0)
        def salvar():
            nome = e_nome.get().strip(); email = e_email.get().strip(); senha = e_senha.get().strip(); disc = cb.get().strip()
            if not nome or not email or not senha or not disc:
                messagebox.showerror("Erro", "Preencha todos os campos."); return
            if not validar_email_unip(email):
                messagebox.showerror("Erro", "E-mail deve terminar com @unip.edu.br"); return
            if not validar_senha5(senha):
                messagebox.showerror("Erro", "Senha deve ter 5 dígitos numéricos."); return
            conn = connect_db(); c = conn.cursor()
            try:
                c.execute("INSERT INTO professores (nome, email, senha, disciplina) VALUES (?, ?, ?, ?)", (nome, email, senha, disc))
                c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", (email, senha, "professor"))
                conn.commit(); conn.close(); db_watcher.bump(); messagebox.showinfo("Sucesso", "Professor cadastrado."); win.destroy()
            except sqlite3.IntegrityError as e:
                conn.close(); messagebox.showerror("Erro", f"E-mail já cadastrado. ({e})")
        tk.Button(card, text="Salvar", bg="#4CAF50", fg='white', width=16, command=salvar).pack(pady=8)
        center(win)

    def open_aluno_dashboard(self):
        """Novo Dashboard Inicial do Aluno com 4 botões."""
        if not self.current_user or self.current_user.get("type") != "aluno":
            messagebox.showerror("Erro", "Aluno não autenticado."); return
        
        aid = self.current_user["id"]; anome = self.current_user["nome"]
        win = tk.Toplevel(self.root); win.title(f"Aluno - Dashboard - {anome}"); win.geometry("600x400"); win.configure(bg=MAIN_BG)
        
        tk.Label(win, text=f"Bem-vindo(a), {anome}", bg=MAIN_BG, fg=UNIP_YELLOW, font=("Arial",16,"bold")).pack(pady=10)
        
        btn_frame = tk.Frame(win, bg=MAIN_BG, pady=10); btn_frame.pack(pady=10)
        
        # 1. Acessar Área do Aluno (Antigo open_aluno_dashboard)
        tk.Button(btn_frame, text="Acessar Área do Aluno", width=30, height=2, bg=BTN_BG, fg=BTN_FG, 
                  command=lambda: [win.destroy(), self.open_aluno_area_academica()]).pack(pady=6)
                  
        # 2. Configurações
        tk.Button(btn_frame, text="Configurações", width=30, height=2, bg=BTN_BG, fg=BTN_FG, 
                  command=self.open_aluno_configuracoes).pack(pady=6)
                  
        # 3. Acessar Financeiro
        tk.Button(btn_frame, text="Acessar Financeiro", width=30, height=2, bg=BTN_BG, fg=BTN_FG, 
                  command=self.open_aluno_financeiro).pack(pady=6)
                  
        # 4. Log Out
        tk.Button(win, text="Log Out", width=15, bg="#B00020", fg='white', 
                  command=lambda: [win.destroy(), self.logout()]).pack(side='bottom', pady=20)
                  
        center(win)

    def open_aluno_configuracoes(self):
        """Tela de Configurações do Aluno: Alterar Senha e Consultar Senha."""
        if not self.current_user or self.current_user.get("type") != "aluno": return
        aid = self.current_user["id"]; anome = self.current_user["nome"]
        
        win = tk.Toplevel(self.root); win.title(f"Aluno - Configurações - {anome}"); win.configure(bg=MAIN_BG)
        card = tk.Frame(win, bg=INNER_BG, padx=20, pady=20); card.pack(padx=24, pady=24)
        
        tk.Label(card, text="CONFIGURAÇÕES DA CONTA", font=FONT_LABEL, bg=INNER_BG).pack(pady=(2,8))

        # --- Alterar Senha ---
        tk.Label(card, text="ALTERAR SENHA (5 DÍGITOS)", font=FONT_LABEL, bg=INNER_BG).pack(pady=(10,2))
        _, e_nova_senha = framed_label_entry(card, "Nova Senha", width=30, center_label=True, show="*"); 
        _.pack(pady=6)

        def alterar_senha():
            nova_senha = e_nova_senha.get().strip()
            if not validar_senha5(nova_senha):
                messagebox.showerror("Erro", "Senha deve ter 5 dígitos numéricos.")
                return
            
            conn = connect_db(); c = conn.cursor()
            try:
                c.execute("UPDATE alunos SET senha=? WHERE id=?", (nova_senha, aid))
                c.execute("UPDATE usuarios SET senha=? WHERE usuario=?", (nova_senha, self.current_user["email"]))
                conn.commit(); conn.close(); db_watcher.bump()
                messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
                e_nova_senha.delete(0, tk.END)
            except Exception as e:
                conn.close(); messagebox.showerror("Erro", f"Erro ao alterar senha: {e}")

        tk.Button(card, text="Alterar Senha", bg=BTN_BG, fg=BTN_FG, width=16, command=alterar_senha).pack(pady=8)

        # --- Consultar Senha ---
        def consultar_senha():
            conn = connect_db(); c = conn.cursor()
            c.execute("SELECT senha FROM alunos WHERE id=?", (aid,)); r = c.fetchone(); conn.close()
            
            if r:
                messagebox.showinfo("Sua Senha Atual", f"Sua senha atual é: {r['senha']}")
            else:
                messagebox.showerror("Erro", "Aluno não encontrado.")

        tk.Button(card, text="Consultar Senha", bg="#FF9800", fg='white', width=16, command=consultar_senha).pack(pady=12)
        
        center(win)

    def open_aluno_financeiro(self):
        """Tela de Acesso Financeiro do Aluno."""
        if not self.current_user or self.current_user.get("type") != "aluno": return
        aid = self.current_user["id"]; anome = self.current_user["nome"]
        
        win = tk.Toplevel(self.root); win.title(f"Aluno - Financeiro - {anome}"); win.geometry("700x500"); win.configure(bg=MAIN_BG)
        
        tk.Label(win, text="SITUAÇÃO FINANCEIRA", bg=MAIN_BG, fg=UNIP_YELLOW, font=("Arial",16,"bold")).pack(pady=10)
        
        nb = ttk.Notebook(win); nb.pack(expand=True, fill='both', padx=10, pady=10)
        
        # 1º Semestre (Jan-Jul)
        t_semestre1 = tk.Frame(nb, bg=INNER_BG); nb.add(t_semestre1, text='1º Semestre (Jan-Jul)')
        # 2º Semestre (Ago-Dez)
        t_semestre2 = tk.Frame(nb, bg=INNER_BG); nb.add(t_semestre2, text='2º Semestre (Ago-Dez)')
        
        def setup_finance_tree(parent_frame):
            tree = ttk.Treeview(parent_frame, columns=("mes", "valor", "status", "forma", "data_hora"), show='headings')
            tree.heading("mes", text="Mês"); tree.column("mes", width=100, anchor='center')
            tree.heading("valor", text="Valor"); tree.column("valor", width=100, anchor='center')
            tree.heading("status", text="Status"); tree.column("status", width=150, anchor='center')
            tree.heading("forma", text="Forma Pgto"); tree.column("forma", width=100, anchor='center')
            tree.heading("data_hora", text="Data/Hora Pgto"); tree.column("data_hora", width=150, anchor='center')
            
            tree.tag_configure('paid', foreground=FINANCE_COLOR_PAID_OK)
            tree.tag_configure('pending', foreground=FINANCE_COLOR_PENDING)
            tree.tag_configure('overdue', foreground=FINANCE_COLOR_OVERDUE)
            
            tree.pack(fill='both', expand=True, padx=8, pady=8)
            return tree

        tree1 = setup_finance_tree(t_semestre1)
        tree2 = setup_finance_tree(t_semestre2)
        
        def load_financeiro_data():
            for i in tree1.get_children(): tree1.delete(i)
            for i in tree2.get_children(): tree2.delete(i)
            
            conn = connect_db(); c = conn.cursor()
            c.execute("SELECT * FROM financeiro WHERE aluno_id=? ORDER BY ano, CASE mes WHEN 'JAN' THEN 1 WHEN 'FEV' THEN 2 WHEN 'MAR' THEN 3 WHEN 'ABR' THEN 4 WHEN 'MAI' THEN 5 WHEN 'JUN' THEN 6 WHEN 'JUL' THEN 7 WHEN 'AGO' THEN 8 WHEN 'SET' THEN 9 WHEN 'OUT' THEN 10 WHEN 'NOV' THEN 11 WHEN 'DEZ' THEN 12 END", (aid,))
            rows = c.fetchall(); conn.close()
            
            semestre1_months = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL"]
            
            for r in rows:
                mes = r["mes"]; valor = f"R$ {r['valor']:.2f}"
                status_raw = r["status"]; forma = r["forma_pagamento"] if r["forma_pagamento"] else "-"
                data_pgto = r["data_pagamento"] if r["data_pagamento"] else "-"
                
                tag = 'pending'
                
                if status_raw == 'PAGO': 
                    tag = 'paid'
                    status_display = "Concluído"
                elif status_raw == 'PENDENTE':
                    tag = 'pending'
                    status_display = "Pendente"
                elif status_raw in ('ATRASO', 'PAGO_ATRASO'): 
                    tag = 'overdue' 
                    status_display = "Em Atraso/Não Pagou" if status_raw == 'ATRASO' else "Pago em Atraso"
                
                data_hora_display = "-"
                if data_pgto != "-":
                    try:
                        # Format YYYY-MM-DDTHH:MM:SS.xxxxxx -> DD/MM/YYYY HH:MM:SS
                        dt_obj = datetime.datetime.fromisoformat(data_pgto)
                        data_hora_display = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
                    except ValueError:
                        data_hora_display = data_pgto 
                        
                values = (mes, valor, status_display, forma, data_hora_display)
                
                if mes in semestre1_months:
                    tree1.insert('', 'end', values=values, tags=(tag,))
                else:
                    tree2.insert('', 'end', values=values, tags=(tag,))
        
        load_financeiro_data()
        
        # Poller for finance data
        def poll_financeiro():
            token = db_watcher.value()
            win._last_token = getattr(win, "_last_token", None)
            if win._last_token != token:
                load_financeiro_data()
                win._last_token = token
            win.after(1500, poll_financeiro)
            
        poll_financeiro()
        center(win)

    def open_aluno_area_academica(self): # Refactored from open_aluno_dashboard
        if not self.current_user or self.current_user.get("type") != "aluno": messagebox.showerror("Erro", "Aluno não autenticado."); return
        aid = self.current_user["id"]; anome = self.current_user["nome"]
        conn = connect_db(); c = conn.cursor()
        c.execute("SELECT d.nome FROM disciplinas d JOIN matriculas m ON d.id=m.disciplina_id WHERE m.aluno_id=?", (aid,));
        disciplinas = [r["nome"] for r in c.fetchall()]; conn.close()
        
        win = tk.Toplevel(self.root); win.title(f"Aluno - Área Acadêmica - {anome}"); win.geometry("1100x700"); win.configure(bg=MAIN_BG)
        tk.Label(win, text=f"Área Acadêmica - {anome}", bg=MAIN_BG, fg=UNIP_YELLOW, font=("Arial",16,"bold")).pack(pady=8)
        
        nb = ttk.Notebook(win); nb.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Tabs
        t_disc = tk.Frame(nb, bg=INNER_BG); nb.add(t_disc, text='Disciplinas')
        t_notas = tk.Frame(nb, bg=INNER_BG); nb.add(t_notas, text='Notas')
        t_freq = tk.Frame(nb, bg=INNER_BG); nb.add(t_freq, text='Frequência')
        t_crono = tk.Frame(nb, bg=INNER_BG); nb.add(t_crono, text='Cronograma')
        t_chat = tk.Frame(nb, bg=INNER_BG); nb.add(t_chat, text='Chat')
        t_ia = tk.Frame(nb, bg=INNER_BG); nb.add(t_ia, text='IA de Apoio')
        
        # Notas tab (Treeview)
        tree = ttk.Treeview(t_notas, columns=("disciplina", "np1", "np2", "sub", "media", "situacao"), show='headings', height=18)
        tree.heading("disciplina", text="Disciplina"); tree.column("disciplina", width=300)
        tree.heading("np1", text="NP1"); tree.column("np1", width=80, anchor='center')
        tree.heading("np2", text="NP2"); tree.column("np2", width=80, anchor='center')
        tree.heading("sub", text="SUB"); tree.column("sub", width=80, anchor='center')
        tree.heading("media", text="Média Final"); tree.column("media", width=100, anchor='center')
        tree.heading("situacao", text="Situação"); tree.column("situacao", width=180, anchor='center')
        
        # Configurações de tag de cores (Notas)
        tree.tag_configure('red', foreground=NOTE_COLOR_RED)
        tree.tag_configure('yellow', foreground=NOTE_COLOR_YELLOW)
        tree.tag_configure('green', foreground=NOTE_COLOR_GREEN)
        
        tree.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Frequência tab (Treeview)
        tree_freq = ttk.Treeview(t_freq, columns=("disciplina", "aulas", "presencas", "faltas", "pct", "situacao"), show='headings', height=18)
        tree_freq.heading("disciplina", text="Disciplina"); tree_freq.column("disciplina", width=300)
        tree_freq.heading("aulas", text="Aulas Totais"); tree_freq.column("aulas", width=100, anchor='center')
        tree_freq.heading("presencas", text="Presenças"); tree_freq.column("presencas", width=100, anchor='center')
        tree_freq.heading("faltas", text="Faltas"); tree_freq.column("faltas", width=80, anchor='center')
        tree_freq.heading("pct", text="% Freq."); tree_freq.column("pct", width=80, anchor='center')
        tree_freq.heading("situacao", text="Situação"); tree_freq.column("situacao", width=180, anchor='center')
        
        # Configurações de tag de cores (Frequência)
        tree_freq.tag_configure('red', foreground=FREQ_COLOR_RED)
        tree_freq.tag_configure('yellow', foreground=FREQ_COLOR_YELLOW)
        tree_freq.tag_configure('green', foreground=FREQ_COLOR_GREEN)
        
        tree_freq.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Disciplinas tab (Canvas for clickable cards)
        canv = tk.Canvas(t_disc, bg=INNER_BG, highlightthickness=0); canv.pack(fill='both', expand=True)
        rect_ids = []
        
        def draw_disciplines(event=None):
            for id in rect_ids: canv.delete(id[0]); canv.delete(id[1])
            rect_ids.clear()
            
            canv_width = canv.winfo_width()
            cols = max(1, canv_width // 280)
            card_width = (canv_width - 24) // cols - 24
            
            max_height = 0
            for i, dname in enumerate(disciplinas):
                row = i // cols
                col = i % cols
                x1 = 12 + col * (card_width + 24)
                y1 = 12 + row * 150
                x2 = x1 + card_width
                y2 = y1 + 120
                
                rect = canv.create_rectangle(x1, y1, x2, y2, fill="#E6C200", outline="#001f3f", width=2)
                text = canv.create_text(x1 + card_width/2, y1 + 60, text=dname, font=("Arial",10,"bold"), fill="#001f3f", width=card_width - 10, justify='center')
                rect_ids.append((rect, text, dname))
                max_height = max(max_height, y2 + 12)
            
            canv.config(scrollregion=(0, 0, canv_width, max_height))
        
        canv.bind("<Configure>", draw_disciplines)
        
        def on_canvas_click(event):
            x, y = event.x, event.y
            for rect, text, dname in rect_ids:
                coords = canv.coords(rect)
                if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                    # NEW FUNCTIONALITY: Go to 'Notas' tab and select the discipline
                    nb.select(t_notas) # Select the Notas tab
                    # Find the item in the treeview that matches dname
                    found_item = None
                    for iid in tree.get_children():
                        if tree.item(iid)['values'][0] == dname:
                            found_item = iid
                            break
                    if found_item:
                        tree.selection_set(found_item) # Select the item
                        tree.focus(found_item) # Focus the item
                        tree.see(found_item) # Ensure it's visible
                    break
        canv.bind("<Button-1>", on_canvas_click)
        
        # Disciplinas tab: only universal disciplines (cards)
        frd = tk.Frame(t_disc, bg=INNER_BG); frd.pack(fill='both', expand=True, padx=12, pady=12)
        for i, dn in enumerate(UNIVERSAL_DISCIPLINES):
            card = tk.Frame(frd, bg="#E6C200", width=220, height=120)
            card.grid(row=i//2, column=i%2, padx=12, pady=12)
            tk.Label(card, text=dn, bg="#E6C200", fg="#001f3f", font=("Arial",10,"bold"), wraplength=200).place(relx=0.5, rely=0.5, anchor='center')
            
        # Notas tab
        def load_notas():
            for i in tree.get_children(): tree.delete(i)
            conn = connect_db(); c = conn.cursor()
            c.execute("""SELECT d.nome as disc, n.np1, n.np2, n.sub 
                         FROM notas n JOIN disciplinas d ON n.disciplina_id=d.id 
                         WHERE n.aluno_id=?""", (aid,))
            
            for r in c.fetchall():
                media = calc_media(r["np1"], r["np2"], r["sub"])
                np1 = r["np1"] if r["np1"] is not None else "-"
                np2 = r["np2"] if r["np2"] is not None else "-"
                sub = r["sub"] if r["sub"] is not None else "-"
                
                situacao = "Em Aberto"
                tag = ''
                if media is not None:
                    tag = get_grade_color_tag(media)
                    if media >= MIN_PASS_GRADE:
                        situacao = "Aprovado"
                    elif media >= 3.0:
                        situacao = "Em Exame"
                    else:
                        situacao = "Reprovado por Nota"
                        
                iid = tree.insert('', 'end', values=(r["disc"], np1, np2, sub, media if media is not None else "-", situacao))
                if tag: tree.item(iid, tags=(tag,))

        # Frequência tab
        def load_frequencia():
            for i in tree_freq.get_children(): tree_freq.delete(i)
            conn = connect_db(); c = conn.cursor()
            c.execute("""SELECT d.nome as disc, f.presencas, f.faltas
                         FROM frequencia f JOIN disciplinas d ON f.disciplina_id=d.id 
                         WHERE f.aluno_id=?""", (aid,))
            
            for r in c.fetchall():
                pct = calc_freq_percent(r["faltas"])
                tag = get_freq_color_tag(pct)
                situacao = "Aprovado"
                if pct < MIN_PASS_FREQUENCY:
                    situacao = "Reprovado por Falta"
                
                iid = tree_freq.insert('', 'end', values=(r["disc"], SEMESTER_TOTAL_CLASSES, r["presencas"], r["faltas"], f"{pct}%", situacao))
                if tag: tree_freq.item(iid, tags=(tag,))
                
        # Cronograma tab: show all modules for all disciplines the student is matriculated in
        fr_crono = tk.Frame(t_crono, bg=INNER_BG); fr_crono.pack(fill='both', expand=True, padx=8, pady=8)
        
        def load_cronograma():
            for w in fr_crono.winfo_children(): w.destroy()
            
            conn = connect_db(); c = conn.cursor()
            c.execute("""SELECT c.modulo_index, c.titulo, c.subtemas, c.marcado, d.nome as disc 
                         FROM cronogramas c 
                         JOIN disciplinas d ON c.disciplina_id=d.id
                         JOIN matriculas m ON d.id=m.disciplina_id
                         WHERE m.aluno_id=? 
                         ORDER BY d.nome, c.modulo_index""", (aid,))
            
            current_disc = None
            for r in c.fetchall():
                if r["disc"] != current_disc:
                    current_disc = r["disc"]
                    tk.Label(fr_crono, text=f"\n--- {current_disc} ---", font=("Arial", 12, "bold"), bg=INNER_BG, fg=BTN_BG).pack(fill='x', pady=(10, 5))

                subtemas = r["subtemas"].replace(';', ', ') if r["subtemas"] else ""
                
                status_text = "Concluído" if r["marcado"] else "Pendente"
                status_fg = '#007E33' if r["marcado"] else '#B00020'
                
                frame = tk.Frame(fr_crono, bg='#E0E0E0', padx=10, pady=5); frame.pack(fill='x', pady=2, padx=10)
                tk.Label(frame, text=f"Módulo {r['modulo_index']}: {r['titulo']}", font=("Arial", 10, "bold"), bg='#E0E0E0').pack(anchor='w')
                tk.Label(frame, text=f"Tópicos: {subtemas}", bg='#E0E0E0').pack(anchor='w')
                tk.Label(frame, text=f"Status: {status_text}", bg='#E0E0E0', fg=status_fg).pack(anchor='w')


        # Chat tab (The simple chat from the original code - kept for structure)
        frame_chat = tk.Frame(t_chat, bg=INNER_BG); frame_chat.pack(expand=True, fill='both', padx=12, pady=12)
        tk.Label(frame_chat, text="CHAT (Mensagens)", font=FONT_LABEL, bg=INNER_BG).pack(pady=5)
        self.aluno_chat_text = tk.Text(frame_chat, wrap='word', bg='white', font=("Arial", 10), state='disabled');
        self.aluno_chat_text.pack(fill='both', expand=True)
        tk.Label(frame_chat, text="Funcionalidade em desenvolvimento...", bg=INNER_BG).pack()

        # IA tab (New Interactive Chat)
        frame_ia = tk.Frame(t_ia, bg=INNER_BG); frame_ia.pack(expand=True, fill='both', padx=12, pady=12)
        
        # Chat area (for displaying history/messages)
        ia_chat_card = tk.Frame(frame_ia, bg="#A9D0F5", pady=10, padx=10); 
        ia_chat_card.pack(fill='both', expand=True, pady=8)
        
        self.aluno_ia_chat_text = tk.Text(ia_chat_card, wrap='word', bg='#F0F8FF', font=("Arial", 10), state='disabled')
        self.aluno_ia_chat_text.pack(fill='both', expand=True)
        
        # User input area
        ia_input_frame = tk.Frame(frame_ia, bg=INNER_BG); ia_input_frame.pack(fill='x', pady=6)
        e_ia_input = tk.Entry(ia_input_frame, width=70); e_ia_input.pack(side='left', padx=5, fill='x', expand=True)

        # Combo box for discipline selection (still needed for analysis options)
        ia_disciplinas = ["TODAS AS DISCIPLINAS"] + UNIVERSAL_DISCIPLINES
        cb_ia_disc = ttk.Combobox(ia_input_frame, values=ia_disciplinas, state='readonly', width=20); 
        cb_ia_disc.pack(side='left', padx=5)
        cb_ia_disc.current(0)
        
        # New Chat/Analysis Button 
        def process_ia_input():
            user_input = e_ia_input.get().strip()
            disc_selected = cb_ia_disc.get()
            e_ia_input.delete(0, tk.END)
            self.ia_handle_chat_input(aid, anome, user_input, disc_selected) # New handler
            
        btn_ia_chat = tk.Button(ia_input_frame, text="INICIAR CHAT / ENVIAR", bg="#FF9800", fg='white', font=("Arial",10,"bold"), command=process_ia_input)
        btn_ia_chat.pack(side='left', padx=10)
        e_ia_input.bind('<Return>', lambda event: process_ia_input())
        
        # Initial greeting/options
        self.ia_handle_chat_input(aid, anome, "", "INICIAL")

        # Polling
        def poll_aluno():
            load_notas(); load_frequencia(); load_cronograma(); # load_chat()
            
        load_notas(); load_frequencia(); load_cronograma()
        win._last_token = None
        def poll_db():
            token = db_watcher.value()
            if win._last_token != token:
                poll_aluno()
                win._last_token = token
            win.after(1500, poll_db)
        poll_db()
        center(win)

    def _ia_append_message(self, sender, message, append_type='normal'):
        """Helper para adicionar mensagens ao chat IA."""
        text_widget = self.aluno_ia_chat_text
        text_widget.configure(state='normal')
        
        if not hasattr(text_widget, '_tags_configured'):
            text_widget.tag_configure('ia', foreground='#00509e')
            text_widget.tag_configure('user', foreground='#000000', font=("Arial", 10, "italic"))
            text_widget._tags_configured = True
            
        if sender == "IA":
            tag = 'ia'
            # Format message from HTML/Markdown-like to plain text
            parser = SimpleHTMLtoText(); parser.feed(message); message_text = parser.get_text()
            
            # Save history only for actual responses, not menu prompts
            if append_type not in ('menu', 'prompt'):
                conn = connect_db(); c = conn.cursor()
                aluno_id = self.current_user["id"]
                c.execute("INSERT INTO ia_historico (aluno_id, data, resumo) VALUES (?, ?, ?)", 
                          (aluno_id, datetime.datetime.now().isoformat(), message_text));
                conn.commit(); conn.close(); db_watcher.bump()
            
            display_message = message # Display formatted HTML/Markdown for IA
        else:
            tag = 'user'
            display_message = message
            
        text_widget.insert(tk.END, f"[{sender}]: {display_message}\n\n", tag)
        text_widget.see(tk.END)
        text_widget.configure(state='disabled')

    def ia_handle_chat_input(self, aid, anome, user_input, disc_selected):
        """Novo handler para o chat interativo da IA."""
        
        # Initial greeting/menu
        if user_input == "" and disc_selected == "INICIAL":
            greeting = f"Bem-vindo(a), **{anome}**! Sou a IA de Apoio Acadêmico. Posso te ajudar com análises e dúvidas. Como posso começar?"
            options_text = """
<p>Digite o número da opção desejada:</p>
<p><b>[1] Gerar Análise de Notas</b> (Análise de notas, média, e necessidade de SUB/Exame)</p>
<p><b>[2] Gerar Análise de Faltas</b> (Análise de frequência e risco de reprovação)</p>
<p><b>[3] Gerar Análise Geral</b> (Combinação de notas e faltas)</p>
<p><b>[4] Tirar Dúvidas com a IA</b> (Modo Interativo)</p>
<p>Ou digite 'sair' para encerrar.</p>
"""
            self._ia_append_message("IA", greeting, 'prompt')
            self._ia_append_message("IA", options_text, 'menu')
            self.aluno_ia_chat_text._chat_state = 'MENU'
            return

        if user_input:
            self._ia_append_message(anome, user_input, 'user')
        
        # State machine/main menu
        
        current_state = getattr(self.aluno_ia_chat_text, '_chat_state', 'MENU')

        if user_input.lower() == 'sair':
            self._ia_append_message("IA", "Até a próxima! Lembre-se, estou sempre aqui para ajudar com seus estudos.", 'prompt')
            self.aluno_ia_chat_text._chat_state = 'CLOSED'
            return

        if current_state == 'MENU':
            if user_input == '1':
                self.ia_generate_aluno_refactored(aid, anome, disc_selected, 'nota')
            elif user_input == '2':
                self.ia_generate_aluno_refactored(aid, anome, disc_selected, 'falta')
            elif user_input == '3':
                self.ia_generate_aluno_refactored(aid, anome, disc_selected, 'geral')
            elif user_input == '4':
                self._ia_append_message("IA", "Ótimo! Para qual tipo de dúvida você precisa de apoio?", 'prompt')
                self.aluno_ia_chat_text._chat_state = 'DUVIDAS'
                options_text = """
<p>Digite o número:</p>
<p><b>[1] Dúvida de Notas</b> (Quanto preciso para passar?)</p>
<p><b>[2] Dúvida de Frequência</b> (Quantas faltas posso ter?)</p>
<p><b>[3] Apoio para mexer no sistema</b> (Ajuda com as telas do sistema)</p>
<p>Ou digite 'menu' para voltar ao menu principal.</p>
"""
                self._ia_append_message("IA", options_text, 'menu')
            else:
                self._ia_append_message("IA", "Opção inválida. Por favor, digite 1, 2, 3, 4, ou 'sair'.", 'prompt')
                
        elif current_state == 'DUVIDAS':
            if user_input == '1':
                self.ia_handle_duvida_notas(aid, anome, disc_selected)
                self.aluno_ia_chat_text._chat_state = 'MENU' # Return to main menu after answering
            elif user_input == '2':
                self._ia_append_message("IA", self._ia_analise_faltas_message(aid, disc_selected), 'analysis')
                self.aluno_ia_chat_text._chat_state = 'MENU'
            elif user_input == '3':
                self._ia_append_message("IA", "Posso te guiar sobre as funções básicas do sistema: Notas, Frequência, Cronograma, Chat, e Financeiro. Se precisar de uma análise mais profunda, volte ao Menu Principal e use as opções 1, 2 ou 3.", 'prompt')
                self.aluno_ia_chat_text._chat_state = 'MENU'
            elif user_input.lower() == 'menu':
                self.ia_handle_chat_input(aid, anome, "", "INICIAL")
            else:
                self._ia_append_message("IA", "Opção de Dúvida inválida. Por favor, digite 1, 2 ou 3. Ou digite 'menu' para voltar ao menu principal.", 'prompt')

        else: # Default/Closed state
            self.ia_handle_chat_input(aid, anome, "", "INICIAL")

    def ia_handle_duvida_notas(self, aluno_id, aluno_nome, selected_discipline):
        """Calcula notas necessárias e necessidade de Exame."""
        if selected_discipline == "TODAS AS DISCIPLINAS":
            self._ia_append_message("IA", "Por favor, selecione uma **Disciplina Específica** na caixa de seleção para a Análise de Notas.", 'prompt')
            return
            
        conn = connect_db(); c = conn.cursor()
        c.execute("SELECT id FROM disciplinas WHERE nome=?", (selected_discipline,))
        drow = c.fetchone()
        if not drow: conn.close(); self._ia_append_message("IA", "Disciplina não encontrada.", 'prompt'); return
        did = drow["id"]
        
        c.execute("""SELECT n.np1, n.np2, n.sub
                     FROM notas n 
                     WHERE n.aluno_id=? AND n.disciplina_id=?""", (aluno_id, did))
        row = c.fetchone(); conn.close()
        
        if not row: 
            self._ia_append_message("IA", f"Notas (NP1/NP2) não registradas ainda para **{selected_discipline}**.", 'prompt')
            return
            
        np1 = row["np1"] if row["np1"] is not None else None
        np2 = row["np2"] if row["np2"] is not None else None
        
        msg = f"<h3>Análise de Notas para {selected_discipline}</h3>"
        
        # Case 1: Only NP1 launched (need NP2)
        if np1 is not None and np2 is None:
            # Need 7.0 average: (NP1 + NP2) / 2 = 7.0 => NP2 = 14.0 - NP1
            needed_np2 = round(14.0 - np1, 2)
            
            if needed_np2 <= 10.0 and needed_np2 >= 0:
                msg += f"<p>Você tirou **{np1}** na NP1. Para atingir a média mínima (**7.0**), você precisa de **{needed_np2}** na NP2.</p>"
            else:
                msg += f"<p>Você tirou **{np1}** na NP1. Infelizmente, mesmo tirando nota máxima (10.0) na NP2, você não atingirá a média 7.0 (você precisaria de {needed_np2}). Você precisará focar no **Exame Final**.</p>"
        
        # Case 2: Both NP1 and NP2 launched (or NP1/SUB)
        elif np1 is not None and np2 is not None:
            media = calc_media(np1, np2, row["sub"])
            
            if media is None:
                 msg += "<p>Não foi possível calcular a média com as notas fornecidas.</p>"
            elif media >= MIN_PASS_GRADE:
                msg += f"<p>Parabéns! Sua média atual é **{media}**. Você já foi aprovado(a) por nota em **{selected_discipline}**!</p>"
            elif media >= 3.0: # Check if eligible for Final Exam (3.0 <= media < 7.0)
                # Need 5.0 average after Final Exam: (Media * 2 + EXAME) / 3 = 5.0 => EXAME = 15.0 - (Media * 2)
                needed_exame = round(15.0 - (media * 2), 2)
                
                if needed_exame <= 10.0 and needed_exame >= 0:
                    msg += f"<p>Sua média atual é **{media}**. Você está de **Exame Final**! Para ser aprovado(a) (média final 5.0), você precisa de **{needed_exame}** no Exame.</p>"
                else:
                    msg += f"<p>Sua média atual é **{media}**. Infelizmente, mesmo com a nota máxima (10.0) no Exame Final, você não atingirá a média mínima de aprovação (5.0) (você precisaria de {needed_exame}).</p>"
            else: # media < 3.0
                msg += f"<p>Sua média atual é **{media}**. Infelizmente, você foi reprovado(a) por nota em **{selected_discipline}**.</p>"
                
        else: # Neither NP1 nor NP2
            msg += f"<p>Nenhuma nota (NP1 ou NP2) foi lançada ainda para **{selected_discipline}**. Acompanhe a aba 'Notas'.</p>"
            
        self._ia_append_message("IA", msg, 'analysis')

    def _ia_analise_faltas_message(self, aluno_id, selected_discipline):
        """Helper para responder à Dúvida de Frequência."""
        if selected_discipline == "TODAS AS DISCIPLINAS":
            conn = connect_db(); c = conn.cursor();
            c.execute("SELECT SUM(faltas) as totalfalt FROM frequencia WHERE aluno_id=?", (aluno_id,)); 
            r = c.fetchone(); conn.close()
            total = r["totalfalt"] or 0
            
            return f"""O limite máximo de faltas por disciplina é de **{MAX_ALLOWED_ABSENCES} faltas** ({round(100 - MIN_PASS_FREQUENCY, 1)}% de falta). 
Se você ultrapassar esse limite, será reprovado por frequência, mesmo com nota alta. 
Você tem um total acumulado de **{total} faltas** no semestre em todas as disciplinas. Consulte a aba 'Frequência' para ver o seu status em cada matéria."""
        else:
            conn = connect_db(); c = conn.cursor();
            c.execute("SELECT id FROM disciplinas WHERE nome=?", (selected_discipline,)); drow = c.fetchone()
            if not drow: conn.close(); return "Disciplina não encontrada." 
            did = drow["id"]
            c.execute("SELECT faltas FROM frequencia WHERE aluno_id=? AND disciplina_id=?", (aluno_id, did));
            row = c.fetchone(); conn.close()
            
            if not row: return f"Dados de frequência não registrados para **{selected_discipline}**."
            
            faltas_atuais = row["faltas"]
            faltas_restantes = MAX_ALLOWED_ABSENCES - faltas_atuais
            
            if faltas_restantes < 0:
                 return f"**ALERTA VERMELHO!** Você tem **{faltas_atuais} faltas** (Limite: {MAX_ALLOWED_ABSENCES}). Você está em **risco de reprovação por frequência** em **{selected_discipline}**."
            elif faltas_restantes <= 3:
                return f"**ATENÇÃO!** Você tem **{faltas_atuais} faltas** em **{selected_discipline}**. Restam apenas **{faltas_restantes} faltas** antes de ser reprovado por frequência."
            else:
                return f"Você tem **{faltas_atuais} faltas** em **{selected_discipline}**. Você ainda pode faltar **{faltas_restantes} vezes** sem reprovar por frequência."
                
    def ia_generate_aluno_refactored(self, aid, anome, disc_selected, analysis_type):
        """Wrapper para gerar a análise acadêmica e usar o novo chat display."""
        is_overall_analysis = disc_selected == "TODAS AS DISCIPLINAS"
        is_grade_analysis = analysis_type in ('nota', 'geral')
        is_freq_analysis = analysis_type in ('falta', 'geral')
        
        resumo_html = self._generate_ia_analysis_formatted(aid, disc_selected, is_overall_analysis, is_grade_analysis, is_freq_analysis) 
        
        if not resumo_html:
            self._ia_append_message("IA", f"Nenhum dado encontrado para análise de **{disc_selected}**.", 'analysis')
            return
            
        self._ia_append_message("IA", resumo_html, 'analysis')
        self.aluno_ia_chat_text._chat_state = 'MENU' # Return to menu after analysis

    def _generate_ia_analysis_formatted(self, aluno_id, selected_discipline, is_overall_analysis=False, is_grade_analysis=True, is_freq_analysis=True):
        """
        Gera um resumo formatado (HTML/Markdown simplificado) da performance do aluno.
        Adicionado is_grade_analysis e is_freq_analysis para análises parciais.
        """
        conn = connect_db(); c = conn.cursor()
        
        # 1. Preparação dos dados: Notas
        disciplinas_atencao_nota = []; disciplinas_sub_needed = []; overall_media = None; notas_rows = []
        if is_grade_analysis:
            if is_overall_analysis:
                c.execute("""SELECT d.nome as disc, n.np1, n.np2, n.sub FROM notas n 
                             JOIN disciplinas d ON n.disciplina_id=d.id 
                             JOIN matriculas m ON d.id=m.disciplina_id 
                             WHERE m.aluno_id=?""", (aluno_id,))
                notas_rows = c.fetchall()
            else:
                c.execute("""SELECT d.nome as disc, n.np1, n.np2, n.sub FROM notas n 
                             JOIN disciplinas d ON n.disciplina_id=d.id 
                             WHERE n.aluno_id=? AND d.nome=?""", (aluno_id, selected_discipline))
                notas_rows = c.fetchall()
            
            # Cálculo da média geral para análise geral
            if is_overall_analysis and notas_rows:
                all_medias = [calc_media(r["np1"], r["np2"], r["sub"]) for r in notas_rows if calc_media(r["np1"], r["np2"], r["sub"]) is not None]
                if all_medias: overall_media = round(sum(all_medias) / len(all_medias), 2)
            
            # Coleta de dados por disciplina para atenção/sub
            for r in notas_rows:
                disc = r['disc']
                media = calc_media(r["np1"], r["np2"], r["sub"])
                if media is not None and media < MIN_PASS_GRADE:
                    disciplinas_atencao_nota.append(f"{disc} (média {media})")

                # NEW SUB CALCULATION
                np1 = r["np1"] if r["np1"] is not None else None
                np2 = r["np2"] if r["np2"] is not None else None
                
                # Logic to check if SUB is needed for passing (media < 7.0 and only one note missing or both present)
                initial_vals = [v for v in (np1, np2) if v is not None]
                if len(initial_vals) > 0 and (len(initial_vals) < 2 or (len(initial_vals) == 2 and sum(initial_vals) / 2 < MIN_PASS_GRADE)):
                    needed_for_sub_passing = None
                    replaced_note = None
                    
                    if np1 is not None and np2 is not None:
                        # SUB substitui a menor nota: (other_note + X) / 2 = 7.0 => X = 14.0 - other_note
                        min_note = min(np1, np2)
                        other_note = max(np1, np2)
                        needed = 14.0 - other_note
                        replaced_note = min_note
                    elif np1 is not None: 
                        # SUB substitui a NP2 que falta: (NP1 + X) / 2 = 7.0 => X = 14.0 - NP1
                        needed = 14.0 - np1
                        replaced_note = 0.0 # Nota ausente
                    elif np2 is not None:
                        # SUB substitui a NP1 que falta: (NP2 + X) / 2 = 7.0 => X = 14.0 - NP2
                        needed = 14.0 - np2
                        replaced_note = 0.0 # Nota ausente
                        
                    needed_for_sub_passing = round(needed, 2)
                    
                    if needed_for_sub_passing <= 10.0:
                        disciplinas_sub_needed.append((disc, needed_for_sub_passing, replaced_note, "possivel"))
                    else:
                        disciplinas_sub_needed.append((disc, needed_for_sub_passing, replaced_note, "impossivel"))

        # 2. Preparação dos dados: Frequência
        disciplinas_atencao_falta = []; overall_freq = None; freq_rows = []
        if is_freq_analysis:
            if is_overall_analysis:
                c.execute("""SELECT d.nome as disc, f.faltas FROM frequencia f 
                             JOIN disciplinas d ON f.disciplina_id=d.id 
                             JOIN matriculas m ON d.id=m.disciplina_id 
                             WHERE m.aluno_id=?""", (aluno_id,))
                freq_rows = c.fetchall()
            else:
                c.execute("""SELECT d.nome as disc, f.faltas FROM frequencia f 
                             JOIN disciplinas d ON f.disciplina_id=d.id 
                             WHERE f.aluno_id=? AND d.nome=?""", (aluno_id, selected_discipline))
                freq_rows = c.fetchall()
            
            # Cálculo da frequência geral
            if is_overall_analysis and freq_rows:
                total_faltas = sum(r["faltas"] for r in freq_rows)
                total_aulas = len(freq_rows) * SEMESTER_TOTAL_CLASSES
                overall_freq = round(((total_aulas - total_faltas) / total_aulas) * 100, 2) if total_aulas > 0 else None
                
            # Coleta de dados por disciplina para atenção (faltas)
            for r in freq_rows:
                disc = r['disc']
                if r["faltas"] > MAX_ALLOWED_ABSENCES:
                    disciplinas_atencao_falta.append(f"{disc} ({r['faltas']} faltas)")

        conn.close()
        
        html_output = "<h2>Análise de Desempenho Acadêmico da IA</h2>"
        html_output += f"<p>Data da Análise: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>"

        # 1. Notas e Média
        if is_grade_analysis:
            html_output += "<h3>[1] Notas e Média</h3>"
            if is_overall_analysis:
                # Mostrar média geral
                if overall_media is not None:
                    tag_nota = get_grade_color_tag(overall_media)
                    status_color = "🟢" if tag_nota == 'green' else "🟡" if tag_nota == 'yellow' else "🔴"
                    html_output += f"<p>Sua **Média Geral** em todas as disciplinas é: <b>{overall_media}</b> {status_color}</p>"
                    if overall_media < MIN_PASS_GRADE:
                        html_output += "<p>Recomendação: A Média Geral está abaixo da nota mínima de aprovação (7.0). Priorize a recuperação e estudos complementares.</p>"
                    else:
                        html_output += "<p>Status: Ótima média geral. Mantenha o esforço!</p>"
                else:
                    html_output += "<p>Não há notas registradas para calcular a média geral.</p>"
            else:
                # Mostrar média da disciplina selecionada
                if notas_rows:
                    r = notas_rows[0]
                    disc = r['disc']
                    media = calc_media(r["np1"], r["np2"], r["sub"])
                    if media is not None:
                        tag_nota = get_grade_color_tag(media)
                        status_color = "🟢" if tag_nota == 'green' else "🟡" if tag_nota == 'yellow' else "🔴"
                        html_output += f"<p>Sua Média em **{disc}** é: <b>{media}</b> {status_color}</p>"
                        if media < MIN_PASS_GRADE:
                            html_output += "<p>Recomendação: Média abaixo de 7.0. Verifique se há necessidade de Prova Substitutiva (SUB) ou Exame Final (se a média for > 3.0).</p>"
                        else:
                            html_output += "<p>Status: Aprovado(a) por nota. Mantenha o foco!</p>"
                    else:
                        html_output += f"<p>Notas insuficientes para calcular a média de **{disc}**.</p>"
                else:
                    html_output += "<p>Nenhuma nota encontrada para a disciplina selecionada.</p>"

        # 2. Frequência e Faltas
        if is_freq_analysis:
            html_output += "<h3>[2] Frequência e Faltas</h3>"
            if is_overall_analysis:
                if overall_freq is not None:
                    tag_freq = get_freq_color_tag(overall_freq)
                    status_color = "🟢" if tag_freq == 'green' else "🟡" if tag_freq == 'yellow' else "🔴"
                    html_output += f"<p>Sua **Frequência Geral** é: <b>{overall_freq}%</b> {status_color}</p>"
                    if overall_freq < MIN_PASS_FREQUENCY:
                        html_output += "<p>ALERTA: A frequência geral está abaixo do mínimo exigido (75% / 74.28%). **Risco de reprovação por falta**.</p>"
                    else:
                        html_output += "<p>Status: Frequência geral saudável. Continue comparecendo!</p>"
                else:
                    html_output += "<p>Não há dados de frequência para calcular a frequência geral.</p>"
            else:
                if freq_rows:
                    r = freq_rows[0]
                    pct = calc_freq_percent(r["faltas"])
                    tag_freq = get_freq_color_tag(pct)
                    status_color = "🟢" if tag_freq == 'green' else "🟡" if tag_freq == 'yellow' else "🔴"
                    html_output += f"<p>Sua Frequência em **{r['disc']}** é: <b>{pct}%</b> {status_color} ({r['faltas']} faltas)</p>"
                    if pct < MIN_PASS_FREQUENCY:
                        html_output += f"<p>ALERTA: Frequência abaixo do mínimo exigido (Mínimo {round(MIN_PASS_FREQUENCY, 2)}%). **Risco de reprovação por falta**.</p>"
                    else:
                        html_output += "<p>Status: Frequência dentro do limite permitido. Mantenha-se presente!</p>"
                else:
                    html_output += "<p>Não há dados de faltas/presenças.</p>"

        # 3. Ações Recomendadas e Pontos de Atenção (Didático)
        if is_grade_analysis or is_freq_analysis:
            html_output += "<h3>[3] Ações Recomendadas e Pontos de Atenção</h3>"
        
        # Faltas
        if is_freq_analysis and disciplinas_atencao_falta:
            html_output += "<h4>Risco de Reprovação por Frequência</h4><ul>"
            for d in disciplinas_atencao_falta:
                html_output += f"<li>**{d}**: Você já atingiu ou ultrapassou o limite máximo de **{MAX_ALLOWED_ABSENCES} faltas** para aprovação. É fundamental comparecer às aulas restantes e contatar a coordenação para avaliar sua situação.</li>"
            html_output += "</ul>"
            
        # Notas Baixas
        if is_grade_analysis and disciplinas_atencao_nota:
            html_output += "<h4>Notas Abaixo do Mínimo (7.0)</h4><ul>"
            for d in disciplinas_atencao_nota:
                html_output += f"<li>**{d}**: Sua média está abaixo de 7.0. Fique atento(a) à necessidade de Prova Substitutiva (SUB) ou Exame Final.</li>"
            html_output += "</ul>"

        # SUB Recommendation
        if is_grade_analysis and disciplinas_sub_needed:
            html_output += "<h4>Recomendação de Prova Substitutiva (SUB)</h4><ul>"
            for item in disciplinas_sub_needed:
                disc, needed, replaced_note, status = item[0], item[1], item[2], item[3]
                if status == "impossivel":
                    html_output += f"<li>Em **{disc}**, mesmo que você tire a nota máxima (10.0) na prova substitutiva (SUB), sua média final ainda ficará abaixo de 7.0 (você precisaria de {needed}). Você precisará de foco total no Exame Final.</li>"
                else:
                    html_output += f"<li>Em **{disc}**, você pode substituir sua menor nota ({replaced_note}) pela SUB. Você precisa de **{needed}** na SUB para atingir a média mínima de 7.0.</li>"
            html_output += "</ul>"

        return html_output if len(notas_rows) > 0 or len(freq_rows) > 0 else None

    # --- Professor and Coordinator functions below (kept original, except for coord dashboard update) ---

    def open_prof_dashboard(self):
        if not self.current_user or self.current_user.get("type") != "professor": messagebox.showerror("Erro", "Professor não autenticado."); return
        pid = self.current_user["id"]
        conn = connect_db(); c = conn.cursor(); c.execute("SELECT * FROM professores WHERE id=?", (pid,)); prof = c.fetchone(); conn.close()
        if not prof: messagebox.showerror("Erro", "Professor não encontrado."); return
        
        win = tk.Toplevel(self.root); win.title(f"Professor - {prof['nome']}"); win.geometry("1100x700"); win.configure(bg=MAIN_BG)
        tk.Label(win, text=f"Bem-vindo(a), Prof. {prof['nome']} - Disciplina: {prof['disciplina']}", bg=MAIN_BG, fg=UNIP_YELLOW, font=("Arial",16,"bold")).pack(pady=8)
        content = tk.Frame(win, bg=INNER_BG); content.pack(expand=True, fill='both', padx=12, pady=12)
        
        left = tk.Frame(content, bg=INNER_BG, width=320); left.pack(side='left', fill='y', padx=(6,12))
        right = tk.Frame(content, bg=INNER_BG); right.pack(side='left', expand=True, fill='both')
        
        tk.Label(left, text="Alunos Matriculados", font=FONT_LABEL, bg=INNER_BG).pack(pady=4)
        
        # Alunos Treeview
        treea = ttk.Treeview(left, columns=("nome", "email"), show='headings', height=18)
        treea.heading("nome", text="Nome"); treea.column("nome", width=160)
        treea.heading("email", text="Email"); treea.column("email", width=160)
        treea.pack(fill='y', expand=True, padx=8)
        
        # Notebook for content tabs
        nb = ttk.Notebook(right); nb.pack(expand=True, fill='both', padx=10, pady=10)
        
        t_notas = tk.Frame(nb, bg=INNER_BG); nb.add(t_notas, text='Lançar Notas/SUB')
        t_faltas = tk.Frame(nb, bg=INNER_BG); nb.add(t_faltas, text='Lançar Faltas')
        t_crono = tk.Frame(nb, bg=INNER_BG); nb.add(t_crono, text='Cronograma')
        t_ia = tk.Frame(nb, bg=INNER_BG); nb.add(t_ia, text='Análise IA')
        
        # Notas Tab
        tv_notas = ttk.Treeview(t_notas, columns=("nome", "email", "np1", "np2", "sub", "media"), show='headings', height=16)
        tv_notas.heading("nome", text="Nome"); tv_notas.column("nome", width=200)
        tv_notas.heading("email", text="Email"); tv_notas.column("email", width=200)
        tv_notas.heading("np1", text="NP1"); tv_notas.column("np1", width=80, anchor='center')
        tv_notas.heading("np2", text="NP2"); tv_notas.column("np2", width=80, anchor='center')
        tv_notas.heading("sub", text="SUB"); tv_notas.column("sub", width=80, anchor='center')
        tv_notas.heading("media", text="Média"); tv_notas.column("media", width=80, anchor='center')
        tv_notas.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Faltas Tab
        tv_faltas = ttk.Treeview(t_faltas, columns=("nome", "email", "aulas", "presencas", "faltas", "pct"), show='headings', height=16)
        tv_faltas.heading("nome", text="Nome"); tv_faltas.column("nome", width=200)
        tv_faltas.heading("email", text="Email"); tv_faltas.column("email", width=200)
        tv_faltas.heading("aulas", text="Aulas Totais"); tv_faltas.column("aulas", width=80, anchor='center')
        tv_faltas.heading("presencas", text="Presenças"); tv_faltas.column("presencas", width=80, anchor='center')
        tv_faltas.heading("faltas", text="Faltas"); tv_faltas.column("faltas", width=80, anchor='center')
        tv_faltas.heading("pct", text="% Freq."); tv_faltas.column("pct", width=80, anchor='center')
        tv_faltas.tag_configure('red', foreground=FREQ_COLOR_RED)
        tv_faltas.tag_configure('yellow', foreground=FREQ_COLOR_YELLOW)
        tv_faltas.tag_configure('green', foreground=FREQ_COLOR_GREEN)
        tv_faltas.pack(fill='both', expand=True, padx=8, pady=8)
        
        # IA Tab
        frame_ia = tk.Frame(t_ia, bg=INNER_BG); frame_ia.pack(expand=True, fill='both', padx=12, pady=12)
        ia_opt_frame = tk.Frame(frame_ia, bg=INNER_BG); ia_opt_frame.pack(fill='x', pady=6)
        
        tk.Label(ia_opt_frame, text="Aluno para Análise:", bg=INNER_BG).pack(side='left', padx=5)
        ia_disciplinas = ["Disciplinas do Professor"] 
        cb_ia_disc = ttk.Combobox(ia_opt_frame, values=ia_disciplinas, state='readonly', width=35); cb_ia_disc.pack(side='left', padx=5)
        cb_ia_disc.current(0)
        cb_ia_disc.configure(state='disabled') # Always analyses for the professor's discipline
        
        tk.Button(ia_opt_frame, text="GERAR ANÁLISE IA", bg="#FF9800", fg='white', font=("Arial",10,"bold"), command=lambda: self.prof_ia_generate(treea, prof["disciplina"])).pack(side='left', padx=10)
        
        ia_card = tk.Frame(frame_ia, bg="#A9D0F5", pady=10, padx=10); ia_card.pack(fill='both', expand=True, pady=8)
        self.prof_ia_text = tk.Text(ia_card, wrap='word', bg='#F0F8FF', font=("Arial", 10), state='disabled'); self.prof_ia_text.pack(fill='both', expand=True)

        # Load functions
        def load_prof_data():
            conn = connect_db(); c = conn.cursor()
            c.execute("SELECT id FROM disciplinas WHERE nome=?", (prof["disciplina"],))
            did_r = c.fetchone()
            if not did_r: conn.close(); return
            did = did_r["id"]
            
            for i in treea.get_children(): treea.delete(i)
            for i in tv_notas.get_children(): tv_notas.delete(i)
            for i in tv_faltas.get_children(): tv_faltas.delete(i)
            
            # Load Alunos
            c.execute("""SELECT a.id, a.nome, a.email FROM alunos a 
                         JOIN matriculas m ON a.id=m.aluno_id WHERE m.disciplina_id=?""", (did,))
            students = c.fetchall()
            for r in students: treea.insert('', 'end', values=(r["nome"], r["email"]), tags=(r["id"],))

            # Load Notas (incluindo 'n.sub')
            c.execute("""SELECT a.id, a.nome, a.email, n.np1, n.np2, n.sub FROM alunos a 
                         JOIN notas n ON a.id=n.aluno_id WHERE n.disciplina_id=? 
                         AND a.id IN (SELECT aluno_id FROM matriculas WHERE disciplina_id=?)""", (did, did))
            for r in c.fetchall():
                media = calc_media(r["np1"], r["np2"], r["sub"]) # Atualizado sub
                sub_disp = r["sub"] if r["sub"] is not None else "-"
                iid = tv_notas.insert('', 'end', values=(r["nome"], r["email"], r["np1"] if r["np1"] is not None else "-", r["np2"] if r["np2"] is not None else "-", sub_disp, media if media is not None else "-"), tags=(r["id"],))
                if media is not None:
                    tag = get_grade_color_tag(media)
                    if tag: tv_notas.item(iid, tags=(tag,))
            
            # Load Faltas
            c.execute("""SELECT a.id, a.nome, a.email, f.presencas, f.faltas FROM alunos a 
                         JOIN frequencia f ON a.id=f.aluno_id WHERE f.disciplina_id=? 
                         AND a.id IN (SELECT aluno_id FROM matriculas WHERE disciplina_id=?)""", (did, did))
            for r in c.fetchall():
                pct = calc_freq_percent(r["faltas"])
                iid = tv_faltas.insert('', 'end', values=(r["nome"], r["email"], SEMESTER_TOTAL_CLASSES, r["presencas"], r["faltas"], f"{pct}%"), tags=(r["id"],))
                tag = get_freq_color_tag(pct)
                if tag: tv_faltas.item(iid, tags=(tag,))
                
            conn.close()
            load_cronograma() # Needs to be called inside load_prof_data as it depends on `did`
            
        def _prof_lancar_notas_faltas(event):
            tree = event.widget
            sel = tree.selection()
            if not sel: return
            
            aluno_id = tree.item(sel[0], 'tags')[0]
            aluno_nome = tree.item(sel[0], 'values')[0]
            is_nota_tab = (tree == tv_notas)
            
            conn = connect_db(); c = conn.cursor()
            c.execute("SELECT id FROM disciplinas WHERE nome=?", (prof["disciplina"],)); did = c.fetchone()["id"]
            c.execute("SELECT np1, np2, sub FROM notas WHERE aluno_id=? AND disciplina_id=?", (aluno_id, did)); notas = c.fetchone()
            c.execute("SELECT faltas FROM frequencia WHERE aluno_id=? AND disciplina_id=?", (aluno_id, did)); frequencia = c.fetchone()
            conn.close()
            
            if not notas: notas = {"np1":None, "np2":None, "sub":None}
            
            popup = tk.Toplevel(win); popup.title(f"Lançar Notas/Faltas - {aluno_nome}"); popup.configure(bg=INNER_BG); popup.grab_set()
            
            tk.Label(popup, text=f"Lançamento para {aluno_nome} ({prof['disciplina']})", font=FONT_LABEL, bg=INNER_BG).pack(pady=10)
            
            # Notes fields
            nf = tk.Frame(popup, bg=INNER_BG); nf.pack(pady=8)
            tk.Label(nf, text="NP1:", bg=INNER_BG).grid(row=0, column=0, padx=5, pady=2); e1 = tk.Entry(nf, width=5); e1.grid(row=0, column=1, padx=5, pady=2)
            tk.Label(nf, text="NP2:", bg=INNER_BG).grid(row=0, column=2, padx=5, pady=2); e2 = tk.Entry(nf, width=5); e2.grid(row=0, column=3, padx=5, pady=2)
            tk.Label(nf, text="SUB:", bg=INNER_BG).grid(row=0, column=4, padx=5, pady=2); e_sub = tk.Entry(nf, width=5); e_sub.grid(row=0, column=5, padx=5, pady=2)
            
            e1.insert(0, str(notas["np1"]) if notas["np1"] is not None else "")
            e2.insert(0, str(notas["np2"]) if notas["np2"] is not None else "")
            e_sub.insert(0, str(notas["sub"]) if notas["sub"] is not None else "")
            
            # Absences field
            af = tk.Frame(popup, bg=INNER_BG); af.pack(pady=8)
            tk.Label(af, text="Total de Faltas:", bg=INNER_BG).grid(row=0, column=0, padx=5, pady=2); e_faltas = tk.Entry(af, width=5); e_faltas.grid(row=0, column=1, padx=5, pady=2)
            if frequencia: e_faltas.insert(0, str(frequencia["faltas"]) if frequencia["faltas"] is not None else "0")

            # Logic to disable SUB field if not eligible (or pre-filled)
            is_eligible_for_sub_display = True
            if notas["np1"] is not None and notas["np2"] is not None:
                initial_media = (notas["np1"] + notas["np2"]) / 2
                if initial_media >= MIN_PASS_GRADE: is_eligible_for_sub_display = False
            
            if is_nota_tab:
                e_faltas.configure(state='disabled')
                # Disable SUB if not eligible and empty
                if not is_eligible_for_sub_display and not e_sub.get():
                     e_sub.configure(state='disabled')
            else:
                e1.configure(state='disabled'); e2.configure(state='disabled'); e_sub.configure(state='disabled')

            def salvar():
                try:
                    # Parse notes
                    np1 = float(e1.get()) if e1.get() else None
                    np2 = float(e2.get()) if e2.get() else None
                    sub = float(e_sub.get()) if e_sub.get() and e_sub.cget('state') != 'disabled' else None
                    
                    if np1 is not None and (np1 < 0 or np1 > 10): raise ValueError("NP1 inválida")
                    if np2 is not None and (np2 < 0 or np2 > 10): raise ValueError("NP2 inválida")
                    if sub is not None and (sub < 0 or sub > 10): raise ValueError("SUB inválida")
                    
                    # Parse absences
                    faltas = int(e_faltas.get()) if e_faltas.get() and e_faltas.cget('state') != 'disabled' else 0
                    if faltas < 0 or faltas > SEMESTER_TOTAL_CLASSES: raise ValueError(f"Faltas inválidas (Máx: {SEMESTER_TOTAL_CLASSES})")

                except ValueError as e:
                    messagebox.showerror("Erro", f"Valor inválido: {e}"); return
                
                conn = connect_db(); c = conn.cursor()
                if not is_nota_tab: # Update absences only
                    presencas = max(0, SEMESTER_TOTAL_CLASSES - faltas)
                    c.execute("UPDATE frequencia SET faltas=?, presencas=? WHERE aluno_id=? AND disciplina_id=?", (faltas, presencas, aluno_id, did))
                else: # Update notes (incluindo 'sub')
                    c.execute("UPDATE notas SET np1=?, np2=?, sub=? WHERE aluno_id=? AND disciplina_id=?", (np1, np2, sub, aluno_id, did))
                
                conn.commit(); conn.close(); db_watcher.bump(); messagebox.showinfo("Sucesso","Dados atualizados."); popup.destroy()
                
            tk.Button(popup, text="Salvar", bg="#4CAF50", fg='white', command=salvar).pack(pady=8)
            center(popup)
            
        tv_notas.bind("<Double-1>", _prof_lancar_notas_faltas)
        tv_faltas.bind("<Double-1>", _prof_lancar_notas_faltas)
        
        # Cronograma tab: show modules and allow marking with date in DD/MM/YYYY
        crf = tk.Frame(t_crono); crf.pack(fill='both', expand=True, padx=8, pady=8)
        
        def load_cronograma():
            for w in crf.winfo_children(): w.destroy()
            conn = connect_db(); c = conn.cursor()
            c.execute("SELECT id FROM disciplinas WHERE nome=?", (prof["disciplina"],)); did_r = c.fetchone()
            if not did_r: conn.close(); return
            did = did_r["id"]
            
            c.execute("SELECT id, modulo_index, titulo, subtemas, marcado, marcado_em FROM cronogramas WHERE disciplina_id=? ORDER BY modulo_index", (did,))
            
            def save_cronograma(mid, var):
                marcado = var.get()
                marcado_em = datetime.datetime.now().strftime("%d/%m/%Y") if marcado else None
                conn = connect_db(); c = conn.cursor()
                c.execute("UPDATE cronogramas SET marcado=?, marcado_em=? WHERE id=?", (marcado, marcado_em, mid))
                conn.commit(); conn.close(); db_watcher.bump()
            
            for r in c.fetchall():
                var = tk.IntVar(value=r["marcado"])
                mid = r["id"]
                subs = r["subtemas"] or ""
                display = f"Modulo {r['modulo_index']}: {r['titulo']}\nSubtemas: " + ", ".join(subs.split(';'))
                
                frame = tk.Frame(crf, bg='#E0E0E0', padx=10, pady=5); frame.pack(fill='x', pady=2)
                
                # Checkbox
                chk = tk.Checkbutton(frame, text=display, variable=var, bg='#E0E0E0', justify='left', 
                                     command=lambda mid=mid, var=var: save_cronograma(mid, var))
                chk.pack(side='left', anchor='w')
                
                # Status
                status_text = f"Lançado em: {r['marcado_em']}" if r["marcado"] else "Não Lançado"
                status_fg = '#007E33' if r["marcado"] else '#B00020'
                tk.Label(frame, text=status_text, bg='#E0E0E0', fg=status_fg, font=("Arial", 9)).pack(side='right', padx=5)

        # Poller for Prof
        win._last_token = None
        def poll_prof():
            token = db_watcher.value()
            if win._last_token != token:
                load_prof_data()
                win._last_token = token
            win.after(1500, poll_prof)
        poll_prof()
        center(win)

    def prof_ia_generate(self, treea, selected_discipline):
        """Wrapper para gerar a análise acadêmica de um aluno selecionado pelo professor."""
        sel = treea.selection()
        if not sel:
            messagebox.showerror("Erro", "Selecione um aluno na lista da esquerda."); return
            
        aluno_id = treea.item(sel[0], 'tags')[0]
        aluno_nome = treea.item(sel[0], 'values')[0]
        
        # Gera a análise (somente para a disciplina do professor)
        resumo_html = self._generate_ia_analysis_formatted(aluno_id, selected_discipline, is_overall_analysis=False)
        
        if not resumo_html:
            self.prof_ia_text.configure(state='normal'); self.prof_ia_text.delete('1.0', tk.END)
            self.prof_ia_text.insert('end', f"Nenhum dado encontrado para análise de {aluno_nome} na(s) disciplina(s) selecionada(s).")
            self.prof_ia_text.configure(state='disabled')
            return
            
        parser = SimpleHTMLtoText(); parser.feed(resumo_html)
        resumo_text = parser.get_text()
        
        conn = connect_db(); c = conn.cursor()
        c.execute("INSERT INTO ia_historico (aluno_id, data, resumo) VALUES (?, ?, ?)", (aluno_id, datetime.datetime.now().isoformat(), f"Análise de Prof. {self.current_user['nome']}:\n{resumo_text}"));
        conn.commit(); conn.close()
        
        self.prof_ia_text.configure(state='normal')
        self.prof_ia_text.delete('1.0', tk.END)
        self.prof_ia_text.insert(tk.END, resumo_text)
        self.prof_ia_text.configure(state='disabled')
        db_watcher.bump()

    def open_coord_dashboard(self):
        if not self.current_user or self.current_user.get("type") != "coordenador": messagebox.showerror("Erro", "Coordenador não autenticado."); return
        win = tk.Toplevel(self.root); win.title("Coordenador - Dashboard"); win.geometry("1100x700"); win.configure(bg=MAIN_BG)
        
        tk.Label(win, text="COORDENADORIA - ADMINISTRAÇÃO", bg=MAIN_BG, fg=UNIP_YELLOW, font=("Arial",16,"bold")).pack(pady=8)
        content = tk.Frame(win, bg=INNER_BG); content.pack(expand=True, fill='both', padx=12, pady=12)
        
        # Main Notebook (Tabs)
        nb = ttk.Notebook(content); nb.pack(expand=True, fill='both', padx=10, pady=10)
        
        # 1. Alunos
        t_alunos = tk.Frame(nb, bg=INNER_BG); nb.add(t_alunos, text='Alunos')
        # 2. Professores
        t_professores = tk.Frame(nb, bg=INNER_BG); nb.add(t_professores, text='Professores')
        # 3. Disciplinas
        t_disciplinas = tk.Frame(nb, bg=INNER_BG); nb.add(t_disciplinas, text='Disciplinas')
        # 4. Histórico IA
        t_ia_hist = tk.Frame(nb, bg=INNER_BG); nb.add(t_ia_hist, text='Histórico IA')
        # 5. Financeiro (NEW)
        t_financeiro = tk.Frame(nb, bg=INNER_BG); nb.add(t_financeiro, text='Financeiro')

        # --- Tab: Alunos ---
        treea = ttk.Treeview(t_alunos, columns=("nome","ra","email"), show='headings', height=16)
        for col in ("nome","ra","email"): treea.heading(col, text=col.capitalize()); treea.column(col, width=300)
        treea.pack(fill='both', expand=True, padx=8, pady=8)
        
        def load_alunos_list():
            for i in treea.get_children(): treea.delete(i)
            conn = connect_db(); c = conn.cursor(); c.execute("SELECT id, nome, ra, email FROM alunos"); rows = c.fetchall(); conn.close()
            for r in rows: treea.insert('', 'end', values=(r["nome"], r["ra"], r["email"]), tags=(r["id"],))
        
        # --- Tab: Professores ---
        treep = ttk.Treeview(t_professores, columns=("nome","disciplina","email"), show='headings', height=16)
        for col in ("nome","disciplina","email"): treep.heading(col, text=col.capitalize()); treep.column(col, width=300)
        treep.pack(fill='both', expand=True, padx=8, pady=8)

        def load_prof_list():
            for i in treep.get_children(): treep.delete(i)
            conn = connect_db(); c = conn.cursor(); c.execute("SELECT id, nome, disciplina, email FROM professores"); rows = c.fetchall(); conn.close()
            for r in rows: treep.insert('', 'end', values=(r["nome"], r["disciplina"], r["email"]), tags=(r["id"],))

        # --- Tab: Disciplinas ---
        frd = tk.Frame(t_disciplinas, bg=INNER_BG); frd.pack(fill='x', padx=8, pady=8)
        tk.Label(frd, text="Nome da Nova Disciplina:", bg=INNER_BG).grid(row=0, column=0, pady=6)
        e_disc = tk.Entry(frd, width=50); e_disc.grid(row=0, column=1, pady=6, padx=5)
        
        def criar_disc():
            dname = e_disc.get().strip()
            if not dname: messagebox.showerror("Erro", "Nome da disciplina vazio."); return
            conn = connect_db(); c = conn.cursor()
            try:
                c.execute("INSERT INTO disciplinas (nome) VALUES (?)", (dname,))
                conn.commit(); conn.close(); db_watcher.bump(); messagebox.showinfo("Sucesso", "Disciplina criada."); e_disc.delete(0, tk.END)
            except sqlite3.IntegrityError:
                conn.close(); messagebox.showerror("Erro", "Disciplina já existe.")
                
        tk.Button(frd, text="Criar Disciplina", bg="#4CAF50", fg='white', command=criar_disc).grid(row=1,column=0,columnspan=2,pady=6)
        
        treed = ttk.Treeview(t_disciplinas, columns=("id","nome"), show='headings', height=16)
        treed.heading("id", text="ID"); treed.column("id", width=50, anchor='center')
        treed.heading("nome", text="Nome"); treed.column("nome", width=550)
        treed.pack(fill='both', expand=True, padx=8, pady=8)

        def load_disc_list():
            for i in treed.get_children(): treed.delete(i)
            conn = connect_db(); c = conn.cursor(); c.execute("SELECT id, nome FROM disciplinas"); rows = c.fetchall(); conn.close()
            for r in rows: treed.insert('', 'end', values=(r["id"], r["nome"]))

        # --- Tab: Histórico IA ---
        tk.Label(t_ia_hist, text="Últimas 200 Análises da IA", font=FONT_LABEL, bg=INNER_BG).pack(pady=5)
        self.coord_ia_text = tk.Text(t_ia_hist, wrap='word', bg='white', font=("Arial", 10), state='disabled');
        self.coord_ia_text.pack(fill='both', expand=True, padx=8, pady=8)
        
        def load_ia_history():
            self.coord_ia_text.configure(state='normal'); self.coord_ia_text.delete('1.0', tk.END)
            conn = connect_db(); c = conn.cursor()
            c.execute("SELECT a.nome, h.data, h.resumo FROM ia_historico h JOIN alunos a ON h.aluno_id=a.id ORDER BY h.id DESC LIMIT 200"); rows = c.fetchall(); conn.close()
            if not rows:
                self.coord_ia_text.insert('end', "Nenhum histórico de análise de desempenho encontrado.")
            else:
                for r in rows: self.coord_ia_text.insert('end', f"*** {r['data']} - {r['nome']} ***\n{r['resumo']}\n\n")
            self.coord_ia_text.configure(state='disabled')
            
        # --- Tab: Financeiro (NEW) ---
        tv_finance = ttk.Treeview(t_financeiro, columns=("aluno_id", "nome", "mes", "valor", "status", "forma"), show='headings', height=18)
        tv_finance.heading("aluno_id", text="ID Aluno"); tv_finance.column("aluno_id", width=60, anchor='center')
        tv_finance.heading("nome", text="Nome"); tv_finance.column("nome", width=200)
        tv_finance.heading("mes", text="Mês"); tv_finance.column("mes", width=80, anchor='center')
        tv_finance.heading("valor", text="Valor"); tv_finance.column("valor", width=100, anchor='center')
        tv_finance.heading("status", text="Status"); tv_finance.column("status", width=100, anchor='center')
        tv_finance.heading("forma", text="Forma Pgto"); tv_finance.column("forma", width=100, anchor='center')
        tv_finance.tag_configure('paid', foreground=FINANCE_COLOR_PAID_OK)
        tv_finance.tag_configure('pending', foreground=FINANCE_COLOR_PENDING)
        tv_finance.tag_configure('overdue', foreground=FINANCE_COLOR_OVERDUE)
        tv_finance.pack(fill='both', expand=True, padx=8, pady=8)
        
        btn_frame_finance = tk.Frame(t_financeiro, bg=INNER_BG); btn_frame_finance.pack(pady=8)
        tk.Button(btn_frame_finance, text="Lançar Pagamento Selecionado", bg=BTN_BG, fg=BTN_FG, 
                  command=lambda: self.open_coord_lancar_pagamento(tv_finance)).pack(side='left', padx=10)
        
        def load_financeiro_coord():
            for i in tv_finance.get_children(): tv_finance.delete(i)
            conn = connect_db(); c = conn.cursor()
            c.execute("""SELECT f.aluno_id, a.nome, f.mes, f.valor, f.status, f.forma_pagamento, f.data_pagamento
                         FROM financeiro f JOIN alunos a ON f.aluno_id=a.id 
                         ORDER BY f.aluno_id, f.ano, 
                         CASE f.mes WHEN 'JAN' THEN 1 WHEN 'FEV' THEN 2 WHEN 'MAR' THEN 3 WHEN 'ABR' THEN 4 WHEN 'MAI' THEN 5 WHEN 'JUN' THEN 6 WHEN 'JUL' THEN 7 WHEN 'AGO' THEN 8 WHEN 'SET' THEN 9 WHEN 'OUT' THEN 10 WHEN 'NOV' THEN 11 WHEN 'DEZ' THEN 12 END""")
            rows = c.fetchall(); conn.close()
            
            for r in rows:
                tag = 'pending'
                
                if r["status"] == 'PAGO': tag = 'paid'
                elif r["status"] in ('ATRASO', 'PAGO_ATRASO'): tag = 'overdue'
                
                status_display = r["status"].replace('PAGO_ATRASO', 'Pago Atraso').replace('ATRASO', 'Em Atraso').capitalize()
                forma_display = r["forma_pagamento"] if r["forma_pagamento"] else "-"
                
                iid = tv_finance.insert('', 'end', 
                                        values=(r["aluno_id"], r["nome"], r["mes"], f"R$ {r['valor']:.2f}", status_display, forma_display), 
                                        tags=(tag, f"finance_id:{r['aluno_id']}:{r['mes']}"))
                                        
        # Poller for Coord
        win._last_token = None
        def poll_coord():
            token = db_watcher.value()
            if win._last_token != token:
                load_prof_list(); load_disc_list(); load_alunos_list(); load_ia_history(); load_financeiro_coord()
                win._last_token = token
            win.after(1500, poll_coord)
        poll_coord()
        
        center(win)

    def open_coord_lancar_pagamento(self, treeview):
        """Popup para o coordenador lançar/atualizar um pagamento."""
        sel = treeview.selection()
        if not sel:
            messagebox.showerror("Erro", "Selecione um pagamento na lista do Financeiro."); return

        item = treeview.item(sel[0])
        try:
            # Tags example: ('pending', 'finance_id:1:JAN')
            tag_data = item['tags'][1]
            aluno_id, mes = tag_data.split(':')[1], tag_data.split(':')[2]
        except IndexError:
            messagebox.showerror("Erro", "Erro ao obter dados do item selecionado."); return
            
        aluno_nome = item['values'][1]
        valor_str = item['values'][3]
        
        popup = tk.Toplevel(self.root); popup.title("Lançar Pagamento"); popup.configure(bg=INNER_BG); popup.grab_set()
        
        tk.Label(popup, text=f"Lançar Pagamento para {aluno_nome}", font=FONT_LABEL, bg=INNER_BG).pack(pady=10)
        tk.Label(popup, text=f"Mês: {mes} | Valor: {valor_str}", bg=INNER_BG).pack(pady=5)
        
        # 1. Status Selection
        f_status = tk.Frame(popup, bg=INNER_BG); f_status.pack(pady=5)
        tk.Label(f_status, text="Status:", bg=INNER_BG).pack(side='left', padx=5)
        # Removendo PAGO_ATRASO, ATRASO para simplificar a seleção para as 3 opções principais de status
        status_options = ["PAGO", "PENDENTE", "ATRASO"] # Coordenador seleciona o status principal
        sv_status = tk.StringVar(value="PENDENTE")
        
        # Pre-load current status (fetch from DB to get full status, including PAGO_ATRASO)
        conn_check = connect_db(); c_check = conn_check.cursor()
        c_check.execute("SELECT status, forma_pagamento, data_pagamento FROM financeiro WHERE aluno_id=? AND mes=?", (aluno_id, mes))
        current_data = c_check.fetchone()
        conn_check.close()
        
        if current_data:
            # Map full status to the simpler select options for the coordinator
            if current_data['status'] in ('PAGO', 'PAGO_ATRASO'): sv_status.set("PAGO")
            elif current_data['status'] == 'PENDENTE': sv_status.set("PENDENTE")
            elif current_data['status'] == 'ATRASO': sv_status.set("ATRASO")
        
        cb_status = ttk.Combobox(f_status, textvariable=sv_status, values=status_options, state='readonly'); cb_status.pack(side='left', padx=5)

        # 2. Forma de Pagamento Selection (Only PAGO status requires this)
        f_forma = tk.Frame(popup, bg=INNER_BG); f_forma.pack(pady=5)
        tk.Label(f_forma, text="Forma de Pgto:", bg=INNER_BG).pack(side='left', padx=5)
        sv_forma = tk.StringVar(value=current_data['forma_pagamento'] if current_data and current_data['forma_pagamento'] else PAYMENT_METHODS[0])
        cb_forma = ttk.Combobox(f_forma, textvariable=sv_forma, values=PAYMENT_METHODS, state='readonly'); cb_forma.pack(side='left', padx=5)

        # 3. Date and Time Input
        f_data = tk.Frame(popup, bg=INNER_BG); f_data.pack(pady=5)
        tk.Label(f_data, text="Data Pgto (DD/MM/AAAA HH:MM:SS):", bg=INNER_BG).pack(side='left', padx=5)
        e_data = tk.Entry(f_data, width=25); e_data.pack(side='left', padx=5)
        
        if current_data and current_data['data_pagamento']:
             try:
                dt_obj = datetime.datetime.fromisoformat(current_data['data_pagamento'])
                e_data.insert(0, dt_obj.strftime("%d/%m/%Y %H:%M:%S"))
             except ValueError:
                e_data.insert(0, current_data['data_pagamento']) # Fallback
        
        def lancar_agora():
            now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            e_data.delete(0, tk.END); e_data.insert(0, now)

        tk.Button(f_data, text="Lançar Agora", bg="#4CAF50", fg='white', command=lancar_agora).pack(side='left', padx=5)

        def salvar():
            status_input = sv_status.get()
            forma = sv_forma.get()
            data_hora_str = e_data.get().strip()
            data_pagamento_iso = None

            if status_input == "PAGO":
                if not data_hora_str:
                    messagebox.showerror("Erro", "Data e hora do pagamento são obrigatórios para status Pago.")
                    return
                try:
                    dt_obj = datetime.datetime.strptime(data_hora_str, "%d/%m/%Y %H:%M:%S")
                    data_pagamento_iso = dt_obj.isoformat()
                    
                    # Assume 'PAGO' is paid on time, 'PAGO_ATRASO' if date is far in the past (simple check)
                    # For simplicity, we assume "PAGO" is the intended final status unless "ATRASO" is selected. 
                    # The coordinator must select "ATRASO" to mark it as delayed.
                    final_status = 'PAGO'
                    
                except ValueError:
                    messagebox.showerror("Erro", "Formato de data/hora inválido. Use DD/MM/AAAA HH:MM:SS.")
                    return
            
            elif status_input == "ATRASO":
                final_status = "ATRASO"
                forma = None; data_pagamento_iso = None # Limpa se estiver atrasado e não pago
                if data_hora_str:
                     # If there is a date, it means it was paid late
                     try:
                        dt_obj = datetime.datetime.strptime(data_hora_str, "%d/%m/%Y %H:%M:%S")
                        data_pagamento_iso = dt_obj.isoformat()
                        final_status = 'PAGO_ATRASO'
                     except ValueError:
                        messagebox.showerror("Erro", "Formato de data/hora inválido. Use DD/MM/AAAA HH:MM:SS para pagamento em atraso.")
                        return
                     
            else: # PENDENTE
                final_status = "PENDENTE"
                forma = None; data_pagamento_iso = None

            conn = connect_db(); c = conn.cursor()
            try:
                # Find the row to get the 'ano' (year)
                c.execute("SELECT ano FROM financeiro WHERE aluno_id=? AND mes=?", (aluno_id, mes))
                ano_data = c.fetchone()
                if not ano_data: raise Exception("Registro financeiro não encontrado.")
                ano = ano_data['ano']
                
                c.execute("""UPDATE financeiro 
                           SET status=?, forma_pagamento=?, data_pagamento=?, data_lancamento=? 
                           WHERE aluno_id=? AND mes=? AND ano=?""", 
                          (final_status, forma, data_pagamento_iso, datetime.datetime.now().isoformat(), aluno_id, mes, ano))
                conn.commit(); conn.close(); db_watcher.bump();
                messagebox.showinfo("Sucesso", "Pagamento lançado com sucesso."); popup.destroy()
            except Exception as e:
                conn.close(); messagebox.showerror("Erro", f"Erro ao salvar: {e}")

        tk.Button(popup, text="Salvar Lançamento", bg=BTN_BG, fg=BTN_FG, width=20, command=salvar).pack(pady=10)
        center(popup)

def framed_label_entry(parent, label_text, **kwargs):
    frame = tk.Frame(parent, bg=INNER_BG); frame.configure(width=kwargs.get('width', 30)*7)
    center_label = kwargs.pop('center_label', False)
    anchor = 'center' if center_label else 'w'
    tk.Label(frame, text=label_text, font=FONT_LABEL, bg=INNER_BG).pack(anchor=anchor)
    entry = tk.Entry(frame, **kwargs)
    entry.pack(fill='x', expand=True)
    return frame, entry

if __name__ == '__main__':
    init_db()
    seed_initial_data()
    root = tk.Tk()
    app = App(root)
    center(root)
    root.mainloop()