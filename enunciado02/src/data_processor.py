import csv
from datetime import datetime
from typing import List, Dict, Tuple
from dateutil import parser as date_parser

class RepositoryDataProcessor:

    @staticmethod
    def calculate_repository_age(created_at: str) -> int:
        created_date = date_parser.parse(created_at)
        now = datetime.utcnow().replace(tzinfo=None)
        age = (now - created_date.replace(tzinfo=None)).days
        return age
    
    @staticmethod
    def calculate_days_since_update(updated_at: str) -> int:
        update_date = date_parser.parse(updated_at)
        now = datetime.utcnow().replace(tzinfo=None)
        days = (now - update_date.replace(tzinfo=None)).days
        return days
    
    @staticmethod
    def calculate_closed_issues_ratio(open_issues: int, closed_issues: int) -> float:
        total = open_issues + closed_issues
        if total == 0:
            return 0.0
        return closed_issues / total
    
    @staticmethod
    def normalize_repository_data(repo_node: Dict) -> Dict:
        node = repo_node.get("node", {})
        open_issues = node.get("issues", {}).get("totalCount", 0)
        closed_issues = node.get("closedIssues", {}).get("totalCount", 0)
        primary_language = node.get("primaryLanguage")
        language_name = primary_language.get("name") if primary_language else "Unknown"
        return {
            "id": node.get("id", ""),
            "name": node.get("nameWithOwner", "").split("/")[1] if "/" in node.get("nameWithOwner", "") else "",
            "nameWithOwner": node.get("nameWithOwner", ""),
            "owner": node.get("nameWithOwner", "").split("/")[0] if "/" in node.get("nameWithOwner", "") else "",
            "url": node.get("url", ""),
            "description": node.get("description", ""),
            "primaryLanguage": language_name,
            "stars": node.get("stargazerCount", 0),
            "forks": node.get("forkCount", 0),
            "createdAt": node.get("createdAt", ""),
            "updatedAt": node.get("updatedAt", ""),
            "pushedAt": node.get("pushedAt", ""),
            "repositoryAge": RepositoryDataProcessor.calculate_repository_age(
                node.get("createdAt", "")
            ),
            "daysSinceUpdate": RepositoryDataProcessor.calculate_days_since_update(
                node.get("updatedAt", "")
            ),
            "mergedPullRequests": node.get("pullRequests", {}).get("totalCount", 0),
            "releases": node.get("releases", {}).get("totalCount", 0),
            "openIssues": open_issues,
            "closedIssues": closed_issues,
            "totalIssues": open_issues + closed_issues,
            "closedIssuesRatio": RepositoryDataProcessor.calculate_closed_issues_ratio(
                open_issues, closed_issues
            ),
            "watchers": 0
        }
    
    @staticmethod
    def save_to_csv(repositories: List[Dict], filename: str):
        if not repositories:
            print("Nenhum repositório para salvar")
            return
        
        fieldnames = [
            "nameWithOwner",
            "owner",
            "description",
            "primaryLanguage",
            "stars",
            "forks",
            "createdAt",
            "updatedAt",
            "repositoryAge",
            "daysSinceUpdate",
            "mergedPullRequests",
            "releases",
            "openIssues",
            "closedIssues",
            "totalIssues",
            "closedIssuesRatio",
            "watchers",
            "url"
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for repo in repositories:
                writer.writerow({field: repo.get(field, "") for field in fieldnames})
        
        print(f"✓ {len(repositories)} repositórios salvos em '{filename}'")
