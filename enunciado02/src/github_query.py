import json
import random
import time
from typing import Dict, List, Optional

import requests


class GitHubGraphQLClient:
    """Cliente para consultas REST e GraphQL do GitHub com retry e controle de rate limit."""

    def __init__(self, token: str):
        self.token = token
        self.url = "https://api.github.com/graphql"
        self.rest_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.rate_limit = {"remaining": 5000, "reset": 0, "limit": 5000}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._query_cache: Dict[str, Dict] = {}

    # ── Rate limit ───────────────────────────────────────────────────────
    def _update_rate_limit(self, response: requests.Response) -> None:
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit["remaining"] = int(response.headers["X-RateLimit-Remaining"])
            self.rate_limit["reset"] = int(response.headers["X-RateLimit-Reset"])
            self.rate_limit["limit"] = int(response.headers.get("X-RateLimit-Limit", 5000))

    def _wait_if_needed(self) -> None:
        if self.rate_limit["remaining"] <= 5:
            wait_time = max(0, self.rate_limit["reset"] - int(time.time()))
            if wait_time > 0:
                print(
                    f"  [AVISO] Rate limit baixo "
                    f"({self.rate_limit['remaining']}/{self.rate_limit['limit']}). "
                    f"Aguardando {wait_time}s..."
                )
                time.sleep(wait_time + 1)

    # ── REST helper ──────────────────────────────────────────────────────
    def _rest_get(self, endpoint: str, params: Optional[Dict] = None, retry: int = 6) -> Dict:
        self._wait_if_needed()

        for attempt in range(retry):
            try:
                response = self.session.get(f"{self.rest_url}{endpoint}", params=params, timeout=60)
                self._update_rate_limit(response)

                if response.status_code == 200:
                    return response.json()

                if response.status_code in [500, 502, 503, 504] and attempt < retry - 1:
                    wait_time = min(60, (2 ** attempt) * 2) + random.uniform(0, 1.5)
                    print(f"  [AVISO] REST erro {response.status_code}. Tentativa {attempt + 1}/{retry}. Aguardando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue

                if response.status_code == 401:
                    raise RuntimeError("Token invalido ou expirado")
                if response.status_code == 403:
                    wait_time = max(0, self.rate_limit["reset"] - int(time.time())) + 2
                    if wait_time > 0 and attempt < retry - 1:
                        print(f"  [AVISO] Rate limit atingido. Aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise RuntimeError(f"Rate limit esgotado: {response.text[:200]}")

                raise RuntimeError(f"REST status {response.status_code}: {response.text[:200]}")

            except requests.exceptions.Timeout:
                if attempt < retry - 1:
                    wait_time = min(60, (2 ** attempt) * 2) + random.uniform(0, 1.5)
                    print(f"  [AVISO] REST timeout. Tentativa {attempt + 1}/{retry}. Aguardando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                raise RuntimeError("REST timeout apos multiplas tentativas")

            except requests.exceptions.RequestException as exc:
                if attempt < retry - 1:
                    wait_time = min(60, (2 ** attempt) * 2) + random.uniform(0, 1.5)
                    print(f"  [AVISO] REST conexao falhou. Tentativa {attempt + 1}/{retry}. Aguardando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                raise RuntimeError(f"Erro de conexao REST: {exc}")

        raise RuntimeError("REST falhou apos multiplas tentativas")

    # ── Search repositories ──────────────────────────────────────────────
    def get_top_repositories_rest(self, per_page: int = 100, page: int = 1, language: str = "Java") -> List[Dict]:
        params = {
            "q": f"language:{language} stars:>1",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page,
        }
        payload = self._rest_get("/search/repositories", params=params)
        return payload.get("items", [])

    # ── Releases count via REST (single repo) ────────────────────────────
    def get_releases_count(self, owner: str, repo: str) -> int:
        """Conta releases via REST API paginada (HEAD para ver total)."""
        try:
            response = self.session.get(
                f"{self.rest_url}/repos/{owner}/{repo}/releases",
                params={"per_page": 1},
                timeout=30,
            )
            self._update_rate_limit(response)
            if response.status_code != 200:
                return 0
            # Check Link header for last page
            link = response.headers.get("Link", "")
            if 'rel="last"' in link:
                import re
                match = re.search(r'page=(\d+)>; rel="last"', link)
                if match:
                    return int(match.group(1))
            # No pagination = count items directly
            data = response.json()
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    # ── Releases count via GraphQL (batch) ───────────────────────────────
    def get_releases_batch_graphql(self, repos: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Busca contagem de releases para múltiplos repos via GraphQL.
        repos: list of {"owner": "...", "name": "..."} dicts.
        Returns: {"owner/name": count, ...}
        """
        results: Dict[str, int] = {}
        batch_size = 40  # Safe batch size for GraphQL

        for i in range(0, len(repos), batch_size):
            batch = repos[i : i + batch_size]
            parts = []
            for idx, repo in enumerate(batch):
                owner = repo["owner"].replace("-", "_").replace(".", "_")
                name = repo["name"].replace("-", "_").replace(".", "_")
                alias = f"r{idx}_{owner[:10]}_{name[:10]}"
                # Ensure alias starts with letter and is valid GraphQL
                alias = "r" + alias.replace("__", "_")
                parts.append(
                    f'  {alias}: repository(owner: "{repo["owner"]}", name: "{repo["name"]}") '
                    f"{{ releases {{ totalCount }} }}"
                )

            query = "{\n" + "\n".join(parts) + "\n}"

            try:
                data = self.execute_query(query)
                if data and "data" in data:
                    for idx, repo in enumerate(batch):
                        owner = repo["owner"].replace("-", "_").replace(".", "_")
                        name = repo["name"].replace("-", "_").replace(".", "_")
                        alias = f"r{idx}_{owner[:10]}_{name[:10]}"
                        alias = "r" + alias.replace("__", "_")
                        repo_data = data["data"].get(alias)
                        if repo_data:
                            count = repo_data.get("releases", {}).get("totalCount", 0)
                            full_name = f"{repo['owner']}/{repo['name']}"
                            results[full_name] = count
            except Exception as exc:
                print(f"  [AVISO] GraphQL batch falhou (batch {i // batch_size + 1}): {exc}")
                # Fallback: try individual REST calls for this batch
                for repo in batch:
                    full_name = f"{repo['owner']}/{repo['name']}"
                    if full_name not in results:
                        count = self.get_releases_count(repo["owner"], repo["name"])
                        results[full_name] = count

            if i + batch_size < len(repos):
                time.sleep(0.5)  # Small delay between batches

        return results

    # ── GraphQL helper ───────────────────────────────────────────────────
    def execute_query(self, query: str, variables: Optional[Dict] = None, retry: int = 6) -> Dict:
        payload = {"query": query, "variables": variables or {}}
        cache_key = json.dumps(payload, sort_keys=True)
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        self._wait_if_needed()

        for attempt in range(retry):
            try:
                response = self.session.post(self.url, json=payload, timeout=60)
                self._update_rate_limit(response)

                if response.status_code == 200:
                    data = response.json()
                    if "errors" not in data:
                        self._query_cache[cache_key] = data
                    return data

                if response.status_code in [500, 502, 503, 504] and attempt < retry - 1:
                    wait_time = min(60, (2 ** attempt) * 2) + random.uniform(0, 1.5)
                    print(f"  [AVISO] GraphQL erro {response.status_code}. Tentativa {attempt + 1}/{retry}. Aguardando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue

                if response.status_code == 401:
                    raise RuntimeError("Token invalido ou expirado")

                raise RuntimeError(f"GraphQL status {response.status_code}: {response.text[:200]}")

            except requests.exceptions.Timeout:
                if attempt < retry - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"  [AVISO] GraphQL timeout. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise RuntimeError("GraphQL timeout apos multiplas tentativas")

            except requests.exceptions.RequestException as exc:
                if attempt < retry - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                raise RuntimeError(f"Erro de conexao GraphQL: {exc}")

        raise RuntimeError("GraphQL falhou apos multiplas tentativas")
