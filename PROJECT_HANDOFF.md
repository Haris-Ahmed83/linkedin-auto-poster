# LinkedIn Auto Poster — Complete Project Handoff

## Project Overview
**GitHub Repo:** `Haris-Ahmed83/linkedin-auto-poster`  
**Local Path:** `e:\New projects\Linkdin Auto posting`  
**Language:** Python 3.11  
**Purpose:** Fully automated LinkedIn posting system — generates post text + professional image and posts to LinkedIn automatically via GitHub Actions. No human needed after setup.

---

## How the System Works (End-to-End Flow)

```
GitHub Actions (cron schedule)
        ↓
generate_post.py  →  picks 1 of 30 topic variants (hash-dedup prevents repeats)
        ↓
image_generator.py  →  generates professional image (Gemini Web → Pillow fallback → Pollinations)
        ↓
linkedin_api.py  →  uploads image + posts text to LinkedIn
        ↓
posted_hashes.json  →  hash of posted text saved → git commit → pushed to repo
```

---

## Posting Schedule

| Day | Time (PKT) | UTC Cron |
|-----|-----------|----------|
| Mon, Wed, Fri | 9:00 AM | `0 4 * * 1,3,5` |
| Tue, Thu, Sat | 10:00 AM | `0 5 * * 2,4,6` |
| Sunday | No post | — |

---

## File Structure

```
e:\New projects\Linkdin Auto posting\
├── scripts\
│   ├── generate_post.py      ← MAIN: picks topic, builds post text, calls image gen + linkedin
│   ├── image_generator.py    ← generates professional HD image for the post
│   ├── linkedin_api.py       ← LinkedIn API wrapper (post + image upload)
│   ├── config.py             ← all env var reading (secrets)
│   ├── posted_hashes.json    ← tracks MD5 hashes of all sent posts (prevents duplicates)
│   ├── templates.py          ← old template system (not used for main posts)
│   ├── github_fetcher.py     ← old GitHub repo fetcher (not used for main posts)
│   └── news_fetcher.py       ← old news fetcher (not used for main posts)
├── .github\workflows\
│   ├── linkedin-post.yml     ← MAIN workflow: runs on schedule + manual
│   └── test_gemini.yml       ← test workflow for debugging image gen
├── requirements.txt
└── .gitignore
```

---

## Core Logic: generate_post.py

### Duplicate Prevention System
- **Old (broken):** Tracked topic INDEX numbers — reset after 6 — same post repeated
- **New (working):** Tracks MD5 hash of actual post text in `posted_hashes.json`
- Same TOPIC can repeat, but exact same POST TEXT can never be sent twice
- After all 30 variants posted — auto-resets and starts fresh

### 30 Topic Variants (6 pillars x 5 angles each)

| Pillar | Count |
|--------|-------|
| GHL / GoHighLevel | 5 unique posts |
| AI Automations | 5 unique posts |
| CRMs & Sales Pipelines | 5 unique posts |
| High-Converting Funnels | 5 unique posts |
| Full-Stack Development | 5 unique posts |
| Robot Engineering & Hardware | 5 unique posts |
| **Total** | **30 unique posts = ~5 months content** |

### Post Format (TRIP Framework)
Every post follows:
- **T** — Triggering Hook (attention-grabbing first line)
- **R** — Reveal (solution / technical breakdown with numbered points)
- **I** — Identity (speaks directly to target audience)
- **P** — Provoking Question (engagement CTA)
- Ends with hashtags

---

## Image Generation System: image_generator.py

### Priority Waterfall
1. **Gemini Web API** (primary) — AI-generated photo-realistic image
   - Uses `GEMINI_COOKIES` secret (JSON with `__Secure-1PSID` and `__Secure-1PSIDTS`)
   - Library: `gemini-webapi`
   - Forces HD: appends `=s2048` to Google CDN URLs
