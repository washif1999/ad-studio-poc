import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

CREATOMATE_API_KEY = os.getenv("CREATOMATE_API_KEY")

async def test():
    url = "https://api.creatomate.com/v1/renders"
    headers = {
        "Authorization": f"Bearer {CREATOMATE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "source": {
            "output_format": "mp4",
            "width": 1920,
            "height": 1080,
            "frame_rate": 30,
            "elements": [
                {"type": "solid", "fill_color": "#FF0000"}
            ]
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print("Status:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    asyncio.run(test())
