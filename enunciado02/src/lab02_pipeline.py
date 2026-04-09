import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Optional

from dotenv import load_dotenv
from github_query import GitHubGraphQLClient
from repository_cloner import RepositoryCloner
from ck_runner import CKRunner

# ── Diretórios ───────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CLONES_DIR = Path(os.getenv("LAB02_CLONES_DIR", "C:/lab02_clones"))
CK_DIR = ROOT / "ck_results"
OUTPUT_DIR = ROOT / "output"
QUALITY_SUMMARY_CSV = DATA_DIR / "lab02_repo_quality_summary.csv"


@dataclass
class RepoStats:
    name_with_owner: str
    stars: float
    releases: float
    maturity_years: float
    loc: float
    comments: float
    cbo_mean: Optional[float]
    dit_mean: Optional[float]
    lcom_mean: Optional[float]


def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def to_float(raw_value) -> Optional[float]:
    if raw_value is None:
        return None
    text = str(raw_value).strip().replace(",", ".")
    if not text or text.lower() in ("", "nan", "none"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def safe_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"count": 0, "mean": 0.0, "median": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "count": len(values),
        "mean": mean(values),
        "median": median(values),
        "stdev": stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def find_ck_class_csv(clone_dir: str) -> Optional[Path]:
    candidates = [
        CK_DIR / clone_dir / "processed_class_metrics.csv",
        CK_DIR / clone_dir / "class.csv",
        CK_DIR / f"{clone_dir}class.csv",
    ]
    for path in candidates:
        try:
            if path.exists() and path.stat().st_size > 100:
                return path
        except OSError:
            continue
    return None


def aggregate_ck_metrics(ck_csv_path: Optional[Path]) -> Dict[str, Optional[float]]:
    defaults = {
        "cbo_mean": None, "dit_mean": None, "lcom_mean": None,
        "loc_mean": None, "methods_mean": None, "loc_sum": 0,
    }
    if not ck_csv_path or not ck_csv_path.exists():
        return defaults

    try:
        values = {"cbo": [], "dit": [], "lcom": [], "loc": [], "methods": []}
        with ck_csv_path.open("r", encoding="utf-8", errors="ignore") as fp:
            reader = csv.DictReader(fp)
            if not reader.fieldnames:
                return defaults
            col_map = {}
            for key in values:
                for col in reader.fieldnames:
                    if col.lower() == key:
                        col_map[key] = col
                        break
                    elif key == "methods" and col.lower() in ("totalmethodsqty", "methods"):
                        col_map[key] = col
                        break

            for row in reader:
                for key, col in col_map.items():
                    val = to_float(row.get(col))
                    if val is not None:
                        values[key].append(val)

        return {
            "cbo_mean": round(mean(values["cbo"]), 4) if values["cbo"] else None,
            "dit_mean": round(mean(values["dit"]), 4) if values["dit"] else None,
            "lcom_mean": round(mean(values["lcom"]), 4) if values["lcom"] else None,
            "loc_mean": round(mean(values["loc"]), 4) if values["loc"] else None,
            "methods_mean": round(mean(values["methods"]), 4) if values["methods"] else None,
            "loc_sum": int(sum(values["loc"])) if values["loc"] else 0,
        }
    except Exception as exc:
        print(f"  [AVISO] Erro ao agregar {ck_csv_path}: {exc}")
        return defaults


def java_loc_and_comments(repo_path: Path) -> Dict[str, int]:
    total_loc = 0
    total_comments = 0
    ignore_dirs = {".git", ".github", "node_modules", "build", "target", ".gradle"}

    for java_file in repo_path.rglob("*.java"):
        # Pular diretórios ignorados
        parts = java_file.parts
        if any(d in parts for d in ignore_dirs):
            continue
        try:
            in_block = False
            with java_file.open("r", encoding="utf-8", errors="ignore") as fp:
                for raw in fp:
                    line = raw.strip()
                    if not line:
                        continue
                    total_loc += 1
                    if in_block:
                        total_comments += 1
                        if "*/" in line:
                            in_block = False
                        continue
                    if line.startswith("//"):
                        total_comments += 1
                    elif line.startswith("/*"):
                        total_comments += 1
                        if "*/" not in line:
                            in_block = True
        except OSError:
            continue

    return {"loc": total_loc, "comments": total_comments}
def collect_top_repositories(token: str, target: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_csv = DATA_DIR / "lab02_repositories.csv"

    if output_csv.exists():
        with output_csv.open("r", encoding="utf-8") as fp:
            existing = sum(1 for _ in fp) - 1
        if existing >= target:
            print(f"[collect] Reutilizando coleta existente: {output_csv} ({existing} repos)")
            return output_csv

    client = GitHubGraphQLClient(token)
    repositories: List[Dict] = []
    page_size = 100
    pages = (target + page_size - 1) // page_size

    for page in range(1, pages + 1):
        for attempt in range(1, 4):
            try:
                items = client.get_top_repositories_rest(
                    per_page=min(page_size, target - len(repositories)),
                    page=page, language="Java",
                )
                break
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError(f"Falha na coleta da página {page}: {exc}") from exc
                time.sleep(attempt * 5)

        if not items:
            break

        for node in items:
            repositories.append({
                "nameWithOwner": node.get("full_name", ""),
                "owner": (node.get("owner") or {}).get("login", ""),
                "url": node.get("html_url", ""),
                "description": (node.get("description") or "")[:200],
                "primaryLanguage": node.get("language") or "Unknown",
                "stars": node.get("stargazers_count", 0),
                "forks": node.get("forks_count", 0),
                "watchers": node.get("watchers_count", 0),
                "createdAt": node.get("created_at", ""),
                "updatedAt": node.get("updated_at", ""),
                "openIssues": node.get("open_issues_count", 0),
                "closedIssues": 0,
                "releases": 0,
                "mergedPullRequests": 0,
            })
        if len(repositories) >= target:
            break
        print(f"[collect] Pagina {page}/{pages}. Total: {len(repositories)}")

    repositories = repositories[:target]
    if repositories:
        fieldnames = list(repositories[0].keys())
        with output_csv.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(repositories)
    print(f"[collect] CSV salvo: {output_csv} ({len(repositories)} repos)")
    return output_csv
def enrich_with_releases(repositories_csv: Path, token: str) -> None:
    with repositories_csv.open("r", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))

    has_releases = any(int(r.get("releases", 0) or 0) > 0 for r in rows)
    if has_releases:
        print("[releases] CSV ja tem releases preenchidos. Pulando enriquecimento.")
        return

    print(f"[releases] Buscando releases para {len(rows)} repositorios via GraphQL...")
    client = GitHubGraphQLClient(token)

    repos_for_query = []
    for row in rows:
        nwo = row.get("nameWithOwner", "")
        if "/" in nwo:
            owner, name = nwo.split("/", 1)
            repos_for_query.append({"owner": owner, "name": name})

    release_counts = client.get_releases_batch_graphql(repos_for_query)
    updated = 0
    for row in rows:
        nwo = row.get("nameWithOwner", "")
        if nwo in release_counts:
            row["releases"] = release_counts[nwo]
            if release_counts[nwo] > 0:
                updated += 1

    # Salvar de volta
    fieldnames = list(rows[0].keys()) if rows else []
    with repositories_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[releases] {updated} repositorios com releases > 0. CSV atualizado.")
def run_pilot_ck(repositories_csv: Path, min_java_files: int = 50) -> Optional[str]:
    CLONES_DIR.mkdir(parents=True, exist_ok=True)
    cloner = RepositoryCloner(str(CLONES_DIR))
    ck = CKRunner()

    with repositories_csv.open("r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            repo_name = row["nameWithOwner"]
            clone_dir = repo_name.replace("/", "_")

            existing = find_ck_class_csv(clone_dir)
            if existing:
                print(f"[pilot] Repositorio piloto ja analisado: {repo_name} ({existing})")
                return repo_name

            repo_url = row.get("url", "")
            if repo_url and not repo_url.endswith(".git"):
                repo_url = f"{repo_url}.git"

            clone_path = cloner.clone_repository(repo_url, clone_dir)
            if not clone_path:
                continue

            java_count = cloner.count_java_files(clone_path)
            if java_count < min_java_files:
                continue

            out_dir = CK_DIR / clone_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            ck.analyze_repository(clone_path, str(out_dir))
            print(f"[pilot] Repositorio piloto analisado: {repo_name}")
            return repo_name

    return None


def run_quality_for_all_repositories(
    repositories_csv: Path,
    max_repositories: Optional[int] = None,
    min_java_files: int = 1,
) -> Dict[str, int]:
    CLONES_DIR.mkdir(parents=True, exist_ok=True)
    CK_DIR.mkdir(parents=True, exist_ok=True)

    default_workers = 15
    max_workers = int(os.getenv("LAB02_WORKERS", str(default_workers)))

    shared_cloner = RepositoryCloner(str(CLONES_DIR))
    shared_ck = CKRunner(auto_download=True)

    summary = {
        "total_rows": 0, "attempted": 0, "analyzed": 0,
        "reused": 0, "skipped_no_java": 0, "skipped_clone_error": 0, "failed_ck": 0,
    }

    def _compute_maturity(created_at: str) -> float:
        if not created_at:
            return 0.0
        try:
            created = parse_iso_datetime(created_at)
            return (datetime.now(timezone.utc) - created).days / 365.25
        except ValueError:
            return 0.0

    def process_row(row: Dict[str, str]) -> Dict:
        repo_name = row.get("nameWithOwner", "")
        clone_dir = repo_name.replace("/", "_")
        maturity_years = _compute_maturity(row.get("createdAt", ""))

        failed_marker = CK_DIR / clone_dir / ".failed"
        if failed_marker.exists():
            return {"status": "failed_ck", "record": None}

        existing_csv = find_ck_class_csv(clone_dir)
        if existing_csv:
            ck_metrics = aggregate_ck_metrics(existing_csv)
            clone_path = CLONES_DIR / clone_dir
            if clone_path.exists():
                size_info = java_loc_and_comments(clone_path)
            elif ck_metrics["loc_sum"] > 0:
                size_info = {"loc": ck_metrics["loc_sum"], "comments": 0}
            else:
                size_info = {"loc": 0, "comments": 0}

            return {
                "status": "reused",
                "record": _build_record(row, maturity_years, size_info, ck_metrics),
            }

        # ── Clonar e analisar ──
        repo_url = row.get("url", "")
        if repo_url and not repo_url.endswith(".git"):
            repo_url = f"{repo_url}.git"

        clone_path = shared_cloner.clone_repository(repo_url, clone_dir)
        if not clone_path:
            return {"status": "skipped_clone_error", "record": None}

        java_count = shared_cloner.count_java_files(clone_path)
        if java_count < min_java_files:
            shared_cloner.cleanup_repository(clone_dir)
            return {"status": "skipped_no_java", "record": None}

        out_dir = CK_DIR / clone_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        size_info = java_loc_and_comments(Path(clone_path))

        shared_ck.analyze_repository(clone_path, str(out_dir))

        shared_cloner.cleanup_repository(clone_dir)

        result_csv = find_ck_class_csv(clone_dir)
        if result_csv:
            ck_metrics = aggregate_ck_metrics(result_csv)
            return {
                "status": "analyzed",
                "record": _build_record(row, maturity_years, size_info, ck_metrics),
            }

        out_dir.mkdir(parents=True, exist_ok=True)
        failed_marker.touch()
        return {"status": "failed_ck", "record": None}

    def _build_record(row, maturity, size_info, ck_metrics):
        return {
            "nameWithOwner": row.get("nameWithOwner", ""),
            "stars": row.get("stars", 0),
            "forks": row.get("forks", 0),
            "watchers": row.get("watchers", 0),
            "releases": row.get("releases", 0),
            "openIssues": row.get("openIssues", 0),
            "closedIssues": row.get("closedIssues", 0),
            "maturityYears": round(maturity, 3),
            "sizeLoc": size_info["loc"],
            "sizeComments": size_info["comments"],
            "cboMean": ck_metrics["cbo_mean"],
            "ditMean": ck_metrics["dit_mean"],
            "lcomMean": ck_metrics["lcom_mean"],
            "classLocMean": ck_metrics["loc_mean"],
            "methodsMean": ck_metrics["methods_mean"],
        }

    with repositories_csv.open("r", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))

    if max_repositories is not None:
        rows = rows[:max_repositories]

    records: List[Dict] = []
    total = len([r for r in rows if r.get("nameWithOwner")])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_row, row): row for row in rows if row.get("nameWithOwner")}
        for index, future in enumerate(as_completed(futures), start=1):
            try:
                result = future.result(timeout=900)
            except Exception as exc:
                result = {"status": "failed_ck", "record": None}
                print(f"  [ERRO] Excecao inesperada: {exc}")

            summary["total_rows"] += 1
            summary["attempted"] += 1
            status = result["status"]
            summary[status] = summary.get(status, 0) + 1
            if result["record"]:
                records.append(result["record"])

            if index % 20 == 0 or index == total:
                print(f"[quality] Progresso: {index}/{total} | analisados={summary.get('analyzed',0)} reusados={summary.get('reused',0)} erros={summary.get('failed_ck',0)+summary.get('skipped_clone_error',0)}")

            if index % 50 == 0 and records:
                _save_quality_summary(records)

    if records:
        _save_quality_summary(records)

    print("[quality] Resumo da etapa de qualidade:")
    for key, value in summary.items():
        print(f"  - {key}: {value}")
    return summary


