import os
import json
from google import genai
from models import AdStoryboardSchema
from dotenv import load_dotenv

load_dotenv()

def generate_storyboard(scraped_text: str) -> dict:
    """Uses Gemini 2.5 Flash to quickly structure the scraped text into our Pydantic schema."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env")
        
    # We initialize the client efficiently
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert ad copywriter and creative director.
    Analyze the following website content and extract the brand details to create a highly engaging, 
    fast-paced video ad storyboard (15 to 30 seconds total).
    
    Keep voiceover scripts short and punchy.
    Ensure visual image prompts are highly descriptive for an AI image generator (like Midjourney/Flux).
    Output valid JSON matching the exact required schema.
    
    Website Content:
    {scraped_text}
    """
    
    # Gemini 2.5 Flash is selected for sub-2-second generation speeds and JSON adherence
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AdStoryboardSchema,
            "temperature": 0.7,
        }
    )
    
    try:
        return json.loads(response.text)
    except Exception as e:
        # Fallback if raw text isn't perfect JSON
        cleaned = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned)
