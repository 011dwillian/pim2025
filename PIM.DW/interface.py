import tkinter as tk
from tkinter import ttk
from datetime import datetime

from .db import init_db, get_connection


class AssistenteAcademica(tk.Toplevel):
    """
    Janela flutuante da IA acadêmica.
    - Pode ser chamada de qualquer lugar do seu main.
    - Usa Frames internos, então no futuro dá pra embutir se quiser.
    """

    def __init__(self, master=None, aluno_id=1, aluno_nome="Aluno"):
        super().__init__(master)

        self.aluno_id = aluno_id
        self.aluno_nome = aluno_nome

        self.title(f"Assistente Acadêmica - {self.aluno_nome}")
        self.geometry("950x600")
        self.configure(bg="#e3f2fd")  # azul claro
        self.minsize(850, 500)

        # garante que o banco existe
        init_db()

        # estilos ttk
        self._build_styles()
        # layout
        self._build_layout()

        # foco na janela
        self.transient(master)
        self.grab_set()  # janela se comporta como modal (tipo “assistente lateral”)
        self.focus_force()

    def _build_styles(self):
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Menu.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("CardTitle.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Info.TLabel", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_layout(self):
        # topo
        header = tk.Frame(self, bg="#1565c0")
        header.pack(side="top", fill="x")

        lbl_title = ttk.Label(
            header,
            text=f"Olá, {self.aluno_nome}! 👋 | Assistente Acadêmica Virtual",
            style="Title.TLabel",
            background="#1565c0",
            foreground="white"
        )
        lbl_title.pack(padx=20, pady=10, anchor="w")

        # área principal
        main = tk.Frame(self, bg="#e3f2fd")
        main.pack(fill="both", expand=True)

        # menu lateral
        menu = tk.Frame(main, bg="#bbdefb", width=220)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)

        ttk.Label(
            menu,
            text="Como posso ajudar hoje?",
            font=("Segoe UI", 11, "bold"),
            background="#bbdefb"
        ).pack(pady=(20, 10), padx=10)

        ttk.Button(
            menu,
            text="📘 Minhas Notas",
            style="Menu.TButton",
            command=lambda: self.show_frame("notas")
        ).pack(fill="x", padx=15, pady=5)

        ttk.Button(
            menu,
            text="📊 Minhas Faltas",
            style="Menu.TButton",
            command=lambda: self.show_frame("faltas")
        ).pack(fill="x", padx=15, pady=5)

        ttk.Button(
            menu,
            text="🧠 Análise Inteligente",
            style="Menu.TButton",
            command=lambda: self.show_frame("analise")
        ).pack(fill="x", padx=15, pady=5)

        ttk.Button(
            menu,
            text="💬 Conversar com a IA",
            style="Menu.TButton",
            command=lambda: self.show_frame("chat")
        ).pack(fill="x", padx=15, pady=5)

        ttk.Separator(menu, orient="horizontal").pack(fill="x", padx=10, pady=15)

        ttk.Button(
            menu,
            text="❌ Fechar Assistente",
            command=self.destroy
        ).pack(fill="x", padx=15, pady=(0, 20))

        # área de conteúdo (lado direito)
        self.container = tk.Frame(main, bg="#e3f2fd")
        self.container.pack(side="left", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # frames internos
        self.frames = {}
        self.frames["notas"] = NotasFrame(self.container, self)
        self.frames["faltas"] = FaltasFrame(self.container, self)
        self.frames["analise"] = AnaliseFrame(self.container, self)
        self.frames["chat"] = ChatFrame(self.container, self)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        # começa em notas
        self.show_frame("notas")

    def show_frame(self, name):
        frame = self.frames.get(name)
        if frame:
            if hasattr(frame, "atualizar_dados"):
                frame.atualizar_dados()
            frame.tkraise()


# ==== Classes base / telas ====

class BaseFrame(tk.Frame):
    def __init__(self, parent, app: AssistenteAcademica, bg_color, title):
        super().__init__(parent, bg=bg_color)
        self.app = app

        title_frame = tk.Frame(self, bg=bg_color)
        title_frame.pack(fill="x", padx=20, pady=(20, 10))

        lbl_title = ttk.Label(
            title_frame,
            text=title,
            style="CardTitle.TLabel",
            background=bg_color
        )
        lbl_title.pack(anchor="w")


class NotasFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, bg_color="#e3f2fd", title="📘 Minhas Notas")

        card = tk.Frame(self, bg="white", bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ttk.Label(
            card,
            text="Aqui você vê suas notas, médias e a situação em cada matéria.",
            style="Info.TLabel",
            background="white"
        ).pack(anchor="w", padx=15, pady=10)

        columns = ("materia", "np1", "np2", "media", "situacao")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", height=10)
        self.tree.heading("materia", text="Matéria")
        self.tree.heading("np1", text="NP1")
        self.tree.heading("np2", text="NP2")
        self.tree.heading("media", text="Média")
        self.tree.heading("situacao", text="Situação")

        self.tree.column("materia", width=220)
        self.tree.column("np1", width=80, anchor="center")
        self.tree.column("np2", width=80, anchor="center")
        self.tree.column("media", width=80, anchor="center")
        self.tree.column("situacao", width=160, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.lbl_resumo = ttk.Label(
            card,
            text="",
            style="Info.TLabel",
            background="white",
            foreground="#1b5e20"
        )
        self.lbl_resumo.pack(anchor="w", padx=15, pady=(0, 10))

    def atualizar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.nome, n.np1, n.np2, n.media
            FROM notas n
            JOIN materias m ON m.id = n.materia_id
            WHERE n.aluno_id = ?
        """, (self.app.aluno_id,))
        rows = cur.fetchall()
        conn.close()

        materias_em_risco = 0
        total = 0

        for materia, np1, np2, media in rows:
            total += 1
            if media is None:
                situacao = "Sem dados"
            elif media >= 7:
                situacao = "Aprovado ✅"
            elif media >= 4:
                situacao = "SUB/Exame 🚨"
                materias_em_risco += 1
            else:
                situacao = "Reprovado ❌"
                materias_em_risco += 1

            self.tree.insert("", "end", values=(
                materia,
                f"{np1:.1f}" if np1 is not None else "-",
                f"{np2:.1f}" if np2 is not None else "-",
                f"{media:.1f}" if media is not None else "-",
                situacao
            ))

        if total == 0:
            txt = "Nenhuma nota cadastrada ainda."
        else:
            txt = f"Você tem {total} matéria(s). {materias_em_risco} em atenção ou reprovação."
        self.lbl_resumo.config(text=txt)


class FaltasFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, bg_color="#fff8e1", title="📊 Minhas Faltas")

        card = tk.Frame(self, bg="white", bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ttk.Label(
            card,
            text="Veja a quantidade de faltas em cada matéria e o risco de reprovação.",
            style="Info.TLabel",
            background="white"
        ).pack(anchor="w", padx=15, pady=10)

        columns = ("materia", "faltas", "limite", "situacao")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", height=10)
        self.tree.heading("materia", text="Matéria")
        self.tree.heading("faltas", text="Faltas")
        self.tree.heading("limite", text="Limite")
        self.tree.heading("situacao", text="Situação")

        self.tree.column("materia", width=220)
        self.tree.column("faltas", width=80, anchor="center")
        self.tree.column("limite", width=80, anchor="center")
        self.tree.column("situacao", width=200, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.lbl_resumo = ttk.Label(
            card,
            text="",
            style="Info.TLabel",
            background="white",
            foreground="#e65100"
        )
        self.lbl_resumo.pack(anchor="w", padx=15, pady=(0, 10))

    def atualizar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.nome, f.total_faltas, f.limite_faltas
            FROM faltas f
            JOIN materias m ON m.id = f.materia_id
            WHERE f.aluno_id = ?
        """, (self.app.aluno_id,))
        rows = cur.fetchall()
        conn.close()

        total_faltas = 0
        materias_criticas = 0

        for materia, faltas, limite in rows:
            total_faltas += faltas
            if faltas >= limite:
                situacao = "Reprovado por faltas ❌"
                materias_criticas += 1
            elif faltas >= limite * 0.8:
                situacao = "Muito próximo do limite ⚠️"
                materias_criticas += 1
            elif faltas >= limite * 0.5:
                situacao = "Atenção 👀"
            else:
                situacao = "Tranquilo ✅"

            self.tree.insert("", "end", values=(materia, faltas, limite, situacao))

        if not rows:
            txt = "Nenhuma falta cadastrada ainda."
        else:
            txt = f"Total de faltas: {total_faltas}. {materias_criticas} matéria(s) em situação crítica."
        self.lbl_resumo.config(text=txt)


class AnaliseFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, bg_color="#f3e5f5", title="🧠 Análise Inteligente")

        card = tk.Frame(self, bg="white", bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ttk.Label(
            card,
            text="Resumo do seu desempenho geral com base nas notas e faltas.",
            style="Info.TLabel",
            background="white"
        ).pack(anchor="w", padx=15, pady=10)

        self.txt = tk.Text(card, wrap="word", height=15, bd=0, padx=10, pady=10)
        self.txt.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.txt.config(state="disabled")

    def atualizar_dados(self):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT m.nome, n.media
            FROM notas n
            JOIN materias m ON m.id = n.materia_id
            WHERE n.aluno_id = ?
        """, (self.app.aluno_id,))
        notas = cur.fetchall()

        cur.execute("""
            SELECT m.nome, f.total_faltas, f.limite_faltas
            FROM faltas f
            JOIN materias m ON m.id = f.materia_id
            WHERE f.aluno_id = ?
        """, (self.app.aluno_id,))
        faltas = cur.fetchall()

        conn.close()

        partes = []

        # Notas
        if not notas:
            partes.append("📘 Ainda não há notas suficientes para gerar uma análise completa.\n")
        else:
            medias = [m for _, m in notas if m is not None]
            if medias:
                media_geral = sum(medias) / len(medias)
                partes.append(f"📘 Sua média geral é **{media_geral:.2f}**.\n")
            else:
                partes.append("📘 As notas ainda não foram totalmente lançadas.\n")

            melhor = max(notas, key=lambda x: (x[1] if x[1] is not None else -1))
            pior = min(notas, key=lambda x: (x[1] if x[1] is not None else 999))

            if melhor[1] is not None:
                partes.append(f"✅ Melhor matéria: {melhor[0]} (média {melhor[1]:.1f}).")
            if pior[1] is not None:
                partes.append(f"\n⚠️ Matéria mais crítica: {pior[0]} (média {pior[1]:.1f}).")

            em_risco = [n for n in notas if n[1] is not None and n[1] < 7]
            if em_risco:
                nomes = ", ".join([m[0] for m in em_risco])
                partes.append(f"\n🚨 Matérias que exigem atenção: {nomes}.")
            else:
                partes.append("\n🎉 Parabéns! Nenhuma matéria em risco pelas notas.")

        partes.append("\n\n——————————————\n")

        # Faltas
        if not faltas:
            partes.append("📊 Não há dados de faltas para análise.")
        else:
            total_faltas = sum([f[1] for f in faltas])
            criticas = [f for f in faltas if f[1] >= f[2] * 0.8]
            partes.append(f"📊 Total de faltas: {total_faltas} em todas as matérias.\n")

            if criticas:
                nomes = ", ".join([f[0] for f in criticas])
                partes.append(f"⚠️ Atenção! Você está próximo do limite em: {nomes}.")
            else:
                partes.append("✅ Sua frequência está sob controle, continue assim!")

        partes.append("\n\n🎯 Recomendações da IA:\n")
        partes.append("- Foque nas matérias em risco primeiro.\n")
        partes.append("- Evite faltar nas próximas aulas das matérias críticas.\n")
        partes.append("- Revise listas de exercícios e anotações das aulas.\n")

        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(partes))
        self.txt.config(state="disabled")


class ChatFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, bg_color="#e8f5e9", title="💬 Conversar com a IA")

        card = tk.Frame(self, bg="white", bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ttk.Label(
            card,
            text="Faça perguntas sobre notas, faltas, aprovação, provas, etc.",
            style="Info.TLabel",
            background="white"
        ).pack(anchor="w", padx=15, pady=10)

        self.txt_chat = tk.Text(
            card, wrap="word", height=15, bd=0, padx=10, pady=10, state="disabled"
        )
        self.txt_chat.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        input_frame = tk.Frame(card, bg="white")
        input_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.entry_msg = ttk.Entry(input_frame)
        self.entry_msg.pack(side="left", fill="x", expand=True, pady=5)
        self.entry_msg.bind("<Return>", lambda event: self.enviar())

        ttk.Button(input_frame, text="Enviar", command=self.enviar).pack(
            side="left", padx=(5, 0)
        )

        self._add("IA", "Olá! 👋 Sou sua assistente acadêmica. Como posso te ajudar hoje?")

    def atualizar_dados(self):
        # Nada específico por enquanto
        pass

    def _add(self, remetente, msg):
        self.txt_chat.config(state="normal")
        hora = datetime.now().strftime("%H:%M")
        self.txt_chat.insert("end", f"[{hora}] {remetente}: {msg}\n")
        self.txt_chat.see("end")
        self.txt_chat.config(state="disabled")

    def enviar(self):
        texto = self.entry_msg.get().strip()
        if not texto:
            return
        self.entry_msg.delete(0, "end")
        self._add("Você", texto)
        resp = self._responder(texto)
        self._add("IA", resp)

    def _responder(self, pergunta: str) -> str:
        p = pergunta.lower()

        if "nota" in p or "média" in p or "media" in p:
            return ("Sobre notas: na aba 'Minhas Notas' você vê suas médias, "
                    "situação (aprovado, SUB ou reprovado) e um resumo geral. 😊")
        if "falta" in p or "frequência" in p or "frequencia" in p:
            return ("Sobre faltas: na aba 'Minhas Faltas' eu mostro quantas faltas você tem, "
                    "o limite e se existe risco de reprovação. ✏️")
        if "aprova" in p or "reprova" in p or "passar" in p:
            return ("A aprovação depende da média final e de não estourar o limite de faltas. "
                    "Na aba 'Análise Inteligente' eu faço um resumo da sua situação geral. 🎯")
        if "oi" in p or "olá" in p or "ola" in p:
            return "Oi! 😄 Como posso te ajudar sobre sua vida acadêmica?"

        return ("Entendi! No momento eu respondo melhor perguntas sobre notas, faltas, aprovação, "
                "provas e estudos. Tente algo como: 'Como está minha situação de faltas?' 😉")


def abrir_assistente_academica(master, aluno_id=1, aluno_nome="Aluno"):
    """
    Função simples para você chamar no seu main.
    """
    AssistenteAcademica(master, aluno_id=aluno_id, aluno_nome=aluno_nome)