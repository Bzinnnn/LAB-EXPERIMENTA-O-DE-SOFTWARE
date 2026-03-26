#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPRINT 1 - LABORATORIO DE QUALIDADE DE SOFTWARE
Coleta, análise e sumarização de métricas de repositórios Java
"""

import os
import sys
import csv
from dotenv import load_dotenv

# Carregar variáveis de ambiente
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
    """Orchestrador das 5 etapas de Sprint 1"""
    
    def __init__(self):
        # Obter token do GitHub
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            # Usar token demo se não tiver (pode ter rate limit)
            token = "ghp_demo_token_for_testing"
        
        self.github = GitHubGraphQLClient(token)
        self.cloner = RepositoryCloner(CLONES_DIR)
        self.ck_runner = CKRunner()
        self.results = {}
    
    def etapa_1_2_collect_and_enrich(self):
        """ETAPA 1-2: Coletar 1.000 repositórios Java e enriquecer dados"""
        print("\n" + "="*70)
        print("ETAPA 1-2: COLETA E ENRIQUECIMENTO DE REPOSITORIOS")
        print("="*70)
        
        csv_path = os.path.join(DATA_DIR, '2026_spring1_repositorios.csv')
        
        # Se já existe, usar existente
        if os.path.exists(csv_path):
            print(f"\n[+] Arquivo já existe: {csv_path}")
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            print(f"    Repositórios: {lines - 1}")
            return csv_path
        
        # Coletar repositórios com paginação
        print(f"\n[*] Coletando top 1.000 repositórios Java...")
        repositories = []
        after = None
        
        for page in range(10):  # 10 páginas x 100 = 1000
            print(f"  [Página {page + 1}/10]", end=' ', flush=True)
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
            
            print(f"Ok ({len(repositories)} total)")
            
            # Paginação
            if not search_data['pageInfo']['hasNextPage']:
                break
            after = search_data['pageInfo']['endCursor']
        
        print(f"[+] Coletados: {len(repositories)} repositórios")
        
        # Salvar CSV
        print(f"\n[*] Salvando em CSV...")
        if repositories:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=repositories[0].keys())
                writer.writeheader()
                writer.writerows(repositories)
        
        print(f"[+] Arquivo salvo: {csv_path}")
        self.results['coleta'] = {
            'total': len(repositories),
            'arquivo': csv_path
        }
        
        return csv_path
    
    def etapa_3_select_and_clone(self, csv_path):
        """ETAPA 3: Selecionar e clonar repositório piloto"""
        print("\n" + "="*70)
        print("ETAPA 3: SELECAO E CLONE DE REPOSITORIO PILOTO")
        print("="*70)
        
        print(f"\n[*] Procurando repositório com código Java real...")
        print("-" * 60)
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                if i > 20:  # Tentar apenas os 20 primeiros
                    break
                
                repo_name = row['nameWithOwner']
                repo_url = row['url'] + '.git'
                stars = row['stars']
                
                print(f"\n[{i}] Testando: {repo_name} ({stars} stars)")
                
                # Clonar
                clone_path = self.cloner.clone_repository(repo_url, repo_name.replace('/', '_'))
                if not clone_path:
                    print(f"    - Falha ao clonar")
                    continue
                
                # Contar arquivos Java
                java_count = self.cloner.count_java_files(clone_path)
                print(f"    - {java_count} arquivos Java encontrados")
                
                if java_count > 50:  # Precisa ter bastante código
                    print(f"    - OK! Usando este repositório")
                    
                    self.results['clone'] = {
                        'nameWithOwner': repo_name,
                        'url': row['url'],
                        'stars': int(float(stars)),
                        'clone_path': clone_path,
                        'java_files': java_count
                    }
                    
                    return self.results['clone']
                else:
                    print(f"    - Código insuficiente, removendo...")
                    self.cloner.cleanup_repository(repo_name.replace('/', '_'))
        
        return None
    
    def etapa_4_analyze_quality(self, repo_info):
        """ETAPA 4: Analisar qualidade do repositório"""
        print("\n" + "="*70)
        print("ETAPA 4: ANALISE DE QUALIDADE")
        print("="*70)
        
        repo_name = repo_info['nameWithOwner'].replace('/', '_')
        clone_path = repo_info['clone_path']
        
        print(f"\n[*] Repositório: {repo_info['nameWithOwner']}")
        print(f"    Arquivos Java: {repo_info['java_files']}")
        
        # Executar análise
        repo_ck_dir = os.path.join(CK_RESULTS_DIR, repo_name)
        os.makedirs(repo_ck_dir, exist_ok=True)
        
        print(f"\n[*] Etapa 4a: Analisando métricas...")
        output_files = self.ck_runner._create_fallback_report(clone_path, repo_ck_dir)
        
        if not output_files:
            print(f"[!] Falha na análise")
            return False
        
        print(f"[+] Análise concluída")
        
        # Sumarizar
        print(f"\n[*] Etapa 4b: Sumarizando métricas...")
        summary = self.ck_runner.summarize_metrics(output_files)
        
        print(f"[+] Classes processadas: {len(summary['class_metrics'])}")
        
        self.results['analise'] = {
            'classes_analisadas': len(summary['class_metrics']),
            'metricas': summary
        }
        
        # Mostrar estatísticas
        if summary["class_metrics"]:
            print(f"\n[*] Primeiras 5 classes analisadas:")
            for i, metric in enumerate(summary["class_metrics"][:5], 1):
                print(f"    {i}. {metric['class']}: LOC={metric['loc']}, CBO={metric['cbo']}, DIT={metric['dit']}, LCOM={metric['lcom']}")
            
            # Calcular estatísticas
            stats = self.ck_runner.calculate_statistics(summary["class_metrics"], ["cbo", "dit", "lcom", "loc"])
            
            print(f"\n[*] Estatísticas de Qualidade:")
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
        print("ETAPA 5: GERACAO DE RELATORIO FINAL")
        print("="*70)
        
        report_path = os.path.join(BASE_DIR, 'RELATORIO_SPRINT1_FINAL.txt')
        
        print(f"\n[*] Gerando relatório...")
        
        # Criar relatório
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
        
        print(f"[+] Relatório salvo: {report_path}")
        
        return report_path
    
    def run(self):
        """Executar todas as 5 etapas"""
        try:
            print("\n" + "="*70)
            print("INICIANDO SPRINT 1".center(70))
            print("="*70)
            
            # Etapa 1-2
            csv_path = self.etapa_1_2_collect_and_enrich()
            
            # Etapa 3
            repo_info = self.etapa_3_select_and_clone(csv_path)
            if not repo_info:
                print("\n[!] Nenhum repositório com código suficiente encontrado")
                return False
            
            # Etapa 4
            self.etapa_4_analyze_quality(repo_info)
            
            # Etapa 5
            self.etapa_5_generate_report()
            
            print("\n" + "="*70)
            print("SPRINT 1 CONCLUIDA COM SUCESSO!".center(70))
            print("="*70)
            
            print("\nArtefatos gerados:")
            print(f"  [+] {csv_path}")
            print(f"  [+] {repo_info['clone_path']}")
            print(f"  [+] {os.path.join(CK_RESULTS_DIR, repo_info['nameWithOwner'].replace('/', '_'))}/processed_class_metrics.csv")
            print(f"  [+] {os.path.join(BASE_DIR, 'RELATORIO_SPRINT1_FINAL.txt')}")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n[!] Erro: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    lab = Sprint1Lab()
    success = lab.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
