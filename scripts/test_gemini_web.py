import asyncio
import os
import json


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

    await client.init(timeout=30)

    prompt = "Create a photorealistic image of a modern office CRM dashboard with sales charts."
    print(f"\nPrompt: {prompt}")

    chat = client.start_chat()
    response = await chat.send_message(prompt)

    print(f"Images count: {len(response.images)}")

    for i, img in enumerate(response.images):
        print(f"Image {i} URL: {img.url[:80]}...")
        try:
            # Use the image's own authenticated session to download
            dl_response = await img.client.get(img.url)
            data = dl_response.content
            size_kb = len(data) // 1024
            print(f"✅ Downloaded via session! Size: {size_kb}KB")
            with open(f"gemini_out_{i}.jpg", "wb") as f:
                f.write(data)
            print(f"Saved to gemini_out_{i}.jpg")
        except Exception as e:
            # Try save() method as fallback
            print(f"Session download failed: {e}, trying img.save()...")
            try:
                await img.save(path=".", skip_invalid_images=False)
                print("Saved via img.save()")
            except Exception as e2:
                print(f"save() also failed: {e2}")


asyncio.run(test_image_gen())
