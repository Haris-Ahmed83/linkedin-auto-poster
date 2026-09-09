import os
import json
import random
from datetime import datetime, timezone
from github_fetcher import get_best_repo, fetch_repo_details
from news_fetcher import fetch_hn_stories, filter_ai_stories, build_news_post, get_trending_repos
from templates import get_template_for_day
from linkedin_api import LinkedInAPI
from image_generator import generate_image_bytes
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

# Target topics for daily posting
CORE_TOPICS = [
    {
        "name": "GHL (GoHighLevel)",
        "tag": "#GoHighLevel #GHL #MarketingAutomation #SaaS",
        "trigger": "Most business owners waste 20+ hours a week switching between 7 different subscriptions.",
        "reveal": "We consolidated our CRM, funnel builder, email marketing, and call booking into a single GoHighLevel architecture. Here is the actual setup:",
        "identity": "If you're an agency owner, SaaS founder, or developer who values lean operations, messy software stacks are costing you revenue.",
        "provoking": "Which software in your stack is currently costing you money without delivering clear ROI?",
        "points": [
            "1. Automated Lead Nurture: Instant SMS & Email follow-ups within 60 seconds of form submission",
            "2. Pipeline Visibility: Real-time dashboard tracking deal progression from lead to closed-won",
            "3. Unified Communication: All WhatsApp, Email, and SMS conversations in one shared inbox"
        ]
    },
    {
        "name": "AI Automations",
        "tag": "#AI #Automation #Python #WorkflowAutomation",
        "trigger": "AI isn't going to replace developers — but developers using AI automation will replace those who don't.",
        "reveal": "I built an autonomous workflow engine that handles lead qualification, data parsing, and auto-responses using custom LLM pipelines.",
        "identity": "As engineers and automation architects, our job isn't to write more code. It's to eliminate manual work entirely.",
        "provoking": "What is one repetitive task in your daily workflow that you haven't automated yet?",
        "points": [
            "1. Event-Driven Triggers: Webhooks intercept inbound leads in real-time",
            "2. Intelligent Parsing: LLM extracts intent, budget, and urgency from unstructured text",
            "3. Zero-Delay Execution: Auto-routes actions directly to CRM and team notifications"
        ]
    },
    {
        "name": "CRMs & Sales Pipelines",
        "tag": "#CRM #SalesPipeline #BusinessGrowth #Tech",
        "trigger": "80% of sales leads are lost simply because of delayed follow-up.",
        "reveal": "A structured CRM workflow with automated stage triggers changes everything. Here's how we structured our sales pipeline:",
        "identity": "If you are building products or offering services, your CRM is the engine of your entire revenue operation.",
        "provoking": "How many minutes does your team take to follow up with a fresh inbound lead?",
        "points": [
            "1. Stage 1 (Prospect): Instant automated greeting + calendar booking link",
            "2. Stage 2 (Demo Done): Automated proposal delivery & follow-up sequence",
            "3. Stage 3 (Closed Won): Instant onboarding trigger & webhook notification"
        ]
    },
    {
        "name": "High-Converting Funnels",
        "tag": "#Funnels #WebDevelopment #ConversionOptimization #Growth",
        "trigger": "A beautiful website without a clear funnel conversion mechanism is just an expensive digital brochure.",
        "reveal": "We redesigned our funnel architecture with lightning-fast load times and a single primary Call-to-Action. The result?",
        "identity": "Whether you are a full-stack dev or a digital marketer, conversion rate optimization (CRO) is a superpower.",
        "provoking": "What is the single biggest bottleneck stopping visitors on your landing page from converting?",
        "points": [
            "1. Sub-1-Second Load Speed: Zero heavy bloat, optimized assets, instant render",
            "2. Frictionless Lead Form: Only ask for essential details to maximize completions",
            "3. One-Click Social Proof: Embed verified customer results directly near the CTA"
        ]
    },
    {
        "name": "Full-Stack Development",
        "tag": "#FullStack #WebDev #SoftwareEngineering #Code",
        "trigger": "Over-engineering your stack in the early stage is the fastest way to kill a project.",
        "reveal": "Here is the exact minimalist full-stack architecture I use to ship fast, reliable applications in days, not months:",
        "identity": "As full-stack developers, we win by shipping clean, maintainable systems that solve real human problems.",
        "provoking": "What tech stack do you default to when you need to ship a new idea in 48 hours?",
        "points": [
            "1. Frontend: Next.js / Tailwind CSS for responsive, accessible, ultra-fast UI",
            "2. Backend: Node.js / Python REST API with clean modular service layers",
            "3. Database & Hosting: PostgreSQL + Vercel / Docker for zero-friction deployments"
        ]
    },
    {
        "name": "Robot Engineering & Hardware",
        "tag": "#Robotics #RoboticEngineering #Hardware #AIHardware",
        "trigger": "Hardware is hard. But combining physical robotics with modern AI vision makes the impossible effortless.",
        "reveal": "We integrated AI vision sensors with robotic microcontrollers to build an autonomous pick-and-place tracking system.",
        "identity": "To all roboticists, hardware builders, and embedded engineers: physical world automation is the next massive frontier.",
        "provoking": "Are you building hardware solutions or software-only systems this year?",
        "points": [
            "1. Real-Time Vision: Embedded camera feeds frames directly to lightweight AI models",
            "2. Kinematic Control: Microsecond motor control for smooth robotic arm movement",
            "3. Edge Compute: Running inference directly on edge hardware for zero latency"
        ]
    }
]

def build_trip_post(topic_item):
    """
    Builds a LinkedIn post adhering strictly to the TRIP framework:
    T = Triggering Hook
    R = Reveal (Solution / Technical Breakdown)
    I = Identity (Aligning with target audience)
    P = Provoking Question (High-engagement CTA)
    """
    post_lines = [
        f"{topic_item['trigger']}\n",
        f"{topic_item['reveal']}\n",
    ]
    for pt in topic_item['points']:
        post_lines.append(f"{pt}")
    
    post_lines.append(f"\n{topic_item['identity']}\n")
    post_lines.append(f"👉 {topic_item['provoking']}\n")
    post_lines.append(topic_item['tag'])
    
    return "\n".join(post_lines)

def generate_post():
    today = datetime.now(timezone.utc)
    weekday = today.weekday()
    
    # Select topic based on day to maintain structured variety across all 6 core topics
    topic_item = CORE_TOPICS[weekday % len(CORE_TOPICS)]
    post_text = build_trip_post(topic_item)
    
    result_data = {
        "template": "trip_framework",
        "topic": topic_item["name"],
        "repo": topic_item["name"],
        "score": 10.0,
        "post": post_text,
        "timestamp": today.isoformat(),
    }
    
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

        image_urn = None
        # Try generating and uploading image
        image_bytes = generate_image_bytes(result)
        if image_bytes:
            try:
                print("Uploading generated image to LinkedIn media assets...")
                image_urn = api.upload_image_asset(author_urn, image_bytes)
                print(f"Image uploaded successfully! Asset URN: {image_urn}")
            except Exception as ie:
                print(f"Failed to upload image to LinkedIn: {ie}. Proceeding with text-only post.")

        response = api.create_post(author_urn, result["post"], image_urn=image_urn)
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
