import requests
import time
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from tqdm import tqdm
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW_DIR = BASE / 'data' / 'raw'
RAW_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FP = BASE / 'data' / 'collector_checkpoint.json'

# Logger
LOG_FP = BASE / 'data' / 'collector.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FP, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('github_collector')

# Config
LANGUAGES = ['Python','JavaScript','TypeScript','Java','C++','C#','PHP','HTML']
REPOS_PER_LANG = 50
MONTHS = 12
MAX_WORKERS = 4
checkpoint_lock = Lock()


def read_token(env_path='.env'):
    p = Path(env_path)
    if not p.exists():
        raise FileNotFoundError('.env not found')
    for line in p.read_text().splitlines():
        if line.strip().startswith('GITHUB_TOKEN='):
            return line.split('=',1)[1].strip()
    raise RuntimeError('GITHUB_TOKEN not found in .env')


class GitHubCollector:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'})

    def _check_rate(self, resp):
        remaining = resp.headers.get('X-RateLimit-Remaining')
        reset = resp.headers.get('X-RateLimit-Reset')
        if remaining is not None and reset is not None:
            remaining = int(remaining)
            reset = int(reset)
            if remaining < 5:
                sleep_for = max(5, reset - int(time.time()) + 5)
                print(f'Rate limit low ({remaining}). Sleeping {sleep_for}s until reset.')
                time.sleep(sleep_for)

    def search_repositories(self, language, per_page=50):
        # Use search/repositories sorted by stars
        q = f'language:{language}'
        url = f'https://api.github.com/search/repositories?q={quote_plus(q)}&sort=stars&order=desc&per_page={per_page}'
        resp = self.session.get(url)
        if resp.status_code != 200:
            self._check_rate(resp)
            logger.error('search_repositories failed: %s %s', resp.status_code, resp.text[:200])
            raise RuntimeError(f'search_repositories failed: {resp.status_code} {resp.text[:200]}')
        self._check_rate(resp)
        data = resp.json()
        return data.get('items', [])

    def paginate(self, url, params=None):
        """Return all items from a paginated GitHub endpoint until exhaustion."""
        params = dict(params or {})
        params.setdefault('per_page', 100)
        page = 1
        items = []
        while True:
            params['page'] = page
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                self._check_rate(resp)
                logger.warning('request failed %s %s', resp.status_code, resp.text[:200])
                break
            self._check_rate(resp)
            batch = resp.json()
            if not isinstance(batch, list):
                logger.warning('unexpected payload from %s', url)
                break
            items.extend(batch)
            if len(batch) < params['per_page']:
                break
            page += 1
        return items

    def count_commits_since(self, full_name, since_date):
        url = f'https://api.github.com/repos/{full_name}/commits'
        commits = self.paginate(url, params={'since': since_date})
        return len(commits)

    def collect_issues_and_prs_since(self, full_name, since_date):
        """Fetch issues endpoint once and split issues vs PRs.

        The issues API returns both issues and pull requests. We stop when the
        created_at timestamp becomes older than the requested window because the
        results are sorted by creation date descending.
        """
        url = f'https://api.github.com/repos/{full_name}/issues'
        params = {'state': 'all', 'sort': 'created', 'direction': 'desc'}
        all_items = []
        page = 1
        stop = False
        since_dt = datetime.fromisoformat(since_date + 'T00:00:00+00:00')

        while not stop:
            params['per_page'] = 100
            params['page'] = page
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                self._check_rate(resp)
                logger.warning('issues request failed for %s: %s %s', full_name, resp.status_code, resp.text[:200])
                break
            self._check_rate(resp)
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break

            for item in batch:
                created_at = item.get('created_at')
                if not created_at:
                    continue
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if created_dt < since_dt:
                    stop = True
                    break
                all_items.append(item)

            if len(batch) < 100:
                break
            page += 1

        return all_items


def compute_time_hours(created_at, closed_at):
    if not created_at or not closed_at:
        return None
    try:
        t1 = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        t2 = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
        return (t2 - t1).total_seconds() / 3600.0
    except Exception:
        return None


