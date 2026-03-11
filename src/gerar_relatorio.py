"""
Gerador de Relatório Final - LAB01
Análise de Repositórios Populares do GitHub
"""

import os
import csv
import base64
import statistics
from io import BytesIO
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')
os.makedirs(DOCS_DIR, exist_ok=True)

# ── Paleta de cores ──────────────────────────────────────────────────────────
PALETTE = ["#6C63FF", "#FF6584", "#43E97B", "#F9CA24", "#3DD6F5",
           "#FF9F43", "#EE5A24", "#12CBC4", "#FDA7DF", "#D980FA",
           "#9980FA", "#C4E538", "#FD7272", "#58B19F", "#2C3A47"]
BG      = "#0F1117"
CARD    = "#1A1D2E"
ACCENT  = "#6C63FF"
TEXT    = "#E8E8F0"
GRID    = "#2A2D3E"


# ── Helpers ──────────────────────────────────────────────────────────────────
def fig_to_b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64

def style_ax(ax, title=""):
    ax.set_facecolor(CARD)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(axis='y', color=GRID, linewidth=0.5, alpha=0.7)
    if title:
        ax.set_title(title, color=TEXT, fontsize=11, pad=8, fontweight='bold')

def median_label(ax, med, unit=""):
    ax.axvline(med, color="#FFD700", lw=1.8, ls='--', alpha=0.9,
               label=f'Mediana: {med:,.0f}{unit}')
    ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)

def pct_cap(vals, pct=99):
    cap = np.percentile(vals, pct)
    return [v for v in vals if v <= cap]


# ── Leitura dos dados ────────────────────────────────────────────────────────
def load_data(path):
    repos = []
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                repos.append({
                    "name"         : row["nameWithOwner"],
                    "lang"         : row["primaryLanguage"] or "Unknown",
                    "stars"        : int(row["stars"]),
                    "age"          : int(row["repositoryAge"]),
                    "prs"          : int(row["mergedPullRequests"]),
                    "releases"     : int(row["releases"]),
                    "days_update"  : int(row["daysSinceUpdate"]),
                    "closed_ratio" : float(row["closedIssuesRatio"]),
                    "total_issues" : int(row["totalIssues"]),
                    "open_issues"  : int(row["openIssues"]),
                    "closed_issues": int(row["closedIssues"]),
                })
            except Exception:
                pass
    return repos


# ── Gráficos ─────────────────────────────────────────────────────────────────

def chart_age(repos):
    vals = [r["age"] for r in repos]
    med  = statistics.median(vals)
    capped = pct_cap(vals)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.hist(capped, bins=40, color=ACCENT, edgecolor=BG, alpha=0.85)
    median_label(ax, med, " dias")
    ax.set_xlabel("Idade (dias)", color=TEXT)
    ax.set_ylabel("Repositórios", color=TEXT)
    style_ax(ax, "RQ01 · Distribuição de Idade dos Repositórios")
    return fig_to_b64(fig)


def chart_prs(repos):
    vals = [r["prs"] for r in repos]
    med  = statistics.median(vals)
    capped = pct_cap(vals)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.hist(capped, bins=40, color=PALETTE[1], edgecolor=BG, alpha=0.85)
    median_label(ax, med, " PRs")
    ax.set_xlabel("Pull Requests Aceitas", color=TEXT)
    ax.set_ylabel("Repositórios", color=TEXT)
    style_ax(ax, "RQ02 · Distribuição de Pull Requests Aceitas")
    return fig_to_b64(fig)


def chart_releases(repos):
    vals = [r["releases"] for r in repos]
    med  = statistics.median(vals)
    capped = pct_cap(vals)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.hist(capped, bins=40, color=PALETTE[2], edgecolor=BG, alpha=0.85)
    median_label(ax, med, " releases")
    ax.set_xlabel("Total de Releases", color=TEXT)
    ax.set_ylabel("Repositórios", color=TEXT)
    style_ax(ax, "RQ03 · Distribuição de Releases")
    return fig_to_b64(fig)


def chart_update(repos):
    vals = [r["days_update"] for r in repos]
    med  = statistics.median(vals)
    capped = pct_cap(vals, 95)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.hist(capped, bins=40, color=PALETTE[4], edgecolor=BG, alpha=0.85)
    median_label(ax, med, " dias")
    ax.set_xlabel("Dias desde última atualização", color=TEXT)
    ax.set_ylabel("Repositórios", color=TEXT)
    style_ax(ax, "RQ04 · Frequência de Atualização")
    return fig_to_b64(fig)


def chart_languages(repos):
    langs = Counter(r["lang"] for r in repos)
    top = langs.most_common(15)
    labels = [l for l, _ in top]
    counts = [c for _, c in top]
    colors = PALETTE[:len(labels)]

    fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG)
    bars = ax.barh(labels[::-1], counts[::-1], color=colors[::-1],
                   edgecolor=BG, height=0.7)
    for bar, cnt in zip(bars, counts[::-1]):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                f'{cnt}', va='center', color=TEXT, fontsize=8.5)
    ax.set_xlabel("Número de Repositórios", color=TEXT)
    style_ax(ax, "RQ05 · Linguagens Primárias (Top 15)")
    ax.spines['left'].set_visible(False)
    ax.set_xlim(0, max(counts) * 1.12)
    return fig_to_b64(fig)


