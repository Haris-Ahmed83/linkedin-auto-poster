import base64
import urllib.parse
import requests
from config import GEMINI_API_KEYS

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1216&height=832&model=flux&nologo=true&enhance=true"

def create_image_prompt(post_data):
    """
    Constructs an optimized visual prompt based on post context.
    """
    repo     = post_data.get("repo", "Software Project")
    template = post_data.get("template", "tech")
    text     = post_data.get("post", "")

    lines          = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#")]
    context_snippet = " ".join(lines[:3])[:200]

    template_styles = {
        "how_i_built":       "developer workspace, code on screen, building something",
        "hot_take":          "bold statement, tech debate, futuristic contrast",
        "lesson_learned":    "journey, growth, lessons, turning point",
        "data_numbers":      "data visualization, charts, analytics dashboard",
        "progress_journey":  "progress bar, milestone, journey forward",
        "news":              "breaking tech news, AI, innovation, digital world",
    }
    style_hint = template_styles.get(template, "tech innovation")

    # Special case for GHL
    if "ghl" in repo.lower() or "gohighlevel" in text.lower() or "GoHighLevel" in text:
        return (
            "Ultra-professional dark-mode LinkedIn banner about GoHighLevel GHL marketing automation. "
            "Split design: LEFT side shows chaos with multiple disconnected app icons floating in red-orange tones, "
            "RIGHT side shows a single clean unified CRM dashboard in glowing emerald green neon. "
            "Bold white headline: ONE PLATFORM ZERO CHAOS. "
            "Dark background, indigo and emerald neon glow accents, futuristic premium SaaS aesthetic, "
            "4K ultra sharp, no text watermarks, professional agency visual."
        )

    prompt = (
        f"Sleek professional dark-mode tech LinkedIn post banner about '{repo}'. "
        f"Theme: {style_hint}. Context: {context_snippet}. "
        f"Style: dark futuristic background, vibrant indigo and emerald neon glow, "
        f"minimalist developer aesthetic, ultra sharp 4K, no watermarks, premium quality."
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
