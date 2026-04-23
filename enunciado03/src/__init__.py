"""
Enunciado 3 - Caracterizando a atividade de code review no GitHub
Package initialization
"""

__version__ = "0.1.0"
__author__ = "Lab Engenharia de Software"

from .repository_selector import RepositorySelector
from .pr_metrics import PRMetricsCollector
from .github_query import GitHubClient

__all__ = [
    'RepositorySelector',
    'PRMetricsCollector',
    'GitHubClient',
]
