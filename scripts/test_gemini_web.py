import asyncio
import os
import json
import urllib.request

async def test_image_gen():
    from gemini_webapi import GeminiClient

    cookies_json = os.environ.get("GEMINI_COOKIES")
    if not cookies_json:
        print("No cookies provided.")
        return

    cookies = json.loads(cookies_json)
    print(f"Using 1PSID: ...{cookies['__Secure-1PSID'][-20:]}")

    client = GeminiClient(
        secure_1psid=cookies["__Secure-1PSID"],
        secure_1psidts=cookies["__Secure-1PSIDTS"],
    )

    await client.init(timeout=30, verbose=True)

    # Try multiple prompts that are known to trigger Imagen in Gemini web
    prompts = [
        "Create a photorealistic image of a modern office CRM dashboard with sales charts.",
        "Generate an image: professional business team in a meeting room with tech screens.",
        "Draw a high-quality 4K image of a futuristic tech workspace with glowing blue screens.",
    ]

    for prompt in prompts:
        print(f"\n--- Trying prompt: {prompt[:60]}...")
        try:
            chat = client.start_chat()
            response = await chat.send_message(prompt)
            print(f"Text response: {response.text[:200]}")
            print(f"Images count: {len(response.images)}")
            for i, img in enumerate(response.images):
                print(f"  Image {i}: {img}")
                # Try to get URL from image object
                url = getattr(img, 'url', None) or getattr(img, 'src', None) or str(img)
                print(f"  URL: {url}")
                if url and url.startswith('http'):
                    data = urllib.request.urlopen(url, timeout=20).read()
                    size_kb = len(data) // 1024
                    print(f"  ✅ Downloaded! Size: {size_kb}KB")
                    with open(f"test_gemini_out_{i}.jpg", "wb") as f:
                        f.write(data)
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
        await asyncio.sleep(3)

asyncio.run(test_image_gen())
