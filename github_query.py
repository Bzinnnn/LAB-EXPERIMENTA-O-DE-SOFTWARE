import requests
import json
import time
from typing import Optional, Dict, List

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
            "reset": 0
        }
    
    def execute_query(self, query: str, variables: Optional[Dict] = None, retry: int = 3) -> Dict:
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        for attempt in range(retry):
            try:
                response = requests.post(
                    self.url,
                    json=payload,
                    headers=self.headers,
                    timeout=60
                )
                
                # Atualizar informações de rate limit
                if "X-RateLimit-Remaining" in response.headers:
                    self.rate_limit["remaining"] = int(response.headers["X-RateLimit-Remaining"])
                    self.rate_limit["reset"] = int(response.headers["X-RateLimit-Reset"])
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 502:
                    if attempt < retry - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"  ⚠ Erro 502 do servidor GitHub. Aguardando {wait_time}s antes de tentar novamente...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Query failed with status {response.status_code}: {response.text}")
                else:
                    raise Exception(f"Query failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                if attempt < retry - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"  ⚠ Timeout. Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    raise Exception("Query timeout após múltiplas tentativas")
        
        raise Exception("Query failed após múltiplas tentativas")
    
    def get_top_repositories(self, first: int = 100, after: Optional[str] = None) -> Dict:
        query = """
        query GetTopRepositories($first: Int!, $after: String) {
            search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $first, after: $after) {
                pageInfo {
                    endCursor
                    hasNextPage
                }
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            description
                            url
                            primaryLanguage {
                                name
                            }
                            stargazerCount
                            forkCount
                            createdAt
                            updatedAt
                            issues(states: OPEN) {
                                totalCount
                            }
                            closedIssues: issues(states: CLOSED) {
                                totalCount
                            }
                            pullRequests(states: MERGED) {
                                totalCount
                            }
                            releases {
                                totalCount
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "first": first,
            "after": after
        }
        
        result = self.execute_query(query, variables)
        
        if "errors" in result:
            raise Exception(f"GraphQL Error: {result['errors']}")
        
        return result
    
    def check_rate_limit(self) -> Dict:
        query = """
        query {
            viewer {
                login
            }
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
    
    def wait_if_rate_limited(self):
        if self.rate_limit["remaining"] <= 10:
            wait_time = self.rate_limit["reset"] - int(time.time())
            if wait_time > 0:
                print(f"Rate limit atingido. Aguardando {wait_time} segundos...")
                time.sleep(wait_time + 1)
