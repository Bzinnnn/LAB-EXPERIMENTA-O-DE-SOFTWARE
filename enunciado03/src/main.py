"""
Script principal para Lab03S01 - Enunciado 3
Executa:
1. Seleção dos 200 repositórios mais populares
2. Coleta de PRs e cálculo de métricas
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from repository_selector import RepositorySelector
from pr_metrics import PRMetricsCollector

load_dotenv()

# Criar diretórios necessários
os.makedirs('enunciado03/data', exist_ok=True)
os.makedirs('enunciado03/docs', exist_ok=True)

def main():
    print("\n" + "="*80)
    print("LAB03S01 - Enunciado 3: Code Review Analysis")
    print("="*80)
    
    # Verificar token
    if not os.getenv('GITHUB_TOKEN'):
        print("\n⚠️  ERRO: GITHUB_TOKEN não configurado!")
        print("Configure a variável de ambiente ou crie um arquivo .env com:")
        print("GITHUB_TOKEN=seu_token_aqui")
        return
    
    try:
        # ETAPA 1: Verificar se repositórios já foram selecionados
        repos_csv_path = 'enunciado03/data/selected_repositories.csv'
        
        if os.path.exists(repos_csv_path):
            print("\n[ETAPA 1] ✓ CSV de repositórios já existe!")
            print("-" * 80)
            print(f"Carregando: {repos_csv_path}")
            
            # Carregar repositórios do CSV
            repos_df = pd.read_csv(repos_csv_path)
            print(f"✓ {len(repos_df)} repositórios carregados do arquivo existente")
            print(f"  - Primeiros 3: {', '.join(repos_df['full_name'].head(3).tolist())}")
            
            # Converter DataFrame para lista de dicts para compatibilidade
            repos = repos_df.to_dict('records')
        else:
            print("\n[ETAPA 1] Selecionando repositórios populares...")
            print("-" * 80)
            
            selector = RepositorySelector()
            repos = selector.get_popular_repositories(max_repos=200)
            
            # Salvar repositórios
            repos_df = selector.save_repositories(repos_csv_path)
            selector.display_summary()
        
        # ETAPA 2: Coletar PRs e métricas
        print("\n[ETAPA 2] Coletando PRs e métricas...")
        print("-" * 80)
        
        collector = PRMetricsCollector()
        
        # Usar lista de repositórios
        repo_names = [repo['full_name'] for repo in repos]
        collector.collect_from_multiple_repositories(repo_names, max_prs_per_repo=50)
        
        # Salvar dados
        pr_df = collector.save_pr_data('enunciado03/data/pr_metrics.csv')
        collector.display_summary()
        
        # ETAPA 3: Gerar relatório inicial
        print("\n[ETAPA 3] Gerando relatório inicial...")
        print("-" * 80)
        
        generate_sprint1_report(repos_df, pr_df)
        
        print("\n" + "="*80)
        print("✅ Lab03S01 concluído com sucesso!")
        print("="*80)
        print("\nArquivos gerados:")
        print("  - enunciado03/data/selected_repositories.csv")
        print("  - enunciado03/data/pr_metrics.csv")
        print("  - enunciado03/docs/RELATORIO_SPRINT1.txt")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()


def generate_sprint1_report(repos_df, pr_df):
    """Gera relatório inicial da Sprint 1"""
    
    if pr_df is None or len(pr_df) == 0:
        print("Nenhum dado de PR para gerar relatório")
        return
    
    report = []
    report.append("="*80)
    report.append("LAB03S01 - RELATÓRIO SPRINT 1")
    report.append("Caracterizando a atividade de code review no GitHub")
    report.append("="*80)
    
    report.append("\n1. REPOSITÓRIOS SELECIONADOS")
    report.append("-" * 80)
    report.append(f"Total de repositórios: {len(repos_df)}")
    report.append(f"Critério: Top 200 repositórios com pelo menos 100 PRs (MERGED + CLOSED)")
    report.append(f"\nTamanho dos repositórios (por número de PRs):")
    report.append(f"  - Mínimo: {repos_df['pr_count'].min()}")
    report.append(f"  - Máximo: {repos_df['pr_count'].max()}")
    report.append(f"  - Mediana: {repos_df['pr_count'].median():.0f}")
    report.append(f"  - Média: {repos_df['pr_count'].mean():.2f}")
    
    report.append(f"\nRepositórios por linguagem:")
    for lang, count in repos_df['language'].value_counts().head(10).items():
        report.append(f"  - {lang}: {count}")
    
    report.append("\n\n2. CRITÉRIOS DE SELEÇÃO DE PRS")
    report.append("-" * 80)
    report.append("✓ Status: MERGED ou CLOSED")
    report.append("✓ Mínimo de 1 revisão (review_comments >= 1)")
    report.append("✓ Tempo de revisão: mínimo 1 hora")
    
    report.append("\n\n3. DADOS COLETADOS")
    report.append("-" * 80)
    report.append(f"Total de PRs coletados: {len(pr_df)}")
    report.append(f"PRs MERGED: {len(pr_df[pr_df['pr_status'] == 'MERGED'])}")
    report.append(f"PRs CLOSED: {len(pr_df[pr_df['pr_status'] == 'CLOSED'])}")
    
    report.append("\n\n4. ESTATÍSTICAS DESCRITIVAS (MEDIANAS)")
    report.append("-" * 80)
    
    report.append("\n--- Tamanho ---")
    report.append(f"Arquivos alterados: {pr_df['files_changed'].median():.0f}")
    report.append(f"Linhas adicionadas: {pr_df['additions'].median():.0f}")
    report.append(f"Linhas removidas: {pr_df['deletions'].median():.0f}")
    report.append(f"Total de mudanças: {pr_df['total_changes'].median():.0f}")
    
    report.append("\n--- Tempo de Análise ---")
    report.append(f"Horas para revisão: {pr_df['time_to_review_hours'].median():.2f} horas")
    report.append(f"Dias para revisão: {(pr_df['time_to_review_hours'].median() / 24):.2f} dias")
    
    report.append("\n--- Descrição ---")
    report.append(f"Caracteres na descrição: {pr_df['description_length'].median():.0f}")
    report.append(f"PRs com descrição: {(pr_df['has_description'].sum() / len(pr_df) * 100):.1f}%")
    
    report.append("\n--- Interações ---")
    report.append(f"Comentários: {pr_df['comment_count'].median():.0f}")
    report.append(f"Comentários de revisão: {pr_df['review_count'].median():.0f}")
    report.append(f"Participantes únicos: {pr_df['participant_count'].median():.0f}")
    
    report.append("\n\n5. HIPÓTESES INICIAIS (INFORMAIS)")
    report.append("-" * 80)
    
    report.append("""
