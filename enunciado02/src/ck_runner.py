import csv
import os
import statistics
import subprocess
from typing import Dict, List, Optional


class CKRunner:
    """Executa a ferramenta CK para metricas de qualidade em codigo Java."""

    def __init__(self, ck_jar_path: str = None, auto_download: bool = True):
        self.ck_jar_path = ck_jar_path or self._find_ck_jar()
        self.ck_available = bool(self.ck_jar_path and os.path.exists(self.ck_jar_path))
        if not self.ck_available and auto_download:
            self.ck_available = self.download_ck()

    def _find_ck_jar(self) -> str:
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "ck-0.7.0-jar-with-dependencies.jar"),
            "ck-0.7.0-jar-with-dependencies.jar",
            "ck.jar",
            os.path.join("ck_results", "ck-jar-with-dependencies.jar"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return ""

    def download_ck(self, output_dir: str = ".") -> bool:
        import requests
        urls = [
            "https://repo1.maven.org/maven2/com/github/mauricioaniche/ck/0.7.0/ck-0.7.0-jar-with-dependencies.jar",
        ]
        jar_path = os.path.join(output_dir, "ck-0.7.0-jar-with-dependencies.jar")
        for url in urls:
            print(f"  Baixando CK de {url}...")
            try:
                response = requests.get(url, stream=True, timeout=60)
                response.raise_for_status()
                with open(jar_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.ck_jar_path = os.path.abspath(jar_path)
                self.ck_available = True
                print(f"  CK baixado em: {jar_path}")
                return True
            except Exception as exc:
                print(f"    Falha ao baixar CK: {str(exc)[:120]}")
        return False

    def analyze_repository(self, repo_path: str, output_dir: str) -> Dict[str, str]:
        """Executa CK e produz processed_class_metrics.csv no output_dir."""
        if not os.path.exists(repo_path):
            print(f"[ERRO] Repositorio nao encontrado: {repo_path}")
            return {}

        os.makedirs(output_dir, exist_ok=True)

        # Já tem resultado processado?
        processed_csv = os.path.join(output_dir, "processed_class_metrics.csv")
        if os.path.exists(processed_csv) and os.path.getsize(processed_csv) > 100:
            return {"processed_class_metrics.csv": processed_csv}

        if not self.ck_available:
            self.ck_available = self.download_ck(output_dir)

        if not self.ck_available:
            print("[AVISO] CK nao disponivel. Gerando fallback.")
            return self._create_fallback_report(repo_path, output_dir)

        try:
            # Trailing separator garante que CK grava DENTRO do diretório
            out_dir_arg = output_dir.rstrip("/\\") + "/"
            cmd = ["java", "-jar", self.ck_jar_path, repo_path, "false", "0", "false", out_dir_arg]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                print(f"[ERRO] CK falhou: {result.stderr[:300]}")
                return self._create_fallback_report(repo_path, output_dir)

            # CK gera class.csv dentro de output_dir
            class_csv = os.path.join(output_dir, "class.csv")
            if os.path.exists(class_csv) and os.path.getsize(class_csv) > 100:
                # Renomear para processed_class_metrics.csv com retry
                for attempt in range(5):
                    try:
                        import shutil
                        shutil.move(class_csv, processed_csv)
                        break
                    except Exception:
                        import time
                        time.sleep(1)
                print(f"  CK executado com sucesso: {processed_csv}")
                return {"processed_class_metrics.csv": processed_csv}

            # Fallback: verificar se CK gerou com prefixo (sem trailing slash)
            parent_dir = os.path.dirname(output_dir.rstrip("/\\"))
            base_name = os.path.basename(output_dir.rstrip("/\\"))
            prefixed = os.path.join(parent_dir, f"{base_name}class.csv")
            if os.path.exists(prefixed) and os.path.getsize(prefixed) > 100:
                for attempt in range(5):
                    try:
                        import shutil
                        shutil.move(prefixed, processed_csv)
                        break
                    except Exception:
                        import time
                        time.sleep(1)
                print(f"  CK executado (prefixed): {processed_csv}")
                return {"processed_class_metrics.csv": processed_csv}

            print("[AVISO] CK nao gerou class.csv valido. Gerando fallback.")
            return self._create_fallback_report(repo_path, output_dir)

        except subprocess.TimeoutExpired:
            print("[ERRO] Timeout ao executar CK (600s). Gerando fallback.")
            return self._create_fallback_report(repo_path, output_dir)
        except Exception as exc:
            print(f"[ERRO] Falha ao executar CK: {exc}. Gerando fallback.")
            return self._create_fallback_report(repo_path, output_dir)

    @staticmethod
    def _create_fallback_report(repo_path: str, output_dir: str) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)

        java_files: List[str] = []
        ignore_dirs = {".git", ".github", "node_modules", "build", "target", ".gradle"}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                if f.endswith(".java"):
                    java_files.append(os.path.join(root, f))

        rows: List[Dict] = []
        for java_file in java_files[:500]:
            try:
                with open(java_file, "r", encoding="utf-8", errors="ignore") as fp:
                    lines = fp.readlines()
                loc = len(lines)
                class_name = os.path.basename(java_file).replace(".java", "")
                import_count = sum(1 for l in lines if l.strip().startswith("import "))
                extends = any("extends " in l for l in lines[:50])
                rows.append({
                    "file": java_file.replace(repo_path, ""),
                    "class": class_name,
                    "type": "class",
                    "cbo": max(1, import_count),
                    "dit": 2 if extends else 1,
                    "lcom": round(max(0, (loc - 50) / max(loc, 1)), 2),
                    "loc": loc,
                    "methods": max(1, sum(1 for l in lines if "void " in l or "public " in l or "private " in l) // 2),
                })
            except Exception:
                continue

        csv_path = os.path.join(output_dir, "processed_class_metrics.csv")
        if rows:
            with open(csv_path, "w", newline="", encoding="utf-8") as fp:
                writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            return {"processed_class_metrics.csv": csv_path}
        return {}
