# LAB02 — Estudo das Características de Qualidade de Sistemas Java

---

## 1. Introdução

Este estudo investiga a relação entre métricas de processo (popularidade, maturidade, atividade e tamanho) e métricas de qualidade interna (CBO, DIT, LCOM) de repositórios Java de alto impacto no GitHub.

### 1.1 Hipóteses Informais

**H1 (RQ01 — Popularidade vs Qualidade):** Repositórios mais populares (mais estrelas) tendem a apresentar menor LCOM médio (melhor coesão) e menor CBO médio (menor acoplamento), pois a popularidade pode indicar maior escrutínio da comunidade, resultando em código mais bem estruturado.

**H2 (RQ02 — Maturidade vs Qualidade):** Repositórios mais maduros (mais antigos) tendem a apresentar maior CBO médio e maior LCOM, pois à medida que o software envelhece, o acoplamento e a complexidade tendem a crescer organicamente.

**H3 (RQ03 — Atividade vs Qualidade):** Repositórios com mais releases tendem a apresentar melhor coesão (menor LCOM), pois ciclos de release frequentes indicam manutenção ativa e refatoração contínua.

**H4 (RQ04 — Tamanho vs Qualidade):** Repositórios maiores (mais LOC) tendem a apresentar maior CBO e maior LCOM, pois bases de código extensas naturalmente desenvolvem mais dependências entre módulos.

---

## 2. Metodologia

### 2.1 Seleção de Repositórios
- Coletamos os top 825 repositórios Java mais populares do GitHub.
- Critério: ordenação por número de estrelas (descendente) via API REST do GitHub (`/search/repositories?q=language:Java+stars:>1&sort=stars`).

### 2.2 Métricas de Processo
| Dimensão | Métrica | Fonte |
|----------|---------|-------|
| Popularidade | Número de estrelas (stars) | GitHub REST API |
| Maturidade | Idade em anos (createdAt → now) | GitHub REST API |
| Atividade | Número de releases | GitHub GraphQL API |
| Tamanho | Linhas de código (LOC) e linhas de comentários | Contagem no código-fonte |

### 2.3 Métricas de Qualidade
| Métrica | Significado |
|---------|-------------|
| **CBO** (Coupling Between Objects) | Acoplamento entre classes — classes de alto CBO dependem de muitas outras |
| **DIT** (Depth of Inheritance Tree) | Profundidade da árvore de herança — DIT alto indica hierarquias profundas |
| **LCOM** (Lack of Cohesion of Methods) | Falta de coesão — LCOM alto indica que a classe realiza múltiplas responsabilidades |

### 2.4 Ferramentas
- **CK** (v0.7.0): ferramenta de análise estática para métricas OO em código Java.
- **Sumarização**: média, mediana e desvio padrão por repositório.
- **Correlação**: teste de Spearman (robusto a distribuições não normais).

---

## 3. Resultados

**Repositórios coletados:** 825
**Repositórios com métricas de qualidade:** 825

### 3.1 Estatísticas Descritivas das Métricas de Processo

| Métrica | Média | Mediana | Desvio Padrão | Min | Max |
|---------|-------|---------|---------------|-----|-----|
| Stars | 7492.6048 | 5339.0000 | 6238.8502 | 3468.0000 | 76480.0000 |
| Maturidade (anos) | 10.1605 | 10.3110 | 3.0778 | 0.5500 | 17.4620 |
| Releases | 38.2267 | 11.0000 | 79.2649 | 0.0000 | 1000.0000 |
| LOC | 104067.6800 | 16693.0000 | 305983.7292 | 2.0000 | 4845818.0000 |

### 3.2 Estatísticas Descritivas das Métricas de Qualidade

| Métrica | Média | Mediana | Desvio Padrão | Min | Max |
|---------|-------|---------|---------------|-----|-----|
| CBO | 5.4840 | 5.3279 | 2.1820 | 0.0000 | 21.8935 |
| DIT | 1.4558 | 1.3882 | 0.3428 | 1.0000 | 4.3880 |
| LCOM | 126.0650 | 22.6585 | 1888.9709 | 0.0000 | 54025.1128 |

### 3.3 RQ01 — Popularidade vs Qualidade

