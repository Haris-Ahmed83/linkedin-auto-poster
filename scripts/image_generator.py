import base64
import urllib.parse
import requests
from config import GEMINI_API_KEYS

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1216&height=832&model=flux&nologo=true&enhance=true"

def create_image_prompt(post_data):
    """
    Constructs an ultra-specific, high-converting visual prompt based on the post content.
    Ensures the image visually depicts the exact topic, code, or architecture discussed.
    """
    topic    = post_data.get("topic", post_data.get("repo", "Tech Innovation"))
    template = post_data.get("template", "trip")
    text     = post_data.get("post", "")

    # Extract key statements and hook from post text
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#")]
    hook_line = lines[0] if lines else topic
    summary_snippet = " ".join(lines[1:4])[:220]

    # Specialized visual mapping per core topic
    topic_visuals = {
        "GHL (GoHighLevel)": (
            "Split visual dashboard comparison for GoHighLevel GHL marketing automation: "
            "Left side: cluttered screen with broken integration red icons (Zapier, Mailchimp, Calendly). "
            "Right side: glowing green unified futuristic CRM workflow hub showing lead conversion funnels and auto-booking. "
            "Text overlay in elegant bold typography: 'GO HIGH LEVEL: ONE UNIFIED AUTOMATION STACK'."
        ),
        "AI Automations": (
            "Futuristic AI automation blueprint diagram: glowing neon nodes connecting LLM APIs, webhooks, auto-responders, and autonomous AI agents. "
            "Dark cyberpunk office setup with translucent glass screens showing python automation code and live data pipelines. "
            "Bold headline visual: 'AUTONOMOUS AI WORKFLOWS IN ACTION'."
        ),
        "CRMs & Sales Pipelines": (
            "Sleek modern CRM sales pipeline analytics matrix. Vibrant kanban columns moving leads automatically from Prospect to Closed Won. "
            "3D rendered floating glowing glass cards showing lead scoring, automated deal stage triggers, and revenue growth charts. "
            "Clean tech aesthetic with dark slate background and bright emerald-cyan lighting."
        ),
        "High-Converting Funnels": (
            "3D holographic funnel structure visualization: top wide section receiving organic multi-channel traffic, "
            "middle section processing automated lead lead magnet nurture sequences, bottom glowing spout outputting qualified sales bookings. "
            "Vibrant gradient lines, modern SaaS landing page UI elements hovering around the funnel."
        ),
        "Full-Stack Development": (
            "Modern full-stack developer workspace setup: high-end vertical monitors showing clean backend API code (Node.js/Python), "
            "frontend React/Next.js UI preview, database schema diagrams, and terminal logs. "
            "Atmospheric dark-mode room with subtle ambient neon lighting and glowing tech badges."
        ),
        "Robot Engineering & Hardware": (
            "High-tech robotics engineering studio: advanced robotic arm assembly integrated with microcontrollers, AI vision sensors, and circuit boards. "
            "Detailed CAD wireframe blueprint overlay combined with real hardware components, showing precision mechanical engineering and ROS code."
        ),
    }

    specific_visual = topic_visuals.get(topic)

    if specific_visual:
        prompt = (
            f"Ultra-professional dark-mode LinkedIn post banner image. {specific_visual} "
            f"Context: {summary_snippet}. "
            f"Style: Premium 4K resolution, sleek modern lighting, dark slate and neon accents, "
            f"no watermarks, photorealistic detail, highly engaging social media graphic."
        )
    else:
        prompt = (
            f"Sleek professional dark-mode LinkedIn graphic about '{topic}'. "
            f"Visual representation: {hook_line}. Context: {summary_snippet}. "
            f"Style: Dark tech aesthetic, vibrant indigo/cyan neon highlights, modern 3D glassmorphic UI elements, "
            f"ultra sharp 4K quality, no text watermarks, professional SaaS visual."
        )

    return prompt


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
