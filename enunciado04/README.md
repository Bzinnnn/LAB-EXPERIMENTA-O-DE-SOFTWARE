Comparação entre linguagens — Lab04

Objetivo
- Comparar produtividade e manutenção entre linguagens através de métricas extraídas de pull requests.

GQM e RQs
- Goal: Avaliar diferenças de produtividade e manutenção entre linguagens em repositórios GitHub.
- RQ1: Qual linguagem apresenta menor tempo médio/mediano de revisão (tempo entre criação e merge/fechamento de PR)?
- RQ2: Há diferença significativa na distribuição do tempo de revisão entre linguagens?

Métricas
- time_to_review_hours (mediana, média, Q1, Q3)
- pr_count por linguagem
- files_changed, additions, deletions (médias)

Arquivos gerados
- enunciado04/data/repo_metrics.csv — métrica consolidada por repositório
- enunciado04/data/language_metrics.csv — agregados por linguagem

Como usar
1. Instale dependências: `pip install -r enunciado04/requirements.txt`.
2. Execute: `python enunciado04/src/data_processor.py` — vai ler os dados coletados em `enunciado03/data` e gerar os CSVs em `enunciado04/data`.
2. Se quiser coletar do zero (recomendado para este trabalho): execute o coletor que busca os top-50 repositórios nas 8 linguagens e coleta métricas dos últimos 12 meses:

```bash
pip install -r enunciado04/requirements.txt
python enunciado04/src/github_collector.py
```

O coletor lê o `GITHUB_TOKEN` de `.env` na raiz do workspace e salva arquivos JSON por repositório em `enunciado04/data/raw` e um resumo em `enunciado04/data/repos_summary.json`.
Ele também grava um checkpoint em `enunciado04/data/collector_checkpoint.json`, então você pode interromper e retomar sem refazer os repositórios já concluídos.

3. Execute: `python enunciado04/src/data_processor.py` — vai ler `enunciado04/data/repos_summary.json` e gerar os CSVs em `enunciado04/data` para import no Power BI/Tableau.
4. Os principais arquivos para o dashboard são `repo_metrics.csv` e `language_metrics.csv`.
5. Abra `enunciado04/data` no Power BI/Tableau ou rode o notebook de exploração (ainda a criar).
