import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
import os

# Set style for "badass" graphs
plt.style.use('dark_background')
sns.set_theme(style="dark", palette="viridis")

# Load data
csv_path = r'c:\Users\jotaa\OneDrive\Documentos\Prado\PUC\Lab-Medicao\LAB-EXPERIMENTA-O-DE-SOFTWARE\enunciado03\data\pr_metrics.csv'
df = pd.read_csv(csv_path)

# Preprocessing
df['pr_status_numeric'] = df['pr_status'].apply(lambda x: 1 if x == 'MERGED' else 0)
df['log_total_changes'] = np.log1p(df['total_changes'])
df['log_time'] = np.log1p(df['time_to_review_hours'])
df['log_desc'] = np.log1p(df['description_length'])

output_dir = r'c:\Users\jotaa\.gemini\antigravity\brain\f6967809-19e8-4af3-93ea-ba80da14735a\artifacts'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def save_plot(name):
    plt.savefig(os.path.join(output_dir, name), dpi=300, bbox_inches='tight')
    plt.close()

# --- ADVANCED GRAPHS ---

# 1. Cumulative Distribution Function (CDF) of Time to Review by Status
plt.figure(figsize=(10, 6))
sns.ecdfplot(data=df, x='time_to_review_hours', hue='pr_status', palette=['#ff007f', '#00ff9f'], linewidth=3)
plt.xscale('log')
plt.title("CDF: Probabilidade Acumulada de Resolução no Tempo (Escala Log)", fontsize=14, pad=15)
plt.xlabel("Tempo de Análise (Horas) - Escala Log")
plt.ylabel("Proporção de PRs")
plt.axvline(x=48, color='#00ff9f', linestyle='--', alpha=0.5, label='Mediana Merged (48h)')
plt.axvline(x=195, color='#ff007f', linestyle='--', alpha=0.5, label='Mediana Closed (195h)')
plt.legend()
save_plot("cdf_time_status.png")

# 2. Multidimensional Bubble Chart: Size vs Time vs Comments vs Status
plt.figure(figsize=(12, 8))
sns.scatterplot(
    data=df, 
    x='log_total_changes', 
    y='log_time', 
    hue='pr_status', 
    size='comment_count', 
    sizes=(20, 500), 
    alpha=0.6, 
    palette=['#ff007f', '#00ff9f'],
    edgecolor='w',
    linewidth=0.5
)
plt.title("Análise Multidimensional: Tempo, Tamanho e Engajamento", fontsize=15, pad=15)
plt.xlabel("Tamanho do PR (Log Total Changes)")
plt.ylabel("Tempo de Análise (Log Hours)")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Status & Comentários")
save_plot("multidimensional_bubble.png")

# 3. PairGrid for Interaction Effects
g = sns.PairGrid(df, vars=['log_total_changes', 'log_time', 'participant_count', 'review_count'], hue='pr_status', palette=['#ff007f', '#00ff9f'], corner=True)
g.map_diag(sns.kdeplot, fill=True, common_norm=False, alpha=0.5)
g.map_offdiag(sns.scatterplot, alpha=0.5, s=15)
g.add_legend()
g.fig.suptitle("Matriz de Interações de Variáveis Críticas", y=1.02, fontsize=16)
save_plot("pairgrid_interactions.png")

# 4. Regression Plot: Participants vs Reviews by Status
plt.figure(figsize=(10, 6))
sns.lmplot(data=df, x='participant_count', y='review_count', hue='pr_status', palette=['#ff007f', '#00ff9f'], height=6, aspect=1.5, scatter_kws={'alpha':0.3})
plt.title("Crescimento de Revisões por Número de Participantes", fontsize=15, pad=15)
save_plot("regression_participants_reviews.png")

print("Advanced analysis and plots generated successfully.")
