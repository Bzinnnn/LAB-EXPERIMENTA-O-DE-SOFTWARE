import re
from pathlib import Path

pdf_path = Path(r"enunciado02/LABORATÓRIO 02 - Um estudo das caracteristicas de qualidade de sistemas java.pdf")

reader = None
lib = None
try:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    lib = "pypdf"
except Exception:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        lib = "PyPDF2"
    except Exception as e:
        print("ERRO_IMPORT", repr(e))
        raise

pages = []
for i, p in enumerate(reader.pages):
    try:
        t = p.extract_text() or ""
    except Exception:
        t = ""
    pages.append(t)

full = "\n".join(pages)
full = full.replace("\r", "\n")
full = re.sub(r"\n{2,}", "\n", full)

print(f"LIB={lib}; PAGES={len(pages)}")


def section_between(start_pat, end_pats, text, flags=re.I|re.S):
    m = re.search(start_pat, text, flags)
    if not m:
        return None
    start = m.start()
    end = len(text)
    for ep in end_pats:
        m2 = re.search(ep, text[m.end():], flags)
        if m2:
            cand = m.end() + m2.start()
            if cand < end:
                end = cand
    return text[start:end]


def clean_snippet(s, max_chars=900):
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s).strip()
    return s[:max_chars]

# 1) cabeçalho/título e objetivo
print("\n=== 1) CABEÇALHO/TÍTULO E OBJETIVO ===")
head = "\n".join(full.splitlines()[:35])
print(clean_snippet(head, 1200))
obj = section_between(r"\bobjetivo\b", [r"\brequisitos\b", r"\bentreg[aá]veis\b", r"\brq0?1\b"], full)
if obj:
    print("\n[OBJETIVO]\n" + clean_snippet(obj, 1200))
else:
    print("\n[OBJETIVO] não encontrado por seção; linhas com 'objetivo':")
    for ln in full.splitlines():
        if re.search(r"objetivo", ln, re.I):
            print(ln.strip())

# 2) requisitos e entregáveis
print("\n=== 2) REQUISITOS E ENTREGÁVEIS ===")
for key in ["requisitos", "entregáveis", "entregaveis"]:
    print(f"\n[{key.upper()}]")
    block = section_between(rf"\b{key}\b", [r"\brq0?1\b", r"\bcrit[eé]rios? de avalia", r"\bavalia[çc][ãa]o\b"], full)
    if block:
        print(clean_snippet(block, 1500))
    else:
        found = False
        for ln in full.splitlines():
            if re.search(key, ln, re.I):
                print(ln.strip()); found = True
        if not found:
            print("(não localizado)")

# 3) RQ01-RQ04 literal
print("\n=== 3) RQ01-RQ04 (LITERAL) ===")
for rq in ["RQ01", "RQ02", "RQ03", "RQ04"]:
    m = re.search(rf"({rq}\s*[:\-–].{{0,600}})", full, re.I|re.S)
    if not m:
        m = re.search(rf"({rq}.{{0,600}})", full, re.I|re.S)
    print(f"\n[{rq}]")
    if m:
        print(clean_snippet(m.group(1), 900))
    else:
        print("(não encontrado)")

# 4) métricas/process metrics pedidas
print("\n=== 4) MÉTRICAS / PROCESS METRICS ===")
metric_lines = []
for ln in full.splitlines():
    if re.search(r"m[eé]trica|metrics|process metric|ckjm|lcom|wmc|dit|noc|cbo|rfc", ln, re.I):
        metric_lines.append(ln.strip())
uniq=[]
for l in metric_lines:
    if l and l not in uniq:
        uniq.append(l)
for l in uniq[:40]:
    print(l)
if not uniq:
    print("(não localizado)")

# 5) amostragem/coleta
print("\n=== 5) AMOSTRAGEM / COLETA ===")
sample_lines=[]
for ln in full.splitlines():
    if re.search(r"1000|mil|reposit[oó]rios|amostr|coleta|github|dataset|sele[cç][ãa]o", ln, re.I):
        sample_lines.append(ln.strip())
uniq2=[]
for l in sample_lines:
    if l and l not in uniq2:
        uniq2.append(l)
for l in uniq2[:40]:
    print(l)
if not uniq2:
    print("(não localizado)")

# 6) critérios de avaliação
print("\n=== 6) CRITÉRIOS DE AVALIAÇÃO ===")
aval = section_between(r"crit[eé]rios? de avalia[çc][ãa]o|avalia[çc][ãa]o", [r"\brefer[eê]ncias\b", r"\banexo\b", r"\bfim\b"], full)
if aval:
    print(clean_snippet(aval, 1600))
else:
    for ln in full.splitlines():
        if re.search(r"avalia[çc][ãa]o|nota|pontua", ln, re.I):
            print(ln.strip())
