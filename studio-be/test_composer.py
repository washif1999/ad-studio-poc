import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

from services.composer import render_video_ad

async def run():
    completed_scenes = [
        {
            "image_url": "https://via.placeholder.com/1920x1080?text=Mock+Image",
            "voice_data": {"audio_base64": "mock_data"},
            "text_overlay": "Hello Scene 1"
        }
    ]
    storyboard = {
        "primary_color": "#FFFFFF",
        "call_to_action": "Buy Now"
    }
    
    url = await render_video_ad(completed_scenes, storyboard)
    print("Final Video URL:", url)

asyncio.run(run())