H1: PRs pequenas (poucas linhas) têm maior chance de serem MERGED
    - Hipótese: Código mais pequeno é mais fácil de revisar e tem menos problemas
    
H2: PRs com descrições detalhadas têm maior chance de serem MERGED
    - Hipótese: Descrição clara facilita a revisão e aumenta confiança
    
H3: PRs que levam mais tempo para revisão têm mais comentários
    - Hipótese: Discussões mais longas indicam revisão mais rigorosa
    
H4: PRs com mais participantes têm maior chance de serem MERGED
    - Hipótese: Mais olhos = mais feedback construtivo
    
H5: PRs grandes levam mais tempo para serem revisadas
    - Hipótese: Complexidade de revisar código aumenta com o tamanho
    
H6: PRs MERGED têm mais participantes que PRs CLOSED
    - Hipótese: Colaboração ativa leva a integração bem-sucedida
""")
    
    report.append("\n" + "="*80)
    report.append("Próximas etapas (Lab03S02):")
    report.append("- Completar dataset com todas as métricas")
    report.append("- Validar dados coletados")
    report.append("- Primeira análise exploratória")
    report.append("="*80)
    
    # Salvar relatório
    report_path = 'enunciado03/docs/RELATORIO_SPRINT1.txt'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\nRelatório salvo em: {report_path}")
    
    # Exibir relatório
    print('\n'.join(report))


if __name__ == "__main__":
    main()
