from pydantic import BaseModel, Field
from typing import List

class VideoScene(BaseModel):
    scene_number: int = Field(..., description="The sequence number of the scene.")
    visual_image_prompt: str = Field(..., description="Detailed prompt for the AI image generator.")
    voiceover_script: str = Field(..., description="The script for the voiceover to read.")
    duration_seconds: float = Field(..., description="Duration of this scene in seconds.")
    text_overlay_headline: str = Field(..., description="Headline text to display on screen.")

class AdStoryboardSchema(BaseModel):
    brand_name: str = Field(..., description="The name of the brand.")
    primary_color: str = Field(..., description="The primary color of the brand in hex code format (e.g., #FFFFFF).")
    call_to_action: str = Field(..., description="The final call to action, e.g., 'Shop Now'.")
    scenes: List[VideoScene] = Field(..., description="List of video scenes for the ad storyboard.")

class AdGenerationRequest(BaseModel):
    url: str = Field(..., description="The target website URL to generate an ad for.")
    tenant_id: str = Field(default="demo-tenant", description="The workspace/tenant ID.")
