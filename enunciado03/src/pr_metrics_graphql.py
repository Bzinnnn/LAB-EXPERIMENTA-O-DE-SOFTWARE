"""
Script otimizado para coletar PRs usando GraphQL + Paralelização
Estratégia: Máxima velocidade (15-20 minutos para 200 repos)
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from github import Github
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json

load_dotenv()

class PRMetricsCollectorGraphQL:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN não configurado")
        
        self.g = Github(self.github_token)
        self.pr_data = []
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
        }
        
    def graphql_query(self, query):
        """Executa uma query GraphQL"""
        try:
            response = requests.post(
                self.graphql_url,
                json={"query": query},
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro GraphQL: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro na requisição GraphQL: {str(e)}")
            return None
    
    def build_pr_query(self, owner, repo_name, cursor=None):
        """Constrói query GraphQL para coletar PRs em batch"""
        
        cursor_param = f', after: "{cursor}"' if cursor else ""
        
        query = f"""
        query {{
            repository(owner: "{owner}", name: "{repo_name}") {{
                pullRequests(first: 100, states: [MERGED, CLOSED]{cursor_param}) {{
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                    nodes {{
                        number
                        title
                        state
                        createdAt
                        mergedAt
                        closedAt
                        additions
                        deletions
                        files {{
                            totalCount
                        }}
                        comments {{
                            totalCount
                        }}
                        reviewThreads {{
                            totalCount
                        }}
                        reviews {{
                            totalCount
                        }}
                        body
                        author {{
                            login
                        }}
                    }}
                }}
            }}
        }}
        """
        
        return query
    
    def calculate_metrics_from_graphql(self, pr_data, repo_full_name):
        """Processa dados do GraphQL e calcula métricas"""
        
        try:
            pr_number = pr_data['number']
            pr_title = pr_data['title']
            state = pr_data['state']
            created_at = datetime.fromisoformat(pr_data['createdAt'].replace('Z', '+00:00'))
            
            # Determinar data final e status
            if state == "MERGED":
                final_date = datetime.fromisoformat(pr_data['mergedAt'].replace('Z', '+00:00'))
                status = "MERGED"
            else:
                final_date = datetime.fromisoformat(pr_data['closedAt'].replace('Z', '+00:00'))
                status = "CLOSED"
            
            # Verificar se levou pelo menos 1 hora
            time_diff = final_date - created_at
            hours_to_review = time_diff.total_seconds() / 3600
            
            if hours_to_review < 1:
                return None  # Filtrar PRs muito rápidos (bots)
            
            # Contar participantes (aproximação via contadores)
            comment_count = pr_data['comments']['totalCount']
            review_count = pr_data['reviews']['totalCount']
            participant_count = 1 + comment_count + review_count  # autor + comentadores + revisores
            
            # Filtro: pelo menos 1 revisão
            if review_count < 1:
                return None
            
            pr_info = {
                'repository': repo_full_name,
                'pr_number': pr_number,
                'pr_title': pr_title,
                'pr_status': status,
                'created_at': created_at,
                'merged_or_closed_at': final_date,
                
                # Tamanho
                'files_changed': pr_data['files']['totalCount'],
                'additions': pr_data['additions'],
                'deletions': pr_data['deletions'],
                'total_changes': pr_data['additions'] + pr_data['deletions'],
                
                # Tempo de análise (em horas)
                'time_to_review_hours': hours_to_review,
                
                # Descrição
                'description_length': len(pr_data['body']) if pr_data['body'] else 0,
                'has_description': 1 if pr_data['body'] and len(pr_data['body']) > 0 else 0,
                
                # Interações
                'comment_count': comment_count,
                'review_count': review_count,
                'participant_count': min(participant_count, comment_count + review_count + 1),
                
                # Autor
                'author': pr_data['author']['login'] if pr_data['author'] else 'unknown',
                
                # URL
                'url': f"https://github.com/{repo_full_name}/pull/{pr_number}",
                'participants': f"approx_{participant_count}_users"
            }
            
            return pr_info
            
        except Exception as e:
            print(f"Erro ao processar PR #{pr_data.get('number', '?')}: {str(e)}")
            return None
    
    def collect_prs_graphql(self, repo_full_name):
        """Coleta PRs de um repositório usando GraphQL (todo em uma query)"""
        
        owner, repo_name = repo_full_name.split('/')
        pr_count = 0
        cursor = None
        
        while True:
            try:
                # Query GraphQL
                query = self.build_pr_query(owner, repo_name, cursor)
                result = self.graphql_query(query)
                
                if not result or 'data' not in result:
                    print(f"  ⚠️  Erro ao buscar PRs de {repo_full_name}")
                    break
                
                repo_data = result['data']['repository']
                if not repo_data:
                    break
                
                prs = repo_data['pullRequests']['nodes']
                
                if not prs:
                    break
                
                # Processar cada PR
                for pr in prs:
                    metrics = self.calculate_metrics_from_graphql(pr, repo_full_name)
                    if metrics:
                        self.pr_data.append(metrics)
                        pr_count += 1
                
                # Paginação
                page_info = repo_data['pullRequests']['pageInfo']
                if not page_info['hasNextPage']:
                    break
                
                cursor = page_info['endCursor']
                time.sleep(0.2)  # Rate limiting entre páginas
                
            except Exception as e:
                print(f"  ❌ Erro ao coletar PRs de {repo_full_name}: {str(e)}")
                break
        
        return pr_count
    
    def collect_from_multiple_repositories_parallel(self, repositories_list, max_workers=4):
        """
        Coleta PRs de múltiplos repositórios em paralelo.
        max_workers: número de threads simultâneas (3-5 recomendado)
        """
        
        print(f"\n⚡ Coletando PRs em paralelo ({max_workers} threads)...")
        print(f"   Total de repositórios: {len(repositories_list)}\n")
        
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submeter todas as tarefas
            futures = {
                executor.submit(self.collect_prs_graphql, repo): repo 
                for repo in repositories_list
            }
            
            # Processar conforme completam
            for future in as_completed(futures):
                repo = futures[future]
                completed += 1
                
                try:
                    pr_count = future.result()
                    print(f"   [{completed}/{len(repositories_list)}] {repo}: {pr_count} PRs ✅")
                except Exception as e:
                    print(f"   [{completed}/{len(repositories_list)}] {repo}: ERRO ❌")
        
        print(f"\n✅ Coleta paralela concluída!")
    
    def save_pr_data(self, output_path='data/pr_metrics.csv'):
        """Salva os dados coletados em CSV"""
        if not self.pr_data:
            print("Nenhum dado para salvar")
            return None
        
        df = pd.DataFrame(self.pr_data)
        
        # Reordenar colunas
        columns = [
            'repository', 'pr_number', 'pr_title', 'pr_status',
            'created_at', 'merged_or_closed_at',
            'files_changed', 'additions', 'deletions', 'total_changes',
            'time_to_review_hours', 'description_length', 'has_description',
            'comment_count', 'review_count', 'participant_count',
            'author', 'url', 'participants'
        ]
        
        df = df[[col for col in columns if col in df.columns]]
        df.to_csv(output_path, index=False)
        
        print(f"\n✅ Dados salvos em: {output_path}")
        print(f"   Total de PRs coletados: {len(df)}")
        
        return df
    
    def display_summary(self):
        """Exibe resumo das métricas coletadas"""
        if not self.pr_data:
            print("Nenhum dado para exibir")
            return
        
        df = pd.DataFrame(self.pr_data)
        
        print("\n" + "="*80)
        print("RESUMO DAS MÉTRICAS COLETADAS (GraphQL + Paralelização)")
        print("="*80)
        
        print(f"\n✅ Total de PRs: {len(df)}")
        print(f"   Status: {df['pr_status'].value_counts().to_dict()}")
        
        print(f"\n--- TAMANHO (Mediana) ---")
        print(f"   Arquivos alterados: {df['files_changed'].median():.0f}")
        print(f"   Linhas adicionadas: {df['additions'].median():.0f}")
        print(f"   Linhas removidas: {df['deletions'].median():.0f}")
        print(f"   Total de mudanças: {df['total_changes'].median():.0f}")
        
        print(f"\n--- TEMPO DE ANÁLISE (Mediana) ---")
        print(f"   Horas para revisão: {df['time_to_review_hours'].median():.2f}")
        
        print(f"\n--- DESCRIÇÃO (Mediana) ---")
        print(f"   Caracteres na descrição: {df['description_length'].median():.0f}")
        print(f"   PRs com descrição: {(df['has_description'].sum() / len(df) * 100):.1f}%")
        
        print(f"\n--- INTERAÇÕES (Mediana) ---")
        print(f"   Comentários: {df['comment_count'].median():.0f}")
        print(f"   Comentários de revisão: {df['review_count'].median():.0f}")
        print(f"   Participantes únicos: {df['participant_count'].median():.0f}")
        
        print(f"\n--- REPOSITÓRIOS ---")
        print(f"   Total de repositórios: {df['repository'].nunique()}")
        print(f"   PRs por repositório (mediana): {df.groupby('repository').size().median():.0f}")
        
        print("="*80)


if __name__ == "__main__":
    try:
        collector = PRMetricsCollectorGraphQL()
        
        # Teste rápido
        print("GraphQL + Paralelização - Módulo carregado com sucesso! ✅")
        
    except Exception as e:
        print(f"Erro: {str(e)}")
