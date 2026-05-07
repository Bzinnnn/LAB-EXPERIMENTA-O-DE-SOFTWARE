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
                participant_count += min(1, pr.comments)
            
            if pr.review_comments > 0:
                participant_count += min(1, pr.review_comments)
            
            participant_count = min(participant_count, pr.comments + pr.review_comments + 1)
            
            pr_row['participant_count'] = participant_count
            pr_row['participants'] = f"approx_{participant_count}_users"
            
            return pr_row
            
        except Exception as e:
            print(f"Erro ao processar PR #{pr.number}: {str(e)}")
            return None
    
    def collect_prs_from_repository(self, repo_name, min_reviews=1, max_prs_per_repo=50):
        """
        Coleta PRs de um repositório específico com melhor tratamento de erros.
        
        Filtros (NECESSÁRIOS para responder as RQs):
        - Status: MERGED ou CLOSED (para feedback final)
        - Mínimo de 1 revisão (para análise de interações)
        - Tempo de revisão >= 0.5 horas (descartar automáticas)
        - Máximo de 50 PRs por repositório (amostra estatística)
        
        Args:
            repo_name: nome completo do repositório (owner/repo)
            min_reviews: mínimo de comentários de revisão
            max_prs_per_repo: limite de PRs a coletar
            
        Returns:
            número de PRs válidas coletadas
        """
        
        print(f"\n  🔍 Coletando PRs de {repo_name} (max {max_prs_per_repo})...")
        
        try:
            # Obter repositório
            repo = self.gh.get_repo(repo_name)
            
            # Validações básicas
            if repo.archived:
                print(f"    ⚠️  Repositório arquivado. Pulando...")
                return 0
            
            if repo.fork:
                print(f"    ⚠️  Repositório é um fork. Processando com cuidado...")
            
            # Buscar PRs fechadas (MERGED ou CLOSED)
            prs = repo.get_pulls(state='closed', sort='created', direction='desc')
            
            valid_prs = 0
            scanned_prs = 0
            filtered_prs = 0
            
            for pr in prs:
                # Limite de PRs por repositório
                if scanned_prs >= max_prs_per_repo:
                    print(f"    ⚠️  Limite de {max_prs_per_repo} PRs atingido para {repo_name}")
                    break
                
                scanned_prs += 1
                
                try:
                    # Validação básica rápida
                    if pr.review_comments < min_reviews:
                        filtered_prs += 1
                        continue
                    
                    # Calcular métricas
                    metrics = self.calculate_pr_metrics(pr, repo)
                    
                    if metrics:  # Se passou em todos os filtros
                        self.pr_rows.append(metrics)
                        valid_prs += 1
                        
                        if valid_prs % 5 == 0:
                            print(f"    ✓ {valid_prs} PRs válidas coletadas...")
                        
                        # Pequena pausa para não sobrecarregar a API
                        time.sleep(0.2)
                    
                except Exception as e:
                    print(f"    ⚠️  Erro ao processar PR #{pr.number}: {str(e)}")
                    continue
            
            summary = f"  ✅ {repo_name}: {valid_prs} PRs válidas coletadas"
            if scanned_prs > 0:
                summary += f" ({valid_prs}/{scanned_prs} processadas, {filtered_prs} filtradas)"
            print(summary)
            
            return valid_prs
            
        except Exception as e:
            print(f"  ❌ Erro crítico ao coletar PRs de {repo_name}: {str(e)}")
            import traceback
            traceback.print_exc()
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
        failed_repos = 0
        successful_repos = 0
        
        for idx, repo_name in enumerate(repositories_list, 1):
            elapsed = (time.time() - start_time) / 60  # Tempo decorrido em minutos
            
            # Cálculo CORRETO de ETA:
            # taxa = minutos por repositório = elapsed / idx
            # repos_restantes = len(repositories_list) - idx
            # ETA = repos_restantes * taxa
            if idx > 0 and elapsed > 0:
                rate_mins_per_repo = elapsed / idx
                repos_remaining = len(repositories_list) - idx
                eta_mins = repos_remaining * rate_mins_per_repo
                prs_per_min = total_prs / elapsed if elapsed > 0 else 0
            else:
                eta_mins = 0
                prs_per_min = 0
            
            # Formatação de progresso
            progress_pct = (idx / len(repositories_list)) * 100
            status_icon = "⏳" if idx < len(repositories_list) else "✅"
            
            print(f"\n[{status_icon} {idx}/{len(repositories_list)} ({progress_pct:.1f}%)] {repo_name}")
            print(f"   ⏱️  Decorrido: {elapsed:.1f}m | Taxa: {prs_per_min:.1f} PRs/min | ETA: {eta_mins:.1f}m")
            
            try:
                prs_collected = self.collect_prs_from_repository(
                    repo_name, 
                    max_prs_per_repo=max_prs_per_repo
                )
                
                if prs_collected > 0:
                    total_prs += prs_collected
                    successful_repos += 1
                else:
                    failed_repos += 1
                
            except Exception as e:
                print(f"   ❌ Erro geral ao processar {repo_name}: {str(e)}")
                failed_repos += 1
                continue
            
            # Rate limiting entre repositórios
            time.sleep(0.3)
        
        elapsed_total = (time.time() - start_time) / 60
        
        print(f"\n{'='*80}")
        print(f"✅ Coleta completa em {elapsed_total:.1f} minutos")
        print(f"   Total de PRs coletados (após filtros): {total_prs}")
        print(f"   Repositórios processados com sucesso: {successful_repos}/{len(repositories_list)}")
        print(f"   Repositórios com erro: {failed_repos}")
        
        if len(repositories_list) > 0:
            print(f"   Média: {(total_prs / len(repositories_list)):.1f} PRs por repositório")
            
        if total_prs > 0:
            status = '✅ SIM - Adequado' if total_prs >= 3000 else '⚠️ INSUFICIENTE - Abaixo de 3000'
            print(f"   Volume adequado para análise: {status}")
        
        print(f"{'='*80}")
    
    def save_pr_data(self, output_path='data/pr_metrics.csv'):
        """
        Salva os dados coletados em CSV com validações e tratamento de dados.
        
        Procedimentos:
        1. Valida estrutura básica
        2. Remove dados duplicados/inválidos
        3. Realiza limpeza de valores extremos
        4. Salva e gera relatório
        
        Args:
            output_path: caminho para salvar o arquivo CSV
            
        Returns:
            DataFrame com os dados salvos, ou None se houve erro
        """
        if not self.pr_rows:
            print("❌ Nenhum dado coletado para salvar")
            return None
        
        try:
            print(f"\n📊 Processando {len(self.pr_rows)} registros de PRs...")
            
            # Criar DataFrame
            df = pd.DataFrame(self.pr_rows)
            
            # Validar colunas críticas
            critical_columns = ['repository', 'pr_number', 'pr_status', 'created_at', 'merged_or_closed_at']
            missing_cols = [col for col in critical_columns if col not in df.columns]
            if missing_cols:
                print(f"❌ Colunas críticas ausentes: {missing_cols}")
                return None
            
            print(f"✓ Validação de estrutura OK - {len(df.columns)} colunas encontradas")
            
            # Remover duplicatas (mesmo PR não deve aparecer 2x)
            df_before = len(df)
            df = df.drop_duplicates(subset=['repository', 'pr_number'], keep='first')
            duplicates_removed = df_before - len(df)
            if duplicates_removed > 0:
                print(f"⚠️  {duplicates_removed} registros duplicados removidos")
            
            # Remover valores nulos críticos
            df = df.dropna(subset=['repository', 'pr_number', 'pr_status'])
            
            # Validar tipos de dados e converter se necessário
            df['time_to_review_hours'] = pd.to_numeric(df['time_to_review_hours'], errors='coerce')
            df['files_changed'] = pd.to_numeric(df['files_changed'], errors='coerce')
            df['additions'] = pd.to_numeric(df['additions'], errors='coerce')
            df['deletions'] = pd.to_numeric(df['deletions'], errors='coerce')
            
            # Detectar outliers extremos (possíveis erros de coleta)
            print(f"\n🔍 Analisando outliers...")
            
            # Valores razoáveis para PR review
            max_reasonable_files = 1000  # PR com >1000 arquivos é suspeita
            max_reasonable_changes = 100000  # >100k linhas é suspeita
            
            outliers = df[
                (df['files_changed'] > max_reasonable_files) |
                (df['total_changes'] > max_reasonable_changes)
            ]
            
            if len(outliers) > 0:
                print(f"⚠️  {len(outliers)} possíveis outliers detectados (PRs muito grandes)")
                print(f"   Mantendo para análise posterior (não removendo)")
            
            # Garantir que o diretório existe
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Reordenar colunas para melhor legibilidade
            column_order = [
                'repository', 'pr_number', 'pr_title', 'pr_status',
                'created_at', 'merged_or_closed_at',
                'files_changed', 'additions', 'deletions', 'total_changes',
                'time_to_review_hours', 'description_length', 'has_description',
                'comment_count', 'review_count', 'participant_count',
                'author', 'url', 'participants'
            ]
            
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
            
            # Salvar CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            print(f"\n✅ Dados salvos com sucesso!")
            print(f"   Arquivo: {output_path}")
            print(f"   Total de PRs: {len(df)}")
            print(f"   Tamanho do arquivo: {os.path.getsize(output_path) / 1024:.1f} KB")
            
            # Estatísticas rápidas
            print(f"\n📈 Estatísticas dos dados salvos:")
            print(f"   Status MERGED: {len(df[df['pr_status'] == 'MERGED'])} ({(len(df[df['pr_status'] == 'MERGED'])/len(df)*100):.1f}%)")
            print(f"   Status CLOSED: {len(df[df['pr_status'] == 'CLOSED'])} ({(len(df[df['pr_status'] == 'CLOSED'])/len(df)*100):.1f}%)")
            print(f"   Repositórios únicos: {df['repository'].nunique()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao salvar dados: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def display_summary(self):
        """
        Exibe resumo estatístico detalhado das métricas coletadas.
        Inclui distribuição, outliers, e análises por status de PR.
        """
        if not self.pr_rows:
            print("❌ Nenhum dado para exibir")
            return
        
        try:
            df = pd.DataFrame(self.pr_rows)
            
            if df.empty:
                print("❌ DataFrame vazio - nenhum dado disponível")
                return
            
            print("\n" + "="*80)
            print("📊 RESUMO DETALHADO DAS MÉTRICAS COLETADAS")
            print("="*80)
            
            # Informações gerais
            print(f"\n📌 INFORMAÇÕES GERAIS:")
            print(f"  Total de PRs: {len(df):,}")
            print(f"  Repositórios únicos: {df['repository'].nunique()}")
            print(f"  Autores únicos: {df['author'].nunique()}")
            
            status_dist = df['pr_status'].value_counts()
            print(f"\n  Distribuição por Status:")
            for status, count in status_dist.items():
                pct = (count / len(df)) * 100
                print(f"    - {status}: {count:,} ({pct:.1f}%)")
            
            # Análise por tamanho
            print(f"\n📏 TAMANHO (Mediana / Média / Máx):")
            print(f"  Arquivos alterados: {df['files_changed'].median():.0f} / {df['files_changed'].mean():.1f} / {df['files_changed'].max():.0f}")
            print(f"  Linhas adicionadas: {df['additions'].median():.0f} / {df['additions'].mean():.1f} / {df['additions'].max():.0f}")
            print(f"  Linhas removidas: {df['deletions'].median():.0f} / {df['deletions'].mean():.1f} / {df['deletions'].max():.0f}")
            print(f"  Total de mudanças: {df['total_changes'].median():.0f} / {df['total_changes'].mean():.1f} / {df['total_changes'].max():.0f}")
            
            # Análise temporal
            print(f"\n⏱️  TEMPO DE ANÁLISE (Mediana / Média / Máx):")
            review_hours_med = df['time_to_review_hours'].median()
            review_hours_mean = df['time_to_review_hours'].mean()
            review_hours_max = df['time_to_review_hours'].max()
            print(f"  Horas para revisão: {review_hours_med:.2f}h / {review_hours_mean:.2f}h / {review_hours_max:.2f}h")
            print(f"  Dias para revisão: {(review_hours_med/24):.2f}d / {(review_hours_mean/24):.2f}d / {(review_hours_max/24):.2f}d")
            
            # Análise de descrição
            print(f"\n📝 DESCRIÇÃO (Estatísticas):")
            desc_med = df['description_length'].median()
            desc_mean = df['description_length'].mean()
            print(f"  Caracteres na descrição: {desc_med:.0f} (mediana) / {desc_mean:.1f} (média)")
            pct_with_desc = (df['has_description'].sum() / len(df)) * 100
            print(f"  PRs com descrição: {pct_with_desc:.1f}%")
            
            # Análise de interações
            print(f"\n💬 INTERAÇÕES (Mediana / Média):")
            print(f"  Comentários: {df['comment_count'].median():.0f} / {df['comment_count'].mean():.1f}")
            print(f"  Comentários de revisão: {df['review_count'].median():.0f} / {df['review_count'].mean():.1f}")
            print(f"  Participantes únicos: {df['participant_count'].median():.0f} / {df['participant_count'].mean():.1f}")
            
            # Análise comparativa: MERGED vs CLOSED
            print(f"\n🔀 COMPARAÇÃO: MERGED vs CLOSED")
            merged_df = df[df['pr_status'] == 'MERGED']
            closed_df = df[df['pr_status'] == 'CLOSED']
            
            if len(merged_df) > 0 and len(closed_df) > 0:
                print(f"\n  MERGED ({len(merged_df)} PRs):")
                print(f"    - Tamanho médio: {merged_df['total_changes'].median():.0f} mudanças")
                print(f"    - Tempo médio: {merged_df['time_to_review_hours'].median():.2f} horas")
                print(f"    - Participantes médios: {merged_df['participant_count'].median():.0f}")
                
                print(f"\n  CLOSED ({len(closed_df)} PRs):")
                print(f"    - Tamanho médio: {closed_df['total_changes'].median():.0f} mudanças")
                print(f"    - Tempo médio: {closed_df['time_to_review_hours'].median():.2f} horas")
                print(f"    - Participantes médios: {closed_df['participant_count'].median():.0f}")
            
            # Top repositórios
            print(f"\n🏆 TOP 10 REPOSITÓRIOS POR NÚMERO DE PRs:")
            top_repos = df['repository'].value_counts().head(10)
            for idx, (repo, count) in enumerate(top_repos.items(), 1):
                print(f"  {idx}. {repo}: {count} PRs")
            
            print("\n" + "="*80)
            
        except Exception as e:
            print(f"❌ Erro ao exibir resumo: {str(e)}")
            import traceback
            traceback.print_exc()


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
