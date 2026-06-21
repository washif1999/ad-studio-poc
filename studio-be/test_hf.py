import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_huggingface():
    api_key = os.getenv("HF_API_KEY")
    if not api_key or api_key == "hf_your_api_key_here":
        print("❌ Error: Please update HF_API_KEY in your .env file first.")
        return

    url = "https://huggingface.co/api/whoami-v2"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        async with httpx.AsyncClient() as client:
            print("Testing Hugging Face connection...")
            # 1. Test Authentication
            whoami_res = await client.get(url, headers=headers)
            if whoami_res.status_code == 200:
                user_info = whoami_res.json()
                print(f"✅ Authentication successful! Logged in as: {user_info.get('name', 'Unknown')}")
            else:
                print(f"❌ Authentication failed (Status {whoami_res.status_code}): {whoami_res.text}")
                return

            # 2. Test the specific Image Generation Model (FLUX.1-schnell)
            print("\nTesting FLUX.1-schnell model access (this might take a few seconds)...")
            model_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
            payload = {"inputs": "A cute cat wearing sunglasses"}
            
            model_res = await client.post(model_url, json=payload, headers=headers, timeout=30.0)
            if model_res.status_code == 200:
                print("✅ Model access successful! Image generated.")
            elif model_res.status_code == 503:
                print("⚠️ Model is currently loading on Hugging Face servers. Try again in a minute.")
            else:
                print(f"❌ Model access failed (Status {model_res.status_code}): {model_res.text}")

            # 3. Test TTS Model (edge-tts)
            print("\nTesting TTS model access (edge-tts 'en-US-JennyNeural')...")
            import edge_tts
            import uuid
            
            communicate = edge_tts.Communicate("This is a voice generation test.", "en-US-JennyNeural")
            temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
            await communicate.save(temp_filename)
            
            if os.path.exists(temp_filename):
                print("✅ TTS access successful! Audio generated natively for free.")
                os.remove(temp_filename)
            else:
                print("❌ TTS access failed.")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_huggingface())
