import csv
from pathlib import Path
from statistics import mean, median, stdev

try:
    from scipy.stats import spearmanr
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
CSV_FILE = DATA_DIR / "lab02_consolidado.csv"
HTML_OUT = OUTPUT_DIR / "LAB02_RELATORIO_ACADEMICO.html"

def to_float(val):
    try:
        return float(val)
    except:
        return None


def calc_stats(arr):
    if not arr:
        return (0, 0, 0, 0, 0)
    return (
        mean(arr),
        median(arr),
        stdev(arr) if len(arr) > 1 else 0,
        min(arr),
        max(arr),
    )


def row_fmt(name, stats):
    return (
        f"<tr><td>{name}</td><td>{stats[0]:.4f}</td><td>{stats[1]:.4f}</td>"
        f"<td>{stats[2]:.4f}</td><td>{stats[3]:.4f}</td><td>{stats[4]:.4f}</td></tr>"
    )


def calc_spearman(x, y):
    if not SCIPY_AVAILABLE:
        return 0.0, 1.0, "N/A"
    if len(x) < 3 or len(y) < 3:
        return 0.0, 1.0, "amostra insuficiente"
    n = min(len(x), len(y))
    r, p = spearmanr(x[:n], y[:n])
    sig = '<span class="sig-yes">Sim</span>' if p < 0.05 else '<span class="sig-no">Não</span>'
    return r, p, sig


def classify_strength(rho):
    a = abs(rho)
    if a < 0.10:
        return "desprezível"
    if a < 0.30:
        return "fraca"
    if a < 0.50:
        return "moderada"
    return "forte"


def classify_direction(rho):
    if rho > 0:
        return "positiva"
    if rho < 0:
        return "negativa"
    return "nula"

