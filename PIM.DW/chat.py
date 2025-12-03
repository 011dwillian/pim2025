# chat/chat.py
import tkinter as tk
from tkinter import scrolledtext, messagebox
from .database import conectar
import datetime

def abrir_chat(usuario_tipo, usuario_id, parceiro_tipo, parceiro_id, nome_usuario):
    janela = tk.Toplevel()
    janela.title(f"Chat - {nome_usuario}")
    janela.geometry("600x450")

    tk.Label(janela, text=f"Chat - {usuario_tipo.capitalize()}: {nome_usuario}", font=("Arial", 12, "bold")).pack(pady=6)

    area = scrolledtext.ScrolledText(janela, wrap=tk.WORD, width=80, height=20, state='disabled')
    area.pack(padx=10, pady=6)

    entry = tk.Entry(janela, width=70)
    entry.pack(side=tk.LEFT, padx=10, pady=6)

    def enviar():
        txt = entry.get().strip()
        if not txt:
            return
        ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        conn = conectar(); c = conn.cursor()
        c.execute("INSERT INTO chat (remetente_tipo, remetente_id, destinatario_tipo, destinatario_id, mensagem, data) VALUES (?, ?, ?, ?, ?, ?)",
                  (usuario_tipo, usuario_id, parceiro_tipo, parceiro_id, txt, ts))
        conn.commit(); conn.close()
        area.configure(state='normal')
        area.insert(tk.END, f"Você ({ts}): {txt}\n")
        area.configure(state='disabled')
        entry.delete(0, tk.END)

        # resposta simples automatizada (pode ser substituída por IA depois)
        if "nota" in txt.lower():
            area.configure(state='normal'); area.insert(tk.END, f"🤖 IA: Verifique a aba de Notas para detalhes.\n"); area.configure(state='disabled')

    tk.Button(janela, text="Enviar", command=enviar).pack(side=tk.LEFT, padx=6, pady=6)

    # Carregar histórico
    conn = conectar(); c = conn.cursor()
    c.execute("""
        SELECT remetente_tipo, mensagem, data
        FROM chat
        WHERE (remetente_tipo=? AND remetente_id=? AND destinatario_tipo=? AND destinatario_id=?)
           OR (remetente_tipo=? AND remetente_id=? AND destinatario_tipo=? AND destinatario_id=?)
        ORDER BY id
    """, (usuario_tipo, usuario_id, parceiro_tipo, parceiro_id, parceiro_tipo, parceiro_id, usuario_tipo, usuario_id))
    msgs = c.fetchall(); conn.close()
    area.configure(state='normal')
    for remetente, mensagem, data in msgs:
        quem = "Você" if remetente == usuario_tipo else "Outro"
        area.insert(tk.END, f"{quem} ({data}): {mensagem}\n")
    area.configure(state='disabled')
