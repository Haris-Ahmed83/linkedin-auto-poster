import os
import json
import base64
import requests
from config import GEMINI_API_KEY

IMAGEN_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"

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
    if not GEMINI_API_KEY:
        print("[ImageGen] GEMINI_API_KEY not configured. Skipping image generation.")
        return None

    prompt = create_image_prompt(post_data)
    print(f"[ImageGen] Generating image with Gemini Imagen API for '{post_data.get('repo', 'post')}'...")

    url = f"{IMAGEN_ENDPOINT}?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "outputMimeType": "image/jpeg"
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            predictions = data.get("predictions", [])
            if predictions and "bytesBase64Encoded" in predictions[0]:
                b64_str = predictions[0]["bytesBase64Encoded"]
                image_bytes = base64.b64decode(b64_str)
                print(f"[ImageGen] Image generated successfully! Size: {len(image_bytes)} bytes.")
                return image_bytes
            else:
                print(f"[ImageGen] Unexpected API response structure: {data}")
        else:
            print(f"[ImageGen] API call failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[ImageGen] Error during image generation: {e}")

    print("[ImageGen] Falling back to text-only post.")
    return None