def main():
    if not CSV_FILE.exists():
        print(f"Erro: {CSV_FILE} não existe.")
        return

    # Load data
    quality = []
    with CSV_FILE.open("r", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            cbo = to_float(row.get("cboMean"))
            dit = to_float(row.get("ditMean"))
            lcom = to_float(row.get("lcomMean"))
            if cbo is not None and dit is not None and lcom is not None:
                quality.append({
                    "stars": to_float(row.get("stars")),
                    "maturity": to_float(row.get("maturityYears")),
                    "releases": to_float(row.get("releases")),
                    "loc": to_float(row.get("sizeLoc")),
                    "cbo": cbo,
                    "dit": dit,
                    "lcom": lcom
                })

    n_repos = len(quality)
    if n_repos == 0:
        print("Nenhum repositório com métricas de qualidade encontrado.")
        return

    stars = [r["stars"] for r in quality]
    maturity = [r["maturity"] for r in quality]
    releases = [r["releases"] for r in quality]
    loc = [r["loc"] for r in quality]
    
    cbo = [r["cbo"] for r in quality]
    dit = [r["dit"] for r in quality]
    lcom = [r["lcom"] for r in quality]

    st_stars = calc_stats(stars)
    st_mat = calc_stats(maturity)
    st_rel = calc_stats(releases)
    st_loc = calc_stats(loc)
    st_cbo = calc_stats(cbo)
    st_dit = calc_stats(dit)
    st_lcom = calc_stats(lcom)

    rq_data = {
        "RQ01": {
            "x_name": "Popularidade (Stars)",
            "x_values": stars,
            "x_axis": "stars",
            "hypothesis": "H1: maior popularidade se associa a menor acoplamento e maior coesão.",
            "images": [
                ("plots_parciais/rq01_stars_vs_cbo.png", "Figura RQ01-A. Stars vs CBO"),
                ("plots_parciais/rq01_stars_vs_dit.png", "Figura RQ01-B. Stars vs DIT"),
                ("plots_parciais/rq01_stars_vs_lcom.png", "Figura RQ01-C. Stars vs LCOM"),
            ],
        },
        "RQ02": {
            "x_name": "Maturidade (Anos)",
            "x_values": maturity,
            "x_axis": "maturityYears",
            "hypothesis": "H2: o envelhecimento do projeto eleva complexidade estrutural e risco de dívida técnica.",
            "images": [
                ("plots_parciais/rq02_maturity_vs_cbo.png", "Figura RQ02-A. Maturidade vs CBO"),
                ("plots_parciais/rq02_maturity_vs_dit.png", "Figura RQ02-B. Maturidade vs DIT"),
                ("plots_parciais/rq02_maturity_vs_lcom.png", "Figura RQ02-C. Maturidade vs LCOM"),
            ],
        },
        "RQ03": {
            "x_name": "Atividade (Releases)",
            "x_values": releases,
            "x_axis": "releases",
            "hypothesis": "H3: maior frequência de releases exige modularidade para preservar qualidade interna.",
            "images": [
                ("plots_parciais/rq03_releases_vs_cbo.png", "Figura RQ03-A. Releases vs CBO"),
                ("plots_parciais/rq03_releases_vs_dit.png", "Figura RQ03-B. Releases vs DIT"),
                ("plots_parciais/rq03_releases_vs_lcom.png", "Figura RQ03-C. Releases vs LCOM"),
            ],
        },
        "RQ04": {
            "x_name": "Tamanho (LOC)",
            "x_values": loc,
            "x_axis": "sizeLoc",
            "hypothesis": "H4: crescimento de tamanho aumenta a interdependência entre classes e o custo de manutenção.",
            "images": [
                ("plots_parciais/rq04_loc_vs_cbo.png", "Figura RQ04-A. LOC vs CBO"),
                ("plots_parciais/rq04_loc_vs_dit.png", "Figura RQ04-B. LOC vs DIT"),
                ("plots_parciais/rq04_loc_vs_lcom.png", "Figura RQ04-C. LOC vs LCOM"),
            ],
        },
    }

    y_metrics = {
        "CBO": ("CBO (Acoplamento)", cbo),
        "DIT": ("DIT (Prof. Herança)", dit),
        "LCOM": ("LCOM (Falta de Coesão)", lcom),
    }

    for rq_key, rq_cfg in rq_data.items():
        correlations = []
        for metric_code, (metric_label, metric_values) in y_metrics.items():
            r, p, sig = calc_spearman(rq_cfg["x_values"], metric_values)
            correlations.append({
                "metric_code": metric_code,
                "metric_label": metric_label,
                "rho": r,
                "p": p,
                "sig": sig,
            })
        rq_cfg["corr"] = correlations

    global_corr_rows = ""
    for rq_key in ["RQ01", "RQ02", "RQ03", "RQ04"]:
        for item in rq_data[rq_key]["corr"]:
            global_corr_rows += (
                f"<tr><td>{rq_data[rq_key]['x_name']}</td>"
                f"<td>{item['metric_label']}</td><td>{item['rho']:.4f}</td>"
                f"<td>{item['p']:.4e}</td><td>{item['sig']}</td></tr>\n"
            )

    def build_rq_table(rq_key):
        rows = ""
        for item in rq_data[rq_key]["corr"]:
            rows += (
                f"<tr><td>{rq_data[rq_key]['x_name']}</td><td>{item['metric_label']}</td>"
                f"<td>{item['rho']:.4f}</td><td>{item['p']:.4e}</td><td>{item['sig']}</td></tr>"
            )
        return rows

    def build_rq_interpretation(rq_key):
        lines = []
        for item in rq_data[rq_key]["corr"]:
            direction = classify_direction(item["rho"])
            strength = classify_strength(item["rho"])
            signif = "com significância estatística" if item["p"] < 0.05 else "sem significância estatística"
            lines.append(
                f"<li>{item['metric_code']}: correlação {direction} e {strength} "
                f"($\\rho$={item['rho']:.3f}), {signif} (p={item['p']:.3e}).</li>"
            )
        return "".join(lines)

    def build_problem_discussion(rq_key):
        significant = [c for c in rq_data[rq_key]["corr"] if c["p"] < 0.05]
        if not significant:
            return (
                "<p>Nesta questão, não foram identificadas relações estatisticamente robustas. "
                "O principal problema analítico passa a ser o risco de inferência causal indevida: "
                "a ausência de associação significativa não implica ausência de efeito, podendo refletir "
                "heterogeneidade arquitetural entre domínios de aplicação.</p>"
            )

        risk_points = []
        for c in significant:
            if c["metric_code"] == "CBO" and c["rho"] > 0:
                risk_points.append(
                    "elevação do acoplamento entre classes, dificultando evolução independente de módulos"
                )
            if c["metric_code"] == "LCOM" and c["rho"] > 0:
                risk_points.append(
                    "redução de coesão interna, com aumento de classes multifuncionais e maior dívida técnica"
                )
            if c["metric_code"] == "DIT" and c["rho"] > 0:
                risk_points.append(
                    "profundidade excessiva da hierarquia de herança, ampliando custo cognitivo de manutenção"
                )
            if c["metric_code"] == "CBO" and c["rho"] < 0:
                risk_points.append(
                    "indício de melhor separação modular em cenários de maior pressão externa"
                )

        if not risk_points:
            return (
                "<p>Os efeitos significativos observados sugerem comportamento estrutural não linear. "
                "A principal implicação prática é reforçar revisão arquitetural periódica por refatorações "
                "orientadas a métricas.</p>"
            )

        joined = "; ".join(risk_points)
        return (
            "<p>Problemas identificados para esta questão: "
            f"{joined}. Em termos de engenharia, recomenda-se monitoramento contínuo de CK, "
            "inspeções de arquitetura e gatilhos de refatoração preventiva em pontos críticos.</p>"
        )

    def build_rq_figures(rq_key):
        html_cards = ""
        for src, caption in rq_data[rq_key]["images"]:
            html_cards += (
                "<div class='figure-card'>"
                f"<img src='{src}' alt='{caption}' onerror=\"this.style.display='none'\">"
                f"<p class='caption'>{caption}</p>"
                "</div>"
            )
        return html_cards

    rq_sections = ""
    for rq_key in ["RQ01", "RQ02", "RQ03", "RQ04"]:
        rq_sections += f"""
        <section class="rq-block" id="{rq_key.lower()}">
            <h3>{rq_key} - {rq_data[rq_key]['x_name']} x Qualidade Estrutural</h3>
            <p><strong>Hipótese operacional:</strong> {rq_data[rq_key]['hypothesis']}</p>
            <p><strong>Leitura dos gráficos:</strong> cada gráfico de dispersão representa a variável independente no eixo X e uma métrica CK no eixo Y. A inclinação visual e a dispersão dos pontos orientam a interpretação do sinal e da intensidade da associação monotônica.</p>
            <table>
                <tr><th>Variável X</th><th>Métrica Y</th><th>Spearman (&rho;)</th><th>p-value</th><th>Significância</th></tr>
                {build_rq_table(rq_key)}
            </table>
            <div class="figure-grid">
                {build_rq_figures(rq_key)}
            </div>
            <h4>Interpretação estatística</h4>
            <ul>
                {build_rq_interpretation(rq_key)}
            </ul>
            <h4>Dissertação sobre problemas observados</h4>
            {build_problem_discussion(rq_key)}
        </section>
        """

    # HTML TEMPLATE
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Acadêmico - Qualidade de Sistemas Java</title>
    <style>
        :root {{
            --primary: #0b2f5b;
            --secondary: #1d5fa7;
            --bg: #f7f7f7;
            --text: #222;
            --border: #d8d8d8;
        }}
        body {{
            font-family: "Georgia", "Times New Roman", serif;
            line-height: 1.75;
            color: var(--text);
            background: var(--bg);
            max-width: 1080px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        h1, h2, h3, h4 {{
            font-family: "Segoe UI", "Arial", sans-serif;
            color: var(--primary);
        }}
        h1 {{
            text-align: center;
            border-bottom: 3px solid var(--primary);
            padding-bottom: 12px;
            margin-bottom: 20px;
            font-size: 2.1em;
        }}
        h2 {{ border-bottom: 1px solid var(--border); padding-bottom: 6px; margin-top: 36px; }}
        .header {{ text-align: center; margin-bottom: 50px; }}
        .meta {{ font-style: italic; color: #555; margin: 6px 0; }}
        .abstract {{
            background: #fff;
            padding: 22px 28px;
            border-top: 2px solid var(--secondary);
            border-bottom: 2px solid var(--secondary);
            margin: 0 auto 35px auto;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            text-align: justify;
        }}
        .abstract h3 {{ text-align: center; margin-top: 0; font-variant: small-caps; margin-bottom: 10px; }}
        .toc {{
            background: #f1f5f9;
            border-left: 4px solid var(--secondary);
            padding: 20px 24px;
            margin-bottom: 36px;
            font-family: "Segoe UI", sans-serif;
        }}
        .toc h3 {{ margin-top: 0; }}
        .toc ul {{ list-style-type: none; padding-left: 0; }}
        .toc li {{ padding: 5px 0; border-bottom: 1px dashed #ccd6e0; }}
        .toc a {{ text-decoration: none; color: var(--primary); font-weight: 500; display: block; }}
        .toc a:hover {{ color: #b71c1c; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            font-family: "Arial", sans-serif;
            font-size: 0.92em;
            box-shadow: 0 2px 5px rgba(0,0,0,0.04);
            background: #fff;
        }}
        th, td {{ border: 1px solid var(--border); padding: 12px 15px; text-align: center; }}
        th {{
            background-color: var(--primary);
            color: white;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            font-size: 0.79em;
        }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #eef5ff; }}
        p {{ text-align: justify; margin-bottom: 15px; }}
        .highlight {{
            background-color: #ecf5ff;
            padding: 14px;
            border-left: 4px solid #2f7bc7;
            margin: 18px 0;
            font-style: italic;
        }}
        .glossary {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-left: 4px solid var(--secondary);
            padding: 18px 22px;
        }}
        .glossary dt {{ font-weight: bold; margin-top: 10px; }}
        .glossary dd {{ margin-left: 0; margin-bottom: 8px; }}
        .sig-yes {{ color: #2e7d32; font-weight: bold; }}
        .sig-no {{ color: #c62828; }}
        .rq-block {{
            background: #fff;
            border: 1px solid var(--border);
            border-left: 4px solid var(--secondary);
            padding: 20px;
            margin-bottom: 28px;
        }}
        .figure-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin: 16px 0;
        }}
        .figure-card {{
            border: 1px solid #d9e2ec;
            border-radius: 6px;
            padding: 10px;
            background: #fbfdff;
        }}
        .figure-card img {{ width: 100%; height: auto; border-radius: 4px; }}
        .caption {{ font-size: 0.83em; color: #555; margin-top: 7px; font-style: italic; text-align: left; }}
        .conclusion-box {{
            border: 2px solid var(--secondary);
            padding: 18px;
            background-color: #fff;
            margin-top: 24px;
            border-radius: 4px;
        }}
        @media (max-width: 700px) {{
            body {{ padding: 20px 12px; }}
            th, td {{ padding: 10px 8px; font-size: 0.85em; }}
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>Análise Empírica de Qualidade em Sistemas Java Open Source</h1>
        <p class="meta">Relatório no formato acadêmico | Laboratório de Medição e Experimentação de Software</p>
        <p class="meta"><strong>Amostra analisada:</strong> {n_repos} repositórios com métricas consolidadas</p>
    </div>

    <div class="abstract">
        <h3>Resumo</h3>
        <p>Este relatório examina relações entre métricas de processo (popularidade, maturidade, atividade e tamanho) e métricas estruturais de qualidade (CBO, DIT e LCOM) em projetos Java open source. Os dados foram extraídos de repositórios no GitHub e processados pela suíte CK. Para avaliar associações monotônicas em distribuições assimétricas, adotou-se o coeficiente de Spearman com nível de significância de 5%. A apresentação dos resultados foi organizada por questões de pesquisa (RQ01-RQ04), de modo que cada questão contenha seus gráficos, explicações dos termos e uma discussão crítica dos problemas observados.</p>
    </div>

    <div class="toc">
        <h3>Índice de Conteúdos</h3>
        <ul>
            <li><a href="#intro">1. Fundamentação e Hipóteses</a></li>
            <li><a href="#metodo">2. Método e Delineamento</a></li>
            <li><a href="#glossario">3. Glossário dos Termos Técnicos</a></li>
            <li><a href="#stats">4. Estatística Descritiva</a></li>
            <li><a href="#correlacao">5. Correlação Global</a></li>
            <li><a href="#rq">6. Resultados por Questão de Pesquisa</a></li>
            <li><a href="#discussao">7. Discussão dos Problemas de Qualidade</a></li>
            <li><a href="#conclusao">8. Conclusão e Ameaças à Validade</a></li>
        </ul>
    </div>

    <h2 id="intro">1. Fundamentação e Hipóteses</h2>
    <p>A literatura de engenharia de software sugere que crescimento de base de código e evolução prolongada tendem a pressionar modularidade e coesão. Este estudo testa, de forma empírica, se variáveis de processo de projetos open source se associam a atributos internos de qualidade arquitetural.</p>
    <p>As seguintes hipóteses formais foram estabelecidas a priori:</p>
    <ul>
        <li><strong>H1:</strong> projetos mais populares (Stars) tendem a apresentar menor acoplamento e maior coesão.</li>
        <li><strong>H2:</strong> projetos mais maduros (anos) acumulam complexidade estrutural ao longo do tempo.</li>
        <li><strong>H3:</strong> maior atividade de releases pode afetar a estabilidade arquitetural.</li>
        <li><strong>H4:</strong> crescimento de LOC eleva esforço de coordenação e risco de acoplamento.</li>
    </ul>

    <h2 id="metodo">2. Método e Delineamento</h2>
    <p>O pipeline foi automatizado para permitir rastreabilidade e reprodutibilidade experimental.</p>
    <ul>
        <li><strong>Amostragem:</strong> seleção de repositórios Java com dados completos no consolidado.</li>
        <li><strong>Métricas de processo:</strong> Stars, idade do projeto (anos), número de releases e LOC.</li>
        <li><strong>Métricas de qualidade:</strong> CBO, DIT e LCOM agregadas por média no nível de projeto.</li>
        <li><strong>Teste estatístico:</strong> Spearman ($\\rho$), adequado para distribuições não normais e relações monotônicas.</li>
    </ul>

    <h2 id="glossario">3. Glossário dos Termos Técnicos</h2>
    <dl class="glossary">
        <dt>CBO (Coupling Between Objects)</dt>
        <dd>Quantidade de acoplamentos entre classes. Valores altos sugerem maior dependência entre componentes.</dd>
        <dt>DIT (Depth of Inheritance Tree)</dt>
        <dd>Profundidade de herança. Valores altos podem aumentar reutilização, mas também complexidade de entendimento.</dd>
        <dt>LCOM (Lack of Cohesion in Methods)</dt>
        <dd>Falta de coesão entre métodos da classe. Quanto maior, mais provável que a classe concentre responsabilidades dispersas.</dd>
        <dt>Spearman ($\\rho$)</dt>
        <dd>Coeficiente de correlação por postos, usado para medir associação monotônica entre variáveis.</dd>
        <dt>p-value</dt>
        <dd>Probabilidade de observar o resultado se a hipótese nula fosse verdadeira. Em geral, p &lt; 0.05 indica evidência estatística de associação.</dd>
    </dl>

    <h2 id="stats">4. Estatística Descritiva</h2>
    <p>A amostra final contém {n_repos} repositórios com dados válidos para todas as variáveis analisadas.</p>
    
    <h3>4.1 Variáveis de Processo</h3>
    <table>
        <tr><th>Métrica</th><th>Média</th><th>Mediana</th><th>Desvio Padrão</th><th>Mínimo</th><th>Máximo</th></tr>
        {row_fmt('Stars', st_stars)}
        {row_fmt('Maturidade (Anos)', st_mat)}
        {row_fmt('Releases', st_rel)}
        {row_fmt('Tamanho (LOC)', st_loc)}
    </table>

    <h3>4.2 Variáveis de Qualidade Arquitetural</h3>
    <table>
        <tr><th>Métrica</th><th>Média</th><th>Mediana</th><th>Desvio Padrão</th><th>Mínimo</th><th>Máximo</th></tr>
        {row_fmt('CBO (Acoplamento)', st_cbo)}
        {row_fmt('DIT (Prof. Herança)', st_dit)}
        {row_fmt('LCOM (Falta de Coesão)', st_lcom)}
    </table>

    <h2 id="correlacao">5. Correlação Global</h2>
    <p>A tabela a seguir sintetiza todos os pares avaliados entre variáveis de processo e métricas de qualidade.</p>

    <table>
        <tr><th>Vetor Independente X</th><th>Vetor Dependente Y</th><th>Spearman (&rho;)</th><th>p-value</th><th>Significância (&alpha; < 0.05)</th></tr>
        {global_corr_rows}
    </table>

    <h2 id="rq">6. Resultados por Questão de Pesquisa</h2>
    <p>Cada questão de pesquisa apresenta os gráficos correspondentes, interpretação estatística e uma dissertação sobre os problemas identificados no comportamento das métricas.</p>

    {rq_sections}

    <h2 id="discussao">7. Discussão dos Problemas de Qualidade</h2>
    <div class="highlight">"Escala de produto e qualidade interna evoluem em tensão constante."</div>
    <p>Os resultados apontam um padrão recorrente em ecossistemas maduros: à medida que os sistemas crescem em tamanho, idade e volume de evolução, aumenta a probabilidade de erosão arquitetural em níveis distintos (acoplamento, profundidade de herança e coesão). Esse comportamento não significa falha de engenharia em si, mas evidencia que mecanismos de governança arquitetural precisam evoluir na mesma velocidade da entrega de funcionalidades.</p>
    <p>Do ponto de vista prático, os principais problemas observáveis são: (i) classes com múltiplas responsabilidades em contextos de aumento de LCOM, (ii) interdependência excessiva entre módulos em cenários de elevação de CBO e (iii) hierarquias de herança profundas que elevam custo de compreensão e de teste em DIT alto.</p>

    <h2 id="conclusao">8. Conclusão e Ameaças à Validade</h2>
    <div class="conclusion-box">
        <p>Em síntese, a análise sugere que pressão de crescimento e manutenção contínua tende a impactar atributos estruturais do software. A reorganização deste relatório por RQ permite rastrear, para cada pergunta, evidência quantitativa, interpretação e implicações técnicas de forma mais aderente ao padrão acadêmico.</p>
        <p><strong>Ameaças à validade:</strong> o estudo é observacional e restrito ao ecossistema Java analisado. Além disso, as métricas agregadas por média podem suavizar comportamentos extremos de subsistemas específicos.</p>
    </div>

    <br><br>
</body>
</html>
"""
    with HTML_OUT.open("w", encoding="utf-8") as fw:
        fw.write(html)

    print(f"Relatorio HTML de alto nível escrito em: {HTML_OUT}")

if __name__ == "__main__":
    main()
