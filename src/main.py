import os
import sys
import time
from typing import List, Dict
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed


from github_query import GitHubGraphQLClient
from data_processor import RepositoryDataProcessor

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

class GitHubResearchLab:

    def __init__(self, token: str):
        self.client = GitHubGraphQLClient(token)
        self.repositories: List[Dict] = []
        self.processor = RepositoryDataProcessor()

    def collect_repositories(self, total: int, batch_size: int = 50) -> bool:
        after_cursor = None
        collected = 0
        batch_num = 0
        t0 = time.time()

        while collected < total:
            remaining = total - collected
            fetch_size = min(batch_size, remaining)
            batch_num += 1

            try:
                pct = collected / total * 100
                bar = ('█' * int(pct / 5)).ljust(20)
                elapsed = time.time() - t0
                print(f"\r  [{bar}] {collected}/{total} ({pct:.0f}%) — {elapsed:.1f}s", end="", flush=True)

                response = self.client.get_top_repositories(first=fetch_size, after=after_cursor)
                search_data = response.get("data", {}).get("search", {})
                edges = search_data.get("edges", [])
                page_info = search_data.get("pageInfo", {})

                for edge in edges:
                    self.repositories.append(self.processor.normalize_repository_data(edge))

                collected += len(edges)

                if not page_info.get("hasNextPage") or not edges:
                    break

                after_cursor = page_info.get("endCursor")
                time.sleep(0.3)

            except Exception as e:
                print(f"\nErro no batch {batch_num}: {e}")
                return False

        elapsed = time.time() - t0
        print(f"\r  [{'█' * 20}] {collected}/{total} (100%) — {collected} repositórios coletados em {elapsed:.1f}s")
        return True

    def enrich_with_details(self, workers: int = 8) -> None:
        """Busca PRs e releases em paralelo para cada repositório coletado."""
        total = len(self.repositories)
        done = 0
        t0 = time.time()

        print(f"  Enriquecendo {total} repositórios com PRs e releases (workers={workers})...", flush=True)

        def fetch(repo):
            owner, name = repo["nameWithOwner"].split("/", 1)
            details = self.client.get_repo_details(owner, name)
            repo["mergedPullRequests"] = details.get("pullRequests", {}).get("totalCount", 0)
            repo["releases"] = details.get("releases", {}).get("totalCount", 0)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(fetch, repo): repo for repo in self.repositories}
            for future in as_completed(futures):
                future.result()
                done += 1
                bar = ('█' * int(done / total * 20)).ljust(20)
                elapsed = time.time() - t0
                print(f"\r  [{bar}] {done}/{total} — {elapsed:.1f}s", end="", flush=True)

        elapsed = time.time() - t0
        print(f"\r  [{'█' * 20}] {total}/{total} — concluído em {elapsed:.1f}s")


    def run_sprint_1(self):
        print("\nSprint 1 — Coletando 100 repositórios")
        t0 = time.time()

        if not self.collect_repositories(total=100, batch_size=50):
            print("Sprint 1 falhou.")
            return False

        self.enrich_with_details()
        csv_path = os.path.join(DATA_DIR, "sprint1_repositorios.csv")
        self.processor.save_to_csv(self.repositories, csv_path)
        print(f"  Salvo em: {csv_path}")
        print(f"  Sprint 1 concluída em {time.time() - t0:.1f}s")
        return True

    def run_sprint_2(self):
        print("\nSprint 2 — Coletando 1000 repositórios")
        self.repositories = []
        t0 = time.time()

        if not self.collect_repositories(total=1000, batch_size=50):
            print("Sprint 2 falhou.")
            return False

        self.enrich_with_details()
        csv_path = os.path.join(DATA_DIR, "repositorios_coletados.csv")
        self.processor.save_to_csv(self.repositories, csv_path)
        print(f"  Salvo em: {csv_path}")
        print(f"  Sprint 2 concluída em {time.time() - t0:.1f}s")
        return True


def main():
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("Erro: GITHUB_TOKEN não configurado!")
        print("\nPor favor:")
        print("1. Crie um arquivo '.env' com: GITHUB_TOKEN=seu_token_aqui")
        print("2. Ou use: copy .env.example .env")
        print("3. Acesse https://github.com/settings/tokens para criar um token")
        print("\nToken necessário com permissões: 'public_repo'")
        sys.exit(1)
    
    lab = GitHubResearchLab(token)

    print("Análise de Repositórios Populares GitHub")
    print("-" * 42)
    t_total = time.time()

    if not lab.run_sprint_1():
        sys.exit(1)

    if not lab.run_sprint_2():
        sys.exit(1)

    print(f"\nConcluído em {time.time() - t_total:.1f}s no total.")



if __name__ == "__main__":
    main()
