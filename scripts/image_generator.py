import base64
import time
import urllib.parse
import requests
from config import GEMINI_API_KEYS, HF_TOKEN


def create_image_prompt(post_data):
    """
    Dynamically constructs professional text-free 4K visual prompts
    tailored to the post topic and context.
    """
    topic = post_data.get("topic", post_data.get("repo", "Tech Innovation"))
    text  = post_data.get("post", "")

    no_text = (
        ", no text, no words, no letters, no captions, "
        "clean professional graphic, ultra-sharp 4K resolution, "
        "cinematic lighting, hyperrealistic studio render"
    )

    if "ghl" in topic.lower() or "gohighlevel" in topic.lower():
        prompt = (
            "Professional 3D glassmorphism marketing automation dashboard, "
            "glowing emerald green CRM workflow nodes connected by light streams, "
            "dark matte slate background, modern SaaS product aesthetic, "
            "depth of field bokeh, octane render"
            + no_text
        )
    elif "ai" in topic.lower() or "automation" in topic.lower():
        prompt = (
            "Futuristic 3D artificial intelligence neural network visualization, "
            "glowing cyan data nodes, holographic pipeline architecture, "
            "dark deep-space background, hyper-detailed octane render, "
            "blue and purple luminous accents"
            + no_text
        )
    elif "crm" in topic.lower() or "sales" in topic.lower() or "pipeline" in text.lower():
        prompt = (
            "Sleek 3D sales pipeline CRM dashboard visualization, "
            "glowing green funnel stages, animated deal progression bars, "
            "dark navy corporate background, premium SaaS UI aesthetic, "
            "professional business technology render"
            + no_text
        )
    elif "funnel" in topic.lower() or "conversion" in topic.lower():
        prompt = (
            "High-end 3D digital marketing funnel visualization, "
            "glowing golden light particles flowing downward, "
            "dark luxury navy corporate background, "
            "conversion optimization concept art, premium tech aesthetic"
            + no_text
        )
    elif "full-stack" in topic.lower() or "full stack" in topic.lower():
        prompt = (
            "Sleek ultrawide developer workspace 3D render, "
            "multiple monitors displaying glowing code architecture diagrams, "
            "ambient violet and blue neon lighting, "
            "premium mechanical keyboard, coffee mug, sharp focus depth of field"
            + no_text
        )
    elif "robot" in topic.lower() or "hardware" in topic.lower():
        prompt = (
            "Highly detailed 3D render of a futuristic robotic arm with carbon fibre joints, "
            "glowing micro-circuitry, dramatic studio lighting, "
            "AI vision sensor integration, industrial engineering aesthetic"
            + no_text
        )
    else:
        prompt = (
            f"Professional 3D isometric tech graphic for '{topic}', "
            "sleek glassmorphism elements, dark slate background, "
            "glowing green and cyan accents, premium corporate aesthetic"
            + no_text
        )

    return prompt


def _try_huggingface(prompt):
    """
    Generate HD image via HuggingFace Inference API.
    Tries multiple working models in order. Returns raw PNG bytes.
    """
    if not HF_TOKEN:
        print("[ImageGen] No HF_TOKEN configured, skipping HuggingFace.")
        return None

    # Models listed from fastest/most reliable to fallback
    models = [
        "black-forest-labs/FLUX.1-schnell",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "runwayml/stable-diffusion-v1-5",
    ]

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Accept": "image/png",
        "Content-Type": "application/json",
    }

    for model in models:
        # Try both the legacy and new router endpoints
        endpoints = [
            f"https://api-inference.huggingface.co/models/{model}",
            f"https://router.huggingface.co/hf-inference/models/{model}",
        ]
        for url in endpoints:
            try:
                print(f"[ImageGen] Trying HuggingFace: {model.split('/')[-1]}...")
                resp = requests.post(
                    url,
                    headers=headers,
                    json={"inputs": prompt, "parameters": {"width": 1024, "height": 576}},
                    timeout=120,
                )
                if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                    size_kb = len(resp.content) // 1024
                    print(f"[ImageGen] ✅ HuggingFace image generated! Size: {size_kb}KB")
                    return resp.content
                elif resp.status_code == 503:
                    # Model loading — wait and retry once
                    print(f"[ImageGen] HF model loading (503), waiting 20s...")
                    time.sleep(20)
                    resp2 = requests.post(url, headers=headers,
                                          json={"inputs": prompt, "parameters": {"width": 1024, "height": 576}},
                                          timeout=120)
                    if resp2.status_code == 200 and resp2.headers.get("content-type", "").startswith("image"):
                        size_kb = len(resp2.content) // 1024
                        print(f"[ImageGen] ✅ HuggingFace image generated after wait! Size: {size_kb}KB")
                        return resp2.content
                    print(f"[ImageGen] HF still unavailable: {resp2.status_code}")
                elif resp.status_code in [410, 404]:
                    print(f"[ImageGen] HF endpoint gone ({resp.status_code}), trying next endpoint...")
                    break  # endpoint gone, try next endpoint for this model
                else:
                    print(f"[ImageGen] HF returned: {resp.status_code} — {resp.text[:100]}")
            except Exception as e:
                print(f"[ImageGen] HF error: {e}")

    return None


def _try_gemini_keys(prompt):
    """Try all configured Gemini keys for image generation, skip on 429."""
    for api_key in GEMINI_API_KEYS:
        print(f"[ImageGen] Trying Gemini key (...{api_key[-4:]})...")
        models_resp = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=30
        )
        if models_resp.status_code != 200:
            continue

        models      = [m["name"] for m in models_resp.json().get("models", [])]
        image_model = next((m for m in models if "-image" in m and "lite" not in m), None) \
                   or next((m for m in models if "-image" in m), None)

        if not image_model:
            print("[ImageGen] No Gemini image model found.")
            continue

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
            print("[ImageGen] Gemini rate limit, trying next key...")
        else:
            print(f"[ImageGen] Gemini failed: {resp.status_code}")

    return None


def _try_pollinations(prompt):
    """Fallback: Pollinations.ai free image generation."""
    encoded = urllib.parse.quote(prompt, safe="")
    seed    = int(time.time()) % 99999
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=627&model=flux&nologo=true&enhance=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=627&model=flux&nologo=true&seed={seed}",
    ]
    for url in urls:
        try:
            print(f"[ImageGen] Trying Pollinations (seed={seed})...")
            resp = requests.get(url, timeout=90)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                size_kb = len(resp.content) // 1024
                print(f"[ImageGen] Pollinations returned {size_kb}KB")
                return resp.content  # take whatever size, it's the last fallback
        except Exception as e:
            print(f"[ImageGen] Pollinations error: {e}")
    return None


def generate_image_bytes(post_data):
    """
    Generate a professional HD image for a LinkedIn post.
    Priority: HuggingFace (HD, has token) → Gemini → Pollinations (fallback).
    Returns raw image bytes or None.
    """
    prompt = create_image_prompt(post_data)
    topic  = post_data.get("topic", post_data.get("repo", "post"))
    print(f"[ImageGen] Generating image for: '{topic}'")
    print(f"[ImageGen] Prompt: {prompt[:120]}...")

    # 1. HuggingFace — best quality, has token
    img = _try_huggingface(prompt)
    if img:
        return img

    # 2. Gemini — usually rate-limited on free tier
    img = _try_gemini_keys(prompt)
    if img:
        return img

    # 3. Pollinations — free fallback, smaller images
    img = _try_pollinations(prompt)
    if img:
        return img

    print("[ImageGen] ❌ All image providers failed — post will go text-only.")
    return None
