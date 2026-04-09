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
- Coletamos os top 593 repositórios Java mais populares do GitHub.
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

**Repositórios coletados:** 593
**Repositórios com métricas de qualidade:** 593

### 3.1 Estatísticas Descritivas das Métricas de Processo

| Métrica | Média | Mediana | Desvio Padrão | Min | Max |
|---------|-------|---------|---------------|-----|-----|
| Stars | 13278.6189 | 8663.0000 | 13138.9940 | 5238.0000 | 124936.0000 |
| Maturidade (anos) | 10.2699 | 10.4480 | 3.2316 | 0.5500 | 17.4620 |
| Releases | 47.6543 | 14.0000 | 96.2270 | 0.0000 | 1000.0000 |
| LOC | 192100.2715 | 28913.0000 | 496590.1565 | 2.0000 | 5901633.0000 |

### 3.2 Estatísticas Descritivas das Métricas de Qualidade

| Métrica | Média | Mediana | Desvio Padrão | Min | Max |
|---------|-------|---------|---------------|-----|-----|
| CBO | 5.5093 | 5.4239 | 2.2572 | 0.0000 | 19.5240 |
| DIT | 1.4587 | 1.3926 | 0.3634 | 1.0000 | 4.3880 |
| LCOM | 157.2685 | 22.9016 | 2226.4043 | 0.0000 | 54025.1128 |

### 3.3 RQ01 — Popularidade vs Qualidade

- Stars × CBO: rho=-0.0860, p=0.03631 (significativo)
- Stars × DIT: rho=-0.0800, p=0.05139 (nao significativo)
- Stars × LCOM: rho=-0.1044, p=0.01093 (significativo)

### 3.4 RQ02 — Maturidade vs Qualidade

- Maturidade × CBO: rho=0.0211, p=0.6076 (nao significativo)
- Maturidade × DIT: rho=0.3236, p=6.325e-16 (significativo)
- Maturidade × LCOM: rho=0.1664, p=4.665e-05 (significativo)

### 3.5 RQ03 — Atividade vs Qualidade

- Releases × CBO: rho=0.3738, p=4.23e-21 (significativo)
- Releases × DIT: rho=0.2407, p=2.908e-09 (significativo)
- Releases × LCOM: rho=0.2331, p=9.236e-09 (significativo)

### 3.6 RQ04 — Tamanho vs Qualidade

- LOC × CBO: rho=0.4000, p=3.413e-24 (significativo)
- LOC × DIT: rho=0.2583, p=1.716e-10 (significativo)
- LOC × LCOM: rho=0.3022, p=5.528e-14 (significativo)

---

## 4. Discussão

### 4.1 RQ01 — Popularidade
Esperava-se que repositórios mais populares tivessem melhor qualidade (menor CBO e LCOM). 
Os resultados confirmam parcialmente H1: há uma correlação negativa significativa entre popularidade e CBO.

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
| Stars | CBO | -0.0860 | 0.03631 | Sim |
| Stars | DIT | -0.0800 | 0.05139 | Não |
| Stars | LCOM | -0.1044 | 0.01093 | Sim |
| Maturidade | CBO | 0.0211 | 0.6076 | Não |
| Maturidade | DIT | 0.3236 | 6.325e-16 | Sim |
| Maturidade | LCOM | 0.1664 | 4.665e-05 | Sim |
| Releases | CBO | 0.3738 | 4.23e-21 | Sim |
| Releases | DIT | 0.2407 | 2.908e-09 | Sim |
| Releases | LCOM | 0.2331 | 9.236e-09 | Sim |
| LOC | CBO | 0.4000 | 3.413e-24 | Sim |
| LOC | DIT | 0.2583 | 1.716e-10 | Sim |
| LOC | LCOM | 0.3022 | 5.528e-14 | Sim |

---

## 6. Visualizações (Bônus)

Os gráficos de correlação foram gerados em `output/plots/` e incluem:
- Scatter plots para cada RQ (popularidade, maturidade, atividade, tamanho) vs cada métrica de qualidade (CBO, DIT, LCOM)
- Heatmap da matriz de correlação de Spearman
- Boxplots das métricas de qualidade por quartis de popularidade

---

## 7. Conclusão

Este estudo analisou 593 repositórios Java com métricas de qualidade extraídas pela ferramenta CK.
Os resultados indicam que as relações entre métricas de processo e qualidade de código são complexas e nem sempre seguem as hipóteses intuitivas.
A análise estatística com teste de Spearman fornece confiança nas conclusões apresentadas.

---

*Relatório gerado automaticamente em 2026-04-09 11:48:07*