def _save_quality_summary(records: List[Dict]) -> None:
    fieldnames = list(records[0].keys())
    with QUALITY_SUMMARY_CSV.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
def consolidate_dataset(repositories_csv: Path) -> Path:
    output = DATA_DIR / "lab02_consolidado.csv"

    if QUALITY_SUMMARY_CSV.exists() and QUALITY_SUMMARY_CSV.stat().st_size > 100:
        print(f"[consolidate] Reaproveitando resumo de qualidade: {QUALITY_SUMMARY_CSV}")
        output.write_text(QUALITY_SUMMARY_CSV.read_text(encoding="utf-8"), encoding="utf-8")
        return output

    now = datetime.now(timezone.utc)
    rows_out: List[Dict] = []
    with repositories_csv.open("r", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            repo = row.get("nameWithOwner", "")
            clone_name = repo.replace("/", "_")
            clone_path = CLONES_DIR / clone_name

            maturity_years = 0.0
            created_at = row.get("createdAt", "")
            if created_at:
                try:
                    maturity_years = (now - parse_iso_datetime(created_at)).days / 365.25
                except ValueError:
                    pass

            ck_csv = find_ck_class_csv(clone_name)
            ck_metrics = aggregate_ck_metrics(ck_csv)

            if clone_path.exists():
                size_info = java_loc_and_comments(clone_path)
            elif ck_metrics["loc_sum"] > 0:
                size_info = {"loc": ck_metrics["loc_sum"], "comments": 0}
            else:
                size_info = {"loc": 0, "comments": 0}

            rows_out.append({
                "nameWithOwner": repo,
                "stars": row.get("stars", 0),
                "forks": row.get("forks", 0),
                "watchers": row.get("watchers", 0),
                "releases": row.get("releases", 0),
                "openIssues": row.get("openIssues", 0),
                "closedIssues": row.get("closedIssues", 0),
                "maturityYears": round(maturity_years, 3),
                "sizeLoc": size_info["loc"],
                "sizeComments": size_info["comments"],
                "cboMean": ck_metrics["cbo_mean"],
                "ditMean": ck_metrics["dit_mean"],
                "lcomMean": ck_metrics["lcom_mean"],
                "classLocMean": ck_metrics["loc_mean"],
                "methodsMean": ck_metrics["methods_mean"],
            })

    if rows_out:
        fieldnames = list(rows_out[0].keys())
        with output.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_out)

    print(f"[consolidate] CSV consolidado salvo: {output} ({len(rows_out)} repos)")
    return output
