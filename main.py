import os
import sys
import time
from typing import List, Dict
from dotenv import load_dotenv

from github_query import GitHubGraphQLClient
from data_processor import RepositoryDataProcessor

load_dotenv()

class GitHubResearchLab:

    def __init__(self, token: str):
        self.client = GitHubGraphQLClient(token)
        self.repositories: List[Dict] = []
        self.processor = RepositoryDataProcessor()

    def collect_repositories(self, total: int, batch_size: int = 10) -> bool:
        print(f"\n{'='*70}")
        print(f"Coletando {total} repositórios com maior número de estrelas")
        print(f"{'='*70}\n")
        
        after_cursor = None
        processed = 0
        batches_needed = (total // batch_size) + (1 if total % batch_size else 0)
        
        for batch_num in range(1, batches_needed + 1):
            # Calcular quantidade para esta requisição
            remaining = total - processed
            fetch_size = min(batch_size, remaining)
            
            if fetch_size <= 0:
                break
            
            try:
                print(f"[Batch {batch_num}/{batches_needed}] Requisitando {fetch_size} repositórios...")
                print(f"  Status: {processed}/{total} Repositórios coletados")
                
                # Executar query
                response = self.client.get_top_repositories(
                    first=fetch_size,
                    after=after_cursor
                )
                
                # Processar resposta
                search_data = response.get("data", {}).get("search", {})
                edges = search_data.get("edges", [])
                page_info = search_data.get("pageInfo", {})
                
                # Processar cada repositório
                for edge in edges:
                    normalized_data = self.processor.normalize_repository_data(edge)
                    self.repositories.append(normalized_data)
                
                processed += len(edges)
                print(f"   {len(edges)} repositórios processados (Total: {processed})\n")
                
                # Verificar paginação
                if not page_info.get("hasNextPage"):
                    print(f"\n Fim da paginação atingido. Total: {processed} repositórios")
                    break
                
                after_cursor = page_info.get("endCursor")
                
               
                
                # Delay maior entre requisições
                if batch_num < batches_needed:
                    time.sleep(3)
                
            except Exception as e:
                print(f"\n Erro ao coletar batch {batch_num}: {str(e)}")
                return False
        
        return True
    
    def run_sprint_1(self):
        print("\n" + "="*70)
        print("SPRINT 1: CONSULTA GRAPHQL PARA 10 REPOSITÓRIOS")
        print("="*70)

        success = self.collect_repositories(total=100, batch_size=10)

        if success:
            print("\n[Salvando dados da Sprint 1 em CSV...]")
            self.processor.save_to_csv(
                self.repositories,
                "sprint1_repositorios.csv"
            )

            print(f"\n Sprint 1 Concluída: {len(self.repositories)} repositórios coletados")
            print(f"  - Arquivo CSV: sprint1_repositorios.csv")
            return True
        else:
            print("\n Sprint 1 Falhou")
            return False
    
    def run_sprint_2(self):
        print("\n" + "="*70)
        print("SPRINT 2: PAGINAÇÃO (1000 REPOSITÓRIOS) + CSV")
        print("="*70)

        self.repositories = []

        success = self.collect_repositories(total=1000, batch_size=10)

        if not success:
            print("\n Sprint 2 Falhou")
            return False
        
        print("\n[Salvando dados em CSV...]")
        self.processor.save_to_csv(
            self.repositories,
            "repositorios_coletados.csv"
        )
        
        print(f"\n Sprint 2 Concluída: {len(self.repositories)} repositórios processados")
        print(f"  - Arquivo CSV: repositorios_coletados.csv")
        
        
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
    
    # Inicializar laboratório
    lab = GitHubResearchLab(token)
    
    # Executar sprints
    print("\n" + "="*70)
    print("Análise de Repositórios Populares GitHub")
    print("="*70)
    
    # Sprint 1
    if not lab.run_sprint_1():
        sys.exit(1)
    
    # Sprint 2
    if not lab.run_sprint_2():
        sys.exit(1)
    


if __name__ == "__main__":
    main()
