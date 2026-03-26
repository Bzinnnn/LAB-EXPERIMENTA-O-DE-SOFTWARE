import os
import subprocess
import shutil
import time
from typing import Dict, List, Optional
from pathlib import Path

class RepositoryCloner:
    """Gerencia clonagem e análise de repositórios"""
    
    def __init__(self, base_clone_dir: str = "clones"):
        self.base_clone_dir = base_clone_dir
        os.makedirs(base_clone_dir, exist_ok=True)
    
    def clone_repository(self, repo_url: str, repo_name: str, max_retries: int = 3) -> Optional[str]:
        """
        Clona um repositório do GitHub.
        
        Args:
            repo_url: URL do repositório (https://github.com/owner/repo)
            repo_name: Nome para o diretório local
            max_retries: Número máximo de tentativas
        
        Returns:
            Caminho completo do repositório clonado ou None se falhar
        """
        clone_path = os.path.join(self.base_clone_dir, repo_name)
        
        # Se já existe, pular
        if os.path.exists(clone_path):
            print(f"  ✓ Repositório já clonado: {clone_path}")
            return clone_path
        
        for attempt in range(max_retries):
            try:
                print(f"  Clonando: {repo_url} (tentativa {attempt + 1}/{max_retries})...")
                
                cmd = ["git", "clone", "--depth", "1", repo_url, clone_path]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    print(f"  ✓ Clonado com sucesso: {clone_path}")
                    return clone_path
                else:
                    print(f"    Erro: {result.stderr.strip()}")
            
            except subprocess.TimeoutExpired:
                print(f"    Timeout na tentativa {attempt + 1}")
            except Exception as e:
                print(f"    Erro: {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"    Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)
        
        print(f"  ✗ Falha ao clonar após {max_retries} tentativas")
        return None
    
    def cleanup_repository(self, repo_name: str) -> bool:
        """
        Remove um repositório clonado para liberar espaço.
        
        Args:
            repo_name: Nome do diretório do repositório
        
        Returns:
            True se removido com sucesso
        """
        clone_path = os.path.join(self.base_clone_dir, repo_name)
        
        try:
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
                print(f"  ✓ Repositório removido: {clone_path}")
                return True
        except Exception as e:
            print(f"  ✗ Erro ao remover repositório: {e}")
        
        return False
    
    def get_repository_size_mb(self, repo_path: str) -> float:
        """
        Calcula o tamanho total do repositório em MB.
        
        Args:
            repo_path: Caminho do repositório
        
        Returns:
            Tamanho em MB
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(repo_path):
                # Ignorar pasta .git
                if '.git' in dirnames:
                    dirnames.remove('.git')
                
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            print(f"  Erro ao calcular tamanho: {e}")
        
        return total_size / (1024 * 1024)
    
    def count_java_files(self, repo_path: str) -> int:
        """
        Conta o número de arquivos Java no repositório.
        
        Args:
            repo_path: Caminho do repositório
        
        Returns:
            Número de arquivos .java
        """
        java_count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(repo_path):
                # Ignorar pastas comuns não relevantes
                ignore_dirs = {'.git', '.github', 'node_modules', '__pycache__'}
                dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
                
                java_count += sum(1 for f in filenames if f.endswith('.java'))
        except Exception as e:
            print(f"  Erro ao contar arquivos Java: {e}")
        
        return java_count
    
    @staticmethod
    def validate_java_repository(repo_path: str) -> bool:
        """
        Valida se um repositório contém código Java.
        
        Args:
            repo_path: Caminho do repositório
        
        Returns:
            True se contém arquivos Java
        """
        java_found = False
        for dirpath, dirnames, filenames in os.walk(repo_path):
            if '.git' in dirnames:
                dirnames.remove('.git')
            for filename in filenames:
                if filename.endswith('.java'):
                    java_found = True
                    break
            if java_found:
                break
        
        return java_found
