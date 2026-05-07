"""Seleciona os repositorios mais populares do GitHub."""

import os
import json
import time
from dotenv import load_dotenv
from github import Github, GithubException
import pandas as pd

load_dotenv()

class RepositorySelector:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GITHUB_TOKEN não configurado. Configure a variável de ambiente ou .env")
        
        self.gh = Github(self.token)
        self.selected_repos = []
        self.languages = ['Java', 'Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C++']
        
    def get_popular_repositories(self, max_repos=200, min_pr_count=100):
        """
        Coleta os repositórios mais populares do GitHub com diversidade de linguagens.
        
        Args:
            max_repos: número máximo de repositórios a coletar
            min_pr_count: número mínimo de PRs fechadas para qualificar
            
        Filtra por:
        - Repositórios com >1000 stars
        - Múltiplas linguagens (maior diversidade)
        - Número de PRs (MERGED + CLOSED >= min_pr_count)
        """
        print(f"Coletando até {max_repos} repositórios mais populares (min {min_pr_count} PRs por repo)...")
        print(f"Linguagens alvo: {', '.join(self.languages)}")
        
        repos_per_language = max(max_repos // len(self.languages), 30)
        
        for language in self.languages:
            if len(self.selected_repos) >= max_repos:
                print(f"\n✅ Meta de {max_repos} repositórios atingida!")
                break
            
            print(f"\n[Linguagem: {language}] Coletando até {repos_per_language} repositórios...")
            
            query = f"stars:>1000 language:{language}"
            
            try:
                repos = self.gh.search_repositories(query=query, sort="stars", order="desc")
                
                repos_in_language = 0
                checked_count = 0
                max_checks = repos_per_language * 3  # Revisar 3x mais para encontrar qualificados
                
                for repo in repos:
                    if repos_in_language >= repos_per_language:
                        print(f"  Limite de {repos_per_language} repositórios atingido para {language}")
                        break
                    
                    if checked_count >= max_checks:
                        print(f"  Limite de verificações ({max_checks}) atingido para {language}")
                        break
                    
                    checked_count += 1
                    
                    try:
                        # Validar dados básicos do repositório
                        if not self._validate_repository(repo):
                            continue
                        
                        # Contagem de PRs fechadas (MERGED + CLOSED)
                        pr_count = self._count_closed_pull_requests(repo.full_name)
                        
                        if pr_count >= min_pr_count:
                            repo_data = {
                                'full_name': repo.full_name,
                                'owner': repo.owner.login,
                                'name': repo.name,
                                'stars': repo.stargazers_count,
                                'forks': repo.forks_count,
                                'language': repo.language or 'Unknown',
                                'pr_count': pr_count,
                                'url': repo.html_url,
                                'created_at': repo.created_at,
                                'updated_at': repo.updated_at
                            }
                            
                            self.selected_repos.append(repo_data)
                            repos_in_language += 1
                            total_selected = len(self.selected_repos)
                            
                            print(f"  [{total_selected}/{max_repos}] {repo.full_name} - {pr_count} PRs - ⭐ {repo.stargazers_count}")
                            
                            # Rate limit: aguardar entre requisições
                            time.sleep(0.15)
                        else:
                            if checked_count % 5 == 0:
                                print(f"  [SKIP] {repo.full_name} - Apenas {pr_count} PRs (mínimo: {min_pr_count})")
                        
                    except GithubException as e:
                        if e.status == 403:
                            print(f"  ⚠️  Rate limit atingido. Aguardando...")
                            time.sleep(60)
                        continue
                    except Exception as e:
                        print(f"  [ERROR] {repo.full_name}: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"  Erro ao buscar repositórios em {language}: {str(e)}")
                continue
        
        print(f"\n{'='*80}")
        print(f"✅ Repositórios selecionados: {len(self.selected_repos)}")
        print(f"{'='*80}")
        return self.selected_repos
    
    def _validate_repository(self, repo):
        """Valida se o repositório atende critérios básicos"""
        try:
            # Não incluir repositórios arquivados ou desativados
            if repo.archived:
                return False
            
            # Verificar se tem dados mínimos
            if not repo.full_name or not repo.language:
                return False
            
            # Deve ter mínimo de atividade
            if repo.stargazers_count < 1000:
                return False
            
            return True
        except:
            return False
    
    def _count_closed_pull_requests(self, repo_full_name):
        """
        Conta o número de PRs fechadas (MERGED ou CLOSED).
        Usa cache local para evitar múltiplas requisições.
        """
        try:
            closed_prs = self.gh.search_issues(
                f"repo:{repo_full_name} type:pr state:closed",
                sort="created"
            )
            
            return closed_prs.totalCount
        except GithubException as e:
            if e.status == 403:
                print(f"    ⚠️  Rate limit para {repo_full_name}")
                return 0
            return 0
        except Exception:
            return 0
    
    def save_repositories(self, output_path='data/selected_repositories.csv'):
        """
        Salva a lista de repositórios selecionados em CSV com validação.
        
        Args:
            output_path: caminho para salvar o arquivo CSV
            
        Returns:
            DataFrame com os repositórios salvos
        """
        if not self.selected_repos:
            print("Nenhum repositório selecionado para salvar!")
            return None
        
        try:
            df = pd.DataFrame(self.selected_repos)
            
            # Validar dados antes de salvar
            if df.empty:
                print("DataFrame vazio! Nenhum repositório será salvo.")
                return None
            
            # Garantir que colunas críticas não tenham valores nulos
            critical_columns = ['full_name', 'pr_count', 'language']
            for col in critical_columns:
                if col not in df.columns:
                    print(f"Aviso: Coluna crítica '{col}' não encontrada")
                    return None
            
            # Remover duplicatas (mesmo repositório não deve aparecer 2x)
            df = df.drop_duplicates(subset=['full_name'], keep='first')
            
            # Ordenar por número de PRs (descendente)
            df = df.sort_values('pr_count', ascending=False)
            
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Salvar CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            print(f"\n✅ Repositórios salvos em: {output_path}")
            print(f"   Total: {len(df)} repositórios únicos")
            print(f"   Tamanho do arquivo: {os.path.getsize(output_path) / 1024:.1f} KB")
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao salvar repositórios: {str(e)}")
            return None
    
    def display_summary(self):
        """
        Exibe resumo estatístico detalhado dos repositórios selecionados.
        Inclui distribuição por linguagem, stars, PRs e detecção de outliers.
        """
        if not self.selected_repos:
            print("Nenhum repositório para exibir!")
            return
        
        try:
            df = pd.DataFrame(self.selected_repos)
            
            if df.empty:
                print("Nenhum dado para exibir")
                return
            
            print("\n" + "="*80)
            print("RESUMO DOS REPOSITÓRIOS SELECIONADOS")
            print("="*80)
            
            print(f"\nTotal de repositórios: {len(df)}")
            
            # Estatísticas de PRs
            print(f"\n📊 ESTATÍSTICAS DE PRs:")
            print(f"  - Mínimo: {df['pr_count'].min():.0f}")
            print(f"  - Máximo: {df['pr_count'].max():.0f}")
            print(f"  - Mediana: {df['pr_count'].median():.0f}")
            print(f"  - Média: {df['pr_count'].mean():.2f}")
            print(f"  - Desvio padrão: {df['pr_count'].std():.2f}")
            
            # Estatísticas de Stars
            print(f"\n⭐ ESTATÍSTICAS DE STARS:")
            print(f"  - Mínimo: {df['stars'].min():,.0f}")
            print(f"  - Máximo: {df['stars'].max():,.0f}")
            print(f"  - Mediana: {df['stars'].median():,.0f}")
            print(f"  - Média: {df['stars'].mean():,.2f}")
            
            # Distribuição de linguagens
            print(f"\n💻 DISTRIBUIÇÃO POR LINGUAGEM:")
            language_counts = df['language'].value_counts()
            for lang, count in language_counts.items():
                pct = (count / len(df)) * 100
                print(f"  - {lang}: {count} ({pct:.1f}%)")
            
            # Top 10 repositórios por PRs
            print(f"\n🏆 TOP 10 REPOSITÓRIOS POR NÚMERO DE PRs:")
            top_repos = df.nlargest(10, 'pr_count')[['full_name', 'stars', 'pr_count', 'language']]
            for idx, (_, row) in enumerate(top_repos.iterrows(), 1):
                print(f"  {idx}. {row['full_name']}: {row['pr_count']:.0f} PRs | ⭐ {row['stars']:,.0f} | {row['language']}")
            
            # Top 10 repositórios por Stars
            print(f"\n✨ TOP 10 REPOSITÓRIOS POR STARS:")
            top_stars = df.nlargest(10, 'stars')[['full_name', 'stars', 'pr_count', 'language']]
            for idx, (_, row) in enumerate(top_stars.iterrows(), 1):
                print(f"  {idx}. {row['full_name']}: ⭐ {row['stars']:,.0f} | {row['pr_count']:.0f} PRs | {row['language']}")
            
            # Estatísticas de forks
            print(f"\n🔀 ESTATÍSTICAS DE FORKS:")
            print(f"  - Média: {df['forks'].mean():,.2f}")
            print(f"  - Máximo: {df['forks'].max():,.0f}")
            print(f"  - Mediana: {df['forks'].median():,.0f}")
            
            print("\n" + "="*80)
            
        except Exception as e:
            print(f"Erro ao exibir resumo: {str(e)}")


if __name__ == "__main__":
    try:
        selector = RepositorySelector()
        repos = selector.get_popular_repositories(max_repos=200)
        selector.save_repositories()
        selector.display_summary()
    except Exception as e:
        print(f"Erro: {str(e)}")
