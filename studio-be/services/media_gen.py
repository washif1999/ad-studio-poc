import os
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

import edge_tts
import uuid

async def upload_to_tmpfiles(file_bytes: bytes, filename: str) -> str:
    """Uploads bytes to a free temporary host so Creatomate can download them via URL."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                'https://tmpfiles.org/api/v1/upload',
                files={'file': (filename, file_bytes)}
            )
            data = r.json()
            if data.get("status") == "success":
                url = data["data"]["url"]
                return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception as e:
        logger.error(f"Upload to tmpfiles failed: {e}")
    return ""

async def generate_voice(script: str) -> dict:
    """Generates voice audio using Microsoft Edge TTS (100% Free, High Quality)."""
    try:
        # We use a popular, natural-sounding free neural voice
        voice = "en-US-JennyNeural"
        communicate = edge_tts.Communicate(script, voice)
        
        temp_filename = f"temp_voice_{uuid.uuid4().hex}.mp3"
        await communicate.save(temp_filename)
        
        import base64
        with open(temp_filename, "rb") as f:
            audio_bytes = f.read()
            
        # Clean up temp file
        os.remove(temp_filename)
        
        audio_url = await upload_to_tmpfiles(audio_bytes, "voice.mp3")
        
        return {
            "audio_base64": audio_url,
            "timestamps": {"characters": [], "character_start_times_seconds": []}
        }
    except Exception as e:
        logger.error(f"Edge TTS Voice generation failed: {e}")
        return {"error": str(e)}

async def generate_image(prompt: str) -> str:
    """Generates stunning ad imagery concurrently using Hugging Face Serverless API."""
    if not HF_API_KEY:
        logger.warning("HF_API_KEY not set. Returning mock image.")
        return "https://via.placeholder.com/1920x1080?text=Mock+Image"
        
    url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 4
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Upload image to tmpfiles instead of returning huge base64
            image_url = await upload_to_tmpfiles(response.content, "image.jpg")
            return image_url
            
    except Exception as e:
        logger.error(f"Hugging Face Image generation failed: {e}")
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
