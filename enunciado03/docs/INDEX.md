# ÍNDICE - LAB03S01 - Enunciado 3

## 📂 Estrutura de Pastas

```
enunciado03/
├── src/                           # Scripts Python
│   ├── __init__.py
│   ├── main.py                    # Orquestrador principal
│   ├── repository_selector.py     # Seleção de repositórios
│   ├── pr_metrics.py              # Coleta de PRs e métricas
│   └── github_query.py            # Utilitários GitHub API
│
├── data/                          # Dados coletados (outputs)
│   ├── selected_repositories.csv  # Lista de 200 repositórios
│   └── pr_metrics.csv             # Métricas de todos os PRs
│
├── docs/                          # Documentação
│   ├── METODOLOGIA_SPRINT1.md     # Metodologia detalhada
│   ├── ANALISE_ESTATISTICA_PLANEJADA.md  # Testes estatísticos
│   └── RELATORIO_SPRINT1.txt      # Relatório gerado automaticamente
│
├── README.md                      # Visão geral do projeto
├── GUIA_EXECUCAO.txt              # Passo a passo de execução
├── RESUMO_LAB03S01.txt            # Sumário executivo
├── requirements.txt               # Dependências Python
├── .env.example                   # Template de configuração
├── .gitignore                     # Arquivos a ignorar
└── INDEX.md                       # Este arquivo
```

## 📄 Guia de Arquivos

### Scripts Python

#### `src/main.py`
- **Propósito**: Orquestrador principal da coleta
- **O que faz**: Executa seleção de repos → coleta de PRs → geração de relatório
- **Como usar**: `python src/main.py`
- **Output**: CSVs + relatório inicial

#### `src/repository_selector.py`
- **Propósito**: Selecionar repositórios populares
- **Classe**: `RepositorySelector`
- **Métodos principais**:
  - `get_popular_repositories()`: Top 200 com ≥100 PRs
  - `save_repositories()`: Salvar em CSV
  - `display_summary()`: Exibir estatísticas
- **Como usar**: `python src/repository_selector.py`

#### `src/pr_metrics.py`
- **Propósito**: Coletar PRs e calcular métricas
- **Classe**: `PRMetricsCollector`
- **Métodos principais**:
  - `calculate_pr_metrics()`: Calcular uma métrica
  - `collect_prs_from_repository()`: Coletar de um repo
  - `collect_from_multiple_repositories()`: Coletar de vários
  - `save_pr_data()`: Salvar em CSV
- **Como usar**: Importar em main.py ou usar diretamente

#### `src/github_query.py`
- **Propósito**: Utilitários para GitHub API
- **Classe**: `GitHubClient`
- **Como usar**: `python src/github_query.py` (teste de conexão)

### Documentação

#### `docs/METODOLOGIA_SPRINT1.md`
- Critérios de seleção detalhados
- Estrutura do dataset
- Descrição de cada métrica
- Fluxo de execução

#### `docs/ANALISE_ESTATISTICA_PLANEJADA.md`
- Testes estatísticos recomendados
- Justificativa: Spearman vs Pearson
- Estratégia de análise
- Interpretação de resultados

#### `docs/RELATORIO_SPRINT1.txt`
- Gerado automaticamente por main.py
- Resumo dos repositórios selecionados
- Estatísticas iniciais
- Hipóteses para análise futura

### Arquivos de Configuração

#### `requirements.txt`
- PyGithub: Cliente Python para GitHub API
- pandas: Manipulação de dados
- requests: HTTP requests
- scipy: Testes estatísticos
- numpy: Operações numéricas
- python-dotenv: Carregar variáveis de ambiente

#### `.env.example`
- Template para configuração
- Deve ser copiado para `.env`
- Nunca versioná-lo com dados reais

#### `.gitignore`
- Ignora .env (tokens reais)
- Ignora CSVs grandes (opcionalmente)
- Ignora cache Python

### Guias e Sumários

#### `README.md`
- Visão geral do projeto
- Estrutura de pastas
- Instruções básicas de execução

#### `GUIA_EXECUCAO.txt`
- **Referência**: Passo a passo completo de execução
- **Use quando**: Quiser instruções detalhadas
- **Seções**:
  - Pré-requisitos
  - Passo a passo (5 etapas)
  - Troubleshooting
  - Próximos passos

