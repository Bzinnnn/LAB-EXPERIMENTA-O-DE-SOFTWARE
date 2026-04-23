# ANÁLISE ESTATÍSTICA - Planejamento para Lab03S02 e Lab03S03

## Objetivo
Definir e justificar os testes estatísticos a serem utilizados para responder às 8 questões de pesquisa (RQs).

## Motivação

As questões de pesquisa buscam identificar **relações entre variáveis** em dados de Pull Requests do GitHub. Para isso, utilizaremos testes de **correlação estatística** que forneçam confiança nas análises.

## Variáveis de Interesse

### Variáveis Independentes (Preditoras)
1. **Tamanho**: files_changed, additions, deletions, total_changes
2. **Tempo de Análise**: time_to_review_hours
3. **Descrição**: description_length, has_description
4. **Interações**: comment_count, review_count, participant_count

### Variáveis Dependentes (Resposta)
1. **Feedback Final**: pr_status (MERGED=1, CLOSED=0) - Binária
2. **Número de Revisões**: review_count - Contagem/Contínua

## Testes Estatísticos Recomendados

### 1. Correlação de Spearman (Recomendado Primário)

**Quando usar:**
- ✓ Quando os dados **não são normalmente distribuídos** (caso típico em dados de GitHub)
- ✓ Para variáveis **ordinais ou contínuas**
- ✓ Para relações **monotônicas** (não necessariamente lineares)
- ✓ Quando há **outliers significativos**

**Características:**
- Teste não-paramétrico (não assume distribuição normal)
- Baseado em **ranks** (posições) dos dados
- Mais robusto que Pearson para dados reais
- Retorna coeficiente rho (ρ) entre -1 e 1
- p-value indica significância estatística

**RQs onde usar:** RQ05-RQ08 (número de revisões é contínua)

### 2. Correlação de Pearson (Secundário)

**Quando usar:**
- ✗ Normalmente, quando dados seguem distribuição normal
- Útil para **comparação** com Spearman

**Características:**
- Teste paramétrico (assume normalidade)
- Baseado em **covariância**
- Sensível a outliers
- Retorna coeficiente r entre -1 e 1

**RQs onde usar:** Como validação adicional (se dados forem normais)

### 3. Teste de Mann-Whitney U (para status binário)

**Quando usar:**
- ✓ Para comparar **dois grupos independentes**
- ✓ Quando a variável dependente é **binária** (MERGED vs CLOSED)
- ✓ Dados **não paramétricos**

**Características:**
- Testa se duas distribuições são diferentes
- Não assume normalidade
- Retorna estatística U e p-value

**RQs onde usar:** RQ01-RQ04 (status do PR é binária)

### 4. Teste de Regressão Logística

**Quando usar:**
- ✓ Para prever **probabilidade de MERGE** (variável binária)
- ✓ Com múltiplas variáveis independentes simultaneamente

**Características:**
- Retorna odd ratio (OR) e p-value
- Indica impacto de cada variável no MERGE
- Permite controlar confundidores

**RQs onde usar:** RQ01-RQ04 (análise mais avançada)

### 5. Regressão de Poisson/Negativa Binomial

**Quando usar:**
- ✓ Para **contar dados** (review_count)
- ✓ Quando há **over-dispersion** (variância > média)

**Características:**
- Apropriada para dados de contagem
- Retorna coeficientes interpretáveis
- Negativa Binomial mais flexível que Poisson

**RQs onde usar:** RQ05-RQ08 (número de revisões é contagem)

## Estratégia de Análise Proposta

### Etapa 1: Análise Descritiva (Lab03S02)
```
Para cada RQ:
1. Calcular estatísticas descritivas (mediana, IQR, etc)
2. Visualizar distribuições (histogramas, box plots)
3. Verificar presença de outliers
```

### Etapa 2: Testes de Correlação (Lab03S03)

**Para RQs 01-04 (Variável binária: MERGED vs CLOSED):**

```python
# Teste recomendado: Mann-Whitney U
from scipy.stats import mannwhitneyu

# Para cada métrica de tamanho, tempo, descrição, interações:
merged_prs = dados[dados['pr_status'] == 'MERGED']['metrica']
closed_prs = dados[dados['pr_status'] == 'CLOSED']['metrica']

statistic, p_value = mannwhitneyu(merged_prs, closed_prs, alternative='two-sided')

# Interpretação:
# p_value < 0.05: Diferença estatisticamente significativa
# Magnitude do efeito: calcular effect size (rank-biserial correlation)
```

**Complementar com Regressão Logística:**

```python
# Para entender simultaneamente o impacto de múltiplas variáveis
from sklearn.linear_model import LogisticRegression
from scipy.stats import chi2

# Model com todas as variáveis independentes
# Retorna coeficientes, odd ratios, p-values
```

