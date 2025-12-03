import os

def criar_pasta(nome):
    if not os.path.exists(nome):
        os.makedirs(nome)
        print(f"[OK] Pasta criada: {nome}")
    else:
        print(f"[OK] Pasta já existia: {nome}")

# Estrutura básica do projeto PIM
pastas = [
    "src",
    "src/interface",
    "src/backend",
    "src/database",
    "assets",
    "assets/imagens",
    "docs",
]

for p in pastas:
    criar_pasta(p)

# Criar README.md
readme = """
# 📘 PIM 2025 - Sistema Acadêmico com Tkinter + SQLite + IA

Este repositório contém o projeto completo do sistema acadêmico desenvolvido em Python,
utilizando:

- **Tkinter** para interface gráfica
- **SQLite3** para banco de dados
- **Threading** e **async** quando necessário
- **Integração com assistente IA**
- **Controle de notas, faltas, ocorrências e permissões**
- **Perfis de Coordenador, Professor e Aluno**

---

## 📁 Estrutura criada automaticamente

