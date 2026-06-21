import os, asyncio
from dotenv import load_dotenv
load_dotenv()
import sys
sys.path.append('.')
from services.composer import render_video_ad
from services.media_gen import generate_image

async def run_test():
    try:
        print("Generating real image via HF...")
        image_b64 = await generate_image("A solid blue background")
        if not image_b64 or image_b64.startswith("http"):
            print("Failed to get HF image.")
            return
            
        print("Got image, size:", len(image_b64))
        scene = {
            "image_url": image_b64,
            "voice_data": {"audio_base64": ""},
            "text_overlay": "Test Scene"
        }
        print("Sending to Creatomate...")
        url = await render_video_ad([scene], {})
        print("Final URL:", url)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(run_test())
