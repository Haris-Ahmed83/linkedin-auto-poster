import base64
import urllib.parse
import requests
from config import GEMINI_API_KEYS, HF_TOKEN

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1216&height=832&model=flux&nologo=true&enhance=true"

def create_image_prompt(post_data):
    """
    Dynamically constructs professional text-free 4K visual prompts
    tailored to the post topic and context.
    """
    topic = post_data.get("topic", post_data.get("repo", "Tech Innovation"))
    text  = post_data.get("post", "")

    no_text = ", no text, no words, no letters, clean visual graphic design, ultra-sharp 8k resolution, photorealistic studio render"

    if "ghl" in topic.lower() or "gohighlevel" in text.lower():
        prompt = (
            "Professional 3D glassmorphism marketing automation hub graphic. "
            "Sleek glowing emerald green workflow nodes, dark slate background, modern SaaS UI visualization"
            + no_text
        )
    elif "ai" in topic.lower() or "automation" in text.lower():
        prompt = (
            "Futuristic 3D artificial intelligence neural network data pipeline visual. "
            "Translucent glowing cyan glass nodes, dark background, octane render, hyper detailed"
            + no_text
        )
    elif "crm" in topic.lower() or "pipeline" in text.lower() or "sales" in text.lower():
        prompt = (
            "Professional 3D glassmorphism tech dashboard visual, glowing green analytics graph, "
            "sleek dark blue slate background, minimalist modern SaaS vector graphic"
            + no_text
        )
    elif "funnel" in topic.lower() or "conversion" in text.lower():
        prompt = (
            "High-end 3D visual concept art of a glowing digital conversion funnel, "
            "golden light particles, dark navy corporate background, luxury tech aesthetic"
            + no_text
        )
    elif "full-stack" in topic.lower() or "dev" in topic.lower() or "stack" in text.lower():
        prompt = (
            "Sleek 3D developer desk workspace aesthetic, ultrawide monitor with glowing code interface structure, "
            "ambient violet neon lighting, sharp focus"
            + no_text
        )
    elif "robot" in topic.lower() or "hardware" in topic.lower():
        prompt = (
            "Detailed 3D render of a futuristic precision robotic arm assembly, carbon fiber joints, "
            "glowing micro-circuitry blueprints, dramatic studio lighting"
            + no_text
        )
    else:
        prompt = (
            f"Professional 3D isometric tech graphic representing '{topic}', sleek glassmorphism elements, dark slate background, glowing green accents"
            + no_text
        )

    return prompt


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

def _try_pollinations(prompt):
    """Reliable HD image via Pollinations.ai — forces fresh generation with unique seed."""
    import time
    encoded = urllib.parse.quote(prompt, safe="")
    seed = int(time.time()) % 99999  # unique seed each run forces fresh generation

    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?width=1920&height=1080&model=flux&nologo=true&enhance=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=627&model=flux&nologo=true&enhance=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=627&model=flux&nologo=true&seed={seed}",
    ]
    for url in urls:
        try:
            print(f"[ImageGen] Requesting Pollinations HD (seed={seed})...")
            resp = requests.get(url, timeout=90)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                size_kb = len(resp.content) // 1024
                print(f"[ImageGen] ✅ Image received! Size: {size_kb}KB")
                if size_kb < 50:
                    print(f"[ImageGen] ⚠️ Image too small ({size_kb}KB) — likely a cached thumbnail. Retrying...")
                    continue
                return resp.content
            else:
                print(f"[ImageGen] Pollinations returned: {resp.status_code}")
        except Exception as e:
            print(f"[ImageGen] Pollinations error: {e}")
    # Last resort: return whatever we got even if small
    try:
        resp = requests.get(urls[1], timeout=60)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            size_kb = len(resp.content) // 1024
            print(f"[ImageGen] ⚠️ Using best-effort image: {size_kb}KB")
            return resp.content
    except Exception:
        pass
    return None


def generate_image_bytes(post_data):
    """
    Generate image for a LinkedIn post.
    Returns raw image bytes or None.
    """
    prompt = create_image_prompt(post_data)
    print(f"[ImageGen] Generating image for topic: '{post_data.get('topic', post_data.get('repo', 'post'))}'")
    print(f"[ImageGen] Prompt: {prompt[:120]}...")

    img = _try_pollinations(prompt)
    if img:
        return img

    print("[ImageGen] ❌ Image generation failed — post will go text-only.")
    return None
