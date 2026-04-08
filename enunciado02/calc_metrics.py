import csv
import statistics
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
METRICS_FILE = BASE_DIR / 'ck_results' / 'krahets_hello-algo' / 'processed_class_metrics.csv'

with METRICS_FILE.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

print(f'Total de classes: {len(data)}')
print()

metrics = {}
for metric in ['cbo', 'dit', 'lcom', 'loc', 'methods']:
    values = [float(d[metric]) for d in data if d[metric]]
    metrics[metric] = {
        'values': values,
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values)
    }

for metric, stats in metrics.items():
    print(f'{metric.upper()}:')
    print(f'  Media: {stats["mean"]:.2f}')
    print(f'  Mediana: {stats["median"]:.2f}')
    print(f'  Desvio Padrao: {stats["stdev"]:.2f}')
    print(f'  Minimo: {stats["min"]:.0f}')
    print(f'  Maximo: {stats["max"]:.0f}')
    print()