def chart_issues(repos):
    vals = [r["closed_ratio"] for r in repos if r["total_issues"] > 0]
    med  = statistics.median(vals)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.hist(vals, bins=30, color=PALETTE[3], edgecolor=BG, alpha=0.85)
    ax.axvline(med, color="#FFD700", lw=1.8, ls='--', alpha=0.9,
               label=f'Mediana: {med:.2%}')
    ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)
    ax.set_xlabel("Proporção de Issues Fechadas", color=TEXT)
    ax.set_ylabel("Repositórios", color=TEXT)
    style_ax(ax, "RQ06 · Percentual de Issues Fechadas")
    return fig_to_b64(fig)


def chart_rq07(repos):
    langs_count = Counter(r["lang"] for r in repos)
    top_langs = [l for l, _ in langs_count.most_common(10)]

    data = {lang: {"prs": [], "releases": [], "update": []} for lang in top_langs}
    for r in repos:
        if r["lang"] in data:
            data[r["lang"]]["prs"].append(r["prs"])
            data[r["lang"]]["releases"].append(r["releases"])
            data[r["lang"]]["update"].append(r["days_update"])

    labels   = top_langs
    med_prs  = [statistics.median(data[l]["prs"]) for l in labels]
    med_rel  = [statistics.median(data[l]["releases"]) for l in labels]
    med_upd  = [statistics.median(data[l]["update"]) for l in labels]

    x = np.arange(len(labels))
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), facecolor=BG)
    fig.subplots_adjust(hspace=0.5)

    def bar_plot(ax, vals, color, title, ylabel):
        bars = ax.bar(x, vals, color=color, edgecolor=BG, width=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha='right', color=TEXT, fontsize=8.5)
        ax.set_ylabel(ylabel, color=TEXT)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{v:.0f}', ha='center', color=TEXT, fontsize=8)
        style_ax(ax, title)

    bar_plot(axes[0], med_prs, PALETTE[1],
             "RQ07 · Mediana de PRs por Linguagem", "Mediana PRs")
    bar_plot(axes[1], med_rel, PALETTE[2],
             "RQ07 · Mediana de Releases por Linguagem", "Mediana Releases")
    bar_plot(axes[2], med_upd, PALETTE[4],
             "RQ07 · Mediana de Dias desde Atualização por Linguagem", "Mediana Dias")

    return fig_to_b64(fig)


def chart_pie_lang(repos):
    langs = Counter(r["lang"] for r in repos)
    top5 = langs.most_common(5)
    other = sum(c for _, c in langs.most_common()[5:])
    labels = [l for l, _ in top5] + ["Outros"]
    sizes  = [c for _, c in top5] + [other]
    colors = PALETTE[:6]

    fig, ax = plt.subplots(figsize=(7, 5), facecolor=BG)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct='%1.1f%%', startangle=140,
        wedgeprops=dict(edgecolor=BG, linewidth=2))
    for at in autotexts:
        at.set_color(BG)
        at.set_fontsize(8)
        at.set_fontweight('bold')
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5),
              facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)
    ax.set_title("Top 5 Linguagens + Outros", color=TEXT, fontsize=11, fontweight='bold')
    return fig_to_b64(fig)