def corr_text(x: List[float], y: List[float]) -> str:
    if len(x) < 3 or len(y) < 3:
        return "amostra insuficiente"
    try:
        from scipy.stats import spearmanr
    except ModuleNotFoundError:
        return "scipy nao instalado"
    n = min(len(x), len(y))
    corr, p = spearmanr(x[:n], y[:n])
    sig = "significativo" if p < 0.05 else "nao significativo"
    return f"rho={corr:.4f}, p={p:.4g} ({sig})"


def load_repo_stats(consolidated_csv: Path) -> List[RepoStats]:
    rows: List[RepoStats] = []
    with consolidated_csv.open("r", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            rows.append(RepoStats(
                name_with_owner=row["nameWithOwner"],
                stars=float(row.get("stars") or 0),
                releases=float(row.get("releases") or 0),
                maturity_years=float(row.get("maturityYears") or 0),
                loc=float(row.get("sizeLoc") or 0),
                comments=float(row.get("sizeComments") or 0),
                cbo_mean=to_float(row.get("cboMean")),
                dit_mean=to_float(row.get("ditMean")),
                lcom_mean=to_float(row.get("lcomMean")),
            ))
    return rows
def generate_markdown_report(consolidated_csv: Path, report_path: Path) -> None:
    repos = load_repo_stats(consolidated_csv)
    quality = [r for r in repos if r.cbo_mean is not None and r.dit_mean is not None and r.lcom_mean is not None]

    total = len(repos)
    n_quality = len(quality)

    cbo_s = safe_stats([r.cbo_mean for r in quality])
    dit_s = safe_stats([r.dit_mean for r in quality])
    lcom_s = safe_stats([r.lcom_mean for r in quality])
    stars_s = safe_stats([r.stars for r in quality])
    mat_s = safe_stats([r.maturity_years for r in quality])
    rel_s = safe_stats([r.releases for r in quality])
    loc_s = safe_stats([r.loc for r in quality])

    stars = [r.stars for r in quality]
    maturity = [r.maturity_years for r in quality]
    releases = [r.releases for r in quality]
    loc = [r.loc for r in quality]
    cbo = [r.cbo_mean for r in quality]
    dit = [r.dit_mean for r in quality]
    lcom = [r.lcom_mean for r in quality]

    def fmt(s, key): return f"{s[key]:.4f}" if isinstance(s[key], float) else str(s[key])

    lines = [
        "# LAB02 — Estudo das Características de Qualidade de Sistemas Java",
        "",
        "---",
        "",
        "## 1. Introdução",
        "",
        "Este estudo investiga a relação entre métricas de processo (popularidade, maturidade, atividade e tamanho) e métricas de qualidade interna (CBO, DIT, LCOM) de repositórios Java de alto impacto no GitHub.",
        "",
        "### 1.1 Hipóteses Informais",
        "",
        "**H1 (RQ01 — Popularidade vs Qualidade):** Repositórios mais populares (mais estrelas) tendem a apresentar menor LCOM médio (melhor coesão) e menor CBO médio (menor acoplamento), pois a popularidade pode indicar maior escrutínio da comunidade, resultando em código mais bem estruturado.",
        "",
        "**H2 (RQ02 — Maturidade vs Qualidade):** Repositórios mais maduros (mais antigos) tendem a apresentar maior CBO médio e maior LCOM, pois à medida que o software envelhece, o acoplamento e a complexidade tendem a crescer organicamente.",
        "",
        "**H3 (RQ03 — Atividade vs Qualidade):** Repositórios com mais releases tendem a apresentar melhor coesão (menor LCOM), pois ciclos de release frequentes indicam manutenção ativa e refatoração contínua.",
        "",
        "**H4 (RQ04 — Tamanho vs Qualidade):** Repositórios maiores (mais LOC) tendem a apresentar maior CBO e maior LCOM, pois bases de código extensas naturalmente desenvolvem mais dependências entre módulos.",
        "",
        "---",
        "",
        "## 2. Metodologia",
        "",
        "### 2.1 Seleção de Repositórios",
        f"- Coletamos os top {total} repositórios Java mais populares do GitHub.",
        "- Critério: ordenação por número de estrelas (descendente) via API REST do GitHub (`/search/repositories?q=language:Java+stars:>1&sort=stars`).",
        "",
        "### 2.2 Métricas de Processo",
        "| Dimensão | Métrica | Fonte |",
        "|----------|---------|-------|",
        "| Popularidade | Número de estrelas (stars) | GitHub REST API |",
        "| Maturidade | Idade em anos (createdAt → now) | GitHub REST API |",
        "| Atividade | Número de releases | GitHub GraphQL API |",
        "| Tamanho | Linhas de código (LOC) e linhas de comentários | Contagem no código-fonte |",
        "",
        "### 2.3 Métricas de Qualidade",
        "| Métrica | Significado |",
        "|---------|-------------|",
        "| **CBO** (Coupling Between Objects) | Acoplamento entre classes — classes de alto CBO dependem de muitas outras |",
        "| **DIT** (Depth of Inheritance Tree) | Profundidade da árvore de herança — DIT alto indica hierarquias profundas |",
        "| **LCOM** (Lack of Cohesion of Methods) | Falta de coesão — LCOM alto indica que a classe realiza múltiplas responsabilidades |",
        "",
        "### 2.4 Ferramentas",
        "- **CK** (v0.7.0): ferramenta de análise estática para métricas OO em código Java.",
        "- **Sumarização**: média, mediana e desvio padrão por repositório.",
        "- **Correlação**: teste de Spearman (robusto a distribuições não normais).",
        "",
        "---",
        "",
        "## 3. Resultados",
        "",
        f"**Repositórios coletados:** {total}",
        f"**Repositórios com métricas de qualidade:** {n_quality}",
        "",
        "### 3.1 Estatísticas Descritivas das Métricas de Processo",
        "",
        "| Métrica | Média | Mediana | Desvio Padrão | Min | Max |",
        "|---------|-------|---------|---------------|-----|-----|",
        f"| Stars | {fmt(stars_s,'mean')} | {fmt(stars_s,'median')} | {fmt(stars_s,'stdev')} | {fmt(stars_s,'min')} | {fmt(stars_s,'max')} |",
        f"| Maturidade (anos) | {fmt(mat_s,'mean')} | {fmt(mat_s,'median')} | {fmt(mat_s,'stdev')} | {fmt(mat_s,'min')} | {fmt(mat_s,'max')} |",
        f"| Releases | {fmt(rel_s,'mean')} | {fmt(rel_s,'median')} | {fmt(rel_s,'stdev')} | {fmt(rel_s,'min')} | {fmt(rel_s,'max')} |",
        f"| LOC | {fmt(loc_s,'mean')} | {fmt(loc_s,'median')} | {fmt(loc_s,'stdev')} | {fmt(loc_s,'min')} | {fmt(loc_s,'max')} |",
        "",
        "### 3.2 Estatísticas Descritivas das Métricas de Qualidade",
        "",
        "| Métrica | Média | Mediana | Desvio Padrão | Min | Max |",
        "|---------|-------|---------|---------------|-----|-----|",
        f"| CBO | {fmt(cbo_s,'mean')} | {fmt(cbo_s,'median')} | {fmt(cbo_s,'stdev')} | {fmt(cbo_s,'min')} | {fmt(cbo_s,'max')} |",
        f"| DIT | {fmt(dit_s,'mean')} | {fmt(dit_s,'median')} | {fmt(dit_s,'stdev')} | {fmt(dit_s,'min')} | {fmt(dit_s,'max')} |",
        f"| LCOM | {fmt(lcom_s,'mean')} | {fmt(lcom_s,'median')} | {fmt(lcom_s,'stdev')} | {fmt(lcom_s,'min')} | {fmt(lcom_s,'max')} |",
        "",
        "### 3.3 RQ01 — Popularidade vs Qualidade",
        "",
        f"- Stars × CBO: {corr_text(stars, cbo)}",
        f"- Stars × DIT: {corr_text(stars, dit)}",
        f"- Stars × LCOM: {corr_text(stars, lcom)}",
        "",
        "### 3.4 RQ02 — Maturidade vs Qualidade",
        "",
        f"- Maturidade × CBO: {corr_text(maturity, cbo)}",
        f"- Maturidade × DIT: {corr_text(maturity, dit)}",
        f"- Maturidade × LCOM: {corr_text(maturity, lcom)}",
        "",
        "### 3.5 RQ03 — Atividade vs Qualidade",
        "",
        f"- Releases × CBO: {corr_text(releases, cbo)}",
        f"- Releases × DIT: {corr_text(releases, dit)}",
        f"- Releases × LCOM: {corr_text(releases, lcom)}",
        "",
        "### 3.6 RQ04 — Tamanho vs Qualidade",
        "",
        f"- LOC × CBO: {corr_text(loc, cbo)}",
        f"- LOC × DIT: {corr_text(loc, dit)}",
        f"- LOC × LCOM: {corr_text(loc, lcom)}",
        "",
        "---",
        "",
        "## 4. Discussão",
        "",
        "### 4.1 RQ01 — Popularidade",
        "Esperava-se que repositórios mais populares tivessem melhor qualidade (menor CBO e LCOM). ",
    ]

    try:
        from scipy.stats import spearmanr
        rho_star_cbo, p_star_cbo = spearmanr(stars, cbo)
        rho_star_lcom, p_star_lcom = spearmanr(stars, lcom)
        if rho_star_cbo < 0 and p_star_cbo < 0.05:
            lines.append("Os resultados confirmam parcialmente H1: há uma correlação negativa significativa entre popularidade e CBO.")
        elif rho_star_cbo > 0 and p_star_cbo < 0.05:
            lines.append("Surpreendentemente, os resultados indicam uma correlação positiva entre popularidade e CBO, sugerindo que projetos populares tendem a ter código mais complexo e acoplado, possivelmente pela amplitude de funcionalidades.")
        else:
            lines.append("Os resultados não mostram correlação significativa entre popularidade e CBO, sugerindo que a popularidade por si só não é indicador de qualidade estrutural do código.")

        lines.extend(["", "### 4.2 RQ02 — Maturidade"])
        rho_mat_cbo, p_mat_cbo = spearmanr(maturity, cbo)
        if rho_mat_cbo > 0 and p_mat_cbo < 0.05:
            lines.append("H2 é parcialmente confirmada: repositórios mais maduros tendem a possuir maior CBO, indicando que o acoplamento cresce com o tempo de desenvolvimento.")
        else:
            lines.append("Os resultados não confirmam H2 de forma significativa, sugerindo que a maturidade não é o principal fator que determina o nível de acoplamento.")

        lines.extend(["", "### 4.3 RQ03 — Atividade"])
        rho_rel_lcom, p_rel_lcom = spearmanr(releases, lcom)
        if rho_rel_lcom < 0 and p_rel_lcom < 0.05:
            lines.append("H3 é confirmada: repositórios com mais releases tendem a ter menor LCOM, sugerindo que ciclos frequentes de release contribuem para melhor coesão.")
        else:
            lines.append("Os resultados não confirmam H3, sugerindo que a frequência de releases não está significativamente correlacionada com a coesão do código.")

        lines.extend(["", "### 4.4 RQ04 — Tamanho"])
        rho_loc_cbo, p_loc_cbo = spearmanr(loc, cbo)
        if rho_loc_cbo > 0 and p_loc_cbo < 0.05:
            lines.append("H4 é confirmada: repositórios maiores tendem a ter maior CBO, indicando que bases de código extensas naturalmente desenvolvem mais acoplamento entre classes.")
        else:
            lines.append("Os resultados não confirmam H4 fortemente, sugerindo que o tamanho não é o único fator determinante do acoplamento.")
    except Exception:
        lines.append("(Análise estatística detalhada requer scipy)")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Análise Estatística (Bônus)",
        "",
        "Foi aplicado o teste de correlação de **Spearman** por ser robusto a distribuições não normais e relações monotônicas, características comuns em métricas de software.",
        "",
        "O p-value < 0.05 indica significância estatística. O coeficiente rho varia de -1 (correlação negativa perfeita) a +1 (correlação positiva perfeita).",
        "",
        "### Tabela de Correlações de Spearman",
        "",
        "| Variável X | Variável Y | rho | p-value | Significativo? |",
        "|-----------|-----------|-----|---------|----------------|",
    ])

    try:
        from scipy.stats import spearmanr
        pairs = [
            ("Stars", "CBO", stars, cbo), ("Stars", "DIT", stars, dit), ("Stars", "LCOM", stars, lcom),
            ("Maturidade", "CBO", maturity, cbo), ("Maturidade", "DIT", maturity, dit), ("Maturidade", "LCOM", maturity, lcom),
            ("Releases", "CBO", releases, cbo), ("Releases", "DIT", releases, dit), ("Releases", "LCOM", releases, lcom),
            ("LOC", "CBO", loc, cbo), ("LOC", "DIT", loc, dit), ("LOC", "LCOM", loc, lcom),
        ]
        for xn, yn, xv, yv in pairs:
            n = min(len(xv), len(yv))
            if n >= 3:
                r, p = spearmanr(xv[:n], yv[:n])
                sig = "Sim" if p < 0.05 else "Não"
                lines.append(f"| {xn} | {yn} | {r:.4f} | {p:.4g} | {sig} |")
    except Exception:
        lines.append("| — | — | — | — | scipy não disponível |")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Visualizações (Bônus)",
        "",
        "Os gráficos de correlação foram gerados em `output/plots/` e incluem:",
        "- Scatter plots para cada RQ (popularidade, maturidade, atividade, tamanho) vs cada métrica de qualidade (CBO, DIT, LCOM)",
        "- Heatmap da matriz de correlação de Spearman",
        "- Boxplots das métricas de qualidade por quartis de popularidade",
        "",
        "---",
        "",
        "## 7. Conclusão",
        "",
        f"Este estudo analisou {n_quality} repositórios Java com métricas de qualidade extraídas pela ferramenta CK.",
        "Os resultados indicam que as relações entre métricas de processo e qualidade de código são complexas e nem sempre seguem as hipóteses intuitivas.",
        "A análise estatística com teste de Spearman fornece confiança nas conclusões apresentadas.",
        "",
        "---",
        "",
        f"*Relatório gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] Relatorio salvo: {report_path}")
