

import os
import sys
import csv
from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from github_query import GitHubGraphQLClient
from repository_cloner import RepositoryCloner
from ck_runner import CKRunner

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CLONES_DIR = os.path.join(BASE_DIR, 'clones')
CK_RESULTS_DIR = os.path.join(BASE_DIR, 'ck_results')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CLONES_DIR, exist_ok=True)
os.makedirs(CK_RESULTS_DIR, exist_ok=True)


class Sprint1Lab:
    """Classe principal para orquestrar as etapas da Sprint 1"""
    
    def __init__(self):
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            token = "ghp_demo_token_for_testing"
        
        self.github = GitHubGraphQLClient(token)
        self.cloner = RepositoryCloner(CLONES_DIR)
        self.ck_runner = CKRunner()
        self.results = {}
    
    def etapa_1_2_collect_and_enrich(self):
        """Etapa 1-2: Coleta e enriquecimento dos repositórios Java"""
        print("\n" + "="*70)
        print("Iniciando coleta e enriquecimento dos repositórios Java")
        print("="*70)
        
        csv_path = os.path.join(DATA_DIR, '2026_spring1_repositorios.csv')
        
        if os.path.exists(csv_path):
            print(f"\n[INFO] Arquivo já existe: {csv_path}")
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            print(f"Total de repositórios já coletados: {lines - 1}")
            return csv_path
        
        print(f"\nBuscando os 1.000 repositórios Java mais populares...")
        repositories = []
        after = None
        
        for page in range(10):
            print(f"  Página {page + 1}/10", end=' ', flush=True)
            result = self.github.get_top_repositories(first=100, after=after, language="Java")
            
            if not result or 'data' not in result:
                print("Erro!")
                break
            
            search_data = result['data'].get('search', {})
            edges = search_data.get('edges', [])
            
            for edge in edges:
                repo = edge['node']
                repositories.append({
                    'nameWithOwner': repo['nameWithOwner'],
                    'owner': repo['nameWithOwner'].split('/')[0],
                    'url': repo['url'],
                    'description': repo.get('description', ''),
                    'primaryLanguage': repo.get('primaryLanguage', {}).get('name', 'Java') if repo.get('primaryLanguage') else 'Java',
                    'stars': str(repo['stargazerCount']),
                    'forks': str(repo['forkCount']),
                    'createdAt': repo['createdAt'],
                    'updatedAt': repo['updatedAt'],
                    'openIssues': str(repo['openIssues']['totalCount']),
                    'closedIssues': str(repo['closedIssues']['totalCount']),
                })
            
            print(f" - Página processada. Total até agora: {len(repositories)} repositórios.")
            
            # Paginação
            if not search_data['pageInfo']['hasNextPage']:
                break
            after = search_data['pageInfo']['endCursor']
        
        print(f"Coleta finalizada. Total de repositórios coletados: {len(repositories)}")
        
        # Salvar CSV
        print(f"\nSalvando os dados em CSV...")
        if repositories:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=repositories[0].keys())
                writer.writeheader()
                writer.writerows(repositories)
        
        print(f"Arquivo salvo em: {csv_path}")
        self.results['coleta'] = {
            'total': len(repositories),
            'arquivo': csv_path
        }
        
        return csv_path
    
    def etapa_3_select_and_clone(self, csv_path):
        """ETAPA 3: Selecionar e clonar repositório piloto"""
        print("\n" + "="*70)
        print("Etapa 3: Seleção e clone do repositório piloto")
        print("="*70)
        print(f"\nBuscando um repositório com código Java real...")
        print("-" * 60)
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                if i > 20:  # Tentar apenas os 20 primeiros
                    break
                
                repo_name = row['nameWithOwner']
                repo_url = row['url'] + '.git'
                stars = row['stars']
                
                print(f"\n[{i}] Testando repositório: {repo_name} ({stars} estrelas)")
                
                # Clonar
                clone_path = self.cloner.clone_repository(repo_url, repo_name.replace('/', '_'))
                if not clone_path:
                    print(f"    Não foi possível clonar este repositório.")
                    continue
                
                # Contar arquivos Java
                java_count = self.cloner.count_java_files(clone_path)
                print(f"    Foram encontrados {java_count} arquivos Java neste repositório.")
                
                if java_count > 50:  # Precisa ter bastante código
                    print(f"    Repositório selecionado para análise.")
                    
                    self.results['clone'] = {
                        'nameWithOwner': repo_name,
                        'url': row['url'],
                        'stars': int(float(stars)),
                        'clone_path': clone_path,
                        'java_files': java_count
                    }
                    
                    return self.results['clone']
                else:
                    print(f"    Pouco código Java, repositório será removido.")
                    self.cloner.cleanup_repository(repo_name.replace('/', '_'))
        
        return None
    
    def etapa_4_analyze_quality(self, repo_info):
        """ETAPA 4: Analisar qualidade do repositório"""
        print("\n" + "="*70)
        print("Etapa 4: Análise de qualidade do repositório")
        print("="*70)
        repo_name = repo_info['nameWithOwner'].replace('/', '_')
        clone_path = repo_info['clone_path']
        print(f"\nRepositório selecionado: {repo_info['nameWithOwner']}")
        print(f"Quantidade de arquivos Java: {repo_info['java_files']}")
        repo_ck_dir = os.path.join(CK_RESULTS_DIR, repo_name)
        os.makedirs(repo_ck_dir, exist_ok=True)
        
        print(f"\nIniciando análise das métricas de qualidade...")
        output_files = self.ck_runner._create_fallback_report(clone_path, repo_ck_dir)
        
        if not output_files:
            print(f"[ERRO] Não foi possível realizar a análise de qualidade.")
            return False
        
        print(f"Análise concluída com sucesso.")
        
        # Sumarizar
        print(f"\nSumarizando as métricas extraídas...")
        summary = self.ck_runner.summarize_metrics(output_files)
        
        print(f"Total de classes processadas: {len(summary['class_metrics'])}")
        
        self.results['analise'] = {
            'classes_analisadas': len(summary['class_metrics']),
            'metricas': summary
        }
        
        # Mostrar estatísticas
        if summary["class_metrics"]:
            print(f"\nExemplo das primeiras 5 classes analisadas:")
            for i, metric in enumerate(summary["class_metrics"][:5], 1):
                print(f"    {i}. {metric['class']}: LOC={metric['loc']}, CBO={metric['cbo']}, DIT={metric['dit']}, LCOM={metric['lcom']}")
            stats = self.ck_runner.calculate_statistics(summary["class_metrics"], ["cbo", "dit", "lcom", "loc"])
            print(f"\nResumo estatístico das métricas de qualidade:")
            print("-" * 70)
            for metric_name, values in stats.items():
                print(f"\n{metric_name.upper()}:")
                print(f"  Média:         {values['mean']:.2f}")
                print(f"  Mediana:       {values['median']:.2f}")
                print(f"  Desvio Padrão: {values['stdev']:.2f}")
                print(f"  Min/Max:       {values['min']:.0f} / {values['max']:.0f}")
            self.results['estatisticas'] = stats
        
        return repo_ck_dir
    
    def etapa_5_generate_report(self):
        """ETAPA 5: Gerar relatório final"""
        print("\n" + "="*70)
        print("Etapa 5: Geração do relatório final")
        print("="*70)
        report_path = os.path.join(BASE_DIR, 'RELATORIO_SPRINT1_FINAL.txt')
        print(f"\nGerando relatório final da Sprint 1...")
        content = []
        content.append("=" * 80)
        content.append("SPRINT 1 - LABORATORIO DE QUALIDADE DE SOFTWARE")
        content.append("=" * 80)
        
        # Etapa 1-2
        content.append("\n1. COLETA DE REPOSITORIOS")
        content.append("-" * 80)
        if 'coleta' in self.results:
            content.append(f"Total coletado: {self.results['coleta']['total']}")
            content.append(f"Arquivo: {self.results['coleta']['arquivo']}")
        
        # Etapa 3
        content.append("\n2. REPOSITORIO PILOTO")
        content.append("-" * 80)
        if 'clone' in self.results:
            clone = self.results['clone']
            content.append(f"Nome: {clone['nameWithOwner']}")
            content.append(f"Stars: {clone['stars']}")
            content.append(f"Arquivos Java: {clone['java_files']}")
            content.append(f"Localização: {clone['clone_path']}")
        
        # Etapa 4
        content.append("\n3. METRICAS DE QUALIDADE")
        content.append("-" * 80)
        if 'analise' in self.results:
            analise = self.results['analise']
            content.append(f"Classes analisadas: {analise['classes_analisadas']}")
        
        if 'estatisticas' in self.results:
            stats = self.results['estatisticas']
            for metric_name, values in stats.items():
                content.append(f"\n{metric_name.upper()}:")
                content.append(f"  Média:        {values['mean']:.2f}")
                content.append(f"  Mediana:      {values['median']:.2f}")
                content.append(f"  Desvio Padrão: {values['stdev']:.2f}")
                content.append(f"  Min/Max:      {values['min']:.0f} / {values['max']:.0f}")
        
        content.append("\n" + "=" * 80)
        content.append("FIM DO RELATORIO")
        content.append("=" * 80)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
        
        print(f"Relatório salvo em: {report_path}")
        
        return report_path
    
    def run(self):
        """Executar todas as 5 etapas"""
        try:
            print("\n" + "="*70)
            print("INICIANDO SPRINT 1".center(70))
            print("="*70)
            csv_path = self.etapa_1_2_collect_and_enrich()
            repo_info = self.etapa_3_select_and_clone(csv_path)
            if not repo_info:
                print("\n[ERRO] Nenhum repositório com código suficiente foi encontrado para análise.")
                return False
            self.etapa_4_analyze_quality(repo_info)
            self.etapa_5_generate_report()
            print("\n" + "="*70)
            print("SPRINT 1 FINALIZADA COM SUCESSO!".center(70))
            print("="*70)
            print("\nArquivos gerados nesta execução:")
            print(f"  - {csv_path}")
            print(f"  - {repo_info['clone_path']}")
            print(f"  - {os.path.join(CK_RESULTS_DIR, repo_info['nameWithOwner'].replace('/', '_'))}/processed_class_metrics.csv")
            print(f"  - {os.path.join(BASE_DIR, 'RELATORIO_SPRINT1_FINAL.txt')}")
            print()
            return True
        except Exception as e:
            print(f"\n[ERRO] Ocorreu um problema: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    lab = Sprint1Lab()
    success = lab.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
