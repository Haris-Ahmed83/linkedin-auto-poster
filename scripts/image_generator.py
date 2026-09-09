import os
import base64
import requests
from config import GEMINI_API_KEY

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
    if not GEMINI_API_KEY:
        print("[ImageGen] GEMINI_API_KEY not configured. Skipping image generation.")
        return None

    # First, list available models to find the correct image generation model
    prompt = create_image_prompt(post_data)
    print(f"[ImageGen] Generating image with Gemini Imagen API for '{post_data.get('repo', 'post')}'...")
    
    models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        models_resp = requests.get(models_url, timeout=30)
        if models_resp.status_code == 200:
            models_data = models_resp.json()
            available_models = [m["name"] for m in models_data.get("models", [])]
            print(f"[ImageGen] Available models: {available_models}")
            
            # Find an imagen model
            imagen_model = next((m for m in available_models if "imagen" in m and "generate" in m), None)
            
            if imagen_model:
                print(f"[ImageGen] Found Imagen model: {imagen_model}")
                url = f"https://generativelanguage.googleapis.com/v1beta/{imagen_model}:predict?key={GEMINI_API_KEY}"
                payload = {
                    "instances": [{"prompt": prompt}],
                    "parameters": {"sampleCount": 1, "aspectRatio": "1:1", "outputMimeType": "image/jpeg"}
                }
                
                resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    predictions = data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        b64_str = predictions[0]["bytesBase64Encoded"]
                        image_bytes = base64.b64decode(b64_str)
                        print(f"[ImageGen] Image generated successfully! Size: {len(image_bytes)} bytes.")
                        return image_bytes
                else:
                    print(f"[ImageGen] Imagen API call failed with status {resp.status_code}: {resp.text}")
            else:
                print("[ImageGen] No 'imagen' model found in available models.")
        else:
            print(f"[ImageGen] Failed to list models: {models_resp.status_code} {models_resp.text}")
    except Exception as e:
        print(f"[ImageGen] Error finding or using model: {e}")

    print("[ImageGen] Falling back to text-only post.")
    return None
