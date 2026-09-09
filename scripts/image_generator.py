import base64
import urllib.parse
import requests
from config import GEMINI_API_KEYS

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1216&height=832&model=flux&nologo=true&enhance=true"

def create_image_prompt(post_data):
    """
    Dynamically constructs a professional 4K image prompt strictly based on 
    the post text content, topic, and key points, excluding text artifacts.
    """
    topic = post_data.get("topic", post_data.get("repo", "Tech Innovation"))
    text  = post_data.get("post", "")

    # Clean text instruction to prevent blurred AI font gibberish
    no_text_suffix = ", no text, no words, no letters, no typography, clean visual illustration, 8k resolution, photorealistic studio render"

    if "ghl" in topic.lower() or "gohighlevel" in text.lower():
        prompt = (
            "Ultra-professional 3D marketing automation hub visual representation for GoHighLevel. "
            "Clean isometric glass CRM dashboard, glowing green workflow nodes, lead pipeline charts, dark navy slate aesthetic"
            + no_text_suffix
        )
    elif "ai" in topic.lower() or "automation" in text.lower():
        prompt = (
            "Futuristic 3D concept art of artificial intelligence workflow automation. "
            "Translucent glowing cyan and purple glass neural nodes, dark background, Unreal Engine 5 render, ray tracing"
            + no_text_suffix
        )
    elif "crm" in topic.lower() or "pipeline" in text.lower() or "sales" in text.lower():
        prompt = (
            "Modern 3D sales analytics dashboard mockup floating visual elements. "
            "Clean glassmorphism UI cards, glowing green growth trend chart, sleek deal pipeline columns, dark backdrop"
            + no_text_suffix
        )
    elif "funnel" in topic.lower() or "conversion" in text.lower():
        prompt = (
            "High-end 3D visual art of a glowing digital conversion funnel. "
            "Streams of golden light particles entering a sleek translucent funnel and transforming into green success badges"
            + no_text_suffix
        )
    elif "full-stack" in topic.lower() or "dev" in topic.lower() or "stack" in text.lower():
        prompt = (
            "Sleek 3D developer workspace aesthetic, holographic code structures floating over a futuristic glass desk setup, dark neon lighting"
            + no_text_suffix
        )
    elif "robot" in topic.lower() or "hardware" in topic.lower():
        prompt = (
            "Close-up detailed 3D render of a futuristic precision robotic arm assembly, carbon fiber joints, glowing micro-circuitry blueprints"
            + no_text_suffix
        )
    else:
        prompt = (
            f"Professional 3D isometric tech visual graphic representing '{topic}', sleek glassmorphism elements, dark slate background, glowing green accents"
            + no_text_suffix
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
