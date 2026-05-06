import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, mannwhitneyu
import os

# Set style for "badass" graphs
plt.style.use('dark_background')
sns.set_theme(style="dark", palette="viridis")
colors = ["#00d4ff", "#ff007f", "#00ff9f", "#ffae00", "#9d00ff"]

# Load data
csv_path = r'c:\Users\jotaa\OneDrive\Documentos\Prado\PUC\Lab-Medicao\LAB-EXPERIMENTA-O-DE-SOFTWARE\enunciado03\data\pr_metrics.csv'
df = pd.read_csv(csv_path)

# Preprocessing
df['pr_status_numeric'] = df['pr_status'].apply(lambda x: 1 if x == 'MERGED' else 0)

# Directory for plots
output_dir = r'c:\Users\jotaa\.gemini\antigravity\brain\f6967809-19e8-4af3-93ea-ba80da14735a\artifacts'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def save_plot(name):
    plt.savefig(os.path.join(output_dir, name), dpi=300, bbox_inches='tight')
    plt.close()

# 1. Summary Statistics (Medians)
summary = df.groupby('pr_status').median(numeric_only=True)
print("### Medians by Status")
print(summary)

# 2. Correlations
metrics = ['files_changed', 'additions', 'deletions', 'total_changes', 'time_to_review_hours', 'description_length', 'comment_count', 'participant_count']
target_status = 'pr_status_numeric'
target_reviews = 'review_count'

results_status = []
results_reviews = []

for m in metrics:
    corr, p = spearmanr(df[m], df[target_status])
    results_status.append({'metric': m, 'correlation': corr, 'p_value': p})
    
    corr_rev, p_rev = spearmanr(df[m], df[target_reviews])
    results_reviews.append({'metric': m, 'correlation': corr_rev, 'p_value': p_rev})

df_status_corr = pd.DataFrame(results_status)
df_reviews_corr = pd.DataFrame(results_reviews)

print("\n### Spearman Correlation with Status (1=Merged, 0=Closed)")
print(df_status_corr)
print("\n### Spearman Correlation with Review Count")
print(df_reviews_corr)

# --- GRAPHS ---

# Graph 1: Correlation Heatmap
plt.figure(figsize=(12, 10))
corr_matrix = df[metrics + ['review_count', 'pr_status_numeric']].corr(method='spearman')
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", cmap='magma', cbar_kws={"shrink": .8})
plt.title("Spearman Correlation Matrix of PR Metrics", fontsize=16, pad=20)
save_plot("correlation_heatmap.png")

# Graph 2: Size vs Status (Violin Plot) - Using Log scale for visual clarity
plt.figure(figsize=(10, 6))
df_log = df.copy()
df_log['log_total_changes'] = np.log1p(df_log['total_changes'])
sns.violinplot(data=df_log, x='pr_status', y='log_total_changes', palette='husl', inner="quart")
plt.title("PR Size (Log Scale) vs Final Status", fontsize=14)
plt.ylabel("Log(Total Changes + 1)")
save_plot("size_vs_status.png")

# Graph 3: Time vs Status
plt.figure(figsize=(10, 6))
df_log['log_time'] = np.log1p(df_log['time_to_review_hours'])
sns.boxenplot(data=df_log, x='pr_status', y='log_time', palette='cool')
plt.title("Time to Review (Log Scale) vs Final Status", fontsize=14)
plt.ylabel("Log(Hours + 1)")
save_plot("time_vs_status.png")

# Graph 4: Description Length vs Review Count (JointPlot)
g = sns.jointplot(data=df, x='description_length', y='review_count', kind="hex", color="#ff007f")
g.fig.suptitle("Description Length vs Review Count", y=1.02)
save_plot("desc_vs_reviews.png")

# Graph 5: Interactions (Comments) vs Status
plt.figure(figsize=(10, 6))
sns.kdeplot(data=df, x='comment_count', hue='pr_status', fill=True, common_norm=False, palette='winter', alpha=.5, linewidth=2)
plt.xlim(0, df['comment_count'].quantile(0.95)) # Focus on 95% of data
plt.title("Distribution of Comment Count by Status", fontsize=14)
save_plot("comments_vs_status.png")

# Graph 6: Review Count Distribution across Size Quartiles
df['size_quartile'] = pd.qcut(df['total_changes'], 4, labels=['Small', 'Medium', 'Large', 'Extra Large'])
plt.figure(figsize=(12, 6))
sns.barplot(data=df, x='size_quartile', y='review_count', palette='flare', errorbar=('ci', 95))
plt.title("Average Review Count by PR Size Quartile", fontsize=14)
save_plot("size_quartile_vs_reviews.png")

print("\nAnalysis complete. Graphs saved to artifacts.")
