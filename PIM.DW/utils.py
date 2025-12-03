# utils.py
def validar_ra(ra):
    """RA: exatamente 7 caracteres alfanuméricos (sem símbolos)."""
    return isinstance(ra, str) and len(ra) == 7 and ra.isalnum()

def validar_senha(senha):
    """Senha: exatamente 5 dígitos numéricos."""
    return isinstance(senha, str) and len(senha) == 5 and senha.isdigit()

def validar_email_institucional(email):
    """Valida e-mail institucional da UNIP (simples)."""
    return isinstance(email, str) and email.endswith("@unip.edu.br")
