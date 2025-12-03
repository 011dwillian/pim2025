# aluno.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import conectar
from ia.analise_ia import analyze_student
import os

def tela_aluno(dados_aluno):
    """
    dados_aluno: tupla (id, nome, data_nascimento, ra, senha, email)
    """
    id_aluno, nome, data_nasc, ra, senha, email = dados_aluno

    aluno_win = tk.Toplevel()
    aluno_win.title(f"Área do Aluno - {nome}")
    aluno_win.geometry("750x520")

    tk.Label(aluno_win, text=f"Bem-vindo, {nome}!", font=("Arial", 14, "bold")).pack(pady=6)
    tk.Label(aluno_win, text=f"RA: {ra} | E-mail: {email or '—'}", font=("Arial", 10)).pack(pady=2)

    abas = ttk.Notebook(aluno_win)
    frame_disciplinas = ttk.Frame(abas)
    frame_notas = ttk.Frame(abas)
    frame_frequencia = ttk.Frame(abas)
    frame_atestados = ttk.Frame(abas)
    frame_cadastro = ttk.Frame(abas)

    abas.add(frame_disciplinas, text="📘 Disciplinas")
    abas.add(frame_notas, text="📊 Notas")
    abas.add(frame_frequencia, text="📅 Frequência")
    abas.add(frame_atestados, text="📎 Atestados")
    abas.add(frame_cadastro, text="👤 Meu Cadastro")
    abas.pack(expand=True, fill="both", padx=6, pady=6)

    # Disciplinas
    tk.Label(frame_disciplinas, text="Disciplinas Matriculadas", font=("Arial", 12, "bold")).pack(pady=8)
    lista_disc = tk.Listbox(frame_disciplinas, width=80, height=8)
    lista_disc.pack(pady=6, padx=8)
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id, nome FROM disciplinas")
    disciplinas = c.fetchall()
    conn.close()
    if disciplinas:
        for d in disciplinas:
            lista_disc.insert(tk.END, d[1])
    else:
        lista_disc.insert(tk.END, "Nenhuma disciplina cadastrada.")

    # Notas
    tk.Label(frame_notas, text="Minhas Notas", font=("Arial", 12, "bold")).pack(pady=8)
    tree_notas = ttk.Treeview(frame_notas, columns=("disciplina", "nota"), show="headings", height=8)
    tree_notas.heading("disciplina", text="Disciplina")
    tree_notas.heading("nota", text="Nota")
    tree_notas.pack(pady=6, fill="both", padx=8)
    conn = conectar(); c = conn.cursor()
    c.execute("""
        SELECT d.nome, n.nota
        FROM notas n
        JOIN disciplinas d ON n.disciplina_id = d.id
        WHERE n.aluno_id = ?
    """, (id_aluno,))
    linhas = c.fetchall()
    conn.close()
    if linhas:
        for l in linhas:
            tree_notas.insert("", tk.END, values=l)
    else:
        tree_notas.insert("", tk.END, values=("Nenhuma nota disponível", ""))

    # Frequência
    tk.Label(frame_frequencia, text="Faltas e Frequência", font=("Arial", 12, "bold")).pack(pady=8)
    tree_freq = ttk.Treeview(frame_frequencia, columns=("disciplina", "presencas", "faltas", "frequencia"), show="headings", height=8)
    for col in tree_freq["columns"]:
        tree_freq.heading(col, text=col.capitalize())
    tree_freq.pack(pady=6, fill="both", padx=8)
    conn = conectar(); c = conn.cursor()
    c.execute("""
        SELECT d.nome, f.presencas, f.faltas,
               CASE WHEN (f.presencas + f.faltas)=0 THEN '0%'
               ELSE ROUND((CAST(f.presencas AS FLOAT) / (f.presencas + f.faltas)) * 100, 1) || '%' END
        FROM frequencia f
        JOIN disciplinas d ON f.disciplina_id = d.id
        WHERE f.aluno_id = ?
    """, (id_aluno,))
    linhas = c.fetchall()
    conn.close()
    if linhas:
        for l in linhas:
            tree_freq.insert("", tk.END, values=l)
    else:
        tree_freq.insert("", tk.END, values=("Nenhum registro", "", "", ""))

    # Atestados
    tk.Label(frame_atestados, text="Envio de Atestados Médicos", font=("Arial", 12, "bold")).pack(pady=8)
    def enviar_atestado():
        arquivo = filedialog.askopenfilename(title="Selecione o Atestado", filetypes=[("PDF", "*.pdf"), ("Imagens", "*.png;*.jpg;*.jpeg")])
        if not arquivo:
            return
        nome_arquivo = os.path.basename(arquivo)
        os.makedirs("atestados", exist_ok=True)
        destino = os.path.join("atestados", f"{ra}_{nome_arquivo}")
        with open(arquivo, "rb") as origem, open(destino, "wb") as dest:
            dest.write(origem.read())
        messagebox.showinfo("Sucesso", "Atestado enviado com sucesso.")
        lista_atestados.insert(tk.END, nome_arquivo)

    tk.Button(frame_atestados, text="📤 Enviar Atestado", bg="#4CAF50", fg="white", command=enviar_atestado).pack(pady=6)
    lista_atestados = tk.Listbox(frame_atestados, width=80, height=8)
    lista_atestados.pack(pady=6, padx=8)
    if os.path.exists("atestados"):
        for f in os.listdir("atestados"):
            if f.startswith(f"{ra}_"):
                lista_atestados.insert(tk.END, f)

    # Meu Cadastro
    tk.Label(frame_cadastro, text="Atualizar Meus Dados", font=("Arial", 12, "bold")).pack(pady=8)
    tk.Label(frame_cadastro, text="Nome completo:").pack()
    entry_nome = tk.Entry(frame_cadastro, width=60)
    entry_nome.insert(0, nome)
    entry_nome.pack(pady=4)
    tk.Label(frame_cadastro, text="E-mail institucional:").pack()
    entry_email = tk.Entry(frame_cadastro, width=60)
    entry_email.insert(0, email or "")
    entry_email.pack(pady=4)
    tk.Label(frame_cadastro, text="Nova senha (5 dígitos):").pack()
    entry_senha = tk.Entry(frame_cadastro, show="*", width=20)
    entry_senha.insert(0, senha)
    entry_senha.pack(pady=4)

    def salvar_cadastro():
        novo_nome = entry_nome.get().strip()
        novo_email = entry_email.get().strip()
        nova_senha = entry_senha.get().strip()
        if not novo_nome or not novo_email or not nova_senha:
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return
        if not nova_senha.isdigit() or len(nova_senha) != 5:
            messagebox.showerror("Erro", "Senha precisa ter 5 dígitos numéricos.")
            return
        if "@unip.edu.br" not in novo_email:
            messagebox.showerror("Erro", "E-mail institucional inválido (use @unip.edu.br).")
            return
        conn = conectar(); c = conn.cursor()
        c.execute("UPDATE alunos SET nome=?, email=?, senha=? WHERE id=?", (novo_nome, novo_email, nova_senha, id_aluno))
        conn.commit(); conn.close()
        messagebox.showinfo("Sucesso", "Dados atualizados. Reinicie o login para ver alterações.")
        aluno_win.destroy()

    tk.Button(frame_cadastro, text="Salvar Alterações", bg="#4CAF50", fg="white", command=salvar_cadastro).pack(pady=12)

    # Análise IA (usa analyze_student(conn, student_id))
    def abrir_ia():
        conn = conectar()
        try:
            resultado = analyze_student(conn, id_aluno)
        finally:
            conn.close()

        ia_win = tk.Toplevel(aluno_win)
        ia_win.title("Análise Inteligente (IA)")
        ia_win.geometry("600x500")
        tk.Label(ia_win, text="Relatório de Análise de Desempenho", font=("Arial", 14, "bold")).pack(pady=8)

        media = resultado.get("overall_media")
        media_disc = resultado.get("overall_media_disc")
        total_pres = resultado.get("total_presencas", 0)
        total_falt = resultado.get("total_faltas", 0)
        risco = resultado.get("risco", "—")
        rec = resultado.get("recomendacao", "")

        resumo_text = f"Média geral (todas as notas): {media if media is not None else '—'}\n"
        resumo_text += f"Média média por disciplina: {media_disc if media_disc is not None else '—'}\n"
        resumo_text += f"Total presenças: {total_pres}    Total faltas: {total_falt}\n"
        resumo_text += f"Risco: {risco}\n\nRecomendações:\n{rec}\n\nDetalhes por disciplina:\n"

        txt = tk.Text(ia_win, wrap="word", width=70, height=20)
        txt.insert("1.0", resumo_text)
        for d in resultado.get("details", []):
            d_nome = d.get("disciplina")
            d_media = d.get("media_disciplina")
            d_pres = d.get("presencas", 0)
            d_falt = d.get("faltas", 0)
            d_freq = d.get("frequencia_pct")
            d_flags = ", ".join(d.get("flags", [])) or "OK"
            txt.insert(tk.END, f"\n- {d_nome} — média: {d_media if d_media is not None else '—'}, presenças: {d_pres}, faltas: {d_falt}, frequência: {d_freq if d_freq is not None else '—'}, flags: {d_flags}")
        txt.configure(state="disabled")
        txt.pack(padx=8, pady=8, fill="both", expand=True)

    tk.Button(aluno_win, text="🔎 Análise Inteligente (IA)", bg="#FF9800", fg="white", command=abrir_ia).pack(pady=8)

    # Chat button (opens chat with professor id 1)
    try:
        from chat.chat import abrir_chat
        tk.Button(aluno_win, text="💬 Chat com Professor", bg="#009688", fg="white",
                  command=lambda: abrir_chat("aluno", id_aluno, "professor", 1, nome)).pack(pady=6)
    except Exception:
        pass
