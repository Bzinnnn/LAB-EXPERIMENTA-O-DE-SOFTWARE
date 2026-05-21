import json
from pathlib import Path

import pandas as pd


def load_summary(summary_fp: Path) -> pd.DataFrame:
    if not summary_fp.exists():
        raise FileNotFoundError(f'Arquivo não encontrado: {summary_fp}')

    with summary_fp.open('r', encoding='utf-8') as fh:
        records = json.load(fh)

    if not isinstance(records, list):
        raise ValueError('repos_summary.json precisa conter uma lista de objetos')

    df = pd.DataFrame(records)
    numeric_cols = [
        'stars',
        'forks',
        'commits_last_12m',
        'pr_count_12m',
        'pr_median_time_hours',
        'issues_count_12m',
        'issues_closed_12m',
        'issue_median_time_hours',
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def build_language_metrics(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.groupby('language', dropna=False)
        .agg(
            repo_count=('full_name', 'count'),
            total_stars=('stars', 'sum'),
            total_forks=('forks', 'sum'),
            total_commits_12m=('commits_last_12m', 'sum'),
            total_prs_12m=('pr_count_12m', 'sum'),
            total_issues_12m=('issues_count_12m', 'sum'),
            total_closed_issues_12m=('issues_closed_12m', 'sum'),
            median_pr_time_hours=('pr_median_time_hours', 'median'),
            mean_pr_time_hours=('pr_median_time_hours', 'mean'),
            median_issue_close_hours=('issue_median_time_hours', 'median'),
            mean_issue_close_hours=('issue_median_time_hours', 'mean'),
            median_commits_12m=('commits_last_12m', 'median'),
            mean_commits_12m=('commits_last_12m', 'mean'),
        )
        .reset_index()
        .sort_values('repo_count', ascending=False)
    )

    return agg


def main():
    base = Path(__file__).resolve().parents[1]
    out_dir = base / 'data'
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_fp = out_dir / 'repos_summary.json'
    df = load_summary(summary_fp)

    repo_fp = out_dir / 'repo_metrics.csv'
    repo_cols = [
        'full_name',
        'language',
        'since_date',
        'stars',
        'forks',
        'commits_last_12m',
        'pr_count_12m',
        'pr_median_time_hours',
        'issues_count_12m',
        'issues_closed_12m',
        'issue_median_time_hours',
    ]
    existing_repo_cols = [col for col in repo_cols if col in df.columns]
    df[existing_repo_cols].to_csv(repo_fp, index=False)

    lang_fp = out_dir / 'language_metrics.csv'
    build_language_metrics(df).to_csv(lang_fp, index=False)

    print(f'CSV gerados em {out_dir}')
    print(f'- {repo_fp.name}')
    print(f'- {lang_fp.name}')


if __name__ == '__main__':
    main()
