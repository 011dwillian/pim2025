# analyze IA module
from collections import defaultdict

def _mean(values):
    return sum(values) / len(values) if values else None

def analyze_student(conn, student_id):
    """
    Recebe conexão sqlite3 (conn) e id do aluno.
    Retorna um dict com detalhes por disciplina e resumo global.
    """
    c = conn.cursor()

    # notas por disciplina
    c.execute("""
        SELECT d.id, d.nome, n.nota
        FROM notas n
        JOIN disciplinas d ON n.disciplina_id = d.id
        WHERE n.aluno_id = ?
    """, (student_id,))
    rows = c.fetchall()
    notas_por_disc = defaultdict(list)
    nome_by_id = {}
    for disc_id, disc_nome, nota in rows:
        if nota is not None:
            notas_por_disc[disc_id].append(float(nota))
        nome_by_id[disc_id] = disc_nome

    # frequencia por disciplina
    c.execute("SELECT disciplina_id, presencas, faltas FROM frequencia WHERE aluno_id = ?", (student_id,))
    freq_rows = c.fetchall()
    freq_by_disc = {r[0]: (r[1] or 0, r[2] or 0) for r in freq_rows}

    details = []
    all_notes = []
    medias_por_disc = []
    total_pres = 0
    total_falt = 0
    disc_ids = set(list(notas_por_disc.keys()) + list(freq_by_disc.keys()))
    for disc_id in disc_ids:
        notas = notas_por_disc.get(disc_id, [])
        pres, falt = freq_by_disc.get(disc_id, (0, 0))
        nome = nome_by_id.get(disc_id, f"Disciplina {disc_id}")
        media_disc = round(_mean(notas), 2) if notas else None
        if media_disc is not None:
            medias_por_disc.append(media_disc)
            all_notes.extend(notas)
        total_pres += pres
        total_falt += falt
        frequencia_pct = None
        if pres + falt > 0:
            frequencia_pct = round((pres / (pres + falt)) * 100, 1)
        flags = []
        if media_disc is None:
            flags.append("sem notas")
        else:
            if media_disc < 5.0:
                flags.append("nota muito baixa")
            elif media_disc < 6.0:
                flags.append("nota baixa")
        if frequencia_pct is not None and frequencia_pct < 75.0:
            flags.append("falta alta")
        details.append({
            "disciplina_id": disc_id,
            "disciplina": nome,
            "notas": notas,
            "media_disciplina": media_disc,
            "presencas": pres,
            "faltas": falt,
            "frequencia_pct": frequencia_pct,
            "flags": flags
        })

    overall_media = round(_mean(all_notes), 2) if all_notes else None
    overall_media_disc = round(_mean(medias_por_disc), 2) if medias_por_disc else None

    risco = "BAIXO"
    recomendacoes = []
    if overall_media is not None and overall_media < 6.0:
        risco = "ALTO"
        recomendacoes.append("Média geral abaixo de 6.0 — atenção.")
    elif overall_media is not None and 6.0 <= overall_media < 7.0:
        risco = "MÉDIO"
        recomendacoes.append("Média entre 6.0 e 7.0 — revisar conteúdos.")

    if total_falt > 10:
        risco = "ALTO"
        recomendacoes.append("Faltas altas — verificar documentação (atestados).")

    disc_warns = [d for d in details if d["flags"]]
    if disc_warns:
        recomendacoes.append(f"{len(disc_warns)} disciplina(s) com flags.")

    if not recomendacoes:
        recomendacoes.append("Bom desempenho — manter ritmo de estudos.")

    return {
        "details": details,
        "overall_media": overall_media,
        "overall_media_disc": overall_media_disc,
        "total_presencas": total_pres,
        "total_faltas": total_falt,
        "risco": risco,
        "recomendacao": " ".join(recomendacoes)
    }
