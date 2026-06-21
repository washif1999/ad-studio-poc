import os
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
FAL_API_KEY = os.getenv("FAL_API_KEY")

async def generate_voice(script: str) -> dict:
    """Generates voice audio and word-level timestamps using ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        logger.warning("ELEVENLABS_API_KEY not set. Returning mock voice.")
        return {"audio_base64": "mock_data", "timestamps": {"characters": [], "character_start_times_seconds": []}}

    # We use Rachel voice_id by default, and request timestamps for captions
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM/with-timestamps"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": script,
        "model_id": "eleven_monolingual_v1"
    }
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "audio_base64": data.get("audio_base64"),
                "timestamps": data.get("alignment")
            }
    except Exception as e:
        logger.error(f"ElevenLabs Voice generation failed: {e}")
        return {"error": str(e)}

async def generate_image(prompt: str) -> str:
    """Generates stunning ad imagery concurrently using Fal.ai (Flux Schnell)."""
    if not FAL_API_KEY:
        logger.warning("FAL_API_KEY not set. Returning mock image.")
        return "https://via.placeholder.com/1920x1080?text=Mock+Image"
        
    url = "https://queue.fal.run/fal-ai/flux/schnell"
    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "image_size": "landscape_16_9", 
        "num_inference_steps": 4 # Optimized for speed
    }
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("images", [{}])[0].get("url", "")
    except Exception as e:
        logger.error(f"Fal.ai Image generation failed: {e}")
        # Operational Safety Control: Automatic Fallback
        return "https://via.placeholder.com/1920x1080?text=Fallback+Image"

async def process_scene(scene: dict) -> dict:
    """Executes Voice and Image generation for a single scene simultaneously."""
    voice_coro = generate_voice(scene["voiceover_script"])
    image_coro = generate_image(scene["visual_image_prompt"])
    
    # Using asyncio.gather to run network requests in parallel
    voice_res, img_res = await asyncio.gather(voice_coro, image_coro)
    
    return {
        "scene_number": scene["scene_number"],
        "image_url": img_res,
        "voice_data": voice_res,
        "text_overlay": scene["text_overlay_headline"]
    }
