# Relatório Técnico: Caracterizando a Atividade de Code Review no GitHub

**Disciplina:** Laboratório de Experimentação de Software  
**Objetivo:** Analisar variáveis que influenciam o merge de Pull Requests (PRs) e o esforço de revisão em repositórios populares.

---

## 1. Introdução e Hipóteses

A prática de *Code Review* é um pilar fundamental no desenvolvimento moderno, servindo como filtro de qualidade antes da integração de código. No ecossistema GitHub, essa atividade é mediada por Pull Requests (PRs). Este estudo busca entender as correlações entre métricas de processo/produto e o resultado final da revisão.

### Hipóteses Informais
*   **H1 (Tamanho):** PRs maiores (mais linhas/arquivos) têm maior probabilidade de serem rejeitados (CLOSED) devido à complexidade e risco.
*   **H2 (Tempo):** PRs que demoram mais para serem analisados tendem a ser fechados sem merge, indicando indecisão ou perda de interesse.
*   **H3 (Descrição):** Descrições mais ricas facilitam a compreensão e aumentam as chances de MERGE.
*   **H4 (Interações):** Um alto volume de comentários indica conflitos ou necessidade de muitas correções, correlacionando-se negativamente com o MERGE.
*   **H5 (Esforço):** O número de revisões cresce linearmente com o tamanho do PR e o número de participantes.

---

## 2. Metodologia

### 2.1 Coleta de Dados
O dataset foi composto por PRs de 200 repositórios populares do GitHub, filtrando apenas aqueles com:
- Status **MERGED** ou **CLOSED**.
- Pelo menos uma revisão humana (campo `review`).
- Duração superior a uma hora (para excluir automações/bots).

### 2.2 Métricas Definidas
- **Tamanho:** Total de arquivos, adições e remoções.
- **Tempo:** Intervalo em horas entre criação e conclusão.
- **Descrição:** Contagem de caracteres no corpo do PR.
- **Interações:** Número de participantes e comentários.

### 2.3 Análise Estatística
Utilizamos a **Correlação de Spearman ($\rho$)**. 
- **Justificativa:** As métricas de software (linhas de código, tempo, comentários) raramente seguem uma distribuição normal, apresentando frequentemente caudas longas e *outliers*. O teste de Spearman é não-paramétrico e avalia a relação monotônica entre variáveis, sendo mais robusto que o de Pearson para este tipo de dado.

---

## 3. Resultados e Análise Visual

Abaixo, apresentamos a matriz de correlação completa que norteia nossas respostas às RQs.

![Matriz de Correlação de Spearman](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/correlation_heatmap.png)

### Dimensão A: Feedback Final das Revisões (Status do PR)

| Métrica (Mediana) | CLOSED | MERGED | Correlação com Status* |
| :--- | :---: | :---: | :---: |
| Total de Mudanças (Linhas) | 89.0 | 120.0 | 0.077 |
| Tempo de Análise (Horas) | 195.32 | 48.25 | -0.261 |
| Tamanho da Descrição (Chars) | 706.0 | 675.0 | 0.051 |
| Número de Comentários | 2.0 | 1.0 | -0.109 |
*\*Status: 0=Closed, 1=Merged*

#### RQ 01. Relação entre Tamanho e Feedback
Contra-intuitivamente, a mediana de linhas alteradas em PRs aceitos (120) é superior aos rejeitados (89). A correlação é positiva mas muito fraca (0.07). Isso sugere que o tamanho, isoladamente, não é o principal fator de rejeição em projetos maduros.

![Distribuição de Tamanho vs Status](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/size_vs_status.png)

#### RQ 02. Relação entre Tempo e Feedback
O tempo apresentou a correlação negativa mais forte com o sucesso do PR (-0.26). PRs rejeitados permanecem no "limbo" por uma mediana de **195 horas (~8 dias)**, enquanto os aceitos são resolvidos em **48 horas**.

Para uma visão mais profunda da distribuição temporal, a Função de Distribuição Acumulada (CDF) abaixo demonstra a probabilidade de um PR ser resolvido ao longo do tempo. Nota-se claramente que a curva de PRs MERGED ascende rapidamente nas primeiras 48h, enquanto a curva CLOSED se arrasta de forma assimptótica ao longo de semanas.

![CDF Tempo vs Status](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/cdf_time_status.png)

![Tempo de Análise vs Status](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/time_vs_status.png)

#### RQ 03. Relação entre Descrição e Feedback
A diferença nas medianas é negligenciável (706 vs 675). A correlação de 0.05 indica que a verbosidade da descrição não dita o sucesso do merge.

