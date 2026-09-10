import hashlib
import os
import json
import random
from datetime import datetime, timezone
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_fetcher import get_best_repo, fetch_repo_details
from news_fetcher import fetch_hn_stories, filter_ai_stories, build_news_post, get_trending_repos
from templates import get_template_for_day
from linkedin_api import LinkedInAPI
from image_generator import generate_image_bytes
from config import (
    LINKEDIN_ACCESS_TOKEN, LINKEDIN_ORG_URN, DRY_RUN,
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

# ─────────────────────────────────────────────────────────────────────────────
# 30 topic variations across 6 pillars
# Same topic can appear multiple times — but the post text is always unique.
# Duplicate-prevention is done by MD5 hash of the actual post content.
# ─────────────────────────────────────────────────────────────────────────────
CORE_TOPICS = [
    # ── GHL / GoHighLevel (5 angles) ─────────────────────────────────────────
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
            "3. Unified Communication: All WhatsApp, Email, and SMS conversations in one shared inbox",
        ],
    },
    {
        "name": "GHL (GoHighLevel)",
        "tag": "#GoHighLevel #GHL #AgencyGrowth #CRM",
        "trigger": "I cancelled 9 SaaS tools in one month and replaced them all with a single platform.",
        "reveal": "GoHighLevel handles every client touchpoint we have. Here's the exact stack replacement breakdown:",
        "identity": "For agency owners who are tired of paying 9 separate bills for tools that barely talk to each other — this is the shift.",
        "provoking": "How many SaaS subscriptions are you currently paying for that could be merged into one?",
        "points": [
            "1. Replaced: Calendly, ActiveCampaign, ClickFunnels, Twilio, Slack bots, and more",
            "2. Result: One dashboard, one login, one monthly bill — zero context-switching",
            "3. Bonus: White-label the entire platform and sell it as your own SaaS to clients",
        ],
    },
    {
        "name": "GHL (GoHighLevel)",
        "tag": "#GoHighLevel #SalesAutomation #LeadGeneration #GHL",
        "trigger": "Your lead responds at 2 AM. Your team sleeps. The deal goes cold.",
        "reveal": "GHL's 24/7 AI chat + automated SMS drip sequence means no lead ever goes unanswered — even at 3 AM. Here's how:",
        "identity": "Every business owner losing leads to slow follow-up: this system runs even while you sleep.",
        "provoking": "What percentage of your inbound leads do you believe currently go cold before your team responds?",
        "points": [
            "1. AI Webchat Widget: Instant reply, qualifies lead intent within 30 seconds",
            "2. Trigger-Based SMS Drip: 5 automated follow-ups spaced over 72 hours",
            "3. Smart Routing: Hot leads go directly to a live call booking page automatically",
        ],
    },
    {
        "name": "GHL (GoHighLevel)",
        "tag": "#GoHighLevel #WhiteLabel #AgencyOwner #SaaSBusiness",
        "trigger": "The most profitable agency business model nobody talks about: selling your own SaaS.",
        "reveal": "With GoHighLevel's white-label feature, we packaged our internal system and now sell it as a standalone product. Here's the model:",
        "identity": "For agency founders ready to move from hourly services to scalable recurring SaaS revenue — this is the blueprint.",
        "provoking": "Would you consider repackaging your internal agency tools into a sellable SaaS product?",
        "points": [
            "1. White-label GHL under your own brand: logo, domain, pricing — fully yours",
            "2. Charge clients $297–$997/month for the platform as a standalone tool",
            "3. Zero extra dev cost: the infrastructure is already built — you just configure and sell",
        ],
    },
    {
        "name": "GHL (GoHighLevel)",
        "tag": "#GoHighLevel #MarketingOps #Snapshots #GHL",
        "trigger": "I deploy a complete business operations system for a new client in under 4 hours.",
        "reveal": "GHL Snapshots let you clone an entire proven system — funnels, automations, pipelines — into any new client account instantly.",
        "identity": "If you're an agency scaling across multiple clients, this is the difference between chaos and a repeatable system.",
        "provoking": "What part of your client onboarding process currently takes the most time to set up from scratch?",
        "points": [
            "1. One Snapshot = complete proven system: funnels, CRM stages, automations, templates",
            "2. Clone into new client account in minutes — no rebuilding from zero",
            "3. Customise only the brand assets; the proven logic stays intact and tested",
        ],
    },

    # ── AI Automations (5 angles) ─────────────────────────────────────────────
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
            "3. Zero-Delay Execution: Auto-routes actions directly to CRM and team notifications",
        ],
    },
    {
        "name": "AI Automations",
        "tag": "#AI #n8n #MakeAutomation #NoCode",
        "trigger": "I automated 40 hours of weekly manual work using three tools most developers already have access to.",
        "reveal": "n8n + Webhooks + an LLM API. That's the stack. Here's exactly how the workflow runs:",
        "identity": "For founders, operators, and developers who still have humans doing tasks a machine can handle — the ROI here is immediate.",
        "provoking": "Which repetitive internal process in your business costs you the most time every single week?",
        "points": [
            "1. Trigger: Webhook receives a form submission, email, or API event",
            "2. Brain: LLM classifies, extracts, and routes the data in natural language",
            "3. Action: Auto-populates CRM, sends notification, creates task — zero human input",
        ],
    },
    {
        "name": "AI Automations",
        "tag": "#AI #GPT #Automation #BusinessProcess",
        "trigger": "Stop copy-pasting data between tools. You're paying for automation and doing it manually.",
        "reveal": "We built a GPT-powered extraction layer that reads raw emails and auto-populates structured CRM fields in real time.",
        "identity": "Operations managers, VAs, and small business owners: the copy-paste workflow era is officially over.",
        "provoking": "How many hours per week does your team spend on data entry that could be handled automatically?",
        "points": [
            "1. Email Parser: GPT reads inbound emails and extracts name, budget, and intent fields",
            "2. Auto-CRM: Structured data pushes directly into GHL or HubSpot via API",
            "3. Confidence Score: System flags low-confidence extractions for 1-click human review",
        ],
    },
    {
        "name": "AI Automations",
        "tag": "#AIAgents #LangChain #Automation #AgenticAI",
        "trigger": "The next evolution isn't just AI — it's AI agents that take action without you asking.",
        "reveal": "We deployed a multi-agent system where one AI researches, another writes, and a third quality-checks — fully autonomous.",
        "identity": "For tech founders and product engineers exploring agentic AI: this is where software stops being a tool and starts being a team member.",
        "provoking": "What's one decision in your business you'd trust an AI agent to make autonomously without human review?",
        "points": [
            "1. Research Agent: Scrapes, summarises, and ranks relevant data from the web in seconds",
            "2. Writer Agent: Generates structured content from research output in your brand voice",
            "3. QA Agent: Reviews, scores, and flags output before it ever reaches a human",
        ],
    },
    {
        "name": "AI Automations",
        "tag": "#PythonAutomation #AI #Scheduling #TaskAutomation",
        "trigger": "I run 12 daily business tasks on autopilot. Total cost: $0/month. No Zapier. No Make.",
        "reveal": "A simple Python scheduler + free API calls handles everything from daily reports to client check-ins. Here's the architecture:",
        "identity": "For developers who are paying for automation platforms when a 50-line Python script would do the job better.",
        "provoking": "What's a business task you do manually every day that could be scripted in under an hour?",
        "points": [
            "1. Python cron scheduler triggers each task at the exact configured time",
            "2. API calls to Gemini / GPT handle all content generation and classification",
            "3. Results auto-send via email, Slack, or webhook — no dashboard required",
        ],
    },

    # ── CRMs & Sales Pipelines (5 angles) ────────────────────────────────────
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
            "3. Stage 3 (Closed Won): Instant onboarding trigger & webhook notification",
        ],
    },
    {
        "name": "CRMs & Sales Pipelines",
        "tag": "#CRM #HubSpot #SalesOps #RevenueGrowth",
        "trigger": "Your CRM is full of leads. Your pipeline is empty. Here's why.",
        "reveal": "Most teams input data but never follow a stage discipline. One structural change tripled our close rate.",
        "identity": "Sales managers and revenue operators: the problem isn't your leads — it's the process those leads fall into.",
        "provoking": "Do you have a documented, stage-by-stage follow-up process that your entire team follows consistently?",
        "points": [
            "1. Define: Each CRM stage has one clear entry condition and one required action",
            "2. Automate: Stage transitions trigger instant follow-up tasks — no manual reminders",
            "3. Measure: Track stage conversion rates weekly — not just total revenue",
        ],
    },
    {
        "name": "CRMs & Sales Pipelines",
        "tag": "#SalesAutomation #CRM #FollowUp #ClientManagement",
        "trigger": "The best salespeople don't work harder. They let their CRM work for them.",
        "reveal": "We built a 7-touch automated follow-up system inside GHL that runs for 14 days after every demo call — zero manual effort.",
        "identity": "For solo founders and small sales teams who can't afford to miss a follow-up: this is how you scale without hiring.",
        "provoking": "How many follow-up touchpoints does your team typically send before giving up on a cold lead?",
        "points": [
            "1. Touch 1–2: Personalised email + SMS immediately post-call recap",
            "2. Touch 3–5: Value-add content sent on days 3, 5, and 7 automatically",
            "3. Touch 6–7: Final soft close + break-up email on days 10 and 14",
        ],
    },
    {
        "name": "CRMs & Sales Pipelines",
        "tag": "#SalesDashboard #Analytics #CRM #DataDrivenSales",
        "trigger": "If you can't see exactly where every deal is at 9 AM, your pipeline is leaking revenue.",
        "reveal": "We built a live sales command dashboard that shows deal health, follow-up status, and projected close revenue in real time.",
        "identity": "Sales leaders and founders who make revenue decisions without real-time pipeline visibility are flying blind.",
        "provoking": "How long does it take your team to produce an accurate snapshot of your current pipeline health?",
        "points": [
            "1. Live Deal View: Every open deal shows last contact date, stage, and next action",
            "2. Revenue Forecast: Weighted pipeline value recalculates automatically each day",
            "3. Alert System: Deals stagnant for 3+ days trigger an automatic team notification",
        ],
    },
    {
        "name": "CRMs & Sales Pipelines",
        "tag": "#OnboardingAutomation #CRM #ClientSuccess #SaaS",
        "trigger": "Winning the sale is step one. Losing the client in onboarding is the real revenue killer.",
        "reveal": "We automated the entire post-sale onboarding sequence — from contract to first delivery — using CRM stage triggers.",
        "identity": "For SaaS founders and service businesses: your onboarding experience is your retention rate. Automate it.",
        "provoking": "What is the most common point in your onboarding where new clients feel confused or unsupported?",
        "points": [
            "1. Contract Signed → instant welcome email + onboarding video delivered automatically",
            "2. Day 3 check-in SMS + setup guide sent without anyone lifting a finger",
            "3. Day 7 milestone review call auto-booked via calendar link in day-5 email",
        ],
    },

    # ── High-Converting Funnels (5 angles) ───────────────────────────────────
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
            "3. One-Click Social Proof: Embed verified customer results directly near the CTA",
        ],
    },
    {
        "name": "High-Converting Funnels",
        "tag": "#LandingPage #CRO #ConversionRate #DigitalMarketing",
        "trigger": "We changed one word on a landing page headline and increased conversions by 34%.",
        "reveal": "Copywriting is the highest-leverage skill in digital marketing. Here's the exact before/after framework we use:",
        "identity": "For marketers and founders writing their own copy: the words matter more than the design. Here's proof.",
        "provoking": "When did you last A/B test the headline on your primary landing page?",
        "points": [
            "1. Before: Feature-first headline ('The All-In-One Marketing Platform')",
            "2. After: Outcome-first headline ('Get 3x More Leads Without Increasing Ad Spend')",
            "3. Rule: Lead with the transformation the client gets — not the tool you built",
        ],
    },
    {
        "name": "High-Converting Funnels",
        "tag": "#SalesFunnel #EmailMarketing #LeadMagnet #MarketingStrategy",
        "trigger": "Your lead magnet is getting downloads. Your sales funnel is getting no sales. Here's why.",
        "reveal": "Most lead magnets collect contacts but don't build intent. We restructured our lead magnet sequence to educate and convert in 5 emails.",
        "identity": "Marketers and course creators: a lead magnet that doesn't move people toward buying is just a free giveaway.",
        "provoking": "What is the conversion rate from lead magnet download to booked call in your current funnel?",
        "points": [
            "1. Email 1 (Instant): Deliver the magnet + set expectations for what's coming next",
            "2. Emails 2–4: One specific problem solved per email — builds authority and trust daily",
            "3. Email 5 (Day 5): Soft pitch with a single clear CTA — call, trial, or purchase",
        ],
    },
    {
        "name": "High-Converting Funnels",
        "tag": "#WebsiteConversion #UXDesign #Funnels #GrowthHacking",
        "trigger": "Most websites are designed for the designer's portfolio — not for the visitor's conversion.",
        "reveal": "We audited 200 business websites and found the same 3 mistakes killing conversion rates across every industry.",
        "identity": "Founders and agency owners: your website is a sales asset, not an art project. Design for the sale.",
        "provoking": "Does your website homepage make it crystal clear what action you want a visitor to take within 5 seconds?",
        "points": [
            "1. Mistake 1: No above-the-fold CTA — visitors scroll but never convert",
            "2. Mistake 2: Describing features instead of outcomes ('what we do' vs 'what you get')",
            "3. Mistake 3: Social proof buried at the bottom — move it right below the headline",
        ],
    },
    {
        "name": "High-Converting Funnels",
        "tag": "#VSL #VideoSalesFunnel #ConversionOptimization #MarketingFunnel",
        "trigger": "A 3-minute video on a landing page can replace a 45-minute sales call. Here's how we built ours.",
        "reveal": "A Video Sales Letter (VSL) that follows the Problem-Agitate-Solve structure converts cold traffic into booked calls consistently.",
        "identity": "For founders who are tired of manually pitching the same thing to every new lead — a VSL is the leverage you need.",
        "provoking": "Have you considered using a short video pitch to replace or pre-qualify your initial discovery calls?",
        "points": [
            "1. First 30 seconds: Name the exact pain point your ideal client is experiencing right now",
            "2. Middle 90 seconds: Show proof of transformation — real results, not vague promises",
            "3. Final 30 seconds: One CTA only — book a call, start trial, or buy — nothing else",
        ],
    },

    # ── Full-Stack Development (5 angles) ─────────────────────────────────────
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
            "3. Database & Hosting: PostgreSQL + Vercel / Docker for zero-friction deployments",
        ],
    },
    {
        "name": "Full-Stack Development",
        "tag": "#APIDesign #REST #BackendDevelopment #SoftwareArchitecture",
        "trigger": "Bad API design costs more time in debugging than it ever saved in the first build.",
        "reveal": "I've reviewed 50+ production APIs. The same three structural mistakes appear in almost every broken one.",
        "identity": "Backend engineers and API architects: clean contracts between services are the foundation of every scalable system.",
        "provoking": "What's the most painful API design decision you've ever had to undo in a production system?",
        "points": [
            "1. Mistake 1: No versioning — breaking changes kill downstream integrations silently",
            "2. Mistake 2: Returning raw DB errors to clients — a security and UX nightmare",
            "3. Mistake 3: Skipping pagination on list endpoints — works fine until it absolutely doesn't",
        ],
    },
    {
        "name": "Full-Stack Development",
        "tag": "#React #NextJS #Frontend #WebPerformance",
        "trigger": "Your React app renders in 4 seconds. You've already lost the user.",
        "reveal": "Frontend performance is not a nice-to-have — it directly affects SEO, bounce rate, and conversion. Here's the fix stack:",
        "identity": "For frontend developers who believe great UI is about looks: performance is the UX nobody talks about.",
        "provoking": "What is the current Lighthouse performance score of your main production frontend?",
        "points": [
            "1. Server Components: Move data fetching out of the client — zero waterfall round trips",
            "2. Image Optimisation: Use next/image with lazy loading — eliminate render-blocking assets",
            "3. Code Splitting: Dynamic imports for heavy components — users only load what they see",
        ],
    },
    {
        "name": "Full-Stack Development",
        "tag": "#DevOps #Docker #CI_CD #SoftwareDeployment",
        "trigger": "If deploying your app is scary, your deployment pipeline is the actual bug.",
        "reveal": "We containerised everything and built a zero-downtime CI/CD pipeline. Now every deploy takes 4 minutes and is fully reversible.",
        "identity": "For developers who still deploy by SSHing into a server manually: this is the ops upgrade your team needs.",
        "provoking": "What is the most stressful part of deploying to production for your current project?",
        "points": [
            "1. Docker: Every environment is identical — dev, staging, and prod run the same container",
            "2. GitHub Actions CI: Tests run automatically on every PR before merge is allowed",
            "3. Blue-Green Deploy: Traffic switches instantly — rollback in 60 seconds with one command",
        ],
    },
    {
        "name": "Full-Stack Development",
        "tag": "#DatabaseDesign #PostgreSQL #Backend #DataEngineering",
        "trigger": "Most slow applications aren't slow because of the code — they're slow because of the database.",
        "reveal": "I optimised a production PostgreSQL database and reduced average query time from 2.3 seconds to 40 milliseconds. Here's exactly what changed:",
        "identity": "Full-stack and backend engineers: database performance is the highest-leverage optimization in any application at scale.",
        "provoking": "When did you last run EXPLAIN ANALYZE on your most-used database queries in production?",
        "points": [
            "1. Added composite indexes on the 3 most-queried column combinations — instant 10x gain",
            "2. Eliminated N+1 queries by rewriting nested loops into single JOIN statements",
            "3. Implemented connection pooling via PgBouncer — reduced connection overhead by 80%",
        ],
    },

    # ── Robot Engineering & Hardware (5 angles) ───────────────────────────────
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
            "3. Edge Compute: Running inference directly on edge hardware for zero latency",
        ],
    },
    {
        "name": "Robot Engineering & Hardware",
        "tag": "#Arduino #RaspberryPi #EmbeddedSystems #IoT",
        "trigger": "Software engineers think in functions. Hardware engineers think in electrons. The best engineers think in both.",
        "reveal": "We built a full IoT telemetry system on a $35 Raspberry Pi that monitors, logs, and alerts in real time — no cloud subscription required.",
        "identity": "For embedded engineers and makers who know that the most powerful systems are built at the intersection of hardware and software.",
        "provoking": "What's the most creative thing you've ever built using a microcontroller or single-board computer?",
        "points": [
            "1. Edge Sensor Network: 12 distributed sensors stream data over MQTT at 100ms intervals",
            "2. Local Processing: Python on Pi classifies anomalies in real time without cloud dependency",
            "3. Alert Engine: Telegram bot sends instant alerts with sensor readings on threshold breach",
        ],
    },
    {
        "name": "Robot Engineering & Hardware",
        "tag": "#ComputerVision #OpenCV #RoboticVision #AIHardware",
        "trigger": "Teaching a machine to see is harder than teaching it to think. Here's how we solved it.",
        "reveal": "We built a real-time object detection and classification pipeline running at 30fps on embedded hardware — no GPU required.",
        "identity": "For computer vision engineers and hardware enthusiasts: edge inference is the bridge between AI research and real-world deployment.",
        "provoking": "Have you worked on a computer vision project running directly on edge hardware without cloud inference?",
        "points": [
            "1. Model: Quantised YOLOv8 running INT8 inference on CPU — 30fps on Raspberry Pi 5",
            "2. Pipeline: OpenCV pre-processing + ONNX Runtime for optimised model execution",
            "3. Output: Bounding box overlays streamed live to a local dashboard at zero cloud cost",
        ],
    },
    {
        "name": "Robot Engineering & Hardware",
        "tag": "#IndustrialAutomation #PLCProgramming #SCADA #ManufacturingTech",
        "trigger": "Factories that haven't automated yet aren't just inefficient — they're already competing with machines and losing.",
        "reveal": "We integrated a PLC control system with real-time SCADA monitoring for a production line — reducing downtime by 67%.",
        "identity": "For industrial engineers and operations managers: the difference between a modern factory and an outdated one is software.",
        "provoking": "What percentage of your production floor operations are currently monitored and controlled automatically?",
        "points": [
            "1. PLC Layer: Ladder logic handles all machine-level control and safety interlocks",
            "2. SCADA Dashboard: Supervisory system visualises all process data in real time",
            "3. Predictive Alerts: ML model trained on vibration data predicts motor failure 48 hours early",
        ],
    },
    {
        "name": "Robot Engineering & Hardware",
        "tag": "#DroneEngineering #UAV #AutonomousSystems #RoboticsAI",
        "trigger": "A drone that follows GPS coordinates is a tool. A drone that understands its environment is a robot.",
        "reveal": "We built an autonomous inspection drone with on-board AI that detects structural defects in real time without a human operator.",
        "identity": "For aerospace engineers, robotics developers, and UAV enthusiasts: autonomous decision-making is the next leap in drone capability.",
        "provoking": "What industry do you think will be most transformed by widespread autonomous drone deployment in the next 5 years?",
        "points": [
            "1. Autonomy Stack: Custom flight controller runs local path planning with obstacle avoidance",
            "2. Vision AI: On-board model detects cracks, corrosion, and deformation at 95% accuracy",
            "3. Report Generation: Inspection results auto-compiled into a PDF report on landing",
        ],
    },
]


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "posted_hashes.json")
MAX_HISTORY = 200  # keep last N hashes; purge older ones to avoid unbounded growth


