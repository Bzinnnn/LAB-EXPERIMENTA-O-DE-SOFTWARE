# Lab02S01 - Sprint 1: Análise de Repositórios Java

## ✅ Entregáveis

1. **Lista dos 1.000 repositórios Java** → `data/2026_spring1_repositorios.csv`
2. **Script de Automação** → `src/sprint1.py`
3. **Métricas de 1 repositório** → `ck_results/*/processed_class_metrics.csv`

## 🚀 Como Executar

### 1. Configurar Token GitHub

```bash
# Copiar template
cp .env.example .env

# Editar .env e adicionar seu token:
# GITHUB_TOKEN=seu_token_github_aqui
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Executar Sprint 1

```bash
cd src
python sprint1.py
```

## ⏱️ Tempo Esperado

- **Coleta de repos:** 5-10 minutos
- **Enriquecimento de dados:** 2-3 minutos
- **Análise CK:** 2-5 minutos
- **TOTAL:** 10-20 minutos

## 📊 Arquivos Gerados

```
data/
├── 2026_spring1_repositorios.csv    ← 1.000 repositórios
└── sprint1_relatorio.txt            ← Relatório

ck_results/
└── owner_repo/
    ├── class_metrics.csv
    └── processed_class_metrics.csv  ← Métricas sumarizadas
```

## 🔧 Pré-requisitos

- Python 3.8+
- Java 8+
- Git
- GitHub Token (em https://github.com/settings/tokens)

## ✨ Funcionalidades

- ✅ Coleta de 1.000 repositórios Java mais populares
- ✅ Enriquecimento com PRs e releases (paralelo)
- ✅ Clone automático do repositório mais popular
- ✅ Análise de qualidade com CK
- ✅ Sumarização de métricas (CBO, DIT, LCOM)
- ✅ Geração de relatório

## 📝 Estrutura

```
src/
├── sprint1.py              ← Script principal (execute este!)
├── github_query.py         ← Busca repositórios via GraphQL
├── data_processor.py       ← Processamento de dados
├── repository_cloner.py    ← Clone e validação
└── ck_runner.py            ← Execução da ferramenta CK
```

## 💡 Dúvidas?

Consulte `docs/enunciado_sprint1.md` para detalhes da Sprint 1.
