import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

# ── Configuração global ──────────────────────────────────────────────────────
sns.set_theme(style="whitegrid")
OUTPUT_DIR = r'c:\Users\jotaa\OneDrive\Documentos\Prado\PUC\Lab-Medicao\LAB-EXPERIMENTA-O-DE-SOFTWARE\enunciado03\graficos'
os.makedirs(OUTPUT_DIR, exist_ok=True)

BG_COLOR   = "#ECEEF8"
COR_CLOSED = "#E91E8C"
COR_MERGED = "#00BFA5"
COR_FRACA  = "#FFD54F"
COR_MOD    = "#FF8F00"
FONTSIZE_TITLE = 14
DPI = 150


# ════════════════════════════════════════════════════════════════════════════
# GRÁFICO 1 — Ranking de Correlações de Spearman
# ════════════════════════════════════════════════════════════════════════════
preditores = [
    "time_to_review_hours",
    "participant_count",
    "comment_count",
    "total_changes",
    "additions",
    "files_changed",
    "deletions",
    "description_length",
]

rho_status      = [-0.261, -0.110, -0.109,  0.077,  0.070,  0.090,  0.050,  0.051]
rho_review_count = [ 0.163,  0.797,  0.190,  0.414,  0.420,  0.367,  0.230,  0.100]

labels_pt = [
    "Tempo de Análise",
    "Nº de Participantes",
    "Nº de Comentários",
    "Total de Mudanças",
    "Adições",
    "Arquivos Alterados",
    "Deleções",
    "Tamanho da Descrição",
]

# Ordenar por |rho_status|
order = np.argsort(np.abs(rho_status))[::-1]
labels_sorted    = [labels_pt[i]        for i in order]
status_sorted    = [rho_status[i]       for i in order]
reviews_sorted   = [rho_review_count[i] for i in order]

y_pos = np.arange(len(labels_sorted))
height = 0.35

fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG_COLOR)
ax.set_facecolor(BG_COLOR)

bars1 = ax.barh(y_pos + height/2, status_sorted,  height, label="Dimensão A — Status do PR",      color=COR_CLOSED, alpha=0.85)
bars2 = ax.barh(y_pos - height/2, reviews_sorted, height, label="Dimensão B — Nº de Revisões",    color=COR_MERGED, alpha=0.85)

# Linhas de referência Cohen
ax.axvline(x= 0.10, color=COR_FRACA, linestyle='--', linewidth=1.4, label="Cohen fraca (|ρ|=0.10)")
ax.axvline(x=-0.10, color=COR_FRACA, linestyle='--', linewidth=1.4)
ax.axvline(x= 0.30, color=COR_MOD,   linestyle='--', linewidth=1.4, label="Cohen moderada (|ρ|=0.30)")
ax.axvline(x=-0.30, color=COR_MOD,   linestyle='--', linewidth=1.4)

ax.set_yticks(y_pos)
ax.set_yticklabels(labels_sorted, fontsize=10)
ax.set_xlabel("Coeficiente de Spearman (ρ)", fontsize=11)
ax.set_title("Ranking de Correlações de Spearman por Dimensão de Análise", fontsize=FONTSIZE_TITLE, fontweight='bold', pad=14)
ax.legend(loc="lower right", fontsize=9)
ax.axvline(0, color='gray', linewidth=0.8)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "ranking_correlacoes.png"), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] ranking_correlacoes.png")


# ════════════════════════════════════════════════════════════════════════════
# GRÁFICO 2 — Comparativo de Medianas MERGED vs. CLOSED (subplots)
# ════════════════════════════════════════════════════════════════════════════
metricas_label = ["Total Changes\n(linhas)", "Tempo\n(horas)", "Descrição\n(chars/10)", "Comentários"]
closed_vals    = [89.0,   195.32, 70.6,  2.0]
merged_vals    = [120.0,   48.25, 67.5,  1.0]

fig, axes = plt.subplots(1, 4, figsize=(14, 6), facecolor=BG_COLOR)
fig.suptitle("Comparativo de Medianas por Status do PR", fontsize=FONTSIZE_TITLE, fontweight='bold', y=1.02)

for idx, ax in enumerate(axes):
    ax.set_facecolor(BG_COLOR)
    vals  = [closed_vals[idx], merged_vals[idx]]
    cores = [COR_CLOSED, COR_MERGED]
    bars  = ax.bar(["CLOSED", "MERGED"], vals, color=cores, width=0.5, edgecolor='white', linewidth=1.2)
    for bar, v in zip(bars, vals):
        label = f"{v:,.1f}".replace(",", ".")
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02,
                label, ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.set_title(metricas_label[idx], fontsize=10, fontweight='bold')
    ax.set_ylabel("Mediana", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.25)
    ax.tick_params(axis='x', labelsize=9)
    ax.grid(axis='y', alpha=0.4)

patch_c = mpatches.Patch(color=COR_CLOSED, label='CLOSED')
patch_m = mpatches.Patch(color=COR_MERGED, label='MERGED')
fig.legend(handles=[patch_c, patch_m], loc='lower center', ncol=2, fontsize=10, bbox_to_anchor=(0.5, -0.06))
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "medianas_comparativo.png"), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] medianas_comparativo.png")


