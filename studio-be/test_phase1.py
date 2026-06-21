import asyncio
import os
import uuid
from services.scraper import scrape_url
from services.llm import generate_storyboard
from database import get_db_client

async def test_all():
    print("--- STARTING PHASE 1 TESTS ---")
    
    print("\n1. Testing Scraper (httpx + BeautifulSoup)...")
    text = await scrape_url("https://example.com")
    print(f"-> Successfully scraped {len(text)} characters.")
    
    print("\n2. Testing Gemini LLM (google-genai)...")
    try:
        storyboard = generate_storyboard(text)
        print("-> Success! Valid JSON Storyboard Generated.")
        print(f"-> Extracted Brand Name: {storyboard.get('brand_name')}")
        print(f"-> Generated Scenes: {len(storyboard.get('scenes', []))}")
    except Exception as e:
        print(f"-> LLM Error: {e}")
        return
        
    print("\n3. Testing Turso Database Update...")
    try:
        db = get_db_client()
        job_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO ads (id, tenant_id, status, video_url, current_progress) VALUES (?, ?, ?, ?, ?)",
            (job_id, "test-tenant", "TESTING", "", 0)
        )
        db.execute("UPDATE ads SET current_progress = 100, status = 'SUCCESS' WHERE id = ?", (job_id,))
        print("-> Database insert and update successful.")
    except Exception as e:
        print(f"-> DB Error: {e}")
        return
    
    print("\n✅ ALL PHASE 1 TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_all())
