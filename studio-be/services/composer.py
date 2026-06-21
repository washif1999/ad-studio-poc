import os
import httpx
import logging

logger = logging.getLogger(__name__)

CREATOMATE_API_KEY = os.getenv("CREATOMATE_API_KEY")

async def render_video_ad(completed_scenes: list, storyboard: dict) -> str:
    """
    Constructs a completely dynamic video composition JSON and sends it to Creatomate.
    Pro Approach: We build the video timeline programmatically here, so you don't 
    even have to manually build a template in the Creatomate dashboard.
    """
    if not CREATOMATE_API_KEY:
        logger.warning("CREATOMATE_API_KEY not set. Returning mock video URL.")
        return "https://creatomate.com/files/assets/demo.mp4"
        
    url = "https://api.creatomate.com/v1/renders"
    headers = {
        "Authorization": f"Bearer {CREATOMATE_API_KEY}",
        "Content-Type": "application/json"
    }

    track_elements = []
    primary_color = storyboard.get("primary_color", "#FFFFFF")
    
    for scene in completed_scenes:
        # 1. Format the ElevenLabs base64 audio into a valid Data URI for Creatomate
        audio_base64 = scene["voice_data"].get("audio_base64", "")
        audio_source = f"data:audio/mp3;base64,{audio_base64}" if audio_base64 else ""
        
        # 2. Build the scene composition
        # Creatomate automatically scales the duration of this composition based on the audio length!
        scene_group = {
            "type": "composition",
            "track": 1, # Placing on track 1 creates a sequential video timeline
            "elements": [
                {
                    "type": "image",
                    "source": scene["image_url"],
                    "animations": [{"type": "pan", "easing": "linear", "scope": "element"}],
                    "time": "start",
                    "duration": "100%"
                },
                {
                    "type": "audio",
                    "source": audio_source,
                    "time": "start"
                },
                {
                    "type": "text",
                    "text": scene["text_overlay"],
                    "fill_color": primary_color,
                    "font_weight": "800",
                    "y": "80%", # Lower third text
                    "animations": [
                        {"type": "text-slide-up", "duration": "0.5 s", "time": "start"},
                        {"type": "fade-out", "duration": "0.3 s", "time": "end"}
                    ]
                }
            ]
        }
        track_elements.append(scene_group)
        
    # Append the Call to Action as the final scene
    track_elements.append({
        "type": "composition",
        "track": 1,
        "duration": "3 s",
        "elements": [
            {"type": "solid", "fill_color": primary_color},
            {"type": "text", "text": storyboard.get("call_to_action", "Learn More"), "fill_color": "#000000", "font_weight": "900"}
        ]
    })
    
    # 3. Master Payload
    payload = {
        "source": {
            "output_format": "mp4",
            "width": 1920,
            "height": 1080,
            "frame_rate": 30,
            "elements": track_elements
        }
    }
    
    try:
        # Creatomate usually returns the response very fast with the render URL
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data[0].get("url", "")
    except Exception as e:
        logger.error(f"Creatomate render failed: {e}")
        return "https://creatomate.com/files/assets/fallback.mp4"
