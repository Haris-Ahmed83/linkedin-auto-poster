import requests
from datetime import datetime, timedelta, timezone
from config import GH_TOKEN, GH_USERNAME

HEADERS = {"Authorization": f"Bearer {GH_TOKEN}"}

REPO_BLACKLIST = [
    "Haris-ahmed83", "test", "test_file", "project1_morning.py",
    "Full_stack_projects", "python-all-series",
    "linkedin-auto-poster", "config-file-manager",
]

REPO_PRIORITY = {
    "production-rag-system": 10,
    "freellmapi": 9,
    "live-sports-scoreboard": 8,
    "parkvault": 7,
    "ImageConverter": 6,
    "linkedin-auto-accept": 5,
    "flutter_weather_app": 5,
    "Flutter-Jenoury": 4,
    "Flutter-pro-developer": 4,
}

def fetch_recent_events():
    url = f"https://api.github.com/users/{GH_USERNAME}/events?per_page=30"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []
    return resp.json()

def fetch_repo_details(repo_name):
    url = f"https://api.github.com/repos/{GH_USERNAME}/{repo_name}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()
    return None

def get_best_repo(cooled_down_repos=None):
    if cooled_down_repos is None:
        cooled_down_repos = set()

    events = fetch_recent_events()
    seen_repos = {}
    
    for event in events:
        repo_full = event.get("repo", {}).get("name", "")
        repo_name = repo_full.split("/")[-1] if "/" in repo_full else repo_full
        
        if repo_name in REPO_BLACKLIST:
            continue
        if repo_name in cooled_down_repos:
            continue
        
        created = event.get("created_at", "")
        if repo_name not in seen_repos or created > seen_repos[repo_name]["time"]:
            seen_repos[repo_name] = {
                "name": repo_name,
                "full_name": repo_full,
                "time": created,
                "type": event.get("type", ""),
            }

    if not seen_repos:
        return None

    scored = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    
    for name, info in seen_repos.items():
        event_time = datetime.fromisoformat(info["time"].replace("Z", "+00:00"))
        recency_score = max(0, 10 - (datetime.now(timezone.utc) - event_time).total_seconds() / 3600)
        priority_score = REPO_PRIORITY.get(name, 3)
        
        details = fetch_repo_details(name)
        if details:
            desc = details.get("description", "") or ""
            has_stars = 2 if details.get("stargazers_count", 0) > 0 else 0
            has_topics = 1 if details.get("topics", []) else 0
        else:
            desc = ""
            has_stars = 0
            has_topics = 0

        total = recency_score * 1.5 + priority_score + has_stars + has_topics
        scored.append((total, name, desc, details))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0] if scored else None
