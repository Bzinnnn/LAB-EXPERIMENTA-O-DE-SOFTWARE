import os
from pathlib import Path
from dotenv import load_dotenv

from lab02_pipeline import (
    DATA_DIR,
    OUTPUT_DIR,
    consolidate_dataset,
    generate_markdown_report,
    generate_bonus_plots,
)

def main():
    print("======================================================================")
    print(" Gerando relatório parcial com os repositórios coletados até o momento")
    print("======================================================================\n")
    
    repo_csv = DATA_DIR / "lab02_repositories.csv"
    if not repo_csv.exists():
        print("Erro: lab02_repositories.csv não encontrado.")
        return

    print("[1/3] Consolidando dados temporários...")
    consolidated_csv = consolidate_dataset(repo_csv)

    print("[2/3] Gerando relatório Markdown parcial...")
    generate_markdown_report(consolidated_csv, OUTPUT_DIR / "LAB02_RELATORIO_PARCIAL.md")

    print("[3/3] Gerando gráficos de correlação parciais...")
    generate_bonus_plots(consolidated_csv, OUTPUT_DIR / "plots_parciais")

    print("\nConcluído!")
    print(f"Relatório gerado em: {OUTPUT_DIR / 'LAB02_RELATORIO_PARCIAL.md'}")
    print(f"Gráficos gerados em: {OUTPUT_DIR / 'plots_parciais'}")

if __name__ == "__main__":
    main()