def collect_one_repo(token, lang, repo, since_date):
    full = repo['full_name']
    cache_fp = RAW_DIR / f"{full.replace('/', '__')}.json"
    if cache_fp.exists():
        try:
            with cache_fp.open('r', encoding='utf-8') as fh:
                cached = json.load(fh)
            if cached.get('language') == lang and cached.get('since_date') == since_date:
                return cached
        except Exception:
            pass

    gh = GitHubCollector(token)
    repo_info = {
        'full_name': full,
        'language': lang,
        'since_date': since_date,
        'stars': repo.get('stargazers_count'),
        'forks': repo.get('forks_count'),
    }

    try:
        repo_info['commits_last_12m'] = gh.count_commits_since(full, since_date)
    except Exception as e:
        logger.warning('commit count error for %s: %s', full, e)
        repo_info['commits_last_12m'] = None

    try:
        items = gh.collect_issues_and_prs_since(full, since_date)
    except Exception as e:
        logger.warning('issue/pr collection error for %s: %s', full, e)
        items = []

    pr_times = []
    issue_times = []
    pr_count = 0
    issue_count = 0
    closed_issues = 0

    for item in items:
        created_at = item.get('created_at')
        closed_at = item.get('closed_at')
        is_pr = 'pull_request' in item
        elapsed = compute_time_hours(created_at, closed_at)

        if is_pr:
            pr_count += 1
            if elapsed is not None:
                pr_times.append(elapsed)
        else:
            issue_count += 1
            if closed_at:
                closed_issues += 1
            if elapsed is not None:
                issue_times.append(elapsed)

    repo_info['pr_count_12m'] = pr_count
    repo_info['pr_median_time_hours'] = None if not pr_times else float(pd.Series(pr_times).median())
    repo_info['issues_count_12m'] = issue_count
    repo_info['issues_closed_12m'] = closed_issues
    repo_info['issue_median_time_hours'] = None if not issue_times else float(pd.Series(issue_times).median())

    with cache_fp.open('w', encoding='utf-8') as fh:
        json.dump(repo_info, fh, ensure_ascii=False, indent=2)

    return repo_info


def load_checkpoint():
    if not CHECKPOINT_FP.exists():
        return {'since_date': None, 'completed': {}, 'failed': {}, 'languages': LANGUAGES}
    try:
        with CHECKPOINT_FP.open('r', encoding='utf-8') as fh:
            data = json.load(fh)
        data.setdefault('completed', {})
        data.setdefault('failed', {})
        data.setdefault('languages', LANGUAGES)
        data.setdefault('since_date', None)
        return data
    except Exception:
        return {'since_date': None, 'completed': {}, 'failed': {}, 'languages': LANGUAGES}


def save_checkpoint(state):
    tmp_fp = CHECKPOINT_FP.with_suffix('.json.tmp')
    with tmp_fp.open('w', encoding='utf-8') as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    tmp_fp.replace(CHECKPOINT_FP)


def iso_months_ago(months):
    dt = datetime.now(timezone.utc) - timedelta(days=30*months)
    return dt.strftime('%Y-%m-%d')


def collect():
    token = read_token(BASE.parent / '.env')
    since_date = iso_months_ago(MONTHS)
    out_repos = []
    checkpoint = load_checkpoint()
    checkpoint['since_date'] = since_date
    checkpoint['languages'] = LANGUAGES

    for lang in LANGUAGES:
        logger.info('Collecting top repos for %s', lang)
        gh = GitHubCollector(token)
        repos = gh.search_repositories(lang, per_page=REPOS_PER_LANG)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for repo in repos:
                full = repo['full_name']
                cached_ok = False
                if full in checkpoint['completed']:
                    cached_ok = True
                else:
                    cache_fp = RAW_DIR / f"{full.replace('/', '__')}.json"
                    if cache_fp.exists():
                        cached_ok = True

                if cached_ok:
                    try:
                        with (RAW_DIR / f"{full.replace('/', '__')}.json").open('r', encoding='utf-8') as fh:
                            cached = json.load(fh)
                        out_repos.append(cached)
                        logger.info('Skipping already completed %s', full)
                        continue
                    except Exception:
                        pass

                futures.append(executor.submit(collect_one_repo, token, lang, repo, since_date))

            for future in tqdm(as_completed(futures), total=len(futures), desc=f'{lang} repos'):
                repo_info = future.result()
                full = repo_info['full_name']
                logger.info('Finished %s', full)
                out_repos.append(repo_info)
                with checkpoint_lock:
                    checkpoint['completed'][full] = {
                        'language': repo_info.get('language'),
                        'since_date': repo_info.get('since_date'),
                        'updated_at': datetime.now(timezone.utc).isoformat(),
                    }
                    checkpoint['failed'].pop(full, None)
                    save_checkpoint(checkpoint)

    # save summary
    summary_fp = BASE / 'data' / 'repos_summary.json'
    with summary_fp.open('w', encoding='utf-8') as fh:
        json.dump(out_repos, fh, ensure_ascii=False, indent=2)
    logger.info('Collection finished. Summary saved to %s', summary_fp)


if __name__ == '__main__':
    try:
        import pandas as pd
    except Exception:
        pass
    collect()