def generate_bonus_plots(consolidated_csv: Path, plots_dir: Path) -> None:
    try:
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ModuleNotFoundError as e:
        print(f"[bonus] Dependencia nao encontrada: {e}. Pulando graficos.")
        return

    df = pd.read_csv(consolidated_csv)
    numeric_cols = ["stars", "releases", "maturityYears", "sizeLoc", "sizeComments", "cboMean", "ditMean", "lcomMean"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    plots_dir.mkdir(parents=True, exist_ok=True)

    df_q = df.dropna(subset=["cboMean", "ditMean", "lcomMean"])
    if df_q.empty:
        print("[bonus] Sem dados de qualidade para graficos.")
        return

    print(f"[bonus] Gerando graficos com {len(df_q)} repositorios...")

    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "#f8f9fa",
        "axes.grid": True, "grid.alpha": 0.3, "font.size": 10,
    })

    def scatter_plot(x_col, y_col, xlabel, ylabel, title, filename):
        data = df_q[[x_col, y_col]].dropna()
        if data.empty:
            return
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.scatter(data[x_col], data[y_col], alpha=0.5, s=25, c="#2563eb", edgecolors="white", linewidths=0.3)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        try:
            from scipy.stats import spearmanr
            rho, p = spearmanr(data[x_col], data[y_col])
            ax.text(0.02, 0.95, f"Spearman ρ={rho:.3f}, p={p:.3g}", transform=ax.transAxes,
                    fontsize=9, verticalalignment="top", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
        except Exception:
            pass
        plt.tight_layout()
        plt.savefig(plots_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    scatter_plot("stars", "cboMean", "Stars", "CBO médio", "RQ01 — Popularidade vs CBO", "rq01_stars_vs_cbo.png")
    scatter_plot("stars", "ditMean", "Stars", "DIT médio", "RQ01 — Popularidade vs DIT", "rq01_stars_vs_dit.png")
    scatter_plot("stars", "lcomMean", "Stars", "LCOM médio", "RQ01 — Popularidade vs LCOM", "rq01_stars_vs_lcom.png")

    scatter_plot("maturityYears", "cboMean", "Maturidade (anos)", "CBO médio", "RQ02 — Maturidade vs CBO", "rq02_maturity_vs_cbo.png")
    scatter_plot("maturityYears", "ditMean", "Maturidade (anos)", "DIT médio", "RQ02 — Maturidade vs DIT", "rq02_maturity_vs_dit.png")
    scatter_plot("maturityYears", "lcomMean", "Maturidade (anos)", "LCOM médio", "RQ02 — Maturidade vs LCOM", "rq02_maturity_vs_lcom.png")

    scatter_plot("releases", "cboMean", "Releases", "CBO médio", "RQ03 — Atividade vs CBO", "rq03_releases_vs_cbo.png")
    scatter_plot("releases", "ditMean", "Releases", "DIT médio", "RQ03 — Atividade vs DIT", "rq03_releases_vs_dit.png")
    scatter_plot("releases", "lcomMean", "Releases", "LCOM médio", "RQ03 — Atividade vs LCOM", "rq03_releases_vs_lcom.png")

    scatter_plot("sizeLoc", "cboMean", "LOC", "CBO médio", "RQ04 — Tamanho vs CBO", "rq04_loc_vs_cbo.png")
    scatter_plot("sizeLoc", "ditMean", "LOC", "DIT médio", "RQ04 — Tamanho vs DIT", "rq04_loc_vs_dit.png")
    scatter_plot("sizeLoc", "lcomMean", "LOC", "LCOM médio", "RQ04 — Tamanho vs LCOM", "rq04_loc_vs_lcom.png")

    corr_cols = ["stars", "releases", "maturityYears", "sizeLoc", "cboMean", "ditMean", "lcomMean"]
    corr_data = df_q[corr_cols].dropna()
    if len(corr_data) >= 3:
        corr = corr_data.corr(method="spearman")
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        labels = ["Stars", "Releases", "Maturidade", "LOC", "CBO", "DIT", "LCOM"]
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center",
                        color="white" if abs(corr.values[i, j]) > 0.5 else "black", fontsize=8)
        plt.colorbar(im, fraction=0.046, pad=0.04)
        ax.set_title("Matriz de Correlação de Spearman", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(plots_dir / "heatmap_spearman.png", dpi=150, bbox_inches="tight")
        plt.close()

    if len(df_q) >= 4:
        df_q = df_q.copy()
        df_q["stars_quartile"] = pd.qcut(df_q["stars"], q=4, labels=["Q1 (menos popular)", "Q2", "Q3", "Q4 (mais popular)"], duplicates="drop")

        for metric, label in [("cboMean", "CBO"), ("ditMean", "DIT"), ("lcomMean", "LCOM")]:
            fig, ax = plt.subplots(figsize=(9, 6))
            box_data = [df_q[df_q["stars_quartile"] == q][metric].dropna().values for q in df_q["stars_quartile"].cat.categories]
            bp = ax.boxplot(box_data, labels=df_q["stars_quartile"].cat.categories, patch_artist=True)
            colors = ["#dbeafe", "#93c5fd", "#3b82f6", "#1d4ed8"]
            for patch, color in zip(bp["boxes"], colors):
                patch.set_facecolor(color)
            ax.set_ylabel(f"{label} médio", fontsize=12)
            ax.set_xlabel("Quartis de Popularidade (Stars)", fontsize=12)
            ax.set_title(f"Distribuição de {label} por Quartis de Popularidade", fontsize=14, fontweight="bold")
            plt.tight_layout()
            plt.savefig(plots_dir / f"boxplot_{metric.lower()}_by_stars.png", dpi=150, bbox_inches="tight")
            plt.close()

    print(f"[bonus] Graficos salvos em: {plots_dir}")