#### RQ 04. Relação entre Interações e Feedback
O número de comentários tem correlação negativa (-0.10). PRs que geram debate excessivo tendem a ser mais difíceis de aprovar.

![Distribuição de Comentários](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/comments_vs_status.png)

---

### Dimensão B: Número de Revisões

| Correlação com Número de Revisões | Coeficiente ($\rho$) | P-Value |
| :--- | :---: | :---: |
| **Participantes** | **0.797** | < 0.001 |
| **Total de Mudanças** | **0.414** | < 0.001 |
| **Arquivos Alterados** | **0.367** | < 0.001 |
| **Tempo de Análise** | **0.163** | < 0.001 |

#### RQ 05 e 06. Tamanho e Tempo vs Número de Revisões
O tamanho do PR tem um impacto moderado-alto no esforço (0.41). Como demonstrado no gráfico abaixo, PRs classificados como "Extra Large" demandam significativamente mais revisões.

![Revisões por Quartil de Tamanho](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/size_quartile_vs_reviews.png)

#### RQ 07. Descrição vs Número de Revisões
A relação é fraca (0.09), indicando que revisores focam mais no código do que na documentação anexa para decidir o número de ciclos de revisão.

#### RQ 08. Interações vs Número de Revisões
Esta é a correlação mais forte encontrada (**0.79**). O número de participantes é um preditor quase linear do número de revisões, sugerindo que a complexidade social é o maior driver de esforço no code review.

![Densidade de Descrição vs Revisões](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/desc_vs_reviews.png)

---

## 4. Análises Multidimensionais Avançadas

Para capturar interações complexas que testes uni ou bivariados não revelam, expandimos a análise para dimensões simultâneas.

### 4.1 O "Cone de Atrito" (Tempo vs Tamanho vs Engajamento)
No gráfico de bolhas abaixo, observamos o relacionamento simultâneo entre Tamanho (eixo X), Tempo (eixo Y), Status (Cor) e Número de Comentários (Tamanho da Bolha). O quadrante superior esquerdo (alto tempo, baixo tamanho) é dominado por PRs vermelhos (CLOSED) com alta densidade de comentários. Isso indica um fenômeno de "atrito": pequenos PRs que geram muito debate rapidamente perdem tração e são abandonados.

![Análise Multidimensional](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/multidimensional_bubble.png)

### 4.2 Matriz de Interações de Variáveis Críticas (PairGrid)
A matriz emparelhada revela a densidade conjunta das variáveis mais preditivas. Observa-se que PRs aprovados formam picos de densidade extremamente concentrados e esguios (indicando previsibilidade de processo), enquanto PRs rejeitados espalham-se difusamente, caracterizando anomalias ou falhas processuais no ciclo de vida do código.

![PairGrid de Interações](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/pairgrid_interactions.png)

### 4.3 Elasticidade de Revisões por Envolvimento Social
A regressão linear com banda de confiança ilustra a elasticidade do esforço. O crescimento do número de revisões é muito mais íngreme e caótico (maior dispersão) em PRs rejeitados do que em aceitos à medida que mais participantes entram. Quando a discussão incha (muitos participantes), PRs MERGED mantêm uma proporção saudável de revisões focadas, enquanto PRs CLOSED tendem à entropia de revisões inconclusivas.

![Regressão Participantes vs Revisões](file:///c:/Users/jotaa/.gemini/antigravity/brain/f6967809-19e8-4af3-93ea-ba80da14735a/artifacts/regression_participants_reviews.png)

---

## 5. Discussão e Conclusão


### Comparação com Hipóteses
1.  **H1 (Tamanho): Refutada.** PRs maiores não foram mais rejeitados; na verdade, a mediana de tamanho dos aceitos foi maior. Isso pode indicar que contribuidores experientes (que fazem PRs maiores) têm maior taxa de aceitação.
2.  **H2 (Tempo): Confirmada.** O tempo é o maior inimigo do merge. A demora sinaliza problemas ou falta de prioridade que levam ao fechamento.
3.  **H3 (Descrição): Refutada.** Não houve vantagem estatística clara para descrições longas.
4.  **H4 (Interações): Confirmada.** Mais comentários correlacionam-se levemente com a rejeição.
5.  **H5 (Esforço): Confirmada.** O esforço (número de revisões) é fortemente dominado pelo número de pessoas envolvidas e pelo volume de código.

### Considerações Finais
A análise demonstra que a dinâmica de code review no GitHub é fortemente influenciada pelo **fator humano (participantes)** e pela **agilidade (tempo)**. Para aumentar as chances de sucesso, o foco deve ser na resolução rápida de discussões, uma vez que o prolongamento da análise é um preditor consistente de rejeição.
