# Enunciado 02 - Sprint 1

Este diretório contém a solução do Enunciado 02.

## Estrutura

- `src/`: scripts principais da coleta, clone e análise.
- `data/`: CSVs gerados na coleta.
- `clones/`: repositórios clonados para análise.
- `ck_results/`: saídas de métricas de qualidade.
- `RELATORIO_SPRINT1_FINAL.txt`: relatório final da sprint 1.

## Como executar

1. Abra terminal em `enunciado02`.
2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Configure o token GitHub no arquivo `.env`:

```env
GITHUB_TOKEN=seu_token_aqui
```

4. Execute o fluxo principal:

```bash
python src/main.py
```

5. Para gerar dados de exemplo da sprint 1:

```bash
python src/generate_sprint1.py
```

6. Para sumarizar métricas já existentes:

```bash
python calc_metrics.py
```

