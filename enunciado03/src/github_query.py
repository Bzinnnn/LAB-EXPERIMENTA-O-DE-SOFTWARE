"""
Utilitários para queries ao GitHub API
"""

import os
from dotenv import load_dotenv
from github import Github
from github.GithubException import RateLimitExceededException
import time

load_dotenv()

class GitHubClient:
    """Cliente reutilizável para GitHub API"""
    
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GITHUB_TOKEN não configurado")
        
        self.github = Github(self.token)
        self._request_count = 0
        
    def get_rate_limit(self):
        """Retorna informações do rate limit"""
        rate_limit = self.github.get_rate_limit()
        return {
            'remaining': rate_limit.core.remaining,
            'limit': rate_limit.core.limit,
            'reset': rate_limit.core.reset
        }
    
    def get_user(self, username):
        """Retorna informações do usuário"""
        try:
            return self.github.get_user(username)
        except Exception as e:
            print(f"Erro ao buscar usuário {username}: {str(e)}")
            return None
    
    def get_repo(self, repo_name):
        """Retorna repositório pelo nome (full_name)"""
        try:
            return self.github.get_repo(repo_name)
        except Exception as e:
            print(f"Erro ao buscar repositório {repo_name}: {str(e)}")
            return None
    
    def search_repos(self, query, sort='stars', order='desc', max_pages=1):
        """
        Busca repositórios com query customizada
        
        Args:
            query: string de busca do GitHub
            sort: campo para ordenação (stars, forks, updated)
            order: asc ou desc
            max_pages: número de páginas a coletar (30 por página)
        """
        try:
            results = self.github.search_repositories(
                query=query,
                sort=sort,
                order=order
            )
            
            repos = []
            for i, repo in enumerate(results):
                if i >= (max_pages * 30):
                    break
                repos.append(repo)
            
            return repos
            
        except RateLimitExceededException:
            print("❌ Rate limit atingido! Tente novamente em alguns minutos.")
            return []
        except Exception as e:
            print(f"Erro na busca: {str(e)}")
            return []
    
    def get_pr_details(self, repo_name, pr_number):
        """Retorna detalhes de um PR específico"""
        try:
            repo = self.get_repo(repo_name)
            if not repo:
                return None
            
            return repo.get_pull(pr_number)
        except Exception as e:
            print(f"Erro ao buscar PR: {str(e)}")
            return None
    
    def get_repo_prs(self, repo_name, state='closed', sort='created', max_prs=None):
        """
        Retorna PRs de um repositório
        
        Args:
            repo_name: nome completo do repositório
            state: 'open', 'closed', 'all'
            sort: 'created', 'updated', 'popularity'
            max_prs: número máximo de PRs a retornar
        """
        try:
            repo = self.get_repo(repo_name)
            if not repo:
                return []
            
            prs = repo.get_pulls(state=state, sort=sort, direction='desc')
            
            result = []
            for i, pr in enumerate(prs):
                if max_prs and i >= max_prs:
                    break
                result.append(pr)
            
            return result
            
        except Exception as e:
            print(f"Erro ao buscar PRs de {repo_name}: {str(e)}")
            return []
    
    def check_health(self):
        """Verifica a saúde da conexão com GitHub API"""
        try:
            limit = self.get_rate_limit()
            print(f"✓ Conectado ao GitHub API")
            print(f"✓ Rate limit: {limit['remaining']}/{limit['limit']}")
            return True
        except Exception as e:
            print(f"✗ Erro de conexão: {str(e)}")
            return False


def test_github_connection():
    """Função para testar a conexão com GitHub"""
    print("\n" + "="*60)
    print("Testando conexão com GitHub API")
    print("="*60)
    
    try:
        client = GitHubClient()
        
        if client.check_health():
            print("\n✓ Configuração validada com sucesso!")
            print("\nVocê está pronto para executar os scripts de coleta.")
        else:
            print("\n✗ Erro na conexão com GitHub")
            
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}")
        print("\nResolva os seguintes pontos:")
        print("1. Verifique se o GITHUB_TOKEN está configurado")
        print("2. Verifique se o token é válido")
        print("3. Tente criar um novo token em: https://github.com/settings/tokens")


if __name__ == "__main__":
    test_github_connection()
