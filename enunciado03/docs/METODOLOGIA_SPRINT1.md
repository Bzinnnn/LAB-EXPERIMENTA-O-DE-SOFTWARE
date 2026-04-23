# METODOLOGIA - Lab03S01

## Objetivo da Sprint 1

Preparar a infraestrutura necessária para:
1. Selecionar os 200 repositórios mais populares do GitHub com pelo menos 100 PRs
2. Criar scripts para coletar dados de PRs
3. Calcular as métricas necessárias para análise

## Critérios de Seleção de Repositórios

### Fase 1: Seleção Inicial
- **Query GitHub**: "sort:stars"
- **Limite**: Os 200 repositórios mais populares (por número de stars)
- **Filtro de PRs**: Apenas repositórios com ≥ 100 PRs no status MERGED ou CLOSED

### Resultado Esperado
- Lista CSV com metadados dos repositórios selecionados
- Campos: full_name, owner, name, stars, forks, language, pr_count, url

## Critérios de Seleção de PRs

Para que um PR seja incluído no dataset, deve atender aos seguintes critérios:

### 1. Status do PR
- ✓ Estado final: **MERGED** ou **CLOSED**
- Objetivo: Analisar PRs que completaram o ciclo de revisão

### 2. Atividade de Revisão
- ✓ Mínimo de **1 revisão** (campo review_comments ≥ 1)
- Objetivo: Filtrar PRs que tiveram ao menos uma revisão humana

### 3. Tempo de Revisão
- ✓ Tempo entre criação e merge/close: **≥ 1 hora**
- Objetivo: Remover PRs aprovadas automaticamente (bots/CI/CD)

## Métricas Coletadas

Para cada PR selecionado, coletaremos:

### 1. Tamanho do PR
```
- files_changed: Número de arquivos alterados
- additions: Total de linhas adicionadas
- deletions: Total de linhas removidas
- total_changes: additions + deletions
```

### 2. Tempo de Análise
```
- time_to_review_hours: Diferença em horas entre criação e merge/close
- Calculado como: (merged_at ou closed_at - created_at) / 3600 segundos
```

### 3. Descrição do PR
```
- description_length: Número de caracteres do corpo da descrição (markdown)
- has_description: Flag binário (1 se tem descrição, 0 caso contrário)
```

### 4. Interações
```
- comment_count: Número de comentários no PR (via API: pr.comments)
- review_count: Número de comentários de revisão (via API: pr.review_comments)
- participant_count: Número de usuários únicos que participaram (comentários + revisões)
- participants: Lista de nomes de usuários (separados por vírgula)
```

### 5. Metadados Adicionais
```
- pr_number: ID único do PR no repositório
- pr_title: Título do PR
- pr_status: MERGED ou CLOSED
- repository: Nome completo do repositório
- author: Login do autor do PR
- created_at: Data de criação
- merged_or_closed_at: Data de merge ou close
- url: URL do PR no GitHub
```

## Estrutura de Dados (CSV)

### selected_repositories.csv
Estrutura esperada:
```
full_name,owner,name,stars,forks,language,pr_count,url
```

Exemplo:
```
facebook/react,facebook,react,200000,45000,JavaScript,2500,https://github.com/facebook/react
```

### pr_metrics.csv
Estrutura esperada:
```
repository,pr_number,pr_title,pr_status,created_at,merged_or_closed_at,
files_changed,additions,deletions,total_changes,time_to_review_hours,
description_length,has_description,comment_count,review_count,participant_count,
author,url,participants
```

## Implementação dos Scripts

### 1. repository_selector.py
- Classe `RepositorySelector`
- Método `get_popular_repositories()`: Busca top 200 repositórios
- Método `save_repositories()`: Salva em CSV
- Método `display_summary()`: Exibe estatísticas

### 2. pr_metrics.py
- Classe `PRMetricsCollector`
- Método `calculate_pr_metrics()`: Calcula todas as métricas para um PR
- Método `collect_prs_from_repository()`: Coleta PRs de um repositório
- Método `collect_from_multiple_repositories()`: Coleta de vários repositórios
- Método `save_pr_data()`: Salva em CSV
- Método `display_summary()`: Exibe estatísticas

### 3. main.py
- Orquestra as etapas 1 e 2
- Gera relatório inicial com hipóteses
- Valida configuração do token

## Considerações sobre Rate Limiting

A API do GitHub tem limites:
- **Autenticado**: 5.000 requisições por hora
- **Estratégia**: Adicionar delays entre chamadas (0.5-1 segundo)
- **Otimização**: Buscar dados eficientemente para reduzir requisições

## Próximas Etapas (Lab03S02)

1. **Validação de Dados**: Verificar integridade dos dados coletados
2. **Análise Exploratória**: Primeira visualização dos dados
3. **Tratamento de Outliers**: Identificar e tratar valores extremos
4. **Relatório Intermediário**: Descrever dataset completo e hipóteses

## Como Executar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar token GitHub
# Copiar .env.example para .env e editar com seu token

# 3. Executar coleta
python src/main.py

# Outputs:
# - enunciado03/data/selected_repositories.csv
# - enunciado03/data/pr_metrics.csv
# - enunciado03/docs/RELATORIO_SPRINT1.txt
```

## Referências

- [GitHub API - Search Repositories](https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories)
- [GitHub API - Pull Requests](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
