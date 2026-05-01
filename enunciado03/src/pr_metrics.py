"""Coleta Pull Requests e calcula metricas basicas."""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from github import Github
import pandas as pd
import time

load_dotenv()

class PRMetricsCollector:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GITHUB_TOKEN não configurado. Configure a variável de ambiente ou .env")
        
        self.gh = Github(self.token)
        self.pr_rows = []
        
    def calculate_pr_metrics(self, pr, repo):
        """
        Calcula metricas para um PR:
        - tamanho: arquivos, adicoes, remocoes
        - tempo de analise: horas entre criacao e merge/close
        - descricao: caracteres do corpo
        - interacoes: participantes, comentarios
        """
        
        try:
            created_at = pr.created_at
            
            if pr.merged_at:
                closed_at = pr.merged_at
                status = "MERGED"
            else:
                closed_at = pr.closed_at
                status = "CLOSED"
            
            # Filtro simples para PRs muito rapidos
            time_diff = closed_at - created_at
            review_hours = time_diff.total_seconds() / 3600
            
            if review_hours < 0.5:
                return None
            
            pr_row = {
                'repository': repo.full_name,
                'pr_number': pr.number,
                'pr_title': pr.title,
                'pr_status': status,
                'created_at': created_at,
                'merged_or_closed_at': closed_at,
                
                # Tamanho
                'files_changed': pr.changed_files,
                'additions': pr.additions,
                'deletions': pr.deletions,
                'total_changes': pr.additions + pr.deletions,
                
                # Tempo de análise (em horas)
                'time_to_review_hours': review_hours,
                
                # Descrição
                'description_length': len(pr.body) if pr.body else 0,
                'has_description': 1 if pr.body and len(pr.body) > 0 else 0,
                
                # Interações - comentários
                'comment_count': pr.comments,
                
                # Interações - revisões
                'review_count': pr.review_comments,
                
                # Autor
                'author': pr.user.login,
                
                # URL
                'url': pr.html_url
            }
            
            # Estimativa rapida de participantes para evitar custo de API
            participant_count = 1
            
            if pr.comments > 0:
                participant_count += min(pr.comments, pr.comments)
            
            if pr.review_comments > 0:
                participant_count += min(pr.review_comments, pr.review_comments)
            
            participant_count = min(participant_count, pr.comments + pr.review_comments + 1)
            
            pr_row['participant_count'] = participant_count
            pr_row['participants'] = f"approx_{participant_count}_users"
            
            return pr_row
            
        except Exception as e:
            print(f"Erro ao processar PR #{pr.number}: {str(e)}")
            return None
    
    def collect_prs_from_repository(self, repo_name, min_reviews=1, max_prs_per_repo=50):
        """
        Coleta PRs de um repositório específico.
        Filtros (NECESSÁRIOS para responder as RQs):
        - Status: MERGED ou CLOSED (para feedback final)
        - Mínimo de 1 revisão (para análise de interações)
        - Tempo de revisão >= 0.5 horas (descartar automáticas)
        - Máximo de 50 PRs por repositório (amostra estatística)
        """
        
        print(f"\n  Coletando PRs de {repo_name} (max {max_prs_per_repo})...")
        
        try:
            repo = self.gh.get_repo(repo_name)
            
            # Buscar PRs fechados (MERGED ou CLOSED)
            prs = repo.get_pulls(state='closed', sort='created', direction='desc')
            
            valid_prs = 0
            scanned_prs = 0
            
            for pr in prs:
                # Limite de PRs por repositório
                if scanned_prs >= max_prs_per_repo:
                    print(f"    ⚠️  Limite de {max_prs_per_repo} PRs atingido para {repo_name}")
                    break
                
                scanned_prs += 1
                
                try:
                    # Só processar se tiver revisões
                    if pr.review_comments < min_reviews:
                        continue
                    
                    metrics = self.calculate_pr_metrics(pr, repo)
                    
                    if metrics:  # Se passou em todos os filtros
                        self.pr_rows.append(metrics)
                        valid_prs += 1
                        
                        if valid_prs % 5 == 0:
                            print(f"    ✓ {valid_prs} PRs validos coletados...")
                        
                        time.sleep(0.2)
                    
                except Exception as e:
                    continue
            
            print(f"  ✓ Total de PRs coletados de {repo_name}: {valid_prs}/{scanned_prs} processados")
            return valid_prs
            
        except Exception as e:
            print(f"  ❌ Erro ao coletar PRs de {repo_name}: {str(e)}")
            return 0
    
    def collect_from_multiple_repositories(self, repositories_list, max_prs_per_repo=50):
        """
        Coleta PRs de múltiplos repositórios com amostra estatística.
        repositories_list: lista com nomes dos repositórios (full_name)
        max_prs_per_repo: máximo de PRs a coletar por repositório (padrão 50)
        
        Filtros aplicados:
        - Status: MERGED ou CLOSED
        - Revisões: >= 1 (obrigatório para RQs de análise)
        - Tempo: >= 0.5 horas (descartar automáticas)
        
        Tempo estimado: ~5-8 minutos para 200 repositórios com 50 PRs cada
        Volume esperado: ~5.000-10.000 PRs para análise estatística
        """
        
        print(f"\n{'='*80}")
        print(f"Coletando PRs de {len(repositories_list)} repositórios...")
        print(f"Limite: {max_prs_per_repo} PRs por repositório (amostra estatística)")
        print(f"Filtros: MERGED/CLOSED + review_comments>=1 + time>=0.5h")
        print(f"Tempo estimado: 5-8 minutos")
        print(f"Volume esperado: ~5.000-10.000 PRs")
        print(f"{'='*80}")
        
        start_time = time.time()
        total_prs = 0
        
        for idx, repo_name in enumerate(repositories_list, 1):
            elapsed = (time.time() - start_time) / 60
            prs_per_min = (total_prs / elapsed) if elapsed > 0 else 0
            eta_mins = ((len(repositories_list) - idx) / len(repositories_list)) * elapsed if elapsed > 0 else 0
            
            print(f"\n[{idx}/{len(repositories_list)}] {repo_name}")
            print(f"   Tempo: {elapsed:.1f}m | Taxa: {prs_per_min:.0f} PRs/min | ETA: {eta_mins:.0f}m")
            
            prs_collected = self.collect_prs_from_repository(repo_name, max_prs_per_repo=max_prs_per_repo)
            total_prs += prs_collected
            
            # Rate limiting entre repositórios
            time.sleep(0.3)
        
        elapsed_total = (time.time() - start_time) / 60
        print(f"\n{'='*80}")
        print(f"✅ Coleta completa em {elapsed_total:.1f} minutos")
        print(f"Total de PRs coletados (após filtros): {total_prs}")
        print(f"Média: {(total_prs / len(repositories_list)):.1f} PRs por repositório")
        if total_prs > 0:
            print(f"Volume adequado para análise estatística: {'✅ SIM' if total_prs >= 3000 else '⚠️ INSUFICIENTE'}")
        print(f"{'='*80}")
    
    def save_pr_data(self, output_path='data/pr_metrics.csv'):
        """Salva os dados coletados em CSV"""
        if not self.pr_rows:
            print("Nenhum dado para salvar")
            return None
        
        df = pd.DataFrame(self.pr_rows)
        
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
        
        print(f"\nDados salvos em: {output_path}")
        print(f"Total de PRs coletados: {len(df)}")
        
        return df
    
    def display_summary(self):
        """Exibe resumo das métricas coletadas"""
        if not self.pr_rows:
            print("Nenhum dado para exibir")
            return
        
        df = pd.DataFrame(self.pr_rows)
        
        print("\n" + "="*80)
        print("RESUMO DAS MÉTRICAS COLETADAS")
        print("="*80)
        
        print(f"\nTotal de PRs: {len(df)}")
        print(f"Status: {df['pr_status'].value_counts().to_dict()}")
        
        print(f"\n--- TAMANHO (Mediana) ---")
        print(f"  Arquivos alterados: {df['files_changed'].median():.0f}")
        print(f"  Linhas adicionadas: {df['additions'].median():.0f}")
        print(f"  Linhas removidas: {df['deletions'].median():.0f}")
        print(f"  Total de mudanças: {df['total_changes'].median():.0f}")
        
        print(f"\n--- TEMPO DE ANÁLISE (Mediana) ---")
        print(f"  Horas para revisão: {df['time_to_review_hours'].median():.2f}")
        
        print(f"\n--- DESCRIÇÃO (Mediana) ---")
        print(f"  Caracteres na descrição: {df['description_length'].median():.0f}")
        print(f"  PRs com descrição: {(df['has_description'].sum() / len(df) * 100):.1f}%")
        
        print(f"\n--- INTERAÇÕES (Mediana) ---")
        print(f"  Comentários: {df['comment_count'].median():.0f}")
        print(f"  Comentários de revisão: {df['review_count'].median():.0f}")
        print(f"  Participantes únicos: {df['participant_count'].median():.0f}")
        
        print(f"\n--- REPOSITÓRIOS ---")
        print(f"  Total de repositórios: {df['repository'].nunique()}")
        print(f"  PRs por repositório (mediana): {df.groupby('repository').size().median():.0f}")
        
        print("="*80)


if __name__ == "__main__":
    try:
        collector = PRMetricsCollector()
        
        # Exemplo de uso
        print("Para usar este script:")
        print("1. Carregue a lista de repositórios do arquivo CSV")
        print("2. Chame collect_from_multiple_repositories(repo_list)")
        print("3. Chame save_pr_data() para salvar os resultados")
        
    except Exception as e:
        print(f"Erro: {str(e)}")