# ════════════════════════════════════════════════════════════════════════════
# GRÁFICO 3 — Tabela Visual de Hipóteses
# ════════════════════════════════════════════════════════════════════════════
hipoteses = ["H1", "H2", "H3", "H4", "H5"]
descricoes = [
    "Tamanho → rejeição",
    "Tempo longo → rejeição",
    "Descrição rica → aprovação",
    "Mais comentários → rejeição",
    "Esforço escala com participantes",
]
resultados = ["✗ Refutada", "✓ Confirmada", "✗ Refutada", "~ Parcialmente Conf.", "✓ Confirmada"]
rhos       = ["ρ = 0.077", "ρ = −0.261", "ρ = 0.051", "ρ = −0.109", "ρ = 0.797"]

cor_resultado = {
    "✓ Confirmada":        "#B9F6CA",  # verde claro
    "✗ Refutada":          "#FFCDD2",  # vermelho claro
    "~ Parcialmente Conf.":"#FFF9C4",  # amarelo claro
}

fig, ax = plt.subplots(figsize=(12, 4), facecolor=BG_COLOR)
ax.set_facecolor(BG_COLOR)
ax.axis('off')
ax.set_title("Sumário de Hipóteses vs. Resultados Obtidos", fontsize=FONTSIZE_TITLE, fontweight='bold', pad=18)

col_labels = ["Hipótese", "Descrição Resumida", "Resultado", "ρ Principal"]
table_data = list(zip(hipoteses, descricoes, resultados, rhos))

table = ax.table(
    cellText=table_data,
    colLabels=col_labels,
    cellLoc='center',
    loc='center',
)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 2.0)

# Estilizar cabeçalho
for j in range(4):
    table[0, j].set_facecolor("#37474F")
    table[0, j].set_text_props(color='white', fontweight='bold')

# Colorir células de resultado
for i, row in enumerate(table_data):
    res = row[2]
    bg = cor_resultado.get(res, "white")
    for j in range(4):
        table[i+1, j].set_facecolor(bg)
    table[i+1, 2].set_text_props(fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "hipoteses_resultado.png"), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] hipoteses_resultado.png")


# ════════════════════════════════════════════════════════════════════════════
# GRÁFICO 4 — Escala de Cohen (Lollipop Chart)
# ════════════════════════════════════════════════════════════════════════════
# Dados: (label, rho, dimensao)  dimensao=A ou B
pontos = [
    ("Tempo → Status",            -0.261, "A"),
    ("Participantes → Status",    -0.110, "A"),
    ("Comentários → Status",      -0.109, "A"),
    ("Total Changes → Status",     0.077, "A"),
    ("Descrição → Status",         0.051, "A"),
    ("Participantes → Revisões",   0.797, "B"),
    ("Total Changes → Revisões",   0.414, "B"),
    ("Adições → Revisões",         0.420, "B"),
    ("Arq. Alterados → Revisões",  0.367, "B"),
    ("Tempo → Revisões",           0.163, "B"),
    ("Comentários → Revisões",     0.190, "B"),
    ("Descrição → Revisões",       0.100, "B"),
]

labels_p  = [p[0] for p in pontos]
rhos_p    = [p[1] for p in pontos]
dims_p    = [p[2] for p in pontos]
y_vals    = list(range(len(pontos)))

fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG_COLOR)
ax.set_facecolor(BG_COLOR)

# Faixas de fundo (Cohen)
faixas = [
    (-1.00, -0.50, "#B71C1C", "Forte Neg."),
    (-0.50, -0.30, "#EF6C00", "Mod. Neg."),
    (-0.30, -0.10, "#F9A825", "Fraca Neg."),
    (-0.10,  0.10, "#BDBDBD", "Negligenciável"),
    ( 0.10,  0.30, "#F9A825", "Fraca Pos."),
    ( 0.30,  0.50, "#EF6C00", "Mod. Pos."),
    ( 0.50,  1.00, "#1B5E20", "Forte Pos."),
]
for x0, x1, cor, nome in faixas:
    ax.axvspan(x0, x1, alpha=0.18, color=cor, label=nome)
    ax.text((x0+x1)/2, len(pontos)+0.2, nome, ha='center', va='bottom', fontsize=7.5, color='#333333')

# Lollipops
for i, (lbl, rho, dim) in enumerate(pontos):
    marker = 'o' if dim == 'A' else 'D'
    cor_pt  = COR_CLOSED if dim == 'A' else COR_MERGED
    ax.hlines(i, 0, rho, color='gray', linewidth=1.2, linestyle='-')
    ax.plot(rho, i, marker=marker, color=cor_pt, markersize=10, zorder=5)
    ax.text(rho + (0.02 if rho >= 0 else -0.02), i, f"  {rho:+.3f}",
            va='center', ha='left' if rho >= 0 else 'right', fontsize=8)

ax.set_yticks(y_vals)
ax.set_yticklabels(labels_p, fontsize=9)
ax.set_xlim(-1.05, 1.05)
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel("Coeficiente de Spearman (ρ)", fontsize=11)
ax.set_title("Posicionamento das Correlações na Escala de Cohen (1988)", fontsize=FONTSIZE_TITLE, fontweight='bold', pad=12)

patch_a = mpatches.Patch(color=COR_CLOSED, label='Dimensão A — Status (círculo ●)')
patch_b = mpatches.Patch(color=COR_MERGED, label='Dimensão B — Revisões (diamante ◆)')
ax.legend(handles=[patch_a, patch_b], loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "magnitude_cohen.png"), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] magnitude_cohen.png")

print("Todos os gráficos gerados com sucesso.")