2. **Pillow HD Card** (fallback 1) — 1200x627 premium dark-mode branded card
   - Instant, no API needed, always works
   - Glassmorphism design, gradient background, Inter font, topic-specific colors
   - 6 color themes: GHL (green), AI (purple), CRM (teal), Funnel (gold), Full-Stack (blue), Robotics (orange)
3. **Pollinations.ai** (fallback 2) — last resort free AI image

### Image Prompt
The Gemini prompt uses 100% exact user words:
The prompt sends the full post text + asks for a "professional Attractive" LinkedIn image that will increase connections.

---

## GitHub Secrets Required

| Secret Name | Description |
|------------|-------------|
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn OAuth token |
| `LINKEDIN_REFRESH_TOKEN` | LinkedIn refresh token |
| `LINKEDIN_USER_URN` | LinkedIn user URN (urn:li:person:xxx) |
| `LINKEDIN_CLIENT_ID` | LinkedIn app client ID |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app client secret |
| `GEMINI_API_KEY` | Gemini API key 1 |
| `GEMINI_API_KEY_2` | Gemini API key 2 |
| `GEMINI_API_KEY_3` | Gemini API key 3 |
| `GEMINI_API_KEY_4` | Gemini API key 4 |
| `GEMINI_COOKIES_TEST` | JSON with Gemini web cookies for image gen |
| `HF_TOKEN` | HuggingFace token (fallback image gen) |
| `GH_TOKEN` | GitHub personal access token |

### GEMINI_COOKIES_TEST format:
```json
{
  "__Secure-1PSID": "...",
  "__Secure-1PSIDTS": "..."
}
```

---

## GitHub Actions Workflow: linkedin-post.yml

Key features:
- `permissions: contents: write` — allows bot to commit `posted_hashes.json` back to repo
- `actions/checkout@v4` with `GITHUB_TOKEN` — authenticated checkout for push
- After posting: commits updated `posted_hashes.json` with `[skip ci]` tag (prevents loop)
- Manual trigger: `workflow_dispatch` with `dry_run` option

---

## Known Issues & Current Status

### Working
- Post text generation (30 unique TRIP-format posts)
- LinkedIn posting via API
- Pillow HD card image (instant fallback, always works)
- Duplicate post prevention via MD5 hash
- State persistence via git commit after each post

### Needs Monitoring
- **Gemini Web image gen:** Works when GEMINI_COOKIES are fresh. Cookies expire periodically — update `GEMINI_COOKIES_TEST` secret when images stop generating.
- **LinkedIn token:** Access token expires. If posts stop, check `LINKEDIN_ACCESS_TOKEN` secret.

### How to Update Gemini Cookies
1. Go to gemini.google.com in browser
2. Open DevTools → Application → Cookies
3. Copy `__Secure-1PSID` and `__Secure-1PSIDTS` values
4. Update `GEMINI_COOKIES_TEST` secret in GitHub repo settings

---

## requirements.txt
```
requests>=2.31.0
python-dotenv>=1.0.0
Pillow>=10.0.0
gemini-webapi>=2.1.1
```

---

## How to Test Manually

### Dry Run (generate post, don't actually post to LinkedIn)
GitHub repo → Actions → "LinkedIn Auto Poster" → Run workflow → Set `dry_run = true`

### Full Test Run
Run workflow with `dry_run = false`

---

## Owner Info
- **GitHub Username:** Haris-Ahmed83
- **LinkedIn:** linkedin.com/in/harisahmed
- **Brand name on images:** "Haris Ahmed"
- **Target audience:** Agency owners, SaaS founders, developers, engineers

---

## What the User (Haris) Wants
1. Fully automated — no daily manual work
2. Professional, high-quality images with each post
3. Posts about: GHL, AI Automation, CRM, Funnels, Full-Stack Dev, Robotics
4. LinkedIn connections growth via consistent professional content
5. No duplicate posts ever — same post should never appear twice
6. Topics CAN repeat but post text must always be unique

