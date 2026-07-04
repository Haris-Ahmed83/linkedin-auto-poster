import os
import json
import random
from datetime import datetime, timezone
from github_fetcher import get_best_repo, fetch_repo_details
from templates import get_template_for_day
from linkedin_api import LinkedInAPI
from config import (
    LINKEDIN_ACCESS_TOKEN, LINKEDIN_USER_URN, DRY_RUN,
    GH_TOKEN, POSTING_DAYS, COOLDOWN_DAYS,
)

COOLDOWN_FILE = "cooldown.json"

def load_cooldown():
    if os.path.exists(COOLDOWN_FILE):
        with open(COOLDOWN_FILE) as f:
            return json.load(f)
    return []

def save_cooldown(repos):
    with open(COOLDOWN_FILE, "w") as f:
        json.dump(repos, f)

def build_post_how_i_built(repo_name, description, details):
    lang = details.get("language", "Python") if details else "Python"
    topics = details.get("topics", []) if details else []
    stars = details.get("stargazers_count", 0)
    
    hooks = [
        f"I built a {description.lower().split('.')[0]}. Cost? $0.",
        f"Most people overcomplicate {repo_name}. Here's the simple version.",
        f"I shipped {repo_name} in under 48 hours. Here's exactly how.",
    ]
    hook = random.choice(hooks)

    body_parts = [f"{hook}\n\nHere's the breakdown:\n"]
    
    tech = lang
    if topics:
        tech = ", ".join(topics[:4])
    
    body_parts.append(f"Stack: {tech}\n")
    body_parts.append(f"Stars: {stars} | Built by: one dev with a laptop and coffee\n")
    body_parts.append("What I learned building this:\n")
    
    lessons = [
        f"1. Start with the hardest problem first — everything else follows",
        f"2. The first version will be ugly. Ship it anyway.",
        f"3. Documentation while building saves 3x time later",
    ]
    for lesson in lessons:
        body_parts.append(lesson)
    
    body_parts.append(f"\nWould you use something like this? What feature matters most to you?\n")
    
    return "\n".join(body_parts)

def build_post_hot_take(repo_name, description, details):
    lang = details.get("language", "code") if details else "code"
    
    hooks = [
        "Everyone's chasing expensive AI tools.\nI went the other direction.",
        "Hot take: you don't need OpenAI credits to ship real AI.",
        "I tested 16 free LLM providers. Here's what shocked me.",
    ]
    hook = random.choice(hooks)
    
    body_parts = [f"{hook}\n"]
    
    if "free" in (description or "").lower() or "llm" in (repo_name or "").lower():
        body_parts.append("The truth is: free tier AI is better than most paid solutions.\n")
        body_parts.append("You just need to know how to stitch them together.\n")
        body_parts.append("Failover between providers. Use caching. Design for rate limits.\n")
        body_parts.append("That's real engineering — not just writing a check to OpenAI.\n")
        body_parts.append("Three things I've learned:\n")
        body_parts.append("1. Free APIs fail. Always have a backup.")
        body_parts.append("2. Latency varies wildly — test before you commit.")
        body_parts.append("3. Most 'limitations' are solvable with good architecture.")
    else:
        body_parts.append(f"I built this with {lang} because it solves a real problem — not because it's trendy.\n")
        body_parts.append("Three beliefs I build by:\n")
        body_parts.append("1. Free tier first. Upgrade only when necessary.")
        body_parts.append(f"2. {lang} gets the job done faster than the 'perfect' stack.")
        body_parts.append("3. Ship fast, refactor later.")
    
    body_parts.append("\nWhat's one tool you're paying for that you could build yourself?\n")
    
    return "\n".join(body_parts)

def build_post_lesson_learned(repo_name, description, details):
    hooks = [
        f"I broke {repo_name} three times before it worked.",
        "This project taught me something I wish I knew earlier.",
        "I made every mistake possible building this. Here's what saved me.",
    ]
    hook = random.choice(hooks)
    
    body_parts = [f"{hook}\n"]
    
    if details and details.get("stargazers_count", 0) > 0:
        body_parts.append(f"It now has {details['stargazers_count']} stars on GitHub. But getting there wasn't pretty.\n")
    
    body_parts.append("The mistakes:\n")
    body_parts.append("1. Over-engineered the first version. Simple works.")
    body_parts.append("2. Didn't ask for feedback early enough.")
    body_parts.append("3. Spent too long on things users never see.\n")
    body_parts.append("The fix for each:\n")
    body_parts.append("1. Ship the MVP in one day, not one week.")
    body_parts.append("2. Share your work-in-progress. The fear is in your head.")
    body_parts.append("3. Perfect is the enemy of shipped.\n")
    body_parts.append("If you're building something right now — what mistake are you currently making?\n")
    
    return "\n".join(body_parts)

