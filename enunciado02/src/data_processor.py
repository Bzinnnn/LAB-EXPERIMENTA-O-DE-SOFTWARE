import csv
from datetime import datetime
from typing import Dict, List

from dateutil import parser as date_parser


class RepositoryDataProcessor:
    """Processa e normaliza dados de repositorios do GitHub."""

    @staticmethod
    def calculate_repository_age(created_at: str) -> int:
        created_date = date_parser.parse(created_at)
        now = datetime.utcnow().replace(tzinfo=None)
        return (now - created_date.replace(tzinfo=None)).days

    @staticmethod
    def calculate_days_since_update(updated_at: str) -> int:
        update_date = date_parser.parse(updated_at)
        now = datetime.utcnow().replace(tzinfo=None)
        return (now - update_date.replace(tzinfo=None)).days

    @staticmethod
    def calculate_closed_issues_ratio(open_issues: int, closed_issues: int) -> float:
        total = open_issues + closed_issues
        if total == 0:
            return 0.0
        return closed_issues / total

    @staticmethod
    def normalize_repository_data(repo_node: Dict) -> Dict:
        node = repo_node.get("node", {})
        open_issues = node.get("openIssues", {}).get("totalCount", 0)
        closed_issues = node.get("closedIssues", {}).get("totalCount", 0)
        watchers = node.get("watchers", {}).get("totalCount", 0)
        primary_language = node.get("primaryLanguage")
        language_name = primary_language.get("name") if primary_language else "Unknown"

        name_with_owner = node.get("nameWithOwner", "")
        owner, name = (name_with_owner.split("/", 1) + [""])[:2] if "/" in name_with_owner else ("", "")

        return {
            "id": node.get("id", ""),
            "name": name,
            "nameWithOwner": name_with_owner,
            "owner": owner,
            "url": node.get("url", ""),
            "description": node.get("description", ""),
            "primaryLanguage": language_name,
            "stars": node.get("stargazerCount", 0),
            "forks": node.get("forkCount", 0),
            "createdAt": node.get("createdAt", ""),
            "updatedAt": node.get("updatedAt", ""),
            "pushedAt": node.get("pushedAt", ""),
            "repositoryAge": RepositoryDataProcessor.calculate_repository_age(node.get("createdAt", "")),
            "daysSinceUpdate": RepositoryDataProcessor.calculate_days_since_update(node.get("updatedAt", "")),
            "mergedPullRequests": node.get("mergedPullRequests", {}).get("totalCount", 0),
            "releases": node.get("releases", {}).get("totalCount", 0),
            "openIssues": open_issues,
            "closedIssues": closed_issues,
            "totalIssues": open_issues + closed_issues,
            "closedIssuesRatio": RepositoryDataProcessor.calculate_closed_issues_ratio(open_issues, closed_issues),
            "watchers": watchers,
        }

    @staticmethod
    def save_to_csv(repositories: List[Dict], filename: str) -> None:
        if not repositories:
            print("Nenhum repositorio para salvar")
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
            "url",
        ]

        with open(filename, "w", newline="", encoding="utf-8") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
            writer.writeheader()
            for repo in repositories:
                writer.writerow({field: repo.get(field, "") for field in fieldnames})

        print(f"{len(repositories)} repositorios salvos em '{filename}'")