---

## Next Possible Improvements (Future Work)
- Add more topic angles to extend content library beyond 30
- Auto-refresh LinkedIn token before expiry
- Add webhook notification (Telegram/Email) when post succeeds or fails
- Track LinkedIn engagement metrics (likes, comments) via API

---

---
---

# NEW CONVERSATION STARTER PROMPT
# (Copy everything below this line and paste into new chat)

---

## PASTE THIS IN NEW CHAT:

```
Mera ek LinkedIn Auto Poster project hai jis par hum kaam kar rahe hain. 
Yeh project fully automated hai — GitHub Actions cron job se automatically LinkedIn par posts karta hai.

PROJECT DETAILS:
- GitHub Repo: Haris-Ahmed83/linkedin-auto-poster
- Local Path: e:\New projects\Linkdin Auto posting
- Language: Python 3.11
- OS: Windows

HOW IT WORKS:
1. GitHub Actions cron (Mon/Wed/Fri 9AM PKT, Tue/Thu/Sat 10AM PKT) triggers linkedin-post.yml
2. generate_post.py runs — picks 1 of 30 TRIP-framework posts (6 topics x 5 angles each)
3. image_generator.py generates image: Gemini Web API (primary) → Pillow HD card (fallback) → Pollinations (last resort)
4. linkedin_api.py posts text + image to LinkedIn
5. posted_hashes.json updated with MD5 hash of sent post → committed back to repo (prevents duplicates)

TOPICS (6 pillars, 5 variants each = 30 unique posts):
- GHL / GoHighLevel
- AI Automations  
- CRMs & Sales Pipelines
- High-Converting Funnels
- Full-Stack Development
- Robot Engineering & Hardware

KEY FILES:
- scripts/generate_post.py — main logic, CORE_TOPICS list, hash-based dedup
- scripts/image_generator.py — image generation (Pillow card primary fallback, Gemini Web preferred)
- scripts/linkedin_api.py — LinkedIn API
- scripts/config.py — env vars
- scripts/posted_hashes.json — tracks sent post hashes (prevents duplicates)
- .github/workflows/linkedin-post.yml — main GitHub Actions workflow

GITHUB SECRETS SET:
LINKEDIN_ACCESS_TOKEN, LINKEDIN_REFRESH_TOKEN, LINKEDIN_USER_URN, LINKEDIN_CLIENT_ID,
LINKEDIN_CLIENT_SECRET, GEMINI_API_KEY (x4), GEMINI_COOKIES_TEST (Gemini web cookies JSON),
HF_TOKEN, GH_TOKEN

IMAGE GENERATION:
- Primary: Gemini Web API using gemini-webapi library + GEMINI_COOKIES_TEST secret
  (cookies JSON: {"__Secure-1PSID": "...", "__Secure-1PSIDTS": "..."})
- Fallback: Pillow 1200x627 dark glassmorphism branded card (instant, always works)
- Last resort: Pollinations.ai

WHAT IS WORKING:
- Post generation and LinkedIn posting works
- Pillow fallback image always works  
- Hash-based duplicate prevention works
- State persisted via git commit to repo after each post
- 30 unique posts = ~5 months of content

WHAT MAY NEED ATTENTION:
- Gemini cookies expire → update GEMINI_COOKIES_TEST secret with fresh cookies from gemini.google.com
- LinkedIn access token expires → update LINKEDIN_ACCESS_TOKEN secret

USER REQUIREMENTS:
- Haris (the owner) wants fully automated system, no manual work
- High-quality professional images per post
- LinkedIn connections growth through consistent posting
- Topics can repeat but EXACT SAME POST TEXT must never be posted twice
- Posts in TRIP framework format (Trigger, Reveal, Identity, Provoking Question)

Ab mujhe batao kya karna hai ya koi problem hai jise fix karna hai.
```
