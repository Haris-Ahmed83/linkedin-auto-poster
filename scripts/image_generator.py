import base64
import urllib.parse
import requests
from config import GEMINI_API_KEYS

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1216&height=832&model=flux&nologo=true&enhance=true"

def create_image_prompt(post_data):
    """
    Dynamically constructs a professional 4K image prompt strictly based on 
    the post text content, topic, and key points.
    """
    topic = post_data.get("topic", post_data.get("repo", "Tech Innovation"))
    text  = post_data.get("post", "")

    # Extract non-empty lines excluding hashtags
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#")]
    hook  = lines[0] if lines else topic
    
    # Extract breakdown points from post text
    points = [l for l in lines if l.startswith(("1.", "2.", "3.", "-", "•", "👉"))]
    points_summary = " ".join(points[:3]) if points else " ".join(lines[1:4])[:200]

    # Map visual style dynamically based on post context & topic
    if "ghl" in topic.lower() or "gohighlevel" in text.lower():
        prompt = (
            f"Ultra-professional 4K LinkedIn infographic for GoHighLevel (GHL) automation. "
            f"Main Concept: {hook}. Key Points: {points_summary}. "
            f"Visual elements: Clean corporate vector infographic, high-contrast dashboard metrics, "
            f"glowing green conversion badges, dark blue and slate accents, crisp executive typography, photorealistic 8k studio render."
        )
    elif "ai" in topic.lower() or "automation" in text.lower():
        prompt = (
            f"Sleek professional 4K tech graphic about AI Automations. "
            f"Topic Context: {hook}. Core Details: {points_summary}. "
            f"Visual elements: Futuristic glowing neural nodes, clean workflow automation flowchart, "
            f"dark slate background with vibrant cyan and emerald lighting, high quality 3D glassmorphic SaaS illustration."
        )
    elif "crm" in topic.lower() or "pipeline" in text.lower() or "sales" in text.lower():
        prompt = (
            f"Professional 4K sales analytics graphic for LinkedIn. "
            f"Headline Concept: {hook}. Focus: {points_summary}. "
            f"Visual elements: Modern CRM deal pipeline cards, green revenue growth charts, "
            f"sleek analytics dashboard UI, dark executive slate aesthetic, ultra sharp 4K render."
        )
    elif "funnel" in topic.lower() or "conversion" in text.lower():
        prompt = (
            f"High-impact 4K marketing funnel visual graphic for LinkedIn. "
            f"Main Theme: {hook}. Highlights: {points_summary}. "
            f"Visual elements: Glowing digital conversion funnel, golden light streams, high-converting landing page UI mockup, "
            f"luxury corporate dark navy background, clean vector graphics."
        )
    elif "full-stack" in topic.lower() or "dev" in topic.lower() or "stack" in text.lower():
        prompt = (
            f"Professional 4K developer tech architecture banner for LinkedIn. "
            f"Main Topic: {hook}. Tech Stack: {points_summary}. "
            f"Visual elements: Ultra-clean full-stack architecture diagram, modern dark IDE syntax window, "
            f"minimalist developer workspace setup, glowing cyan and violet lighting, crisp 8k render."
        )
    elif "robot" in topic.lower() or "hardware" in topic.lower():
        prompt = (
            f"High-tech 4K engineering graphic for LinkedIn. "
            f"Core Topic: {hook}. Hardware Specs: {points_summary}. "
            f"Visual elements: Detailed 3D robotic arm vision assembly, glowing micro-circuitry blueprints, "
            f"dramatic studio lighting, ultra-sharp cybernetic engineering art."
        )
    else:
        prompt = (
            f"Ultra-professional 4K corporate tech graphic for LinkedIn about '{topic}'. "
            f"Main Headline: {hook}. Context: {points_summary}. "
            f"Visual style: High contrast vector infographic, dark mode SaaS design, glowing green accents, 8k resolution, crisp photorealistic quality."
        )

    return prompt


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