#### `RESUMO_LAB03S01.txt`
- **Referência**: Resumo executivo
- **Use quando**: Quiser overview rápido
- **Seções**:
  - Objetivos
  - Arquivos criados
  - Questões de pesquisa
  - Métricas
  - Hipóteses
  - Próximas sprints

#### `INDEX.md` (este arquivo)
- Mapa completo do projeto
- Descrição de cada arquivo
- Fluxo de uso

## 🚀 Fluxo de Execução

### Primeira Vez
```
1. Ler: README.md (overview)
2. Ler: GUIA_EXECUCAO.txt (instruções)
3. Executar: python src/main.py
4. Gerar: data/selected_repositories.csv + data/pr_metrics.csv
5. Revisar: docs/RELATORIO_SPRINT1.txt
```

### Próximas Vezes
```
1. Se editar código: Testar script específico
2. Para continuar coleta: Executar novamente (é incremental)
3. Consultar GUIA_EXECUCAO.txt para troubleshooting
```

## 📊 Dados Gerados

### `data/selected_repositories.csv`
**Colunas:**
- full_name, owner, name, stars, forks, language, pr_count, url

**Linha exemplo:**
```
facebook/react,facebook,react,200000,45000,JavaScript,2500,https://github.com/facebook/react
```

**Linhas esperadas:** ~200 (ou menos se alguns repos não tiverem 100 PRs)

### `data/pr_metrics.csv`
**Colunas principais:**
- repository, pr_number, pr_title, pr_status
- files_changed, additions, deletions, total_changes
- time_to_review_hours
- description_length, has_description
- comment_count, review_count, participant_count
- author, url

**Linhas esperadas:** Variável (N PRs coletados)

**Exemplo de linha:**
```
facebook/react,12345,Fix: performance optimization,MERGED,
5,120,45,165,2.5,250,1,3,2,5,
username@github,https://github.com/facebook/react/pull/12345,user1,user2,user3
```

## ✅ Verificação de Sucesso

### Após executar os scripts
- [ ] Arquivo `selected_repositories.csv` existe e não está vazio
- [ ] Arquivo `pr_metrics.csv` existe e não está vazio
- [ ] Arquivo `RELATORIO_SPRINT1.txt` foi gerado
- [ ] Nenhuma mensagem de erro no console
- [ ] Rate limit não foi atingido (aviso no console)

### Validação de dados
- [ ] Todos os CSVs têm colunas esperadas
- [ ] Nenhuma linha com valores inválidos
- [ ] time_to_review_hours ≥ 1 em todas as linhas
- [ ] review_count ≥ 1 em todas as linhas
- [ ] pr_status é sempre "MERGED" ou "CLOSED"

## 🔧 Troubleshooting Rápido

| Problema | Solução | Arquivo para ler |
|----------|---------|------------------|
| "GITHUB_TOKEN não configurado" | Criar .env com token | GUIA_EXECUCAO.txt |
| "Rate limit atingido" | Aguardar 1 hora | GUIA_EXECUCAO.txt |
| Scripts muito lentos | É normal, aguarde | GUIA_EXECUCAO.txt |
| CSVs vazios | Verificar token/filtros | GUIA_EXECUCAO.txt |
| Como executar | Ver passo a passo | GUIA_EXECUCAO.txt |

## 📋 Próximas Etapas

### Lab03S02 (Continuação)
- Validar dados coletados
- Análise exploratória
- Primeira aplicação de testes estatísticos
- Atualizar relatório

### Lab03S03 (Finalização)
- Análise estatística completa (Spearman, Mann-Whitney, etc)
- Visualizações avançadas
- Relatório final com conclusões

**Mais detalhes:** Ver RESUMO_LAB03S01.txt

## 📚 Recursos Externos

- [GitHub REST API](https://docs.github.com/en/rest)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [GitHub Personal Tokens](https://github.com/settings/tokens)
- [scipy.stats Documentation](https://docs.scipy.org/doc/scipy/reference/stats.html)

## 📞 Suporte

Se encontrar problemas:
1. Consulte GUIA_EXECUCAO.txt - Seção "Possíveis Problemas"
2. Verifique se GITHUB_TOKEN está configurado
3. Teste conexão: `python src/github_query.py`
4. Verifique logs no console
5. Consulte documentação oficial (links acima)

---

**Última atualização:** Lab03S01 concluído ✅

**Próximo passo:** Lab03S02 - Validação e análise inicial
