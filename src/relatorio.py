import os
import sys
import time
import csv
from typing import List, Dict
from collections import Counter

# Obter o diretório base do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')

class ReportGenerator:
    
    def __init__(self):
        self.repositories: List[Dict] = []
    
    def load_from_csv(self, filename: str) -> bool:
        if not os.path.exists(filename):
            print(f"Arquivo {filename} não encontrado")
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    repo = {
                        "nameWithOwner": row.get("nameWithOwner", ""),
                        "owner": row.get("owner", ""),
                        "description": row.get("description", ""),
                        "primaryLanguage": row.get("primaryLanguage", "Unknown"),
                        "stars": int(row.get("stars", 0)),
                        "forks": int(row.get("forks", 0)),
                        "createdAt": row.get("createdAt", ""),
                        "updatedAt": row.get("updatedAt", ""),
                        "repositoryAge": int(row.get("repositoryAge", 0)),
                        "daysSinceUpdate": int(row.get("daysSinceUpdate", 0)),
                        "mergedPullRequests": int(row.get("mergedPullRequests", 0)),
                        "releases": int(row.get("releases", 0)),
                        "openIssues": int(row.get("openIssues", 0)),
                        "closedIssues": int(row.get("closedIssues", 0)),
                        "totalIssues": int(row.get("totalIssues", 0)),
                        "closedIssuesRatio": float(row.get("closedIssuesRatio", 0)),
                        "watchers": int(row.get("watchers", 0)),
                        "url": row.get("url", "")
                    }
                    self.repositories.append(repo)
            
            print(f"✓ {len(self.repositories)} repositorios carregados de {filename}")
            return True
        except Exception as e:
            print(f"Erro ao carregar CSV: {str(e)}")
            return False
    
    def generate_initial_report(self, output_file: str = None):
        if not self.repositories:
            print("Nenhum repositorio para gerar relatorio")
            return
        
        if output_file is None:
            output_file = os.path.join(DOCS_DIR, 'relatorio_inicial.md')

        stats = self._calculate_statistics()
        language_stats = self._analyze_by_language()

        def rq_section(number, question, metric_desc, hypothesis, expected, actual):
            status = "✓ Confirmada" if self._check_hypothesis(expected, actual) else "✗ Não confirmada"
            return (
                f"### RQ{number}: {question}\n"
                f"- *Hipótese:* {hypothesis}\n"
                f"- *Métrica calculada:* {metric_desc}\n"
                f"- *Esperado:* {expected}\n"
                f"- *Obtido:* {actual}\n"
                f"- *Status:* {status}\n\n"
            )

        content = []
        content.append("# Analise de Repositorios Populares do GitHub")
        content.append("## Relatorio Inicial - Sprint 2\n")
        content.append(f"**Data de Coleta:** {time.strftime('%d/%m/%Y %H:%M:%S')}")
        content.append(f"**Total de Repositorios Analisados:** {len(self.repositories)}\n")

        content.append("## Hipoteses Iniciais:\n")
        content.append(rq_section(1,
                          "Sistemas populares sao maduros/antigos?",
                          "Idade mediana dos repositórios (dias)",
                          "Repositórios populares tendem a ser mais antigos, pois ganharam estrelas ao longo do tempo.",
                          "> 1095 dias (3 anos)",
                          f"{stats['age']['median']} dias ({stats['age']['median']/365:.1f} anos)"))
        
        content.append(rq_section(2,
                          "Sistemas populares recebem muita contribuicao externa?",
                          "Mediana de pull requests aceitas",
                          "Projetos com maior visibilidade atraem mais contribuições externas.",
                          "> 50 PRs",
                          f"{stats['pr']['median']} PRs"))
        
        content.append(rq_section(3,
                          "Sistemas populares lancam releases com frequencia?",
                          "Mediana de número de releases",
                          "Projetos maturos e ativos publicam releases regularmente.",
                          "> 20 releases",
                          f"{stats['releases']['median']} releases"))
        
        content.append(rq_section(4,
                          "Sistemas populares sao atualizados com frequencia?",
                          "Mediana de dias desde a última atualização",
                          "Projetos bem mantidos recebem commits e merges frequentemente, reduzindo este valor.",
                          "< 30 dias",
                          f"{stats['update']['median']} dias"))
        
        # RQ05: Top 3 linguagens
        top_3_langs = self._get_top_languages_percentage()
        content.append(rq_section(5,
                          "Sistemas populares sao escritos nas linguagens mais populares?",
                          "Distribuição de linguagens primárias",
                          "Linguagens populares (JavaScript, Python, etc.) devem predominar entre os top sistemas.",
                          "> 40% (top 3 linguagens)",
                          f"{top_3_langs:.1f}% (top 3 linguagens)"))
        
        content.append(rq_section(6,
                          "Sistemas populares possuem alto percentual de issues fechadas?",
                          "Mediana da razão de issues fechadas",
                          "Projetos bem gerenciados fecham a maior parte das issues abertas.",
                          "> 70% (0.7)",
                          f"{stats['closed_ratio']['median']*100:.2f}% ({stats['closed_ratio']['median']:.2f})"))

        content.append("## Estatisticas Gerais")
        content.append(f"- Idade mediana: {stats['age']['median']} dias ({stats['age']['median']/365:.1f} anos)")
        content.append(f"- PRs aceitas mediana: {stats['pr']['median']}")
        content.append(f"- Releases mediana: {stats['releases']['median']}")
        content.append(f"- Dias desde atualizacao mediana: {stats['update']['median']}")
        content.append(f"- Razao issues fechadas mediana: {stats['closed_ratio']['median']:.2%}\n")

        content.append("## Distribuicao de Linguagens (Top 15)")
        content.append(language_stats + "\n")

        def median(lst):
            s = sorted(lst)
            n = len(s)
            return int(s[n//2] if n%2 else (s[n//2-1] + s[n//2]) / 2)

        lang_metrics = {}
        for r in self.repositories:
            lang = r["primaryLanguage"]
            entry = lang_metrics.setdefault(lang, {"pr": [], "releases": [], "update": []})
            entry["pr"].append(r["mergedPullRequests"])
            entry["releases"].append(r["releases"])
            entry["update"].append(r["daysSinceUpdate"])

        rq07_lines = []
        rq07_lines.append("## RQ07: Analise por Linguagem")
        rq07_lines.append("- *Hipótese:* Sistemas em linguagens mais populares recebem mais PRs, fazem mais releases e são atualizados com mais frequencia.\n")
        rq07_lines.append("### Comparação de Métricas por Linguagem (Top 10)\n")
        rq07_lines.append("Linguagem | Repositórios | PRs mediana | Releases mediana | Dias desde atualização")
        rq07_lines.append("--- | --- | --- | --- | ---")
        for lang, data in sorted(lang_metrics.items(), key=lambda x: len(x[1]["pr"]), reverse=True)[:10]:
            count = len(data['pr'])
            rq07_lines.append(
                f"{lang} | {count} | {median(data['pr'])} | {median(data['releases'])} | {median(data['update'])}"
            )
        
        rq07_lines.append("\n**Análise:** Linguagens populares como Python, TypeScript e JavaScript mostram padrões de contribuição e manutenção.")
        content.append("\n".join(rq07_lines))

        report_content = "\n".join(content)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"\n✓ Relatorio inicial criado: {output_file}")
    
    def _calculate_statistics(self) -> Dict:
        def get_stats(values):
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
            return {
                "median": int(median),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values)
            }
        
        def get_stats_float(values):
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
            return {
                "median": median,
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values)
            }
        
        return {
            "age": get_stats([r["repositoryAge"] for r in self.repositories]),
            "pr": get_stats([r["mergedPullRequests"] for r in self.repositories]),
            "releases": get_stats([r["releases"] for r in self.repositories]),
            "update": get_stats([r["daysSinceUpdate"] for r in self.repositories]),
            "closed_ratio": get_stats_float([r["closedIssuesRatio"] for r in self.repositories]),
            "stars": get_stats([r["stars"] for r in self.repositories]),
            "forks": get_stats([r["forks"] for r in self.repositories])
        }
    
    def _analyze_by_language(self) -> str:
        languages = Counter([r["primaryLanguage"] for r in self.repositories])
        total = len(self.repositories)

        rows = []
        for lang, count in languages.most_common(15):
            percentage = (count / total) * 100
            rows.append(f"| {lang} | {count} | {percentage:.1f}% |")

        return "\n".join(rows)
    
    def _get_top_languages_percentage(self) -> float:
        languages = Counter([r["primaryLanguage"] for r in self.repositories])
        total = len(self.repositories)
        
        top_3_count = sum(count for lang, count in languages.most_common(3))
        return (top_3_count / total) * 100
    
    def _check_hypothesis(self, expected: str, actual: str) -> bool:
        try:
            if "> " in expected:
                threshold = float(expected.replace("> ", "").replace("%", "").replace("(", "").split()[0])
                actual_val = float(str(actual).replace("%", "").split()[0])
                return actual_val > threshold
            elif "< " in expected:
                threshold = float(expected.replace("< ", "").replace("dias", "").split()[0])
                actual_val = float(str(actual).replace("dias", "").split()[0])
                return actual_val < threshold
        except:
            return False
        return False


def main():
    generator = ReportGenerator()
    
    if generator.load_from_csv(os.path.join(DATA_DIR, "repositorios_coletados.csv")):
        generator.generate_initial_report()
        print("\n✓ Relatório gerado com sucesso!")
    else:
        print("\n✗ Erro ao carregar dados")
        sys.exit(1)


if __name__ == "__main__":
    main()
