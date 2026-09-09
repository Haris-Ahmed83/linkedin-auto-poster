import asyncio
import os
import json
from gemini_webapi import GeminiClient

cookies_json = os.environ.get("GEMINI_COOKIES")

async def test_image_gen():
    if not cookies_json:
        print("No cookies provided.")
        return
        
    cookies = json.loads(cookies_json)
    client = GeminiClient(cookies)
    
    try:
        await client.init(timeout=30)
        chat = client.start_chat()
        print("Sending request for image...")
        resp = await chat.send_message("Generate an image of a futuristic CRM dashboard.")
        print("Response received.")
        print(f"Text: {resp.text}")
        print(f"Images: {resp.images}")
        
        # Print all attributes to inspect
        print(dir(resp))
        for img in getattr(resp, 'images', []):
            print(f"Image dict/object: {img}")
            
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_image_gen())
