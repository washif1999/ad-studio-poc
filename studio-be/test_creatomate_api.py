import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def run():
    CREATOMATE_API_KEY = os.getenv('CREATOMATE_API_KEY')
    url = 'https://api.creatomate.com/v1/renders'
    headers = {
        'Authorization': f'Bearer {CREATOMATE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Try empty audio source
    payload = {
        'source': {
            'output_format': 'mp4',
            'width': 1920,
            'height': 1080,
            'frame_rate': 30,
            'elements': [
                {
                    "type": "audio",
                    "source": "",
                    "time": "start"
                }
            ]
        }
    }
    async with httpx.AsyncClient() as c:
        r = await c.post(url, json=payload, headers=headers)
        print("Status:", r.status_code)
        print("Response:", r.text)

asyncio.run(run())
