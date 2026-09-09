import asyncio
import base64
import io
import json
import os
import time
import textwrap
import urllib.parse
import urllib.request
import requests
from config import GEMINI_API_KEYS, HF_TOKEN




# ─────────────────────────────────────────────────────────────
#  Topic → visual style map
# ─────────────────────────────────────────────────────────────
TOPIC_STYLES = {
    "ghl": {
        "bg_top":   (8, 20, 35),
        "bg_bot":   (5, 45, 25),
        "accent":   (0, 220, 100),
        "bar":      (0, 180, 80),
        "label":    "GO HIGH LEVEL",
        "icon":     "⚡",
    },
    "ai": {
        "bg_top":   (10, 5, 30),
        "bg_bot":   (20, 10, 60),
        "accent":   (139, 92, 246),
        "bar":      (99, 60, 220),
        "label":    "AI AUTOMATIONS",
        "icon":     "🤖",
    },
    "crm": {
        "bg_top":   (5, 18, 40),
        "bg_bot":   (5, 35, 25),
        "accent":   (34, 197, 94),
        "bar":      (16, 160, 70),
        "label":    "CRM & SALES",
        "icon":     "📈",
    },
    "funnel": {
        "bg_top":   (20, 10, 5),
        "bg_bot":   (40, 20, 5),
        "accent":   (251, 191, 36),
        "bar":      (200, 150, 20),
        "label":    "FUNNELS",
        "icon":     "🎯",
    },
    "full": {
        "bg_top":   (5, 10, 30),
        "bg_bot":   (15, 5, 40),
        "accent":   (56, 189, 248),
        "bar":      (30, 140, 200),
        "label":    "FULL-STACK DEV",
        "icon":     "💻",
    },
    "robot": {
        "bg_top":   (10, 10, 10),
        "bg_bot":   (5, 25, 35),
        "accent":   (249, 115, 22),
        "bar":      (200, 80, 10),
        "label":    "ROBOTICS",
        "icon":     "🦾",
    },
}


def _pick_style(topic: str) -> dict:
    t = topic.lower()
    if "ghl" in t or "gohigh" in t:
        return TOPIC_STYLES["ghl"]
    if "ai" in t or "automat" in t:
        return TOPIC_STYLES["ai"]
    if "crm" in t or "sales" in t or "pipeline" in t:
        return TOPIC_STYLES["crm"]
    if "funnel" in t or "convers" in t:
        return TOPIC_STYLES["funnel"]
    if "full" in t or "stack" in t:
        return TOPIC_STYLES["full"]
    if "robot" in t or "hardware" in t:
        return TOPIC_STYLES["robot"]
    return TOPIC_STYLES["ai"]   # default


