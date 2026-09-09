import os
import base64
import requests
from config import GEMINI_API_KEYS

# Use Gemini 2.0 Flash image generation (generateContent with responseModalities)
GEMINI_IMAGE_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent"

def create_image_prompt(post_data):
    """
    Constructs an optimized visual prompt for Gemini Imagen based on post context.
    """
    repo = post_data.get("repo", "Software Project")
    template = post_data.get("template", "tech")
    text = post_data.get("post", "")
    
    # Extract first few lines for context
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#")]
    context_snippet = " ".join(lines[:3])[:200]
    
    prompt = (
        f"A sleek, modern, professional dark-mode tech infographic banner for a LinkedIn post about '{repo}'. "
        f"Concept: {context_snippet}. "
        f"Style: Dark futuristic theme, vibrant indigo and emerald neon glow accents, minimalist developer aesthetic, "
        f"high resolution, 4k, ultra clean composition, professional software engineering graphic."
    )
    return prompt

def generate_image_bytes(post_data):
    """
    Calls Gemini API to generate an image based on post context.
    Returns raw JPEG bytes or None if key is missing or request fails.
    """
    if not GEMINI_API_KEYS:
        print("[ImageGen] No GEMINI_API_KEYS configured. Skipping image generation.")
        return None

    prompt = create_image_prompt(post_data)
    print(f"[ImageGen] Generating image with Gemini Imagen API for '{post_data.get('repo', 'post')}'...")

    for api_key in GEMINI_API_KEYS:
        print(f"[ImageGen] Trying key (ends with {api_key[-4:] if len(api_key)>4 else '***'})...")
        models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            models_resp = requests.get(models_url, timeout=30)
            if models_resp.status_code == 200:
                models_data = models_resp.json()
                available_models = [m["name"] for m in models_data.get("models", [])]
                
                # Find a Gemini image model
                imagen_model = next((m for m in available_models if "-image" in m and "lite" not in m), None)
                if not imagen_model:
                    imagen_model = next((m for m in available_models if "-image" in m), None)
                
                if imagen_model:
                    print(f"[ImageGen] Found Image model: {imagen_model}")
                    url = f"https://generativelanguage.googleapis.com/v1beta/{imagen_model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseModalities": ["IMAGE"]}
                    }
                    
                    resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        for candidate in candidates:
                            for part in candidate.get("content", {}).get("parts", []):
                                if "inlineData" in part:
                                    b64_str = part["inlineData"]["data"]
                                    image_bytes = base64.b64decode(b64_str)
                                    print(f"[ImageGen] Image generated successfully! Size: {len(image_bytes)} bytes.")
                                    return image_bytes
                        print(f"[ImageGen] No image found in response: {data}")
                    else:
                        print(f"[ImageGen] API call failed with status {resp.status_code}: {resp.text}")
                        if resp.status_code == 429:
                            print("[ImageGen] Rate limit hit. Trying next key if available...")
                            continue # Try next key
                else:
                    print("[ImageGen] No image model found in available models.")
            else:
                print(f"[ImageGen] Failed to list models: {models_resp.status_code} {models_resp.text}")
                if models_resp.status_code == 429:
                    continue # Try next key
        except Exception as e:
            print(f"[ImageGen] Error finding or using model: {e}")

    print("[ImageGen] Exhausted all keys. Falling back to text-only post.")
    return None