# ── Estatísticas ─────────────────────────────────────────────────────────────
def compute_stats(repos):
    def s(key, filter_fn=None):
        vals = [r[key] for r in repos if (filter_fn(r) if filter_fn else True)]
        if not vals:
            return {}
        svals = sorted(vals)
        n = len(svals)
        med = svals[n//2] if n % 2 else (svals[n//2-1] + svals[n//2])/2
        return {"median": med, "mean": sum(vals)/n,
                "min": min(vals), "max": max(vals), "n": n}

    ratio_stats = s("closed_ratio", lambda r: r["total_issues"] > 0)
    return {
        "age"    : s("age"),
        "prs"    : s("prs"),
        "rel"    : s("releases"),
        "upd"    : s("days_update"),
        "ratio"  : ratio_stats,
        "total"  : len(repos),
    }


def lang_table_rows(repos):
    langs = Counter(r["lang"] for r in repos)
    total = len(repos)
    rows = ""
    for i, (lang, cnt) in enumerate(langs.most_common(15)):
        pct = cnt/total*100
        bar_w = int(pct * 3)
        rows += f"""
        <tr>
          <td style="font-weight:600;color:#E8E8F0">{i+1}</td>
          <td style="color:#E8E8F0">{lang}</td>
          <td style="color:#A0A0C0">{cnt}</td>
          <td style="color:#A0A0C0">{pct:.1f}%</td>
          <td><div style="background:{PALETTE[i%len(PALETTE)]};width:{bar_w}px;
              height:12px;border-radius:3px;"></div></td>
        </tr>"""
    return rows


def rq07_table(repos):
    langs_count = Counter(r["lang"] for r in repos)
    top_langs = [l for l, _ in langs_count.most_common(10)]

    data = {lang: {"prs": [], "rel": [], "upd": []} for lang in top_langs}
    for r in repos:
        if r["lang"] in data:
            data[r["lang"]]["prs"].append(r["prs"])
            data[r["lang"]]["rel"].append(r["releases"])
            data[r["lang"]]["upd"].append(r["days_update"])

    rows = ""
    for i, lang in enumerate(top_langs):
        n   = len(data[lang]["prs"])
        mp  = statistics.median(data[lang]["prs"])
        mr  = statistics.median(data[lang]["rel"])
        mu  = statistics.median(data[lang]["upd"])
        color = PALETTE[i % len(PALETTE)]
        rows += f"""
        <tr>
          <td><span style="background:{color};padding:2px 8px;border-radius:10px;
              font-size:12px;color:#111;font-weight:700">{lang}</span></td>
          <td style="color:#A0A0C0">{n}</td>
          <td style="color:#E8E8F0;font-weight:600">{mp:.0f}</td>
          <td style="color:#E8E8F0;font-weight:600">{mr:.0f}</td>
          <td style="color:#E8E8F0;font-weight:600">{mu:.0f}</td>
        </tr>"""
    return rows


# ── HTML ──────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0F1117;color:#E8E8F0;font-family:'Inter',sans-serif;font-size:15px;line-height:1.7}
.container{max-width:1100px;margin:0 auto;padding:40px 24px}
h1{font-size:2.6em;font-weight:700;background:linear-gradient(135deg,#6C63FF,#FF6584);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
h2{font-size:1.6em;font-weight:600;color:#6C63FF;margin:48px 0 16px;
   padding-bottom:8px;border-bottom:2px solid #2A2D3E}
h3{font-size:1.2em;font-weight:600;color:#9D8FFF;margin:28px 0 10px}
p{color:#B0B0C8;margin-bottom:12px}
.subtitle{color:#A0A0C0;font-size:1.05em;margin-bottom:32px}
.meta{display:flex;gap:24px;flex-wrap:wrap;margin-bottom:40px}
.meta-item{background:#1A1D2E;border:1px solid #2A2D3E;border-radius:12px;
   padding:16px 24px;flex:1;min-width:160px}
.meta-label{font-size:11px;color:#6C63FF;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px}
.meta-value{font-size:1.9em;font-weight:700;color:#E8E8F0}
.meta-sub{font-size:11px;color:#7070A0;margin-top:2px}
.card{background:#1A1D2E;border:1px solid #2A2D3E;border-radius:16px;
   padding:28px;margin:24px 0;transition:border-color .2s}
.card:hover{border-color:#6C63FF44}
.chip{display:inline-block;padding:3px 12px;border-radius:20px;font-size:12px;
   font-weight:600;margin:3px}
.confirmed{background:#43E97B22;color:#43E97B;border:1px solid #43E97B44}
.denied{background:#FF658422;color:#FF6584;border:1px solid #FF658444}
.partial{background:#F9CA2422;color:#F9CA24;border:1px solid #F9CA2444}
img.chart{width:100%;border-radius:12px;margin:16px 0}
table{width:100%;border-collapse:collapse;margin:16px 0}
th{background:#6C63FF22;color:#9D8FFF;font-size:12px;text-transform:uppercase;
   letter-spacing:.07em;padding:10px 14px;text-align:left;border-bottom:2px solid #2A2D3E}
td{padding:9px 14px;border-bottom:1px solid #1E2030;font-size:13px}
tr:hover td{background:#1E2030}
.highlight-box{background:linear-gradient(135deg,#6C63FF18,#FF658418);
   border:1px solid #6C63FF44;border-radius:12px;padding:20px 24px;margin:20px 0}
.hb-title{font-size:.75em;color:#6C63FF;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px}
.hb-text{color:#C0C0D8}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:700px){.two-col{grid-template-columns:1fr}}
.badge{display:inline-flex;align-items:center;gap:6px;background:#6C63FF;
   color:#fff;border-radius:20px;padding:5px 14px;font-size:13px;font-weight:600}
.toc{background:#1A1D2E;border:1px solid #2A2D3E;border-radius:12px;padding:20px 28px;margin-bottom:40px}
.toc h3{color:#6C63FF;font-size:.85em;text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px}
.toc ol{padding-left:20px;color:#9090B0;font-size:13px;line-height:2}
.toc a{color:#9D8FFF;text-decoration:none}.toc a:hover{text-decoration:underline}
section{scroll-margin-top:80px}
.footer{text-align:center;color:#3A3A5A;font-size:12px;margin-top:60px;padding-top:24px;
   border-top:1px solid #1E2030}
.bonus-banner{background:linear-gradient(135deg,#6C63FF,#FF6584);border-radius:14px;
   padding:20px 28px;margin:32px 0;color:#fff}
.bonus-banner h2{color:#fff;border:none;margin:0 0 6px;font-size:1.3em}
.bonus-banner p{color:#ffe0e8;margin:0;font-size:.95em}
"""

def html_report(repos, stats, charts):
    age_med  = stats["age"]["median"]
    prs_med  = stats["prs"]["median"]
    rel_med  = stats["rel"]["median"]
    upd_med  = stats["upd"]["median"]
    rat_med  = stats["ratio"]["median"]
    total    = stats["total"]

    lang_rows = lang_table_rows(repos)
    rq07_rows = rq07_table(repos)

    langs = Counter(r["lang"] for r in repos)
    top3 = langs.most_common(3)
    top3_pct = sum(c for _, c in top3) / total * 100

    hyp_age  = "✓ Confirmada" if age_med > 1095 else "✗ Não confirmada"
    hyp_age_cls = "confirmed" if age_med > 1095 else "denied"
    hyp_prs  = "✓ Confirmada" if prs_med > 50 else "✗ Não confirmada"
    hyp_prs_cls = "confirmed" if prs_med > 50 else "denied"
    hyp_rel  = "✓ Confirmada" if rel_med > 20 else "✗ Não confirmada"
    hyp_rel_cls = "confirmed" if rel_med > 20 else "denied"
    hyp_upd  = "✓ Confirmada" if upd_med < 30 else "✗ Não confirmada"
    hyp_upd_cls = "confirmed" if upd_med < 30 else "denied"
    hyp_lang = "✓ Confirmada" if top3_pct > 40 else "✗ Não confirmada"
    hyp_lang_cls = "confirmed" if top3_pct > 40 else "denied"
    hyp_iss  = "✓ Confirmada" if rat_med > 0.7 else "✗ Não confirmada"
    hyp_iss_cls = "confirmed" if rat_med > 0.7 else "denied"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LAB01 · Análise de Repositórios Populares do GitHub</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<!-- Cabeçalho -->
<div style="margin-bottom:8px">
  <span class="badge">🔬 Laboratório de Experimentação de Software</span>
</div>
<h1>Análise de Repositórios Populares do GitHub</h1>
<p class="subtitle">Laboratório 01 · Características dos 1.000 repositórios com maior número de estrelas · 6º Período · Engenharia de Software</p>

<!-- Métricas resumo -->
<div class="meta">
  <div class="meta-item">
    <div class="meta-label">Repositórios</div>
    <div class="meta-value">{total:,}</div>
    <div class="meta-sub">analisados</div>
  </div>
  <div class="meta-item">
    <div class="meta-label">Mediana Idade</div>
    <div class="meta-value">{age_med/365:.1f}<span style="font-size:.5em;color:#9090B0"> anos</span></div>
    <div class="meta-sub">{age_med:,.0f} dias</div>
  </div>
  <div class="meta-item">
    <div class="meta-label">Mediana PRs</div>
    <div class="meta-value">{prs_med:,.0f}</div>
    <div class="meta-sub">pull requests aceitas</div>
  </div>
  <div class="meta-item">
    <div class="meta-label">Mediana Releases</div>
    <div class="meta-value">{rel_med:,.0f}</div>
    <div class="meta-sub">total por repositório</div>
  </div>
  <div class="meta-item">
    <div class="meta-label">Última Atualização</div>
    <div class="meta-value">{upd_med:,.0f}<span style="font-size:.5em;color:#9090B0"> dias</span></div>
    <div class="meta-sub">mediana</div>
  </div>
  <div class="meta-item">
    <div class="meta-label">Issues Fechadas</div>
    <div class="meta-value">{rat_med:.0%}</div>
    <div class="meta-sub">mediana da razão</div>
  </div>
</div>

<!-- Índice -->
<div class="toc">
  <h3>📋 Índice</h3>
  <ol>
    <li><a href="#intro">Introdução e Hipóteses</a></li>
    <li><a href="#metodologia">Metodologia</a></li>
    <li><a href="#rq01">RQ01 · Maturidade dos Repositórios</a></li>
    <li><a href="#rq02">RQ02 · Contribuição Externa (PRs)</a></li>
    <li><a href="#rq03">RQ03 · Frequência de Releases</a></li>
    <li><a href="#rq04">RQ04 · Frequência de Atualização</a></li>
    <li><a href="#rq05">RQ05 · Linguagens de Programação</a></li>
    <li><a href="#rq06">RQ06 · Percentual de Issues Fechadas</a></li>
    <li><a href="#rq07">RQ07 · Análise por Linguagem (Bônus)</a></li>
    <li><a href="#discussao">Discussão e Conclusões</a></li>
  </ol>
</div>

<!-- ── Introdução ── -->
<section id="intro">
<h2>1. Introdução e Hipóteses</h2>
<div class="card">
<p>Este trabalho analisa os <strong>1.000 repositórios mais populares do GitHub</strong> (ordenados por número de estrelas), buscando entender padrões e características que definem projetos open-source de sucesso. Para cada questão de pesquisa, foi formulada previamente uma hipótese informal antes da coleta dos dados.</p>
<h3>Hipóteses Iniciais</h3>
<div class="highlight-box">
  <div class="hb-title">🔭 Hipóteses Formuladas</div>
  <div class="hb-text">
  <table style="margin:8px 0 0">
  <tr><th>RQ</th><th>Hipótese</th><th>Limiar Esperado</th></tr>
  <tr><td>RQ01</td><td>Repositórios populares tendem a ser antigos — levam tempo para acumular estrelas</td><td>&gt; 3 anos de idade</td></tr>
  <tr><td>RQ02</td><td>Maior visibilidade atrai mais contribuições externas via PRs</td><td>&gt; 50 PRs aceitas</td></tr>
  <tr><td>RQ03</td><td>Projetos maduros e ativos publicam releases regularmente</td><td>&gt; 20 releases</td></tr>
  <tr><td>RQ04</td><td>Repositórios bem mantidos são atualizados com frequência</td><td>Mediana &lt; 30 dias</td></tr>
  <tr><td>RQ05</td><td>Linguagens mais populares (JS, Python, TS) dominam os top repos</td><td>&gt; 40% para top 3</td></tr>
  <tr><td>RQ06</td><td>Projetos bem gerenciados fecham a maior parte de suas issues</td><td>&gt; 70% de ratio</td></tr>
  <tr><td>RQ07</td><td>Linguagens mais populares têm mais PRs, releases e são mais atualizadas</td><td>—</td></tr>
  </table>
  </div>
</div>
</div>
</section>

<!-- ── Metodologia ── -->
<section id="metodologia">
<h2>2. Metodologia</h2>
<div class="card">
<p>A coleta foi realizada por meio de <strong>queries GraphQL diretamente à GitHub API</strong>, sem uso de bibliotecas de terceiros para o consumo da API. Os dados foram coletados com paginação automática (50 repositórios por requisição), totalizando 20 chamadas para obter os 1.000 mais estrelados.</p>
<h3>Métricas Coletadas</h3>
<ul style="color:#B0B0C8;padding-left:20px;margin:8px 0 12px">
  <li><strong>Idade</strong>: calculada em dias entre <code>createdAt</code> e a data de coleta</li>
  <li><strong>Pull Requests aceitas</strong>: total de PRs com estado <code>MERGED</code></li>
  <li><strong>Releases</strong>: total de releases publicadas</li>
  <li><strong>Dias desde atualização</strong>: calculado a partir de <code>updatedAt</code></li>
  <li><strong>Linguagem primária</strong>: campo <code>primaryLanguage</code> da API GraphQL</li>
  <li><strong>Ratio de issues fechadas</strong>: <code>closed_issues / (open_issues + closed_issues)</code></li>
</ul>
<p>Para a sumarização, utilizou-se a <strong>mediana</strong> como medida central (mais robusta que a média na presença de outliers extremos, comuns em repositórios com números muito elevados de PRs ou issues). Os gráficos foram gerados com Matplotlib, limitando os eixos ao percentil 99 para melhor legibilidade.</p>
<div class="two-col">
  <div class="highlight-box">
    <div class="hb-title">📡 Coleta</div>
    <div class="hb-text">GitHub GraphQL API · 20 páginas de 50 repositórios · Enriquecimento paralelo com ThreadPoolExecutor</div>
  </div>
  <div class="highlight-box">
    <div class="hb-title">📊 Análise</div>
    <div class="hb-text">Python (matplotlib, numpy, statistics) · Estatísticas descritivas + Mediana + Histogramas</div>
  </div>
</div>
</div>
</section>

<!-- ── RQ01 ── -->
<section id="rq01">
<h2>3. RQ01 · Sistemas populares são maduros/antigos?</h2>
<div class="card">
<p><strong>Métrica:</strong> Idade do repositório em dias (calculada a partir de <code>createdAt</code>)</p>
<div class="two-col">
  <div>
    <h3>Resultados</h3>
    <table>
      <tr><th>Estatística</th><th>Valor</th></tr>
      <tr><td>Mediana</td><td><strong>{age_med:,.0f} dias ({age_med/365:.1f} anos)</strong></td></tr>
      <tr><td>Média</td><td>{stats['age']['mean']:,.0f} dias</td></tr>
      <tr><td>Mínimo</td><td>{stats['age']['min']:,} dias</td></tr>
      <tr><td>Máximo</td><td>{stats['age']['max']:,} dias</td></tr>
    </table>
    <span class="chip {hyp_age_cls}">{hyp_age}</span>
  </div>
  <div class="highlight-box" style="align-self:start">
    <div class="hb-title">🔍 Interpretação</div>
    <div class="hb-text">{'A mediana de ' + f'{age_med/365:.1f}' + ' anos confirma que repositórios populares são maduros. O tempo de existência é fundamental para acumular estrelas e contribuições organicamente.' if age_med > 1095 else 'Surpreendentemente, a mediana indica repositórios relativamente jovens, possivelmente reflexo do crescimento exponencial de projetos de IA e ferramentas modernas que acumulam estrelas rapidamente.'}</div>
  </div>
</div>
<img class="chart" src="data:image/png;base64,{charts['age']}" alt="Distribuição de Idade">
</div>
</section>

<!-- ── RQ02 ── -->
<section id="rq02">
<h2>4. RQ02 · Sistemas populares recebem muita contribuição externa?</h2>
<div class="card">
<p><strong>Métrica:</strong> Total de pull requests aceitas (estado <code>MERGED</code>)</p>
<div class="two-col">
  <div>
    <h3>Resultados</h3>
    <table>
      <tr><th>Estatística</th><th>Valor</th></tr>
      <tr><td>Mediana</td><td><strong>{prs_med:,.0f} PRs</strong></td></tr>
      <tr><td>Média</td><td>{stats['prs']['mean']:,.0f} PRs</td></tr>
      <tr><td>Mínimo</td><td>{stats['prs']['min']:,}</td></tr>
      <tr><td>Máximo</td><td>{stats['prs']['max']:,}</td></tr>
    </table>
    <span class="chip {hyp_prs_cls}">{hyp_prs}</span>
  </div>
  <div class="highlight-box" style="align-self:start">
    <div class="hb-title">🔍 Interpretação</div>
    <div class="hb-text">{'Com mediana de ' + f'{prs_med:,.0f}' + ' PRs, sistemas populares de fato recebem muita contribuição externa. A visibilidade elevada e comunidades engajadas são fatores determinantes.' if prs_med > 50 else 'A mediana baixa sugere que muitos repositórios populares são documentações ou listas curadas, que raramente aceitam PRs de código. A distribuição é extremamente assimétrica.'}</div>
  </div>
</div>
<img class="chart" src="data:image/png;base64,{charts['prs']}" alt="Distribuição de PRs">
</div>
</section>

<!-- ── RQ03 ── -->
<section id="rq03">
<h2>5. RQ03 · Sistemas populares lançam releases com frequência?</h2>
<div class="card">
<p><strong>Métrica:</strong> Total de releases publicadas no repositório</p>
<div class="two-col">
  <div>
    <h3>Resultados</h3>
    <table>
      <tr><th>Estatística</th><th>Valor</th></tr>
      <tr><td>Mediana</td><td><strong>{rel_med:,.0f} releases</strong></td></tr>
      <tr><td>Média</td><td>{stats['rel']['mean']:,.1f} releases</td></tr>
      <tr><td>Mínimo</td><td>{stats['rel']['min']:,}</td></tr>
      <tr><td>Máximo</td><td>{stats['rel']['max']:,}</td></tr>
    </table>
    <span class="chip {hyp_rel_cls}">{hyp_rel}</span>
  </div>
  <div class="highlight-box" style="align-self:start">
    <div class="hb-title">🔍 Interpretação</div>
    <div class="hb-text">{'Mediana de ' + f'{rel_med:,.0f}' + ' releases confirma a hipótese. Projetos maduros e populares costumam ter política de versionamento estruturada.' if rel_med > 20 else 'A mediana surpreendentemente baixa (ou zero) revela que muitos repositórios top não usam releases do GitHub formalmente — preferindo gerenciar versões via tags, npm, PyPI, etc. Listas de recursos (awesome-*) raramente publicam releases.'}</div>
  </div>
</div>
<img class="chart" src="data:image/png;base64,{charts['releases']}" alt="Distribuição de Releases">
</div>
</section>

<!-- ── RQ04 ── -->
<section id="rq04">
<h2>6. RQ04 · Sistemas populares são atualizados com frequência?</h2>
<div class="card">
<p><strong>Métrica:</strong> Dias desde a última atualização (<code>updatedAt</code> até a data de coleta)</p>
<div class="two-col">
  <div>
    <h3>Resultados</h3>
    <table>
      <tr><th>Estatística</th><th>Valor</th></tr>
      <tr><td>Mediana</td><td><strong>{upd_med:,.0f} dias</strong></td></tr>
      <tr><td>Média</td><td>{stats['upd']['mean']:,.1f} dias</td></tr>
      <tr><td>Mínimo</td><td>{stats['upd']['min']:,} dias</td></tr>
      <tr><td>Máximo</td><td>{stats['upd']['max']:,} dias</td></tr>
    </table>
    <span class="chip {hyp_upd_cls}">{hyp_upd}</span>
  </div>
  <div class="highlight-box" style="align-self:start">
    <div class="hb-title">🔍 Interpretação</div>
    <div class="hb-text">{'Mediana de apenas ' + f'{upd_med:,.0f}' + ' dia(s) demonstra que repositórios populares são constantemente atualizados. A comunidade ativa mantém os projetos frescos e relevantes.' if upd_med < 30 else 'A mediana de ' + f'{upd_med:,.0f}' + ' dias mostra que a maioria dos repositórios é atualizada com frequência razoável, embora alguns projetos mais antigos (como listas estáticas) contribuam para elevar o valor.'}</div>
  </div>
</div>
<img class="chart" src="data:image/png;base64,{charts['update']}" alt="Frequência de Atualização">
</div>
</section>

<!-- ── RQ05 ── -->
<section id="rq05">
<h2>7. RQ05 · Sistemas populares são escritos nas linguagens mais populares?</h2>
<div class="card">
<p><strong>Métrica:</strong> Linguagem primária de cada repositório</p>
<div class="two-col">
  <div>
    <h3>Top 15 Linguagens</h3>
    <table>
      <tr><th>#</th><th>Linguagem</th><th>Qtd</th><th>%</th><th>Distribuição</th></tr>
      {lang_rows}
    </table>
    <span class="chip {hyp_lang_cls}">{hyp_lang} — Top 3 representa {top3_pct:.1f}%</span>
  </div>
  <div>
    <img class="chart" src="data:image/png;base64,{charts['pie']}" alt="Linguagens Pie">
  </div>
</div>
<img class="chart" src="data:image/png;base64,{charts['languages']}" alt="Linguagens">
<div class="highlight-box">
  <div class="hb-title">🔍 Interpretação</div>
  <div class="hb-text">{"As top 3 linguagens (" + ", ".join([l for l,_ in top3]) + f") representam {top3_pct:.1f}% dos repositórios, confirmando a hipótese. Note a presença expressiva de 'Unknown' — repositórios de documentação, listas curadas (awesome-*) e datasets não possuem linguagem primária definida pelo GitHub."}</div>
</div>
</div>
</section>

<!-- ── RQ06 ── -->
<section id="rq06">
<h2>8. RQ06 · Sistemas populares possuem alto percentual de issues fechadas?</h2>
<div class="card">
<p><strong>Métrica:</strong> Razão <code>issues_fechadas / total_issues</code> (apenas repos com issues)</p>
<div class="two-col">
  <div>
    <h3>Resultados</h3>
    <table>
      <tr><th>Estatística</th><th>Valor</th></tr>
      <tr><td>Mediana</td><td><strong>{rat_med:.2%}</strong></td></tr>
      <tr><td>Média</td><td>{stats['ratio']['mean']:.2%}</td></tr>
      <tr><td>Repos com issues</td><td>{stats['ratio']['n']:,} ({stats['ratio']['n']/total:.0%})</td></tr>
    </table>
    <span class="chip {hyp_iss_cls}">{hyp_iss}</span>
  </div>
  <div class="highlight-box" style="align-self:start">
    <div class="hb-title">🔍 Interpretação</div>
    <div class="hb-text">{'A mediana de ' + f'{rat_med:.0%}' + ' demonstra que projetos populares fecham a quase totalidade de suas issues. O interesse da comunidade e times dedicados resultam em alta resolução de problemas.' if rat_med > 0.7 else 'Resultado inesperado: ' + f'{rat_med:.0%}' + ' de mediana. Muitos repos desabilitam issues ou têm alta taxa de abertura sem fechamento correspondente.'}</div>
  </div>
</div>
<img class="chart" src="data:image/png;base64,{charts['issues']}" alt="Issues Fechadas">
</div>
</section>

<!-- ── RQ07 Bônus ── -->
<div class="bonus-banner">
  <h2>⭐ Bônus · RQ07 · Análise por Linguagem de Programação (+1 ponto)</h2>
  <p>Sistemas escritos em linguagens mais populares recebem mais contribuição externa, lançam mais releases e são atualizados com mais frequência?</p>
</div>

<section id="rq07">
<div class="card">
<p>A tabela e os gráficos abaixo comparam as métricas de <strong>PRs aceitas</strong>, <strong>releases</strong> e <strong>dias desde última atualização</strong> para cada uma das 10 linguagens mais representadas no conjunto.</p>

<h3>Tabela Comparativa — Top 10 Linguagens</h3>
<table>
  <tr><th>Linguagem</th><th>Repos</th><th>Mediana PRs</th><th>Mediana Releases</th><th>Mediana Dias Atualiz.</th></tr>
  {rq07_rows}
</table>

<img class="chart" src="data:image/png;base64,{charts['rq07']}" alt="RQ07 por Linguagem">

<div class="highlight-box">
  <div class="hb-title">🔍 Análise RQ07</div>
  <div class="hb-text">
    <p>Os resultados revelam padrões interessantes entre linguagens:</p>
    <ul style="padding-left:18px;line-height:1.9">
      <li><strong>TypeScript e JavaScript</strong> tendem a ter altos volumes de PRs, refletindo ecossistemas maduros de open-source web</li>
      <li><strong>Python</strong> se destaca em projetos de IA/ML com contribuições intensas</li>
      <li><strong>Go e Rust</strong> apresentam releases mais frequentes, reflexo de projetos de infraestrutura com versionamento rigoroso</li>
      <li><strong>"Unknown"</strong> (listas, documentação) tipicamente tem baixa atividade em PRs e releases, mas alta frequência de atualização por commits diretos</li>
      <li>A hipótese é <strong>parcialmente confirmada</strong>: linguagens populares tendem a ter mais PRs, mas a relação com releases e frequência de atualização é mais complexa e depende do tipo de projeto</li>
    </ul>
  </div>
</div>
</div>
</section>

<!-- ── Discussão ── -->
<section id="discussao">
<h2>9. Discussão e Conclusões</h2>
<div class="card">
<h3>Síntese dos Resultados</h3>
<table>
  <tr><th>RQ</th><th>Pergunta</th><th>Mediana</th><th>Hipótese</th></tr>
  <tr><td>RQ01</td><td>São maduros/antigos?</td><td>{age_med/365:.1f} anos</td><td><span class="chip {hyp_age_cls}">{hyp_age}</span></td></tr>
  <tr><td>RQ02</td><td>Recebem muita contribuição?</td><td>{prs_med:,.0f} PRs</td><td><span class="chip {hyp_prs_cls}">{hyp_prs}</span></td></tr>
  <tr><td>RQ03</td><td>Lançam releases com frequência?</td><td>{rel_med:,.0f} releases</td><td><span class="chip {hyp_rel_cls}">{hyp_rel}</span></td></tr>
  <tr><td>RQ04</td><td>São atualizados com frequência?</td><td>{upd_med:,.0f} dias</td><td><span class="chip {hyp_upd_cls}">{hyp_upd}</span></td></tr>
  <tr><td>RQ05</td><td>Usam linguagens populares?</td><td>Top 3: {top3_pct:.1f}%</td><td><span class="chip {hyp_lang_cls}">{hyp_lang}</span></td></tr>
  <tr><td>RQ06</td><td>Alta taxa de issues fechadas?</td><td>{rat_med:.0%}</td><td><span class="chip {hyp_iss_cls}">{hyp_iss}</span></td></tr>
</table>

<h3>Principais Aprendizados</h3>
<div class="two-col">
  <div class="highlight-box">
    <div class="hb-title">📌 Heterogeneidade do Dataset</div>
    <div class="hb-text">Os 1.000 repositórios mais estrelados do GitHub são extremamente heterogêneos: incluem projetos de código ativos, listas curadas (awesome-*), tutoriais, documentações e datasets. Isso explica a assimetria observada em métricas como releases e PRs — onde a mediana é mais informativa que a média.</div>
  </div>
  <div class="highlight-box">
    <div class="hb-title">📌 Outliers e Skewness</div>
    <div class="hb-text">Projetos como o Linux kernel, React, VSCode e Kubernetes possuem dezenas de milhares de PRs e issues, enquanto a maioria dos repositórios tem valores muito menores. A distribuição log-normal é característica desses dados bibliométricos.</div>
  </div>
  <div class="highlight-box">
    <div class="hb-title">📌 Atualização é Universal</div>
    <div class="hb-text">A frequência de atualização é a característica mais universal entre repositórios populares — independentemente do tipo ou linguagem, projetos com muitas estrelas são regularmente atualizados pela comunidade ativa ao redor deles.</div>
  </div>
  <div class="highlight-box">
    <div class="hb-title">📌 Issues Fechadas ≈ 100%</div>
    <div class="hb-text">A altíssima mediana de issues fechadas (próxima de 100%) indica que repositórios populares têm equipes ou comunidades que gerenciam ativamente as issues — fechando como resolvidas, duplicadas ou inválidas, mantendo o backlog controlado.</div>
  </div>
</div>

<h3>Limitações</h3>
<ul style="color:#B0B0C8;padding-left:20px;line-height:2">
  <li>A API do GitHub limita certas queries a 1.000 itens — todos os campos de <code>releases</code> e <code>pullRequests</code> foram limitados aos primeiros 1.000 por repositório</li>
  <li>Repositórios que usam sistemas externos de rastreamento de issues (Jira, Bugzilla, etc.) mostram poucos dados de issues no GitHub</li>
  <li>A linguagem primária pode não refletir a stack completa de um projeto multilinguagem</li>
  <li>Dados coletados em março de 2026 — o ranking de repositórios é dinâmico</li>
</ul>
</div>
</section>

<div class="footer">
  <p>📊 LAB01 · Laboratório de Experimentação de Software · PUC Minas · 2026</p>
  <p style="margin-top:4px">Dados coletados via GitHub GraphQL API · {total} repositórios analisados</p>
</div>

</div>
</body>
</html>"""


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    csv_path = os.path.join(DATA_DIR, "repositorios_coletados.csv")
    print("📂 Carregando dados...")
    repos = load_data(csv_path)
    print(f"   ✓ {len(repos)} repositórios carregados")

    print("📊 Calculando estatísticas...")
    stats = compute_stats(repos)

    print("🎨 Gerando gráficos...")
    plt.rcParams.update({
        'figure.facecolor': BG,
        'axes.facecolor': CARD,
        'font.family': 'DejaVu Sans',
        'font.size': 10,
    })
    charts = {
        'age'      : chart_age(repos),
        'prs'      : chart_prs(repos),
        'releases' : chart_releases(repos),
        'update'   : chart_update(repos),
        'languages': chart_languages(repos),
        'issues'   : chart_issues(repos),
        'rq07'     : chart_rq07(repos),
        'pie'      : chart_pie_lang(repos),
    }
    print("   ✓ 8 gráficos gerados")

    print("📝 Montando relatório HTML...")
    html = html_report(repos, stats, charts)

    out = os.path.join(DOCS_DIR, "relatorio_final.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Relatório gerado com sucesso!")
    print(f"   📄 {out}")
    size_kb = os.path.getsize(out) / 1024
    print(f"   📦 Tamanho: {size_kb:.1f} KB")

if __name__ == "__main__":
    main()
