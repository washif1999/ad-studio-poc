import os
import asyncio
import logging
import uuid
import httpx
from PIL import Image, ImageDraw, ImageFont
import textwrap

logger = logging.getLogger(__name__)

# Output format -> (width, height)
FORMAT_DIMENSIONS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
}

AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "audio_cache")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")

def _download_image_to_local(image_url: str) -> str:
    """If the image_url is a local path (starts with BACKEND), return the file path. Otherwise, download it."""
    if image_url.startswith(BACKEND_BASE_URL):
        filename = image_url.split("/")[-1]
        return os.path.join(AUDIO_CACHE_DIR, filename)
    
    # Download remote image
    local_path = os.path.join(AUDIO_CACHE_DIR, f"dl_{uuid.uuid4().hex}.jpg")
    try:
        import requests
        r = requests.get(image_url, timeout=10)
        with open(local_path, "wb") as f:
            f.write(r.content)
        return local_path
    except Exception as e:
        logger.error(f"Failed to download image {image_url}: {e}")
        return ""

def _create_scene_image_with_text(image_path: str, text: str, width: int, height: int, is_cta: bool = False, primary_color: str = "#5e6ad2") -> str:
    """Uses PIL to resize image and draw centered text on it."""
    try:
        if is_cta:
            img = Image.new("RGB", (width, height), primary_color)
        else:
            img = Image.open(image_path).convert("RGBA")
            img_ratio = img.width / img.height
            target_ratio = width / height
            
            if img_ratio > target_ratio:
                new_width = int(target_ratio * img.height)
                offset = (img.width - new_width) // 2
                img = img.crop((offset, 0, offset + new_width, img.height))
            else:
                new_height = int(img.width / target_ratio)
                offset = (img.height - new_height) // 2
                img = img.crop((0, offset, img.width, offset + new_height))
                
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
        if text:
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            draw = ImageDraw.Draw(overlay)
            if not is_cta:
                draw.rectangle([(0, height//2), (width, height)], fill=(0,0,0,180))
            
            img = Image.alpha_composite(img.convert("RGBA"), overlay)
            draw = ImageDraw.Draw(img)
            
            try:
                # Need absolute path to a ttf if possible. Fallback will look ugly.
                font_path = "arial.ttf"
                if os.name == 'nt':
                    font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
                font = ImageFont.truetype(font_path, int(height * (0.06 if not is_cta else 0.10)))
            except IOError:
                font = ImageFont.load_default()
                
            lines = textwrap.wrap(text, width=35 if not is_cta else 20)
            
            # total height of text block
            line_heights = [draw.textbbox((0,0), line, font=font)[3] for line in lines]
            total_text_height = sum(line_heights) + len(lines)*10
            
            y_text = height * 0.7 if not is_cta else (height - total_text_height) / 2
                
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x_text = (width - line_width) / 2
                
                # Stroke
                stroke_width = 3
                for dx in range(-stroke_width, stroke_width+1):
                    for dy in range(-stroke_width, stroke_width+1):
                        draw.text((x_text+dx, y_text+dy), line, font=font, fill="black")
                        
                draw.text((x_text, y_text), line, font=font, fill="white")
                y_text += line_heights[0] + 10

        out_path = os.path.join(AUDIO_CACHE_DIR, f"comp_{uuid.uuid4().hex}.jpg")
        img.convert("RGB").save(out_path, quality=95)
        return out_path
    except Exception as e:
        logger.error(f"Failed to process image with PIL: {e}")
        return image_path

async def render_video_ad(
    completed_scenes: list,
    storyboard: dict,
    brand_kit: dict | None = None,
    output_format: str = "16:9",
) -> dict:
    # Import moviepy inside the function to ensure it doesn't break startup if missing
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    
    brand_kit = brand_kit or {}
    width, height = FORMAT_DIMENSIONS.get(output_format, (1920, 1080))
    primary_color = storyboard.get("primary_color", brand_kit.get("primary_color", "#5e6ad2"))
    
    clips = []
    
    for scene in completed_scenes:
        image_url = scene["image_url"]
        audio_url = scene.get("voice_data", {}).get("audio_url", "")
        text = scene["text_overlay"]
        
        local_img = _download_image_to_local(image_url)
        if not local_img:
            continue
            
        comp_img = _create_scene_image_with_text(local_img, text, width, height)
        
        audio_clip = None
        duration = scene.get("duration_seconds", 5.0)
        
        if audio_url:
            local_audio = _download_image_to_local(audio_url)
            if local_audio and os.path.exists(local_audio):
                try:
                    audio_clip = AudioFileClip(local_audio)
                    duration = max(audio_clip.duration, 3.0)
                except Exception as e:
                    logger.error(f"AudioFileClip error: {e}")
                    
        # Moviepy requires duration to be explicitly set for ImageClips
        img_clip = ImageClip(comp_img).with_duration(duration)
        if audio_clip:
            img_clip = img_clip.with_audio(audio_clip)
            
        clips.append(img_clip)
        
    # CTA clip
    cta_text = storyboard.get("call_to_action", "Learn More")
    cta_img = _create_scene_image_with_text("", cta_text, width, height, is_cta=True, primary_color=primary_color)
    cta_clip = ImageClip(cta_img).with_duration(3.0)
    clips.append(cta_clip)
    
    if not clips:
        return {"video_url": "https://placehold.co/1920x1080?text=No+Clips", "source": {}}
        
    try:
        final_video = concatenate_videoclips(clips, method="compose")
        out_filename = f"final_{uuid.uuid4().hex}.mp4"
        out_filepath = os.path.join(AUDIO_CACHE_DIR, out_filename)
        
        logger.info(f"Writing moviepy video to {out_filepath}...")
        # Write file. We use logger instead of terminal output
        final_video.write_videofile(out_filepath, fps=24, codec="libx264", audio_codec="aac", ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "faststart"], logger=None)
        
        video_url = f"{BACKEND_BASE_URL}/api/audio/{out_filename}"
        
        # To not break the frontend entirely, just pass an empty source
        return {"video_url": video_url, "source": None}
    except Exception as e:
        logger.error(f"Moviepy render failed: {e}")
        return {"video_url": "", "source": None}
