# Analise de Repositorios Populares do GitHub
## Relatorio Inicial - Sprint 2

**Data de Coleta:** 05/03/2026 16:04:30
**Total de Repositorios Analisados:** 1000

## Hipoteses Iniciais:

### RQ1: Sistemas populares sao maduros/antigos?
- *Hipótese:* Repositórios populares tendem a ser mais antigos, pois ganharam estrelas ao longo do tempo.
- *Métrica calculada:* Idade mediana dos repositórios (dias)
- *Esperado:* > 1095 dias (3 anos)
- *Obtido:* 3061 dias (8.4 anos)
- *Status:* Confirmada


### RQ2: Sistemas populares recebem muita contribuicao externa?
- *Hipótese:* Projetos com maior visibilidade atraem mais contribuições externas.
- *Métrica calculada:* Mediana de pull requests aceitas
- *Esperado:* > 50 PRs
- *Obtido:* 739 PRs
- *Status:* Confirmada


### RQ3: Sistemas populares lancam releases com frequencia?
- *Hipótese:* Projetos maturos e ativos publicam releases regularmente.
- *Métrica calculada:* Mediana de número de releases
- *Esperado:* > 20 releases
- *Obtido:* 40 releases
- *Status:* Confirmada


### RQ4: Sistemas populares sao atualizados com frequencia?
- *Hipótese:* Projetos bem mantidos recebem commits e merges frequentemente, reduzindo este valor.
- *Métrica calculada:* Mediana de dias desde a última atualização
- *Esperado:* < 30 dias
- *Obtido:* 0 dias
- *Status:* Confirmada


### RQ5: Sistemas populares sao escritos nas linguagens mais populares?
- *Hipótese:* Linguagens populares (JavaScript, Python, etc.) devem predominar entre os top sistemas.
- *Métrica calculada:* Distribuição de linguagens primárias
- *Esperado:* > 40% (top 3 linguagens)
- *Obtido:* 47.5% (top 3 linguagens)
- *Status:* Confirmada


### RQ6: Sistemas populares possuem alto percentual de issues fechadas?
- *Hipótese:* Projetos bem gerenciados fecham a maior parte das issues abertas.
- *Métrica calculada:* Mediana da razão de issues fechadas
- *Esperado:* > 70% (0.7)
- *Obtido:* 86.79% (0.87)
- *Status:* Confirmada


## Estatisticas Gerais
- Idade mediana: 3061 dias (8.4 anos)
- PRs aceitas mediana: 739
- Releases mediana: 40
- Dias desde atualizacao mediana: 0
- Razao issues fechadas mediana: 86.79%

## Distribuicao de Linguagens (Top 15)

| Linguagem | Repositórios | Percentual |
| --- | --- | --- |
| Python | 200 | 20.0% |
| TypeScript | 160 | 16.0% |
| JavaScript | 115 | 11.5% |
| Unknown | 95 | 9.5% |
| Go | 77 | 7.7% |
| Rust | 54 | 5.4% |
| Java | 47 | 4.7% |
| C++ | 46 | 4.6% |
| C | 25 | 2.5% |
| Jupyter Notebook | 23 | 2.3% |
| Shell | 21 | 2.1% |
| HTML | 18 | 1.8% |
| Ruby | 12 | 1.2% |
| C# | 11 | 1.1% |
| Kotlin | 10 | 1.0% |

## RQ07: Analise por Linguagem
- *Hipótese:* Sistemas em linguagens mais populares recebem mais PRs, fazem mais releases e são atualizados com mais frequencia.

### Comparação de Métricas por Linguagem (Top 10)

Linguagem | Repositórios | PRs mediana | Releases mediana | Dias desde atualização
--- | --- | --- | --- | ---
Python | 200 | 631 | 23 | 0
TypeScript | 160 | 2582 | 158 | 0
JavaScript | 115 | 576 | 40 | 0
Unknown | 95 | 129 | 0 | 0
Go | 77 | 1690 | 132 | 0
Rust | 54 | 2370 | 76 | 0
Java | 47 | 605 | 42 | 0
C++ | 46 | 982 | 63 | 0
C | 25 | 145 | 39 | 0
Jupyter Notebook | 23 | 88 | 0 | 0

**Análise:** Linguagens populares como Python, TypeScript e JavaScript mostram padrões de contribuição e manutenção.
