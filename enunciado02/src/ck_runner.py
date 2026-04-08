import os
import subprocess
import shutil
import csv
import statistics
from typing import List, Dict, Tuple
from pathlib import Path

class CKRunner:
    """Executa a ferramenta CK para análise de qualidade de código Java"""
    
    def __init__(self, ck_jar_path: str = None):
        """
        Inicializa o CKRunner.
        ck_jar_path: Caminho para o JAR do CK. Se None, tenta encontrar automaticamente.
        """
        self.ck_jar_path = ck_jar_path or self._find_ck_jar()
        self.ck_available = os.path.exists(self.ck_jar_path) if self.ck_jar_path else False
    
    def _find_ck_jar(self) -> str:
        """Tenta encontrar o CK automaticamente no sistema"""
        possible_paths = [
            "ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar",
            "ck.jar",
            "/opt/ck/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def download_ck(self, output_dir: str = ".") -> bool:
        """
        Baixa a ferramenta CK (versão standalone).
        
        Args:
            output_dir: Diretório onde salvar o CK
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        import requests
        
        # Tenta baixar de múltiplas URLs do CK
        urls = [
            "https://github.com/mauricioaniche/ck/releases/download/v0.7.1/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar",
            "https://github.com/mauricioaniche/ck/releases/download/v0.6.0/ck-0.6.0-SNAPSHOT-jar-with-dependencies.jar",
            "https://github.com/mauricioaniche/ck/releases/download/v0.5.1/ck-0.5.1-SNAPSHOT-jar-with-dependencies.jar"
        ]
        
        jar_path = os.path.join(output_dir, "ck-jar-with-dependencies.jar")
        
        for url in urls:
            print(f"  Baixando CK de {url}...")
            
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(jar_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.ck_jar_path = jar_path
                self.ck_available = True
                print(f"  CK baixado com sucesso em: {jar_path}")
                return True
            
            except Exception as e:
                print(f"    Falha ao baixar: {str(e)[:80]}")
                continue
        
        print(f"  Não foi possível baixar CK de nenhuma das URLs testadas.")
        return False
    
    def analyze_repository(self, repo_path: str, output_dir: str) -> Dict:
        """
        Executa o CK em um repositório Java.
        
        Args:
            repo_path: Caminho para o repositório Clone
            output_dir: Diretório para salvar resultados
        
        Returns:
            Dicionário com os caminhos dos arquivos CSV gerados
        """
        if not self.ck_available:
            print("[AVISO] CK não está disponível. Será criado um relatório simulado.")
            return self._create_fallback_report(repo_path, output_dir)
        
        if not os.path.exists(repo_path):
            print(f"[ERRO] Repositório não encontrado: {repo_path}")
            return {}
        
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"  Executando CK no repositório: {repo_path}")
        
        try:
            cmd = ["java", "-jar", self.ck_jar_path, repo_path, "false", "0", output_dir]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"  [ERRO] CK retornou erro: {result.stderr}")
                return {}
            
            # Localizar arquivos gerados pelo CK
            output_files = {}
            for file in os.listdir(output_dir):
                if file.endswith(".csv"):
                    filepath = os.path.join(output_dir, file)
                    output_files[file] = filepath
            
            print(f"  CK executado com sucesso. Arquivos gerados: {list(output_files.keys())}")
            return output_files
        
        except subprocess.TimeoutExpired:
            print(f"  [ERRO] CK demorou demais e foi interrompido (timeout de 300 segundos)")
            return {}
        except Exception as e:
            print(f"  [ERRO] Falha ao executar CK: {e}")
            return {}
    
    @staticmethod
    def _create_fallback_report(repo_path: str, output_dir: str) -> Dict:
        """
        Cria relatório fallback quando CK não está disponível.
        Escaneia os arquivos Java e cria métricas simuladas.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Escaneia arquivos Java
        java_classes = []
        for root, dirs, files in os.walk(repo_path):
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                if file.endswith('.java'):
                    filepath = os.path.join(root, file)
                    java_classes.append(filepath)
        
        # Cria CSV com métricas simuladas (baseadas em contagem de linhas)
        class_metrics = []
        for java_file in java_classes[:100]:  # Limite a 100 classes para não ficar muito lento
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    loc = len(lines)
                    
                class_name = os.path.basename(java_file).replace('.java', '')
                class_metrics.append({
                    'file': java_file.replace(repo_path, ''),
                    'class': class_name,
                    'type': 'class',
                    'cbo': max(1, loc // 50),  # Simulado
                    'dit': 1 if 'Abstract' in class_name else 2,  # Simulado
                    'lcom': 0.5 if loc > 100 else 0.3,  # Simulado
                    'loc': loc,
                    'methods': max(1, loc // 20)  # Simulado
                })
            except:
                pass
        
        # Salvar CSV processado
        csv_path = os.path.join(output_dir, 'processed_class_metrics.csv')
        if class_metrics:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = list(class_metrics[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(class_metrics)
            print(f"  Relatório simulado criado: {csv_path}")
            print(f"    Total de arquivos Java encontrados: {len(java_classes)}")
            print(f"    Total de classes analisadas (simulado): {len(class_metrics)}")
        
        return {'processed_class_metrics.csv': csv_path}
    
    @staticmethod
    def summarize_metrics(csv_files: Dict) -> Dict:
        """
        Sumariza as métricas extraídas pelo CK.
        
        Args:
            csv_files: Dicionário com caminhos dos CSVs gerados
        
        Returns:
            Dicionário com métricas sumarizadas
        """
        summary = {
            "class_metrics": [],
            "method_metrics": []
        }
        
        # Processar arquivo de classes
        class_csv = csv_files.get("class_metrics.csv")
        if class_csv and os.path.exists(class_csv):
            with open(class_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    summary["class_metrics"].append(row)
        
        # Processar arquivo de métodos
        method_csv = csv_files.get("method_metrics.csv")
        if method_csv and os.path.exists(method_csv):
            with open(method_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    summary["method_metrics"].append(row)
        
        return summary
    
    @staticmethod
    def calculate_statistics(metrics: List[Dict], metric_names: List[str]) -> Dict:
        """
        Calcula estatísticas descritivas para as métricas.
        
        Args:
            metrics: Lista de dicionários com métricas
            metric_names: Nomes das métricas a analisar
        
        Returns:
            Dicionário com estatísticas (média, mediana, desvio padrão, min, max)
        """
        statistics_result = {}
        
        for metric_name in metric_names:
            values = []
            for metric in metrics:
                try:
                    val = float(metric.get(metric_name, 0))
                    values.append(val)
                except (ValueError, TypeError):
                    pass
            
            if values:
                statistics_result[metric_name] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values)
                }
        
        return statistics_result
