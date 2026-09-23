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
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.5-flash",
]

def _try_gemini_api_key(topic: str, text: str) -> bytes | None:
    """
    Generate an image via the official Gemini API using generateContent and
    Gemini's native image models. Works with normal API keys.
    Tries google-genai SDK first, then REST API, across all configured keys.
    Also falls back to imagen-3.0-generate-001 via predict API.
    """
    if not GEMINI_API_KEYS:
        print("[ImageGen] GEMINI_API_KEYS not configured - skipping Gemini API.")
        return None

    prompt = _build_image_prompt(topic, text)

    def failure_state(msg: str) -> str:
        if "denied access" in msg or "PERMISSION_DENIED" in msg or "403" in msg:
            return "denied"
        if "RESOURCE_EXHAUSTED" in msg or "Quota" in msg or "429" in msg:
            return "quota"
        return "other"

    denied: set = set()

    def pause_on_quota(msg: str):
        if failure_state(msg) == "quota":
            time.sleep(3)

    def _attempt() -> tuple[bytes | None, bool]:
        keys = list(GEMINI_API_KEYS)
        random.shuffle(keys)
        saw_quota = False

        # 1) Try standard Imagen 3 via predict (REST API)
        for key in keys:
            if key in denied:
                continue
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={key}"
            payload = {
                "instances": [{"prompt": prompt[:1000]}],
                "parameters": {"sampleCount": 1, "aspectRatio": "16:9"}
            }
            try:
                print(f"[ImageGen] Trying imagen-3.0-generate-001 via predict (key ...{key[-4:]})...")
                resp = requests.post(url, json=payload, timeout=90)
                if resp.status_code == 200:
                    data = resp.json()
                    if "predictions" in data and len(data["predictions"]) > 0:
                        img_b64 = data["predictions"][0].get("bytesBase64Encoded")
                        if img_b64:
                            img_bytes = base64.b64decode(img_b64)
                            print(f"[ImageGen] imagen-3.0 predict generated! Size: {len(img_bytes)//1024}KB")
                            return img_bytes, True
                elif resp.status_code == 403:
                    print(f"[ImageGen] predict (403, key skipped)")
                    denied.add(key)
                elif resp.status_code == 429:
                    saw_quota = True
                    print(f"[ImageGen] predict (429 quota)")
                    time.sleep(3)
                else:
                    print(f"[ImageGen] predict ({resp.status_code}): {resp.text[:150]}")
            except Exception as e:
                print(f"[ImageGen] predict error: {e}")

        # 2) google-genai SDK for gemini flash models
        try:
            from google import genai
            from google.genai import types
        except ImportError as ie:
            print(f"[ImageGen] google-genai not installed: {ie}")
        else:
            for key in keys:
                if key in denied:
                    continue
                for model in _GEMINI_IMAGE_MODELS:
                    try:
                        print(f"[ImageGen] Trying Gemini image model {model} via SDK (key ...{key[-4:]})...")
                        client = genai.Client(api_key=key)
                        result = client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_modalities=["TEXT", "IMAGE"],
                            ),
                        )
                        for part in result.candidates[0].content.parts:
                            if part.inline_data is not None and part.inline_data.data:
                                img_bytes = part.inline_data.data
                                print(f"[ImageGen] Gemini {model} SDK generated! Size: {len(img_bytes)//1024}KB")
                                return img_bytes, True
                    except Exception as sdk_e:
                        msg = str(sdk_e)[:200]
                        state = failure_state(msg)
                        if state == "denied":
                            print(f"[ImageGen] SDK error ({model}, key ...{key[-4:]}): {msg} (key skipped)")
                            denied.add(key)
                            break
                        if state == "quota":
                            saw_quota = True
                        pause_on_quota(msg)
                        print(f"[ImageGen] SDK error ({model}): {msg[:50]}...")

        # 3) REST API for gemini flash models
        for key in keys:
            if key in denied:
                continue
            for model in _GEMINI_IMAGE_MODELS:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models"
                    f"/{model}:generateContent?key={key}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
                }
                try:
                    print(f"[ImageGen] Trying Gemini image model {model} via REST (key ...{key[-4:]})...")
                    resp = requests.post(url, json=payload, timeout=90)
                    if resp.status_code == 200:
                        parts = resp.json()["candidates"][0]["content"]["parts"]
                        for part in parts:
                            inline = part.get("inlineData", {})
                            if inline.get("data"):
                                img_bytes = base64.b64decode(inline["data"])
                                print(f"[ImageGen] Gemini {model} REST generated! Size: {len(img_bytes)//1024}KB")
                                return img_bytes, True
                    elif resp.status_code == 403:
                        print(f"[ImageGen] REST {model} (403, key skipped)")
                        denied.add(key)
                        break
                    elif resp.status_code == 429:
                        saw_quota = True
                        print(f"[ImageGen] REST {model} (429 quota)")
                        time.sleep(3)
                    else:
                        print(f"[ImageGen] REST {model} ({resp.status_code}): {resp.text[:100]}...")
                except Exception as e:
                    print(f"[ImageGen] REST error ({model}): {e}")

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
