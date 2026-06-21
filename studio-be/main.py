import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, Request
from sse_starlette.sse import EventSourceResponse
from models import AdGenerationRequest
from database import get_db_client
from services.scraper import scrape_url
from services.llm import generate_storyboard
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Studio BE API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active progress per job ID locally to stream via SSE
# In production, this can come straight from Turso, but memory dict is faster for SSE
progress_streams = {}

async def generate_ad_pipeline(job_id: str, url: str):
    """The core asynchronous pipeline running in the background."""
    db = get_db_client()
    
    def update_progress(progress: int, status: str):
        # Update local stream dict for SSE
        progress_streams[job_id] = {"progress": progress, "status": status}
        # Update Turso DB to persist state
        db.execute("UPDATE ads SET current_progress = ?, status = ? WHERE id = ?", (progress, status, job_id))

    try:
        # Step 1: Scrape & Extract
        update_progress(15, "[15%] Scraping Website...")
        scraped_text = await scrape_url(url)
        
        # Step 2: LLM Structuring
        update_progress(40, "[40%] Writing Script & Storyboard...")
        # Since LLM call is synchronous, we run it in a thread to not block the async event loop
        storyboard = await asyncio.to_thread(generate_storyboard, scraped_text)
        
        # Step 3: Concurrent Media Generation (Phase 2)
        update_progress(70, "[70%] Generating Voice & Media Assets...")
        from services.media_gen import process_scene
        
        # Spin up parallel tasks for EVERY scene at the exact same time
        scene_tasks = [process_scene(scene) for scene in storyboard.get("scenes", [])]
        completed_scenes = await asyncio.gather(*scene_tasks)
        
        # Phase 3 Composition will map 'completed_scenes' into Creatomate
        update_progress(85, "[85%] Compositing Video Render...")
        from services.composer import render_video_ad
        
        # Sort scenes to ensure correct timeline order
        completed_scenes.sort(key=lambda x: x["scene_number"])
        
        final_video_url = await render_video_ad(completed_scenes, storyboard)
        
        # Save the final video URL back to the Turso DB state
        db.execute("UPDATE ads SET video_url = ? WHERE id = ?", (final_video_url, job_id))
        
        # For now, mark as complete and send the URL back to the frontend
        update_progress(100, f"SUCCESS|{final_video_url}")
        
    except Exception as e:
        update_progress(0, f"FAILED: {str(e)}")


@app.post("/api/ads")
async def create_ad(req: AdGenerationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    # Initialize DB row
    db = get_db_client()
    db.execute(
        "INSERT INTO ads (id, tenant_id, status, video_url, current_progress) VALUES (?, ?, ?, ?, ?)",
        (job_id, req.tenant_id, "QUEUED", "", 0)
    )
    
    # Initialize SSE progress
    progress_streams[job_id] = {"progress": 0, "status": "QUEUED"}
    
    # Add to background tasks so API returns instantly
    background_tasks.add_task(generate_ad_pipeline, job_id, req.url)
    
    return {"job_id": job_id, "message": "Ad generation started"}

@app.get("/api/ads/stream/{job_id}")
async def stream_progress(request: Request, job_id: str):
    """Streams real-time progress to the Next.js frontend using Server-Sent Events."""
    async def event_generator():
        while True:
            # If client disconnects
            if await request.is_disconnected():
                break
                
            state = progress_streams.get(job_id)
            if not state:
                yield {"data": "Job not found"}
                break
                
            yield {"data": f"[{state['progress']}%] {state['status']}"}
            
            if state["status"] == "SUCCESS" or "FAILED" in state["status"]:
                break
                
            await asyncio.sleep(1) # Poll memory every 1 sec
            
    return EventSourceResponse(event_generator())