def build_post_data_numbers(repo_name, description, details):
    lang = details.get("language", "code") if details else "code"
    stars = details.get("stargazers_count", 0) if details else 0
    size = details.get("size", 0) if details else 0
    
    hooks = [
        f"Numbers don't lie. Here's what building {repo_name} taught me in data.",
        f"I tracked everything while building this. The numbers surprised me.",
    ]
    hook = random.choice(hooks)
    
    body_parts = [f"{hook}\n"]
    body_parts.append(f"Project: {repo_name}")
    body_parts.append(f"Language: {lang}")
    body_parts.append(f"GitHub stars: {stars}")
    body_parts.append(f"Repo size: ~{size}KB\n")
    body_parts.append("What the data says:\n")
    body_parts.append("1. Most features users request are already in your roadmap")
    body_parts.append("2. Code you delete is more valuable than code you write")
    body_parts.append("3. Small, daily commits > big weekly pushes\n")
    body_parts.append("Build in public. The data compounds.\n")
    body_parts.append("What metric do you track when building?\n")
    
    return "\n".join(body_parts)

def build_post_progress_journey(repo_name, description, details):
    lang = details.get("language", "code") if details else "code"
    
    hooks = [
        f"Day [X] of building in public.\nToday I worked on {repo_name}.",
        "Building in public isn't comfortable. But it works.",
    ]
    hook = random.choice(hooks)
    
    body_parts = [f"{hook}\n"]
    
    if "60" in (description or ""):
        body_parts.append(f"This is part of my 60-project challenge in {lang}.\n")
    
    body_parts.append("What I did today:\n")
    body_parts.append("Fixed one bug. Added one feature. Learned one thing.\n")
    body_parts.append("That's the formula.\n")
    body_parts.append("Not complicated. Just consistent.\n")
    body_parts.append("The hardest part isn't the code — it's showing up every day.\n")
    body_parts.append("3 things that help me stay consistent:\n")
    body_parts.append("1. Ship something small every single day")
    body_parts.append("2. Don't break the streak")
    body_parts.append("3. Share the journey — it keeps you accountable\n")
    body_parts.append("What keeps YOU consistent?\n")
    
    return "\n".join(body_parts)

BUILDERS = {
    "how_i_built": build_post_how_i_built,
    "hot_take": build_post_hot_take,
    "lesson_learned": build_post_lesson_learned,
    "data_numbers": build_post_data_numbers,
    "progress_journey": build_post_progress_journey,
}

def generate_post():
    today = datetime.now(timezone.utc)
    weekday = today.weekday()
    week_parity = today.isocalendar()[1] % 2

    template = get_template_for_day(weekday, week_parity)
    template_key = template["name"].lower().replace(" / ", "_").replace(" ", "_")

    cooled_down = load_cooldown()
    result = get_best_repo(cooled_down_repos=set(cooled_down))
    
    if not result:
        print("No suitable repo found for today. Skipping.")
        return None

    score, repo_name, description, details = result
    
    builder = BUILDERS.get(template_key)
    if not builder:
        print(f"No builder for template: {template_key}")
        return None

    post_text = builder(repo_name, description, details)
    
    lines = post_text.strip().split("\n")
    short_lines = [l for l in lines if len(l.split()) > 5]
    char_count = len(post_text)
    
    hashtags = ""
    if details and details.get("topics"):
        used = []
        for t in details["topics"]:
            clean = t.replace("-", "").replace(" ", "")
            if clean not in used and len(used) < 2:
                used.append(clean)
        if used:
            hashtags = "\n" + " ".join(f"#{h}" for h in used)
    
    post_text = post_text.strip() + hashtags
    
    if len(post_text) > 3000:
        lines = post_text.split("\n")
        post_text = "\n".join(lines[:40]) + "\n\n[continued...]"

    result_data = {
        "template": template_key,
        "repo": repo_name,
        "score": score,
        "post": post_text,
        "timestamp": today.isoformat(),
    }
    
    # Update cooldown
    cooled_down.append(repo_name)
    save_cooldown(cooled_down[-20:])
    
    return result_data

def post_to_linkedin(result):
    if not LINKEDIN_ACCESS_TOKEN:
        print("No LinkedIn access token configured. Skipping post.")
        return False

    try:
        api = LinkedInAPI(LINKEDIN_ACCESS_TOKEN)
        
        if LINKEDIN_USER_URN:
            author_urn = LINKEDIN_USER_URN
        else:
            author_urn = api.get_user_urn()
        
        response = api.create_post(author_urn, result["post"])
        print(f"Posted successfully! Repo: {result['repo']}")
        print(f"Response: {response}")
        return True
    
    except Exception as e:
        print(f"Failed to post: {e}")
        return False

if __name__ == "__main__":
    print("Generating post...")
    result = generate_post()
    
    if result:
        print(f"\n=== POST DRAFT ===")
        print(f"Template: {result['template']}")
        print(f"Repo: {result['repo']}")
        print(f"Score: {result['score']:.1f}")
        print(f"\nContent:\n{result['post']}")
        print(f"\n=== END ===")
        
        if not DRY_RUN:
            success = post_to_linkedin(result)
            if success:
                print("Post published to LinkedIn!")
            else:
                print("Failed to publish. Check logs above.")
        else:
            print("\n[DRY RUN] Post would be published. Set DRY_RUN=False in config to go live.")
    else:
        print("No post generated.")
