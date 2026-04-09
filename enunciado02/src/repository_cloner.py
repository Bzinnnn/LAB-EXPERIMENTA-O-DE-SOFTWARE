import os
import shutil
import stat
import subprocess
import time
from typing import Optional


class RepositoryCloner:
    def __init__(self, base_clone_dir: str = "clones"):
        self.base_clone_dir = base_clone_dir
        os.makedirs(base_clone_dir, exist_ok=True)

    def clone_repository(self, repo_url: str, repo_name: str, max_retries: int = 3) -> Optional[str]:
        clone_path = os.path.join(self.base_clone_dir, repo_name)

        if os.path.exists(clone_path):
            self.cleanup_repository(repo_name)

        for attempt in range(max_retries):
            try:
                print(f"  Clonando {repo_url} (tentativa {attempt + 1}/{max_retries})...")
                cmd = [
                    "git",
                    "-c", "core.longpaths=true",
                    "clone",
                    "--depth", "1",
                    "--single-branch",
                    "--no-tags",
                    repo_url,
                    clone_path,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print(f"  Clone concluido: {clone_path}")
                    return clone_path

                print(f"    [ERRO] Falha no clone: {result.stderr.strip()[:200]}")
                self.cleanup_repository(repo_name)

            except subprocess.TimeoutExpired:
                print(f"    [ERRO] Timeout na tentativa {attempt + 1}")
                self.cleanup_repository(repo_name)
            except Exception as exc:
                print(f"    [ERRO] {exc}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                print(f"    Aguardando {wait_time}s para nova tentativa...")
                time.sleep(wait_time)

        print(f"  [ERRO] Nao foi possivel clonar apos {max_retries} tentativas")
        return None

    def cleanup_repository(self, repo_name: str) -> bool:
        clone_path = os.path.join(self.base_clone_dir, repo_name)
        try:
            if os.path.exists(clone_path):
                def on_rm_error(func, path, exc_info):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception:
                        pass

                for attempt in range(5):
                    try:
                        shutil.rmtree(clone_path, onerror=on_rm_error)
                        return True
                    except Exception as exc:
                        if attempt == 4:
                            print(f"  [ERRO] Falha ao remover repositorio apos 5 tentativas: {exc}")
                        time.sleep(2)
        except Exception as exc:
            print(f"  [ERRO] Falha ao remover repositorio: {exc}")
        return False

    def count_java_files(self, repo_path: str) -> int:
        java_count = 0
        ignore_dirs = {".git", ".github", "node_modules", "__pycache__", "build", "target", ".gradle"}
        try:
            for _, dirnames, filenames in os.walk(repo_path):
                dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
                java_count += sum(1 for f in filenames if f.endswith(".java"))
        except Exception:
            pass
        return java_count

    @staticmethod
    def validate_java_repository(repo_path: str) -> bool:
        for _, dirnames, filenames in os.walk(repo_path):
            if ".git" in dirnames:
                dirnames.remove(".git")
            if any(f.endswith(".java") for f in filenames):
                return True
        return False