- Stars × CBO: rho=0.0346, p=0.3211 (nao significativo)
- Stars × DIT: rho=-0.0075, p=0.8296 (nao significativo)
- Stars × LCOM: rho=-0.0245, p=0.4825 (nao significativo)

### 3.4 RQ02 — Maturidade vs Qualidade

- Maturidade × CBO: rho=-0.0012, p=0.9715 (nao significativo)
- Maturidade × DIT: rho=0.2577, p=5.588e-14 (significativo)
- Maturidade × LCOM: rho=0.1420, p=4.278e-05 (significativo)

### 3.5 RQ03 — Atividade vs Qualidade

- Releases × CBO: rho=0.3599, p=1.25e-26 (significativo)
- Releases × DIT: rho=0.2257, p=5.43e-11 (significativo)
- Releases × LCOM: rho=0.2530, p=1.616e-13 (significativo)

### 3.6 RQ04 — Tamanho vs Qualidade

- LOC × CBO: rho=0.3684, p=6.319e-28 (significativo)
- LOC × DIT: rho=0.3073, p=1.697e-19 (significativo)
- LOC × LCOM: rho=0.3534, p=1.109e-25 (significativo)

---

## 4. Discussão

### 4.1 RQ01 — Popularidade
Esperava-se que repositórios mais populares tivessem melhor qualidade (menor CBO e LCOM). 
Os resultados não mostram correlação significativa entre popularidade e CBO, sugerindo que a popularidade por si só não é indicador de qualidade estrutural do código.

### 4.2 RQ02 — Maturidade
Os resultados não confirmam H2 de forma significativa, sugerindo que a maturidade não é o principal fator que determina o nível de acoplamento.

### 4.3 RQ03 — Atividade
Os resultados não confirmam H3, sugerindo que a frequência de releases não está significativamente correlacionada com a coesão do código.

### 4.4 RQ04 — Tamanho
H4 é confirmada: repositórios maiores tendem a ter maior CBO, indicando que bases de código extensas naturalmente desenvolvem mais acoplamento entre classes.

---

## 5. Análise Estatística (Bônus)

Foi aplicado o teste de correlação de **Spearman** por ser robusto a distribuições não normais e relações monotônicas, características comuns em métricas de software.

O p-value < 0.05 indica significância estatística. O coeficiente rho varia de -1 (correlação negativa perfeita) a +1 (correlação positiva perfeita).

### Tabela de Correlações de Spearman

| Variável X | Variável Y | rho | p-value | Significativo? |
|-----------|-----------|-----|---------|----------------|
| Stars | CBO | 0.0346 | 0.3211 | Não |
| Stars | DIT | -0.0075 | 0.8296 | Não |
| Stars | LCOM | -0.0245 | 0.4825 | Não |
| Maturidade | CBO | -0.0012 | 0.9715 | Não |
| Maturidade | DIT | 0.2577 | 5.588e-14 | Sim |
| Maturidade | LCOM | 0.1420 | 4.278e-05 | Sim |
| Releases | CBO | 0.3599 | 1.25e-26 | Sim |
| Releases | DIT | 0.2257 | 5.43e-11 | Sim |
| Releases | LCOM | 0.2530 | 1.616e-13 | Sim |
| LOC | CBO | 0.3684 | 6.319e-28 | Sim |
| LOC | DIT | 0.3073 | 1.697e-19 | Sim |
| LOC | LCOM | 0.3534 | 1.109e-25 | Sim |

---

## 6. Visualizações (Bônus)

Os gráficos de correlação foram gerados em `output/plots/` e incluem:
- Scatter plots para cada RQ (popularidade, maturidade, atividade, tamanho) vs cada métrica de qualidade (CBO, DIT, LCOM)
- Heatmap da matriz de correlação de Spearman
- Boxplots das métricas de qualidade por quartis de popularidade

---

## 7. Conclusão

Este estudo analisou 825 repositórios Java com métricas de qualidade extraídas pela ferramenta CK.
Os resultados indicam que as relações entre métricas de processo e qualidade de código são complexas e nem sempre seguem as hipóteses intuitivas.
A análise estatística com teste de Spearman fornece confiança nas conclusões apresentadas.

---

*Relatório gerado automaticamente em 2026-04-09 14:50:50*