def _hash_post(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def load_posted_hashes() -> set:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_posted_hashes(hashes: set):
    # Keep only the last MAX_HISTORY hashes to prevent the file growing forever
    data = list(hashes)[-MAX_HISTORY:]
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[GeneratePost] Warning: could not save hash state: {e}")


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
    
    post_text = "\n".join(post_lines)
    # Automatically convert tone for company page
    post_text = post_text.replace("I ", "We ").replace(" my ", " our ").replace("I've ", "We've ").replace(" me.", " us.").replace("I'm ", "We're ").replace("I’ve ", "We’ve ").replace("I’m ", "We’re ").replace("My ", "Our ")
    
    return post_text

def generate_post():
    today = datetime.now(timezone.utc)

    posted_hashes = load_posted_hashes()

    # Shuffle all topics, pick first one whose text hash is not in posted set
    indices = list(range(len(CORE_TOPICS)))
    random.shuffle(indices)

    selected_topic = None
    selected_text = None
    selected_hash = None

    for idx in indices:
        topic_item = CORE_TOPICS[idx]
        post_text = build_trip_post(topic_item)
        h = _hash_post(post_text)
        if h not in posted_hashes:
            selected_topic = topic_item
            selected_text = post_text
            selected_hash = h
            break

    # All 30 posts already sent — reset and start fresh
    if selected_topic is None:
        print("[GeneratePost] All 30 post variants already posted. Resetting history.")
        posted_hashes = set()
        idx = random.randint(0, len(CORE_TOPICS) - 1)
        selected_topic = CORE_TOPICS[idx]
        selected_text = build_trip_post(selected_topic)
        selected_hash = _hash_post(selected_text)

    posted_hashes.add(selected_hash)
    save_posted_hashes(posted_hashes)
    print(f"[GeneratePost] Topic: {selected_topic['name']} | Hash: {selected_hash}")

    return {
        "template": "trip_framework",
        "topic": selected_topic["name"],
        "repo": selected_topic["name"],
        "score": 10.0,
        "post": selected_text,
        "timestamp": today.isoformat(),
    }




def post_to_linkedin(result):
    if not LINKEDIN_ACCESS_TOKEN:
        print("No LinkedIn access token configured. Skipping post.")
        return False

    try:
        api = LinkedInAPI(LINKEDIN_ACCESS_TOKEN)
        
        if LINKEDIN_ORG_URN:
            author_urn = LINKEDIN_ORG_URN
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
