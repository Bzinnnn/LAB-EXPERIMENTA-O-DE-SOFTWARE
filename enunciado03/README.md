# Enunciado 3 - Caracterizando a atividade de code review no GitHub

## Objetivo
Analisar a atividade de code review desenvolvida em repositórios populares do GitHub, identificando variáveis que influenciam no merge de um PR.

## Sprint 1 (Lab03S01)
- Lista de repositórios selecionados
- Criação do script de coleta dos PRs e das métricas definidas

## Estrutura de Pastas
```
enunciado03/
├── src/
│   ├── main.py
│   ├── github_query.py
│   ├── pr_metrics.py
│   └── repository_selector.py
├── data/
│   └── (arquivos de dados gerados)
├── docs/
├── requirements.txt
└── README.md
```

## Como Executar

### 1. Configurar variáveis de ambiente
Criar um arquivo `.env` na raiz do projeto com:
```
GITHUB_TOKEN=seu_token_aqui
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Executar a coleta
```bash
python src/main.py
```

Tempo esperado: ~45 minutos ⚡ (otimizado)

## Métricas Coletadas

### Tamanho do PR
- Número de arquivos alterados
- Total de linhas adicionadas
- Total de linhas removidas

### Tempo de Análise
- Intervalo entre criação e última atividade (em horas)

### Descrição
- Número de caracteres do corpo da descrição (markdown)

### Interações
- Número de participantes
- Número de comentários

## Requisitos de Seleção
- Repositórios: Top 200 repositórios mais populares do GitHub
- PRs com status: MERGED ou CLOSED
- Cada repositório com pelo menos 100 PRs (MERGED + CLOSED)
- PRs com pelo menos 1 revisão
- Tempo de revisão: mínimo 1 hora
