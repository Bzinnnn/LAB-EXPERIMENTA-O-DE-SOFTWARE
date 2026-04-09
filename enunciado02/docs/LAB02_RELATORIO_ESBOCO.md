# LAB02 - Estudo de Qualidade de Repositórios Java

## 1. Introdução
Este relatório apresenta a análise da relação entre métricas de processo de desenvolvimento e métricas de qualidade de código em repositórios Java.

Problema: entender se popularidade, maturidade, atividade e tamanho dos repositórios estão associados a variações em CBO, DIT e LCOM.

Hipóteses informais:
- H1 (RQ01): repositórios mais populares tendem a melhor qualidade.
- H2 (RQ02): repositórios mais maduros tendem a melhor qualidade.
- H3 (RQ03): repositórios mais ativos tendem a melhor qualidade.
- H4 (RQ04): repositórios maiores tendem a maior complexidade e acoplamento.

## 2. Metodologia
### 2.1 Coleta de dados (GitHub API)
- População: top-1.000 repositórios Java.
- Critério de busca: `language:Java stars:>1 sort:stars-desc`.
- Fonte: GitHub GraphQL API.
- Campos coletados: `nameWithOwner`, `stars`, `forks`, `createdAt`, `updatedAt`, `releases`, `openIssues`, `closedIssues`.

### 2.2 Medição de qualidade (CK)
- Ferramenta: CK.
- Métricas extraídas: CBO, DIT, LCOM.
- Nível de análise: classe.
- Sumarização: agregação por repositório.

### 2.3 Pipeline
1. Coletar os 1.000 repositórios.
2. Clonar repositórios.
3. Executar CK.
4. Consolidar dataset por repositório.
5. Analisar RQ01-RQ04.

### 2.4 Definição das métricas
Métricas de processo:
- Popularidade: estrelas.
- Tamanho: LOC e linhas de comentários.
- Atividade: número de releases.
- Maturidade: idade do repositório (anos).

Métricas de qualidade:
- CBO.
- DIT.
- LCOM.

## 3. Modelagem dos Dados
Dataset consolidado: `data/lab02_consolidado.csv`

Campos de processo:
- `stars`, `releases`, `maturityYears`, `sizeLoc`, `sizeComments`

Campos de qualidade:
- `cboMean`, `ditMean`, `lcomMean`

## 4. Resultados
Preencher para cada RQ com:
- Métricas utilizadas
- Média
- Mediana
- Desvio padrão

### RQ01 - Popularidade vs Qualidade
- Variável de processo: `stars`
- Qualidade: `cboMean`, `ditMean`, `lcomMean`
- Estatísticas:
  - CBO: média = ___ | mediana = ___ | desvio padrão = ___
  - DIT: média = ___ | mediana = ___ | desvio padrão = ___
  - LCOM: média = ___ | mediana = ___ | desvio padrão = ___
- Interpretação inicial: ___

### RQ02 - Maturidade vs Qualidade
- Variável de processo: `maturityYears`
- Qualidade: `cboMean`, `ditMean`, `lcomMean`
- Estatísticas:
  - CBO: média = ___ | mediana = ___ | desvio padrão = ___
  - DIT: média = ___ | mediana = ___ | desvio padrão = ___
  - LCOM: média = ___ | mediana = ___ | desvio padrão = ___
- Interpretação inicial: ___

### RQ03 - Atividade vs Qualidade
- Variável de processo: `releases`
- Qualidade: `cboMean`, `ditMean`, `lcomMean`
- Estatísticas:
  - CBO: média = ___ | mediana = ___ | desvio padrão = ___
  - DIT: média = ___ | mediana = ___ | desvio padrão = ___
  - LCOM: média = ___ | mediana = ___ | desvio padrão = ___
- Interpretação inicial: ___

### RQ04 - Tamanho vs Qualidade
- Variável de processo: `sizeLoc` e `sizeComments`
- Qualidade: `cboMean`, `ditMean`, `lcomMean`
- Estatísticas:
  - CBO: média = ___ | mediana = ___ | desvio padrão = ___
  - DIT: média = ___ | mediana = ___ | desvio padrão = ___
  - LCOM: média = ___ | mediana = ___ | desvio padrão = ___
- Interpretação inicial: ___

## 5. Análise e Discussão
- Comparar resultados observados com H1-H4.
- Discutir possíveis explicações para correlações fracas/fortes.
- Discutir impacto de vieses da amostra (somente top repositórios por estrelas).

## 6. Análise Estatística (Bônus)
- Teste sugerido: Spearman (ou Pearson).
- Relatar para cada RQ: coeficiente e p-value.
- Interpretar direção e intensidade da relação.

## 7. Visualizações (Bônus)
- Scatter plot: `stars` vs `lcomMean`
- Scatter plot: `maturityYears` vs `cboMean`
- Scatter plot: `releases` vs `ditMean`
- Heatmap de correlação entre variáveis de processo e qualidade

## 8. Conclusão
- Principais achados por RQ.
- Limitações do estudo.
- Próximos passos.