def _get_font(url: str, size: int):
    """Download a TTF font and return a PIL ImageFont, fall back to default."""
    try:
        from PIL import ImageFont
        data = urllib.request.urlopen(url, timeout=10).read()
        return ImageFont.truetype(io.BytesIO(data), size)
    except Exception:
        from PIL import ImageFont
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────
#  Primary: Pillow HD card generator
# ─────────────────────────────────────────────────────────────
def _try_pillow_card(post_data: dict) -> bytes | None:
    """
    Generates a premium 1200×627 dark-mode text-card image using Pillow.
    No API calls required — instant, always works, always HD.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[ImageGen] Pillow not installed, skipping card generator.")
        return None

    topic = post_data.get("topic", post_data.get("repo", "Technology"))
    text  = post_data.get("post", post_data.get("text", ""))

    # ── Pick the hook line (first non-empty line) ──────────────
    hook = ""
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            hook = line
            break
    if not hook:
        hook = topic

    # ── Strip emoji from hook for cleaner card rendering ──────
    import re
    hook_clean = re.sub(r'[^\x00-\x7F]+', '', hook).strip(" :-.")
    if len(hook_clean) < 8:
        hook_clean = hook  # keep original if stripping removes too much

    style  = _pick_style(topic)
    W, H   = 1200, 627

    # ── Canvas + vertical gradient ─────────────────────────────
    img  = Image.new("RGB", (W, H), style["bg_top"])
    draw = ImageDraw.Draw(img, "RGBA")

    for y in range(H):
        r_ratio = y / H
        r = int(style["bg_top"][0] + (style["bg_bot"][0] - style["bg_top"][0]) * r_ratio)
        g = int(style["bg_top"][1] + (style["bg_bot"][1] - style["bg_top"][1]) * r_ratio)
        b = int(style["bg_top"][2] + (style["bg_bot"][2] - style["bg_top"][2]) * r_ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # ── Glassmorphism card ─────────────────────────────────────
    card_x1, card_y1, card_x2, card_y2 = 60, 60, W - 60, H - 60
    glass_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glass_draw    = ImageDraw.Draw(glass_overlay)
    glass_draw.rounded_rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        radius=24,
        fill=(255, 255, 255, 12),
        outline=(*style["accent"], 60),
        width=1,
    )
    img.paste(Image.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), glass_overlay), mask=glass_overlay.split()[3])

    # ── Accent top bar ─────────────────────────────────────────
    bar_y = card_y1 + 2
    draw.rounded_rectangle(
        [card_x1 + 2, bar_y, card_x1 + 2 + 200, bar_y + 5],
        radius=3,
        fill=style["bar"],
    )

    # ── Decorative circles (background depth) ─────────────────
    for cx, cy, cr, alpha in [
        (W - 120, 100, 200, 18),
        (150, H - 100, 150, 12),
        (W // 2, H // 2, 80, 8),
    ]:
        circle_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        circle_draw    = ImageDraw.Draw(circle_overlay)
        circle_draw.ellipse(
            [cx - cr, cy - cr, cx + cr, cy + cr],
            fill=(*style["accent"], alpha),
        )
        img.paste(Image.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), circle_overlay), mask=circle_overlay.split()[3])

    # ── Fonts ──────────────────────────────────────────────────
    INTER_BOLD = "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Bold.ttf"
    INTER_REG  = "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Regular.ttf"
    INTER_MED  = "https://github.com/google/fonts/raw/main/ofl/inter/static/Inter-Medium.ttf"

    font_label  = _get_font(INTER_MED, 22)
    font_hook   = _get_font(INTER_BOLD, 62)
    font_sub    = _get_font(INTER_REG, 28)
    font_brand  = _get_font(INTER_MED, 24)

    # ── Label (topic pill) ─────────────────────────────────────
    label_text = style["label"]
    label_x, label_y = card_x1 + 40, card_y1 + 34
    lw = draw.textlength(label_text, font=font_label) if hasattr(draw, 'textlength') else 140
    pill_pad = 14
    draw.rounded_rectangle(
        [label_x - pill_pad, label_y - 6, label_x + lw + pill_pad, label_y + 30],
        radius=20,
        fill=(*style["accent"], 30),
        outline=(*style["accent"], 120),
        width=1,
    )
    draw.text((label_x, label_y), label_text, font=font_label, fill=(*style["accent"], 230))

    # ── Hook text (auto-wrapped) ───────────────────────────────
    max_chars = 38
    lines = textwrap.wrap(hook_clean, width=max_chars)[:3]  # max 3 lines
    hook_y = card_y1 + 110
    line_h = 80
    for line in lines:
        draw.text((card_x1 + 40, hook_y), line, font=font_hook, fill=(245, 248, 255))
        hook_y += line_h

    # ── Accent divider ─────────────────────────────────────────
    div_y = hook_y + 20
    draw.line([(card_x1 + 40, div_y), (card_x1 + 240, div_y)], fill=style["accent"], width=3)

    # ── Sub-label ─────────────────────────────────────────────
    draw.text(
        (card_x1 + 40, div_y + 20),
        "Insight for Builders & Operators",
        font=font_sub,
        fill=(180, 190, 210),
    )

    # ── Author branding bottom-right ───────────────────────────
    brand = "Haris Ahmed  -  linkedin.com/in/harisahmed"
    brand_w = draw.textlength(brand, font=font_brand) if hasattr(draw, 'textlength') else 240
    draw.text(
        (card_x2 - brand_w - 20, card_y2 - 38),
        brand,
        font=font_brand,
        fill=(140, 160, 190),
    )

    # ── Accent dot cluster bottom-right ───────────────────────
    for i in range(3):
        dot_x = card_x2 - 60 - i * 20
        draw.ellipse([dot_x, card_y1 + 30, dot_x + 8, card_y1 + 38], fill=(*style["accent"], 160 - i * 40))

    # ── Render to bytes ───────────────────────────────────────
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=95, optimize=True)
    size_kb = buf.tell() // 1024
    print(f"[ImageGen] ✅ Pillow card generated! Size: {size_kb}KB (1200×627, {topic})")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────
#  Primary: Gemini Web API Image Generation (via cookie session)
# ─────────────────────────────────────────────────────────────
def _try_gemini_image(prompt: str) -> bytes | None:
    """
    Generate HD image via Gemini Web API using cookie authentication.
    """
    cookies_json = os.environ.get("GEMINI_COOKIES")
    if not cookies_json:
        print("[ImageGen] GEMINI_COOKIES env var not set — skipping Gemini Web.")
        return None

    try:
        cookies = json.loads(cookies_json)
        psid = cookies.get("__Secure-1PSID")
        psidts = cookies.get("__Secure-1PSIDTS")
        if not psid or not psidts:
            print("[ImageGen] Missing __Secure-1PSID or __Secure-1PSIDTS in GEMINI_COOKIES.")
            return None
    except Exception as e:
        print(f"[ImageGen] Failed to parse GEMINI_COOKIES: {e}")
        return None

    async def _async_gen():
        from gemini_webapi import GeminiClient
        client = GeminiClient(secure_1psid=psid, secure_1psidts=psidts)
        await client.init(timeout=30)
        chat = client.start_chat()
        response = await chat.send_message(prompt)
        if not response.images:
            print("[ImageGen] Gemini Web returned no images.")
            return None
        for img in response.images:
            try:
                dl = await img.client.get(img.url)
                data = dl.content
                size_kb = len(data) // 1024
                print(f"[ImageGen] ✅ Gemini Web image generated! Size: {size_kb}KB")
                return data
            except Exception as e:
                print(f"[ImageGen] Failed to download Gemini Web image: {e}")
        return None

    try:
        print("[ImageGen] Trying Gemini Web API image gen...")
        return asyncio.run(_async_gen())
    except Exception as e:
        print(f"[ImageGen] Gemini Web error: {e}")
        return None



# ─────────────────────────────────────────────────────────────
#  Fallback 1: Pillow branded card (instant, no API)
# ─────────────────────────────────────────────────────────────
def _try_pollinations(prompt):
    """Last-resort fallback: Pollinations.ai free image generation."""
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
                return resp.content
        except Exception as e:
            print(f"[ImageGen] Pollinations error: {e}")
    return None


# ─────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────
def generate_image_bytes(post_data):
    """
    Generate a professional HD image for a LinkedIn post.
    Priority:
      1. Gemini 2.0 Flash  — AI-generated photo-realistic images (preferred)
      2. Pillow HD card     — instant branded fallback, no API needed
      3. Pollinations       — last resort
    """
    topic  = post_data.get("topic", post_data.get("repo", "post"))
    text   = post_data.get("post", post_data.get("text", ""))
    prompt = _build_prompt(topic, text)

    print(f"[ImageGen] Generating image for: '{topic}'")
    print(f"[ImageGen] Prompt: {prompt[:120]}...")

    # 1. Gemini — primary, photo-realistic AI images
    img = _try_gemini_image(prompt)
    if img:
        return img

    # 2. Pillow card — instant fallback (if Gemini rate-limited)
    print("[ImageGen] Gemini unavailable, falling back to Pillow card...")
    img = _try_pillow_card(post_data)
    if img:
        return img

    # 3. Pollinations — last resort
    img = _try_pollinations(prompt)
    if img:
        return img

    print("[ImageGen] ❌ All image providers failed — post will go text-only.")
    return None


def _build_prompt(topic: str, text: str = "") -> str:
    """Build a rich Gemini image generation prompt from topic and post text."""
    # Extract hook line for context
    hook = ""
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            hook = line[:120]
            break

    style = _pick_style(topic)
    label = style["label"]

    base = (
        f"Professional LinkedIn post image about {label}. "
        f"Photorealistic office or tech environment scene. "
        f"The visual should relate to: {hook or topic}. "
        "High-end corporate aesthetic, cinematic lighting, 4K quality. "
        "No overlaid text, no words, clean composition."
    )
    return base