**Para RQs 05-08 (Variável contínua: número de revisões):**

```python
# Teste recomendado: Correlação de Spearman
from scipy.stats import spearmanr

# Para cada métrica:
rho, p_value = spearmanr(dados['metrica'], dados['review_count'])

# Interpretação:
# rho > 0: correlação positiva (aumenta métrica, aumenta revisões)
# rho < 0: correlação negativa (aumenta métrica, diminui revisões)
# |rho| > 0.7: correlação forte
# |rho| < 0.3: correlação fraca
# p_value < 0.05: estatisticamente significativa
```

## Interpretação dos Resultados

### Força da Correlação
```
|r| ou |ρ|      Interpretação
0.0 - 0.3      Fraca
0.3 - 0.5      Moderada
0.5 - 0.7      Forte
0.7 - 1.0      Muito Forte
```

### Significância Estatística
```
p-value        Interpretação
< 0.001        Altamente significativa
0.001-0.01     Muito significativa
0.01-0.05      Significativa (limite)
> 0.05         Não significativa
```

### Effect Size (Tamanho do Efeito)
```
Cohen's d      Interpretação
0.2            Pequeno
0.5            Médio
0.8            Grande
```

## Procedimento Recomendado para cada RQ

### RQ01-RQ04 (Feedback Final)

1. **Estatística Descritiva**
   - Comparar medianas (MERGED vs CLOSED)
   - Calcular IQR

2. **Mann-Whitney U Test**
   - Testar diferença entre grupos
   - p-value < 0.05 → significativa

3. **Effect Size**
   - Rank-biserial correlation
   - Magnitude da diferença

4. **Visualização**
   - Box plot (MERGED vs CLOSED)
   - Distribuição da métrica por status

### RQ05-RQ08 (Número de Revisões)

1. **Estatística Descritiva**
   - Correlação Spearman
   - r ou ρ + p-value

2. **Verificar Normalidade (complementar)**
   - Teste Shapiro-Wilk
   - Se normal: Pearson como controle

3. **Validação Robustez**
   - Remover outliers extremos
   - Recalcular correlação

4. **Visualização**
   - Scatter plot
   - Linha de tendência (se correlação forte)

## Justificativa da Escolha: Spearman vs Pearson

### Por que Spearman é mais adequado para este projeto:

1. **Dados Reais do GitHub:**
   - Distribuições são **não-normais** (skewed)
   - Presença de **outliers** frequentes
   - PRs muito pequenas coexistem com PRs gigantes

2. **Características dos Dados:**
   - Contagens (files, lines) têm distribuição Poisson/similar
   - Tempo de revisão tem distribuição log-normal
   - Comment count e participant_count têm distribuição heavy-tailed

3. **Robustez:**
   - Spearman é **resistente a outliers**
   - Não assume linearidade
   - Funciona bem com variáveis ordinais (ranking)

4. **Comparabilidade:**
   - Testes de correlação permitem comparação entre RQs
   - Escala consistente (ρ sempre entre -1 e 1)

### Quando usar Pearson como complemento:

- Para validar resultados de Spearman
- Se dados forem normalizados (log-transform)
- Para comparação com literatura externa

## Estrutura de Resultados Esperados

Para cada RQ, estruturar resultados assim:

```
RQ01. Tamanho vs Feedback Final

Hipótese: PRs menores têm maior chance de MERGE

Dados:
- MERGED: mediana=15 arquivos, IQR=[5, 40]
- CLOSED: mediana=22 arquivos, IQR=[8, 60]

Teste Mann-Whitney U:
- Estatística U = X
- p-value = 0.001 (significativa)
- Effect size (rank-biserial) = 0.35

Conclusão:
✓ Diferença SIGNIFICATIVA entre grupos
✓ PRs MERGED são menores que CLOSED
✓ Hipótese CONFIRMADA
```

## Ferramentas Python

```python
# Imports recomendados
import scipy.stats as stats
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
import seaborn as sns

# Funções úteis
stats.spearmanr()        # Correlação Spearman
stats.pearsonr()         # Correlação Pearson
stats.mannwhitneyu()     # Teste Mann-Whitney
stats.shapiro()          # Teste normalidade
stats.ranksums()         # Teste Wilcoxon
```

## Cronograma

### Lab03S02
- [ ] Implementar testes de normalidade
- [ ] Calcular correlações Spearman
- [ ] Primeira interpretação dos resultados

### Lab03S03
- [ ] Validar com Pearson
- [ ] Regressão logística/Poisson
- [ ] Visualizações finais
- [ ] Relatório com interpretação completa

---

**Nota:** Esta estratégia pode ser refinada durante a Lab03S02, quando tivermos visto a distribuição real dos dados coletados.
