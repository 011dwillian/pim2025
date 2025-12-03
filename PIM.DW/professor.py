# professor.py
import tkinter as tk
from tkinter import ttk, messagebox
from database import conectar
import sqlite3

def tela_professor(dados_prof):
    """
    dados_prof: tupla (id, nome, email, senha, disciplina)
    """
    id_prof, nome, email, senha, disciplina = dados_prof

    prof_win = tk.Toplevel()
    prof_win.title(f"Área do Professor - {nome}")
    prof_win.geometry("800x550")

    tk.Label(prof_win, text=f"Bem-vindo, Prof. {nome}", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(prof_win, text=f"Disciplina: {disciplina} | E-mail: {email}", font=("Arial", 10)).pack(pady=5)

    abas = ttk.Notebook(prof_win)
    frame_notas = ttk.Frame(abas)
    frame_faltas = ttk.Frame(abas)
    frame_cronograma = ttk.Frame(abas)
    frame_cadastro = ttk.Frame(abas)

    abas.add(frame_notas, text="📊 Gerenciar Notas")
    abas.add(frame_faltas, text="📅 Faltas e Presença")
    abas.add(frame_cronograma, text="🗓️ Cronograma")
    abas.add(frame_cadastro, text="👤 Meu Cadastro")
    abas.pack(expand=True, fill="both")

    # Notas - listar
    tk.Label(frame_notas, text="Lançamento e Revisão de Notas", font=("Arial", 12, "bold")).pack(pady=10)
    tree_notas = ttk.Treeview(frame_notas, columns=("id", "aluno", "nota"), show="headings", height=8)
    tree_notas.heading("id", text="ID")
    tree_notas.heading("aluno", text="Aluno")
    tree_notas.heading("nota", text="Nota")
    tree_notas.pack(pady=5, fill="x")

    conn = conectar(); c = conn.cursor()
    c.execute("""
        SELECT n.id, a.nome, n.nota
        FROM notas n
        JOIN alunos a ON n.aluno_id = a.id
        WHERE n.disciplina = ?
    """, (disciplina,))
    notas = c.fetchall()
    conn.close()
    for n in notas:
        tree_notas.insert("", tk.END, values=n)

    tk.Label(frame_notas, text="Nova Nota:").pack()
    entry_nota = tk.Entry(frame_notas)
    entry_nota.pack(pady=5)

    def atualizar_nota():
        sel = tree_notas.selection()
        if not sel:
            messagebox.showerror("Erro", "Selecione um aluno.")
            return
        item = sel[0]
        nova = entry_nota.get().strip()
        try:
            nova_val = float(nova)
        except:
            messagebox.showerror("Erro", "Nota inválida.")
            return
        conn = conectar(); c = conn.cursor()
        nota_id = tree_notas.item(item)['values'][0]
        c.execute("UPDATE notas SET nota=? WHERE id=?", (nova_val, nota_id))
        conn.commit(); conn.close()
        tree_notas.item(item, values=(nota_id, tree_notas.item(item)['values'][1], nova_val))
        messagebox.showinfo("Sucesso", "Nota atualizada.")

    tk.Button(frame_notas, text="Salvar Alteração", bg="#4CAF50", fg="white", command=atualizar_nota).pack(pady=8)

    # Faltas - listar e atualizar
    tk.Label(frame_faltas, text="Gerenciar Faltas e Presença", font=("Arial", 12, "bold")).pack(pady=10)
    tree_faltas = ttk.Treeview(frame_faltas, columns=("id", "aluno", "presencas", "faltas"), show="headings", height=8)
    for col in tree_faltas["columns"]:
        tree_faltas.heading(col, text=col.capitalize())
    tree_faltas.pack(pady=5, fill="x")

    conn = conectar(); c = conn.cursor()
    c.execute("""
        SELECT f.id, a.nome, f.presencas, f.faltas
        FROM frequencia f
        JOIN alunos a ON f.aluno_id = a.id
        WHERE f.disciplina_id IN (SELECT id FROM disciplinas WHERE nome = ?)
    """, (disciplina,))
    faltas = c.fetchall()
    conn.close()
    for f in faltas:
        tree_faltas.insert("", tk.END, values=f)

    tk.Label(frame_faltas, text="Nova quantidade de faltas:").pack()
    entry_falta = tk.Entry(frame_faltas)
    entry_falta.pack(pady=5)

    def atualizar_faltas():
        sel = tree_faltas.selection()
        if not sel:
            messagebox.showerror("Erro", "Selecione um aluno.")
            return
        item = sel[0]
        novas = entry_falta.get().strip()
        if not novas.isdigit():
            messagebox.showerror("Erro", "Quantidade inválida.")
            return
        conn = conectar(); c = conn.cursor()
        freq_id = tree_faltas.item(item)['values'][0]
        c.execute("UPDATE frequencia SET faltas=? WHERE id=?", (int(novas), freq_id))
        conn.commit(); conn.close()
        tree_faltas.item(item, values=(tree_faltas.item(item)['values'][0], tree_faltas.item(item)['values'][1], tree_faltas.item(item)['values'][2], int(novas)))
        messagebox.showinfo("Sucesso", "Faltas atualizadas.")

    tk.Button(frame_faltas, text="Salvar Alterações", bg="#2196F3", fg="white", command=atualizar_faltas).pack(pady=8)

    # Cronograma
    tk.Label(frame_cronograma, text="Cronograma de Aulas", font=("Arial", 12, "bold")).pack(pady=10)
    lista_crono = tk.Listbox(frame_cronograma, width=90, height=8)
    lista_crono.pack(pady=5)
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT c.conteudo FROM cronograma c JOIN disciplinas d ON c.disciplina_id = d.id WHERE d.nome = ?", (disciplina,))
    linhas = c.fetchall()
    conn.close()
    for l in linhas:
        lista_crono.insert(tk.END, l[0])

    tk.Label(frame_cronograma, text="Adicionar conteúdo:").pack()
    entry_crono = tk.Entry(frame_cronograma, width=80)
    entry_crono.pack(pady=4)

    def adicionar_cronograma():
        conteudo = entry_crono.get().strip()
        if not conteudo:
            messagebox.showerror("Erro", "Digite o conteúdo.")
            return
        # buscar disciplina id
        conn = conectar(); c = conn.cursor()
        c.execute("SELECT id FROM disciplinas WHERE nome = ?", (disciplina,))
        disc_row = c.fetchone()
        if not disc_row:
            messagebox.showerror("Erro", "Disciplina não encontrada.")
            conn.close(); return
        disc_id = disc_row[0]
        c.execute("INSERT INTO cronograma (disciplina_id, conteudo, data) VALUES (?, ?, date('now'))", (disc_id, conteudo))
        conn.commit(); conn.close()
        lista_crono.insert(tk.END, conteudo)
        entry_crono.delete(0, tk.END)
        messagebox.showinfo("Sucesso", "Conteúdo adicionado.")

    tk.Button(frame_cronograma, text="Adicionar", bg="#4CAF50", fg="white", command=adicionar_cronograma).pack(pady=8)

    # Meu Cadastro
    tk.Label(frame_cadastro, text="Atualizar Meus Dados", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(frame_cadastro, text="Nome completo:").pack()
    entry_nome = tk.Entry(frame_cadastro); entry_nome.insert(0, nome); entry_nome.pack(pady=4)
    tk.Label(frame_cadastro, text="E-mail institucional:").pack()
    entry_email = tk.Entry(frame_cadastro); entry_email.insert(0, email); entry_email.pack(pady=4)
    tk.Label(frame_cadastro, text="Nova senha (5 dígitos):").pack()
    entry_senha = tk.Entry(frame_cadastro, show="*"); entry_senha.insert(0, senha); entry_senha.pack(pady=4)

    def salvar_dados_prof():
        novo_nome = entry_nome.get().strip()
        novo_email = entry_email.get().strip()
        nova_senha = entry_senha.get().strip()
        if not novo_nome or not novo_email or not nova_senha:
            messagebox.showerror("Erro", "Preencha todos os campos.")
            return
        if "@unip.edu.br" not in novo_email:
            messagebox.showerror("Erro", "E-mail institucional inválido (use @unip.edu.br).")
            return
        if len(nova_senha) != 5 or not nova_senha.isdigit():
            messagebox.showerror("Erro", "A senha deve ter 5 dígitos numéricos.")
            return
        conn = conectar(); c = conn.cursor()
        c.execute("UPDATE professores SET nome=?, email=?, senha=? WHERE id=?", (novo_nome, novo_email, nova_senha, id_prof))
        conn.commit(); conn.close()
        messagebox.showinfo("Sucesso", "Dados atualizados. Reinicie o painel para ver alterações.")
        prof_win.destroy()

    tk.Button(frame_cadastro, text="Salvar Alterações", bg="#4CAF50", fg="white", command=salvar_dados_prof).pack(pady=12)

    # Chat button
    try:
        from chat.chat import abrir_chat
        tk.Button(prof_win, text="💬 Chat com Aluno", bg="#009688", fg="white",
                  command=lambda: abrir_chat("professor", id_prof, "aluno", 1, nome)).pack(pady=6)
    except Exception:
        pass
