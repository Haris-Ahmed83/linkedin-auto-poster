import base64
import urllib.parse
import requests
from config import GEMINI_API_KEYS

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1216&height=832&model=flux&nologo=true&enhance=true"

def create_image_prompt(post_data):
    """
    Constructs ultra-clean, high-impact 3D visual prompts optimized for AI image generation.
    Focuses on photorealistic, high-end 3D art without distorted text artifacts.
    """
    topic = post_data.get("topic", post_data.get("repo", "Tech Innovation"))

    # Crisp, impressive 3D visual concepts tailored specifically to each topic
    topic_prompts = {
        "GHL (GoHighLevel)": (
            "Professional 3D isometric mockup of an all-in-one digital marketing automation hub. "
            "Glowing glass nodes connecting lead funnels, CRM dashboards, and automated messaging. "
            "Dark blue and emerald green ambient lighting, cinematic studio render, 8k resolution, photorealistic, trending on Polycount."
        ),
        "AI Automations": (
            "Futuristic 3D concept art of artificial intelligence neural network processing data streams. "
            "Translucent glowing cyan and purple glass nodes, sleek workflow automation pipelines, dark slate background, "
            "Unreal Engine 5 render, ray tracing, octave render, hyper detailed."
        ),
        "CRMs & Sales Pipelines": (
            "Modern 3D financial and sales CRM dashboard floating isometric cards. "
            "Clean glassmorphism UI, glowing green growth analytics chart, sleek deal pipeline columns, "
            "dark sleek backdrop, studio lighting, highly detailed 3D visualization."
        ),
        "High-Converting Funnels": (
            "High-end 3D visual art of a glowing digital conversion funnel. "
            "Streams of golden light particles entering a sleek translucent funnel and transforming into green success checkmarks. "
            "Dark executive navy background, 3D render, luxury corporate tech aesthetic."
        ),
        "Full-Stack Development": (
            "Sleek 3D developer workspace aesthetic. Holographic code structures floating over a futuristic glass desk setup, "
            "ultrawide monitor with clean glowing syntax code, subtle dark neon lighting, sharp focus, 8k photorealistic architecture."
        ),
        "Robot Engineering & Hardware": (
            "Close-up detailed 3D render of a futuristic precision robotic arm assembly. "
            "Carbon fiber joint components, glowing micro-circuitry, industrial cybernetic design, "
            "dramatic studio lighting, ultra-sharp detail, Octane Render."
        )
    }

    # Fallback for any other topic
    fallback = (
        f"Professional 3D isometric graphic representing '{topic}'. "
        "Sleek glassmorphism visual elements, futuristic dark mode tech aesthetic, "
        "vibrant glowing neon highlights, 8k resolution, cinematic lighting, ultra high quality."
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
