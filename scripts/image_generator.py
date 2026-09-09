import base64
import urllib.parse
import requests
from config import GEMINI_API_KEYS

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1216&height=832&model=flux&nologo=true&enhance=true"

def create_image_prompt(post_data):
    """
    Constructs detailed, high-converting Before/After Infographic visual prompts
    matching top-performing LinkedIn business case study graphics.
    """
    topic = post_data.get("topic", post_data.get("repo", "Tech Automation"))

    topic_prompts = {
        "GHL (GoHighLevel)": (
            "High-converting 2D business infographic comparison banner for LinkedIn. "
            "Top banner title: 'FROM 40% NO-SHOWS TO 8% IN THREE WEEKS'. "
            "Split screen: LEFT section labeled 'BEFORE' with red accent background showing high no-show appointment rate, broken calendar icons, and lost revenue. "
            "RIGHT section labeled 'AFTER' with vibrant green accent background showing GoHighLevel automated SMS and email reminders, green calendar checkmarks, and 90% show-up rate. "
            "Bottom bar text: 'THE FIX: AUTOMATED REMINDERS IN GOHIGHLEVEL'. Clean vector infographics, high contrast typography, flat modern design."
        ),
        "AI Automations": (
            "High-converting 2D business infographic comparison banner for LinkedIn. "
            "Top headline: 'MANUAL DATA ENTRY VS 100% AI AUTOMATION WORKFLOW'. "
            "Split visual design: LEFT side labeled 'MANUAL PROCESS (20 HOURS/WEEK)' showing slow manual copy-pasting and human error icons. "
            "RIGHT side labeled 'AI AUTOMATED (INSTANT)' showing automated Python LLM pipeline, instant API webhooks, green checkmarks. "
            "Bottom bar text: 'RESULT: 95% TIME SAVED WITH AI AGENTS'. Professional crisp vector graphic, clean typography."
        ),
        "CRMs & Sales Pipelines": (
            "High-converting 2D business infographic visual for LinkedIn. "
            "Top headline: 'LEAKY PIPELINE VS HIGH-CONVERTING AUTOMATED CRM'. "
            "LEFT section: 'UNORGANIZED SPREADSHEETS' with red warning icons, forgotten leads, cold leads. "
            "RIGHT section: 'AUTOMATED CRM PIPELINE' with green kanban deal stages (Prospect -> Demo -> Deal Won), instant notifications. "
            "Bottom bar text: 'THE FIX: AUTOMATED CRM FOLLOW-UP TRIPPERS'. Clean modern corporate vector infographics."
        ),
        "High-Converting Funnels": (
            "High-converting 2D digital funnel comparison infographic banner for LinkedIn. "
            "Top headline: 'LOW CONVERTING WEBSITE VS HIGH-CONVERTING FUNNEL'. "
            "LEFT side: 'GENERIC WEBSITE (1% CONVERSION)' with distracting links, slow load time, lost visitors. "
            "RIGHT side: 'HIGH-CONVERTING FUNNEL (12% CONVERSION)' with clear single CTA, sub-second speed, glowing green conversion graph. "
            "Bottom bar text: 'THE FIX: OPTIMIZED 1-CLICK FUNNEL ARCHITECTURE'. Flat vector design, bold typography."
        ),
        "Full-Stack Development": (
            "High-converting 2D architecture comparison infographic banner for LinkedIn. "
            "Top headline: 'MONOLITH BLOAT VS CLEAN FULL-STACK ARCHITECTURE'. "
            "LEFT side: 'OVER-ENGINEERED MONOLITH' showing broken dependencies, high server costs, crash alerts. "
            "RIGHT side: 'MODERN FULL-STACK (NEXT.JS + PYTHON REST API)' showing fast serverless deployments, sub-100ms response time, green uptime badge. "
            "Bottom bar text: 'THE FIX: MINIMALIST SCALABLE STACK'. Modern vector graphic."
        ),
        "Robot Engineering & Hardware": (
            "High-converting 2D engineering comparison infographic banner for LinkedIn. "
            "Top headline: 'MANUAL ASSEMBLY VS AI VISION ROBOTIC AUTOMATION'. "
            "LEFT side: 'MANUAL INSPECTION' showing high cycle times, human fatigue, defect risk. "
            "RIGHT side: 'AI VISION ROBOTIC ARM' showing microsecond camera tracking, 99.9% precision, green quality badge. "
            "Bottom bar text: 'THE FIX: EDGE COMPUTING & ROBOTIC VISION'. Crisp vector blueprint graphic."
        )
    }

    fallback = (
        f"High-converting 2D business infographic comparison banner for LinkedIn about '{topic}'. "
        "Top headline, split comparison view with red Before side and green After side, "
        "clean vector icons, high contrast text blocks, modern corporate visual design."
    )

    return topic_prompts.get(topic, fallback)


def _try_pollinations(prompt):
    """Free image generation via Pollinations.ai — no API key needed."""
    try:
        encoded = urllib.parse.quote(prompt, safe="")
        url     = POLLINATIONS_URL.format(prompt=encoded)
        print(f"[ImageGen] Trying Pollinations.ai (free)...")
        resp    = requests.get(url, timeout=60)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            print(f"[ImageGen] ✅ Pollinations image generated! Size: {len(resp.content)//1024}KB")
            return resp.content
        else:
            print(f"[ImageGen] Pollinations failed: {resp.status_code}")
    except Exception as e:
        print(f"[ImageGen] Pollinations error: {e}")
    return None


def _try_gemini_keys(prompt):
    """Try all configured Gemini keys, skip on 429."""
    for api_key in GEMINI_API_KEYS:
        print(f"[ImageGen] Trying Gemini key (ends ...{api_key[-4:]})...")
        # Find model
        models_resp = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=30
        )
        if models_resp.status_code != 200:
            print(f"[ImageGen] Model list failed: {models_resp.status_code}")
            continue

        models      = [m["name"] for m in models_resp.json().get("models", [])]
        image_model = next((m for m in models if "-image" in m and "lite" not in m), None) \
                   or next((m for m in models if "-image" in m), None)

        if not image_model:
            print("[ImageGen] No image model found.")
            continue

        print(f"[ImageGen] Found model: {image_model}")
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/{image_model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["IMAGE"]}
            },
            timeout=60
        )

        if resp.status_code == 200:
            for candidate in resp.json().get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        img = base64.b64decode(part["inlineData"]["data"])
                        print(f"[ImageGen] ✅ Gemini image generated! Size: {len(img)//1024}KB")
                        return img
            print("[ImageGen] No image in Gemini response.")
        elif resp.status_code == 429:
            print("[ImageGen] Rate limit hit, trying next key...")
            continue
        else:
            print(f"[ImageGen] Gemini failed: {resp.status_code}")

    return None


def generate_image_bytes(post_data):
    """
    Generate image for a LinkedIn post.
    Strategy: Try Gemini keys first, fallback to Pollinations.ai (free).
    Returns raw image bytes or None.
    """
    prompt = create_image_prompt(post_data)
    print(f"[ImageGen] Generating image for '{post_data.get('repo', 'post')}'...")

    # 1. Try Gemini (if keys available)
    if GEMINI_API_KEYS:
        img = _try_gemini_keys(prompt)
        if img:
            return img

    # 2. Free fallback: Pollinations.ai
    img = _try_pollinations(prompt)
    if img:
        return img

    print("[ImageGen] All methods failed. Falling back to text-only post.")
    return None
