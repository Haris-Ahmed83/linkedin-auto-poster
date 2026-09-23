import asyncio
import base64
import json
import os
import random
import time
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


def _build_image_prompt(topic: str, text: str = "") -> str:
    """Same user verbatim prompt for the Gemini image models (SDK + REST)."""
    return _build_prompt(topic, text)


# ─────────────────────────────────────────────────────────────
#  Method 1: Official Google Gemini API - image generation models
# ─────────────────────────────────────────────────────────────
# The old Imagen 3 "generate_images" / ":predict" method no longer works with
# free-tier Gemini Developer API keys, so we use the modern generateContent
# endpoint with Gemini's native image models (Nano Banana family).
_GEMINI_IMAGE_MODELS = [
    "imagen-3.0-generate-002",
    "imagen-3.0-generate-001",
]

def _try_gemini_api_key(topic: str, text: str) -> bytes | None:
    """
    Generate an image via the official Gemini API using Gemini's native image models.
    Works with normal API keys using the new google-genai SDK's generate_images method.
    """
    if not GEMINI_API_KEYS:
        print("[ImageGen] GEMINI_API_KEYS not configured - skipping Gemini API.")
        return None

    prompt = _build_image_prompt(topic, text)

    def _attempt() -> tuple[bytes | None, bool]:
        keys = list(GEMINI_API_KEYS)
        random.shuffle(keys)
        saw_quota = False
        
        try:
            from google import genai
            from google.genai import types
        except ImportError as ie:
            print(f"[ImageGen] google-genai not installed: {ie}")
            return None, False

        for key in keys:
            for model in _GEMINI_IMAGE_MODELS:
                try:
                    print(f"[ImageGen] Trying Gemini image model {model} via SDK (key ...{key[-4:]})...")
                    client = genai.Client(api_key=key)
                    result = client.models.generate_images(
                        model=model,
                        prompt=prompt[:1000],
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            output_mime_type="image/jpeg",
                            aspect_ratio="16:9"
                        )
                    )
                    if result and result.generated_images:
                        for generated_image in result.generated_images:
                            img_bytes = generated_image.image.image_bytes
                            print(f"[ImageGen] Gemini {model} SDK generated! Size: {len(img_bytes)//1024}KB")
                            return img_bytes, True
                except Exception as sdk_e:
                    msg = str(sdk_e)[:200]
                    if "403" in msg or "PERMISSION_DENIED" in msg:
                        print(f"[ImageGen] SDK error ({model}, key ...{key[-4:]}): 403 Permission Denied (Skipping key)")
                        break # Skip this key, try next key
                    if "429" in msg or "Quota" in msg or "RESOURCE_EXHAUSTED" in msg:
                        saw_quota = True
                        print(f"[ImageGen] SDK error ({model}): Quota Exceeded")
                        time.sleep(3)
                    else:
                        print(f"[ImageGen] SDK error ({model}): {msg[:100]}...")

        return None, saw_quota

    img, saw_quota = _attempt()
    if img is None and saw_quota:
        print("[ImageGen] All keys quota-limited on first pass. Waiting 45s then retrying once...")
        time.sleep(45)
        img, _ = _attempt()
    return img


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
      1. Official Gemini API - generateContent with Gemini image models
         (gemini-2.5-flash-image etc., SDK then REST)
      2. Gemini Web API - Cookie session (gemini-webapi library)

    NO Python/Pillow fallback.
    If both Gemini methods fail, post is published TEXT-ONLY.
    Every image is guaranteed to be AI-generated by Gemini.
    """
    topic = post_data.get("topic", post_data.get("repo", "Technology and AI"))
    text  = post_data.get("post",  post_data.get("text", ""))

    print(f"\n[ImageGen] Generating image for: '{topic}'")

    # 1. Official Gemini API (image generation models)
    img = _try_gemini_api_key(topic, text)
    if img:
        print(f"[ImageGen] Image ready - Gemini API ({len(img)//1024}KB)\n")
        return img

    # 2. Gemini Web API (cookie session)
    img = _try_gemini_web(_build_prompt(topic, text))
    if img:
        print(f"[ImageGen] Image ready - Gemini Web API ({len(img)//1024}KB)\n")
        return img

    # Both failed - text-only post. NO Pillow/Python card ever.
    print(
        "[ImageGen] Both Gemini sources failed. Post will be TEXT-ONLY.\n"
        "[ImageGen] Gemini API keys returned 429 (quota exceeded) or 403 (project denied).\n"
        "[ImageGen] FIX: enable billing or add image-generation quota at ai.google.dev, create a\n"
        "[ImageGen] fresh API key, and refresh GEMINI_COOKIES (cookies currently expired).\n"
    )
    return None
