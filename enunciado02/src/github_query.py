import requests
import json
import time
from typing import Optional, Dict, List
from urllib.parse import quote

class GitHubGraphQLClient:

    def __init__(self, token: str):
        self.token = token
        self.url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.rate_limit = {
            "remaining": 5000,
            "reset": 0,
            "limit": 5000
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._query_cache = {}
    
    def _update_rate_limit(self, response: requests.Response):
        """Extrai informações de rate limit dos headers da resposta."""
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit["remaining"] = int(response.headers["X-RateLimit-Remaining"])
            self.rate_limit["reset"] = int(response.headers["X-RateLimit-Reset"])
            self.rate_limit["limit"] = int(response.headers.get("X-RateLimit-Limit", 5000))
    
    def _wait_if_needed(self):
        """Aguarda se o rate limit da API está baixo para evitar bloqueio."""
        if self.rate_limit["remaining"] <= 5:
            wait_time = max(0, self.rate_limit["reset"] - int(time.time()))
            if wait_time > 0:
                print(f"  [AVISO] Rate limit crítico ({self.rate_limit['remaining']}/{self.rate_limit['limit']}). Aguardando {wait_time}s para continuar...")
                time.sleep(wait_time + 1)
    
    def execute_query(self, query: str, variables: Optional[Dict] = None, retry: int = 3) -> Dict:
        """
        Executa query GraphQL com retry automático e backoff exponencial.
        
        Args:
            query: Query GraphQL
            variables: Variáveis da query
            retry: Número de tentativas (padrão: 3)
        
        Returns:
            Resposta JSON da API
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        # Cachear resultado se for query idêntica
        cache_key = json.dumps(payload, sort_keys=True)
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]
        
        self._wait_if_needed()
        
        for attempt in range(retry):
            try:
                response = self.session.post(
                    self.url,
                    json=payload,
                    timeout=60
                )
                
                self._update_rate_limit(response)
                
                if response.status_code == 200:
                    data = response.json()
                    if "errors" not in data:
                        self._query_cache[cache_key] = data
                    return data
                    
                elif response.status_code in [500, 502, 503]:
                    if attempt < retry - 1:
                        wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                        print(f"  [AVISO] Erro {response.status_code}. Tentativa {attempt + 1}/{retry}. Aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Erro {response.status_code} após {retry} tentativas: {response.text[:200]}")
                        
                elif response.status_code == 401:
                    raise Exception("Token inválido ou expirado")
                    
                else:
                    raise Exception(f"Status {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                if attempt < retry - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"  [AVISO] Timeout. Tentativa {attempt + 1}/{retry}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception("Timeout após múltiplas tentativas")
                    
            except requests.exceptions.RequestException as e:
                if attempt < retry - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                else:
                    raise Exception(f"Erro de conexão: {str(e)}")
        
        raise Exception("Query falhou após múltiplas tentativas")
    
    def get_top_repositories(self, first: int = 100, after: Optional[str] = None, language: str = "Java") -> Dict:
        """
        Busca repositórios mais populares, filtrados por linguagem.
        Otimizado para reduzir custo de query.
        
        Args:
            first: Número de repositórios a retornar
            after: Cursor para paginação
            language: Linguagem de programação (padrão: Java)
        """
        query = """
        query GetTopRepositories($first: Int!, $after: String) {
            search(query: "language:Java stars:>1 sort:stars-desc", 
                   type: REPOSITORY, first: $first, after: $after) {
                pageInfo {{
                    endCursor
                    hasNextPage
                }}
                edges {{
                    node {{
                        ... on Repository {{
                            nameWithOwner
                            description
                            url
                            primaryLanguage {{
                                name
                            }}
                            stargazerCount
                            forkCount
                            watchers: watchers {{
                                totalCount
                            }}
                            createdAt
                            updatedAt
                            openIssues: issues(states: OPEN) {{
                                totalCount
                            }}
                            closedIssues: issues(states: CLOSED) {{
                                totalCount
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """

        variables = {"first": first, "after": after}
        result = self.execute_query(query, variables)

        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors'][0]['message']}")

        return result

    def get_repo_details(self, owner: str, name: str) -> Dict:
        """
        Busca informações detalhadas de um repositório.
        Otimizado para uma única query eficiente.
        """
        query = """
        query GetRepoDetails($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                mergedPRs: pullRequests(states: MERGED) {
                    totalCount
                }
                releases {
                    totalCount
                }
            }
        }
        """
        variables = {"owner": owner, "name": name}
        result = self.execute_query(query, variables)

        if "errors" in result:
            return {"mergedPRs": {"totalCount": 0}, "releases": {"totalCount": 0}}

        return result.get("data", {}).get("repository", {})
    
    def check_rate_limit(self) -> Dict:
        """Verifica rate limit atual."""
        query = """
        query {
            rateLimit {
                limit
                cost
                remaining
                resetAt
            }
        }
        """
        
        result = self.execute_query(query)
        return result.get("data", {})
    
    def get_rate_limit_status(self) -> str:
        """Retorna status legível do rate limit."""
        percentage = (self.rate_limit["remaining"] / self.rate_limit["limit"] * 100) if self.rate_limit["limit"] > 0 else 0
        return f"{self.rate_limit['remaining']}/{self.rate_limit['limit']} ({percentage:.1f}%)"
