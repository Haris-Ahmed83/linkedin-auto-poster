import requests
import random

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"

AI_KEYWORDS = [
    "ai", "machine learning", "llm", "gpt", "rag", "langchain",
    "python", "javascript", "react", "flutter", "open source",
    "chatgpt", "claude", "gemini", "groq", "mistral", "llama",
    "coding", "programming", "developer", "startup", "tech",
    "cloud", "api", "docker", "kubernetes", "github",
    "neural", "deep learning", "transformer", "agent",
    "finetune", "fine-tune", "prompt", "rag", "vector",
    "database", "framework", "typescript", "nextjs",
]

def fetch_hn_stories(limit=30):
    try:
        resp = requests.get(HN_TOP, timeout=10)
        top_ids = resp.json()[:limit]
        stories = []
        for sid in top_ids:
            try:
                item = requests.get(HN_ITEM.format(sid), timeout=10).json()
                title = item.get("title", "")
                url = item.get("url", "")
                score = item.get("score", 0)
                hn_url = f"https://news.ycombinator.com/item?id={sid}"
                if title and score > 0:
                    stories.append({
                        "title": title,
                        "url": url if url else hn_url,
                        "score": score,
                        "hn_url": hn_url,
                    })
            except:
                continue
        return stories
    except:
        return []

def filter_ai_stories(stories, min_score=5):
    matched = []
    for s in stories:
        title_lower = s["title"].lower()
        if any(kw in title_lower for kw in AI_KEYWORDS):
            if s["score"] >= min_score:
                matched.append(s)
    return matched

def build_news_post(story):
    title = story["title"]
    score = story["score"]
    url = story["url"]
    hn_url = story["hn_url"]

    hooks = [
        f"Big news in tech today:\n{title}",
        f"This is generating buzz right now:\n{title}",
        f"If you work in tech, you should see this:\n{title}",
    ]
    hook = random.choice(hooks)

    body = [
        hook,
        "",
        f"This story has {score} points on Hacker News — the community is actively discussing it.",
        "",
        "Here's why it matters:",
        "",
        "New tools, frameworks, and models come out every week.",
        "Most won't survive. But the ones worth watching share a pattern:",
        "they solve a real problem, not a hypothetical one.",
        "",
        "Keep building. Keep watching.",
        "",
        f"Source: {url if url else hn_url}",
        "",
        "What's your take on this?",
    ]

    return "\n".join(body)

def get_trending_repos():
    try:
        url = "https://api.github.com/search/repositories?q=created:>2026-06-01+language:python+language:typescript&sort=stars&order=desc&per_page=10"
        headers = {"Accept": "application/vnd.github.v3+json"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            repos = resp.json().get("items", [])[:5]
            return [{"name": r["name"], "desc": r.get("description", ""),
                     "stars": r["stargazers_count"], "url": r["html_url"],
                     "lang": r.get("language", "")} for r in repos]
    except:
        return []
