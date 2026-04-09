import argparse
import os
import shutil
import sys
import time
from dotenv import load_dotenv
from lab02_pipeline import (
    collect_top_repositories,
    enrich_with_releases,
    consolidate_dataset,
    generate_markdown_report,
    generate_bonus_plots,
    run_pilot_ck,
    run_quality_for_all_repositories,
    DATA_DIR,
    OUTPUT_DIR,
)


def cleanup_generated_outputs(fresh: bool = False) -> None:
    report_file = OUTPUT_DIR / "LAB02_RELATORIO_ESBOCO.md"
    plots_dir = OUTPUT_DIR / "plots"
    consolidated_csv = DATA_DIR / "lab02_consolidado.csv"
    summary_csv = DATA_DIR / "lab02_repo_quality_summary.csv"

    for path in [report_file, consolidated_csv, summary_csv]:
        if path.exists():
            path.unlink()

    if plots_dir.exists():
        shutil.rmtree(plots_dir, ignore_errors=True)

    if fresh:
        ck_results_dir = OUTPUT_DIR.parent / "ck_results"
        clones_dir = os.getenv("LAB02_CLONES_DIR", "C:/lab02_clones")
        if ck_results_dir.exists():
            shutil.rmtree(ck_results_dir, ignore_errors=True)
        if os.path.exists(clones_dir):
            shutil.rmtree(clones_dir, ignore_errors=True)
        print("[cleanup] Modo fresh ativo: caches de clones e CK removidos.")
    else:
        print("[cleanup] Mantendo caches de clones e CK para acelerar execucao.")


def _elapsed(start: float) -> str:
    secs = time.time() - start
    if secs < 60:
        return f"{secs:.1f}s"
    mins = secs / 60
    return f"{mins:.1f}min"


def main() -> None:
    try:
        parser = argparse.ArgumentParser(description="Executa o fluxo completo do LAB02")
        parser.add_argument("--fresh", action="store_true", help="Limpa caches e refaz do zero")
        parser.add_argument("--max-repos", type=int, default=1000, help="Numero maximo de repositorios a processar")
        args = parser.parse_args()

        print("\n" + "=" * 70)
        print("  LAB02")
        print("=" * 70)
        print("Fluxo: coleta -> releases -> piloto -> qualidade -> consolidacao -> relatorio -> graficos\n")

        t_total = time.time()

        cleanup_generated_outputs(fresh=args.fresh)

        env_path = DATA_DIR.parent / ".env"
        load_dotenv(env_path)
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            raise RuntimeError("GITHUB_TOKEN nao definido em .env")

        t = time.time()
        print("\n[1/7] Coleta dos repositorios...")
        repo_csv = collect_top_repositories(token=token, target=args.max_repos)
        if not repo_csv.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {repo_csv}")
        print(f"[1/7] Concluido em {_elapsed(t)}\n")

        t = time.time()
        print("[2/7] Enriquecimento com releases...")
        enrich_with_releases(repo_csv, token)
        print(f"[2/7] Concluido em {_elapsed(t)}\n")

        t = time.time()
        print("[3/7] Analise piloto...")
        pilot = run_pilot_ck(repo_csv)
        print(f"[3/7] Piloto: {pilot or 'nenhum'} em {_elapsed(t)}\n")

        t = time.time()
        print("[4/7] Analise de qualidade para todos os repositorios...")
        run_quality_for_all_repositories(repo_csv, max_repositories=args.max_repos, min_java_files=1)
        print(f"[4/7] Concluido em {_elapsed(t)}\n")

        t = time.time()
        print("[5/7] Consolidacao...")
        consolidated_csv = consolidate_dataset(repo_csv)
        if not consolidated_csv.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {consolidated_csv}")
        print(f"[5/7] Concluido em {_elapsed(t)}\n")

        t = time.time()
        print("[6/7] Geracao do relatorio...")
        generate_markdown_report(consolidated_csv, OUTPUT_DIR / "LAB02_RELATORIO_ESBOCO.md")
        print(f"[6/7] Concluido em {_elapsed(t)}\n")

        t = time.time()
        print("[7/7] Graficos de correlacao (bonus)...")
        generate_bonus_plots(consolidated_csv, OUTPUT_DIR / "plots")
        print(f"[7/7] Concluido em {_elapsed(t)}\n")

        print("=" * 70)
        print(f"  Pipeline finalizado com sucesso em {_elapsed(t_total)}")
        print(f"  Relatorio: output/LAB02_RELATORIO_ESBOCO.md")
        print(f"  Graficos:  output/plots/")
        print(f"  Dados:     data/lab02_consolidado.csv")
        print("=" * 70 + "\n")

    except Exception as exc:
        print(f"\n[ERRO FATAL] {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
