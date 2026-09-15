import asyncio
import base64
import json
import os
import random
import requests
from config import GEMINI_API_KEYS


# ─────────────────────────────────────────────────────────────
#  Prompt (user's exact verbatim prompt — always used for Gemini)
# ─────────────────────────────────────────────────────────────
def _build_prompt(topic: str, text: str = "") -> str:
    """
    Build the image generation prompt exactly as requested by the user.
    The user's custom prompt string is sent VERBATIM to Gemini — never
    replaced or rewritten by any other prompt.
    """
    body = (text or topic).strip()
    if len(body) > 1500:
        body = body[:1500]
    return (
        f"{body}\n\n"
        f"ma yh post linkdin pa post karna wala ho muja ek professional Atttractive is k lea image bana k do jo ma post kar sako\n"
        f"is text k sat images high class or attractive ho ma linkdin account pa connection zada karna chata ho is lea agr tuma muj sa kuch\n"
        f"require ho to poch lana"
    )


def _build_imagen_prompt(topic: str, text: str = "") -> str:
    """Same user verbatim prompt for Google Imagen 3 (both SDK and REST)."""
    return _build_prompt(topic, text)


# ─────────────────────────────────────────────────────────────
#  Method 1: Official Google Gemini API - Imagen 3
# ─────────────────────────────────────────────────────────────
def _try_gemini_api_key(topic: str, text: str) -> bytes | None:
    """
    Generate HD image via official Google Gemini API (Imagen 3).
    Tries google-genai SDK first, then falls back to REST API.
    """
    if not GEMINI_API_KEYS:
        print("[ImageGen] GEMINI_API_KEYS not configured - skipping Imagen 3.")
        return None

    imagen_prompt = _build_imagen_prompt(topic, text)
    keys = list(GEMINI_API_KEYS)
    random.shuffle(keys)

    # Try official google-genai SDK
    try:
        from google import genai
        from google.genai import types
        for key in keys:
            try:
                print(f"[ImageGen] Trying Imagen 3 via SDK (key ...{key[-4:]})...")
                client = genai.Client(api_key=key)
                result = client.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=imagen_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="16:9",
                        output_mime_type="image/jpeg",
                    ),
                )
                if result and hasattr(result, "generated_images") and result.generated_images:
                    img_bytes = result.generated_images[0].image.image_bytes
                    print(f"[ImageGen] Imagen 3 SDK generated! Size: {len(img_bytes)//1024}KB")
                    return img_bytes
            except Exception as sdk_e:
                print(f"[ImageGen] SDK error (key ...{key[-4:]}): {sdk_e}")
    except ImportError as ie:
        print(f"[ImageGen] google-genai not installed: {ie}")

    # Fallback: REST API endpoints
    models = [
        "imagen-3.0-generate-002",
        "imagen-3.0-generate-001",
        "imagen-3.0-fast-generate-001",
    ]
    for key in keys:
        for model in models:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models"
                f"/{model}:predict?key={key}"
            )
            payload = {
                "instances": [{"prompt": imagen_prompt}],
                "parameters": {"sampleCount": 1, "aspectRatio": "16:9"},
            }
            try:
                print(f"[ImageGen] Trying Imagen 3 REST {model} (key ...{key[-4:]})...")
                resp = requests.post(url, json=payload, timeout=60)
                if resp.status_code == 200:
                    predictions = resp.json().get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        img_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                        print(f"[ImageGen] Imagen 3 REST generated! Size: {len(img_bytes)//1024}KB")
                        return img_bytes
                else:
                    print(f"[ImageGen] REST {model} ({resp.status_code}): {resp.text[:200]}")
            except Exception as e:
                print(f"[ImageGen] REST error ({model}): {e}")

    return None


# ─────────────────────────────────────────────────────────────
#  Method 2: Gemini Web API - Cookie Session
# ─────────────────────────────────────────────────────────────
def _try_gemini_web(prompt: str) -> bytes | None:
    """
    Generate HD image via Gemini Web API using cookie authentication.
    Requires GEMINI_COOKIES secret with __Secure-1PSID and __Secure-1PSIDTS.
    """
    cookies_json = os.environ.get("GEMINI_COOKIES")
    if not cookies_json:
        print("[ImageGen] GEMINI_COOKIES not set - skipping Gemini Web API.")
        return None

    try:
        cookies = json.loads(cookies_json)
        psid   = cookies.get("__Secure-1PSID")
        psidts = cookies.get("__Secure-1PSIDTS")
        if not psid or not psidts:
            print("[ImageGen] GEMINI_COOKIES missing required fields.")
            return None
    except Exception as e:
        print(f"[ImageGen] Failed to parse GEMINI_COOKIES: {e}")
        return None

    async def _async_gen():
        try:
            from gemini_webapi import GeminiClient
        except ImportError:
            print("[ImageGen] gemini-webapi not installed.")
            return None

        try:
            client = GeminiClient(secure_1psid=psid, secure_1psidts=psidts)
            await client.init(timeout=30)
            chat = client.start_chat()
            response = await chat.send_message(prompt)

            if not response.images:
                print("[ImageGen] Gemini Web returned no images.")
                return None

            for img_obj in response.images:
                try:
                    dl = await img_obj.client.get(img_obj.url)
                    if dl.status_code == 200:
                        data = dl.content
                        # Force HD resolution for Google-hosted images
                        if "=s" not in img_obj.url:
                            hd_url = img_obj.url + "=s2048"
                            dl_hd = await img_obj.client.get(hd_url)
                            if dl_hd.status_code == 200:
                                data = dl_hd.content
                        print(f"[ImageGen] Gemini Web HD image: {len(data)//1024}KB")
                        return data
                except Exception as e:
                    print(f"[ImageGen] Image download error: {e}")
        except Exception as e:
            print(f"[ImageGen] Gemini Web session error: {e}")

        return None

    try:
        print("[ImageGen] Requesting image via Gemini Web API (cookie session)...")
        return asyncio.run(_async_gen())
    except Exception as e:
        print(f"[ImageGen] Gemini Web asyncio error: {e}")
        return None


# ─────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────
def generate_image_bytes(post_data: dict) -> bytes | None:
    """
    Generate an HD AI image for a LinkedIn post using Gemini ONLY.

    Priority:
      1. Official Google Gemini API - Imagen 3 (google-genai SDK then REST API)
      2. Gemini Web API - Cookie session (gemini-webapi library)

    NO Python/Pillow fallback.
    If both Gemini methods fail, post is published TEXT-ONLY.
    Every image is guaranteed to be AI-generated by Gemini.
    """
    topic = post_data.get("topic", post_data.get("repo", "Technology and AI"))
    text  = post_data.get("post",  post_data.get("text", ""))

    print(f"\n[ImageGen] Generating image for: '{topic}'")

    # 1. Official Gemini API (Imagen 3)
    img = _try_gemini_api_key(topic, text)
    if img:
        print(f"[ImageGen] Image ready - Gemini Imagen 3 ({len(img)//1024}KB)\n")
        return img

    # 2. Gemini Web API (cookie session)
    img = _try_gemini_web(_build_prompt(topic, text))
    if img:
        print(f"[ImageGen] Image ready - Gemini Web API ({len(img)//1024}KB)\n")
        return img

    # Both failed - text-only post. NO Pillow/Python card ever.
    print(
        "[ImageGen] Both Gemini sources failed. Post will be TEXT-ONLY.\n"
        "[ImageGen] Verify GEMINI_API_KEY and GEMINI_COOKIES in GitHub Secrets.\n"
    )
    return None
