"""
Script para selecionar os 200 repositórios mais populares do GitHub.
Critérios: ao menos 100 PRs (MERGED + CLOSED)
"""

import os
import json
import time
from dotenv import load_dotenv
from github import Github
import pandas as pd

load_dotenv()

class RepositorySelector:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN não configurado. Configure a variável de ambiente ou .env")
        
        self.g = Github(self.github_token)
        self.selected_repos = []
        
    def get_popular_repositories(self, max_repos=200):
        """
        Coleta os repositórios mais populares do GitHub.
        Filtra por número de PRs (MERGED + CLOSED >= 100)
        """
        print(f"Coletando os {max_repos} repositórios mais populares...")
        
        query = "stars:>1000 language:java"
        repos = self.g.search_repositories(query=query, sort="stars", order="desc")
        
        selected_count = 0
        checked_count = 0
        
        for repo in repos:
            if selected_count >= max_repos:
                break
            
            checked_count += 1
            
            try:
                # Contar PRs com status MERGED ou CLOSED
                merged_prs = self.g.search_issues(
                    f"repo:{repo.full_name} type:pr state:closed",
                    sort="created"
                )
                
                merged_count = merged_prs.totalCount
                
                if merged_count >= 100:
                    self.selected_repos.append({
                        'full_name': repo.full_name,
                        'owner': repo.owner.login,
                        'name': repo.name,
                        'stars': repo.stargazers_count,
                        'forks': repo.forks_count,
                        'language': repo.language,
                        'pr_count': merged_count,
                        'url': repo.html_url
                    })
                    
                    selected_count += 1
                    print(f"[{selected_count}/{max_repos}] {repo.full_name} - {merged_count} PRs")
                    
                    # Respeitar rate limit (otimizado)
                    time.sleep(0.1)
                else:
                    print(f"[SKIP] {repo.full_name} - Apenas {merged_count} PRs")
                    
            except Exception as e:
                print(f"[ERROR] {repo.full_name}: {str(e)}")
                continue
        
        print(f"\nRepositórios selecionados: {selected_count}")
        return self.selected_repos
    
    def save_repositories(self, output_path='data/selected_repositories.csv'):
        """Salva a lista de repositórios selecionados em CSV"""
        df = pd.DataFrame(self.selected_repos)
        df.to_csv(output_path, index=False)
        print(f"\nRepositórios salvos em: {output_path}")
        print(f"Total: {len(df)} repositórios")
        return df
    
    def display_summary(self):
        """Exibe resumo dos repositórios selecionados"""
        df = pd.DataFrame(self.selected_repos)
        
        print("\n" + "="*80)
        print("RESUMO DOS REPOSITÓRIOS SELECIONADOS")
        print("="*80)
        print(f"Total de repositórios: {len(df)}")
        print(f"\nEstatísticas de PRs:")
        print(f"  - Mínimo: {df['pr_count'].min()}")
        print(f"  - Máximo: {df['pr_count'].max()}")
        print(f"  - Mediana: {df['pr_count'].median()}")
        print(f"  - Média: {df['pr_count'].mean():.2f}")
        
        print(f"\nEstatísticas de Stars:")
        print(f"  - Mínimo: {df['stars'].min()}")
        print(f"  - Máximo: {df['stars'].max()}")
        print(f"  - Mediana: {df['stars'].median()}")
        print(f"  - Média: {df['stars'].mean():.2f}")
        
        print(f"\nLinguagens mais comuns:")
        language_counts = df['language'].value_counts().head(10)
        for lang, count in language_counts.items():
            print(f"  - {lang}: {count}")
        
        print("\nTop 10 repositórios por número de PRs:")
        top_repos = df.nlargest(10, 'pr_count')[['full_name', 'stars', 'pr_count']]
        for idx, row in top_repos.iterrows():
            print(f"  {row['full_name']}: {row['pr_count']} PRs ({row['stars']} stars)")
        
        print("="*80)


if __name__ == "__main__":
    try:
        selector = RepositorySelector()
        repos = selector.get_popular_repositories(max_repos=200)
        selector.save_repositories()
        selector.display_summary()
    except Exception as e:
        print(f"Erro: {str(e)}")
