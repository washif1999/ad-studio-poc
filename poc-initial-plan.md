Here is your complete, battle-tested blueprint for building the **Automated Ad Creation & Editing Platform prototype**.

This plan is focused entirely on shipping maximum speed, elite quality, and advanced editing features (like subtitles, asset swapping, and canvas updates) with a small team in record time.

---

## 1. Prototype Technical Architecture

The architecture relies on a **Stateless Event-Driven Pipeline**. To keep things fast and remove operational bloat, we use FastAPI's built-in `BackgroundTasks` instead of Celery, and **Server-Sent Events (SSE)** to stream progress back to Next.js in real time.

```
┌────────────────────────────────────────────────────────┐
│             Next.js + TypeScript Frontend              │
└─────────────┬──────────────────────────────▲───────────┘
              │                               │ 
    1. POST /api/ads (Submit URL)             │ 2. SSE Progress Stream
              ▼                               │    (/api/ads/stream/{id})
┌─────────────┴───────────────────────────────┴──────────┐
│                    FastAPI Backend                     │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  BackgroundTasks (Sequential Pipe Execution)     │  │
│  │  - Step 1: Scrape & Extract                      │  │
│  │  - Step 2: LLM Structuring                       │  │
│  │  - Step 3: Audio/Visual Generation              │  │
│  │  - Step 4: Creatomate Composition               │  │
│  └────────────────────────┬─────────────────────────┘  │
└───────────────────────────┼────────────────────────────┘
                            │
               Writes State / Reads Specs
                            ▼
               ┌──────────────────────────┐
               │    SQLite Database       │
               │   (ads & tenants schema) │
               └──────────────────────────┘

```

---

## 2. Complete Technology Stack Matrix

| Component | Tool / Library Chosen | Why for this Prototype? |
| --- | --- | --- |
| **Frontend** | **Next.js 15 (App Router) + TS** | Immediate hot-reloading for UI state, native support for SSE streams, and quick deployment. |
| **Backend** | **FastAPI + Uvicorn** | Built on top of `asyncio` for blazing-fast concurrent API requests to AI providers. |
| **Database** | **SQLite** | Zero config. It’s a single file inside your repo, making migrations instant. |
| **Scraping** | **Cloudflare BR (`/crawl`)** | Zero proxy management. Returns clean, LLM-ready Markdown with a single call. |
| **LLM Engine** | **Gemini 2.5 Flash** or **GPT-4o-mini** | Sub-2-second generation speeds, dirt cheap, and supports strict JSON Pydantic output. |
| **Voice Sync** | **ElevenLabs API** | Best emotional inflection; returns precise word-level timestamps needed for auto-captions. |
| **Visual Gen** | **Fal.ai (Flux Fast / SD3)** | Produces stunning, photorealistic images at custom aspect ratios in under 1.5 seconds. |
| **Composition** | **Creatomate API** | Takes a JSON layout blueprint and renders full 1080p video ads in less than 7 seconds. |

---

## 3. Phase-by-Phase Implementation Plan

### Phase 1: Ingestion & Brain Setup (Days 1–2)

*Goal: Turn a raw URL into a highly structured JSON storyboard blueprint.*

* **Step 1:** Create your FastAPI server shell and set up a local SQLite database with an `ads` table tracking `id`, `tenant_id`, `status`, `video_url`, and `current_progress`.
* **Step 2:** Implement the scraping service. Send the user's URL to Cloudflare’s `/crawl` endpoint to extract clean markdown text, primary colors, and logo URLs.
* **Step 3:** Use **Pydantic** to declare the exact ad schema you need. Pass the scraped markdown to Gemini 2.5 Flash using structured JSON mode.

```python
# The structural blueprint the LLM MUST return
class VideoScene(BaseModel):
    scene_number: int
    visual_image_prompt: str
    voiceover_script: str
    duration_seconds: float
    text_overlay_headline: str

class AdStoryboardSchema(BaseModel):
    brand_name: str
    primary_color: str
    call_to_action: str  # e.g., "Shop Now"
    scenes: list[VideoScene]

```

### Phase 2: Asynchronous Generation Pipeline (Days 3–4)

*Goal: Spin up background generations and stream real-time progress updates to the UI.*

* **Step 1:** Implement a FastAPI endpoint (`/api/ads/stream/{id}`) using `sse_starlette.sse.EventSourceResponse`. When Next.js connects, it streams state mutations straight from the SQLite row.
* **Step 2:** Write the core pipeline inside a FastAPI `BackgroundTask`. It executes sequentially, running database updates at every step to feed the SSE stream:
1. Update status to `[15%] Scraping Website...`
2. Run LLM script ➔ Update status to `[40%] Writing Script & Storyboard...`
3. Trigger **Fal.ai** (for images) and **ElevenLabs** (for audio) concurrently using `asyncio.gather()`. Update status to `[70%] Generating Voice & Media Assets...`
4. Save audio and image files locally or to Cloudinary.



### Phase 3: The Engine Room & Video Compositing (Days 5–6)

*Goal: Assemble the loose AI media components into a cohesive 1080p MP4 ad with captions.*

* **Step 1:** Log into the Creatomate dashboard and build a master template layout containing standard placeholders: `Image_Placeholder`, `Text_Overlay`, `Voiceover_Audio`, and `Background_Music`.
* **Step 2:** Extract the **word-level timestamps** from the ElevenLabs API response. Format them into an SRT or standard subtitle format array.
* **Step 3:** Have your backend compile a master payload mapping your generated image URLs, audio tracks, text headlines, and timestamps into the template schema, then fire it off to the Creatomate render endpoint.
* **Step 4:** Once Creatomate yields the finished MP4 link, update the database state to `SUCCESS`. The Next.js frontend catches this via the open SSE stream and renders the final video player.

### Phase 4: Advanced Next.js Interactive Editing Canvas (Days 7–8)

*Goal: Give users the power to alter captions, swap scenes, and change CTAs in real time.*

* **Step 1:** Build a timeline workspace in Next.js. Render individual text input boxes for each scene headline and a dropdown selector for the background music tracks.
* **Step 2:** When a marketer changes a headline or uploads a brand-new image slot, your UI captures that specific layer update in its local state.
* **Step 3:** Next.js sends a quick `PATCH /api/ads/{id}/edit` call containing only the altered layer fields to FastAPI.
* **Step 4:** Your backend bypasses the slow AI scraping and generation engines entirely! It takes the updated text strings, modifies the existing JSON layer structure, and hits Creatomate's render pipeline directly.

```
[User edits a caption or swaps an image in Next.js UI]
                           │
                           ▼ Updates UI React State
┌────────────────────────────────────────────────────────┐
│  Patched JSON Payload Schema                           │
│  {                                                     │
│    "Scene_2_Text": "Limited Stock - Order Today!",     │
│    "Logo_Layer": "https://cdn.com/new-brand-logo.png"  │
│  }                                                     │
└──────────────────────────┬─────────────────────────────┘
                           │ Direct HTTP POST (Bypasses AI)
                           ▼
┌────────────────────────────────────────────────────────┐
│  Creatomate Render Pipeline                            │
│  - Re-composes asset layout layer directly             │
│  - Returns fresh preview MP4 URL in < 3 seconds       │
└────────────────────────────────────────────────────────┘

```

---

## 4. Operational Safety Controls for the Prototype

To prevent users from spamming your API, burning through your generation credits, or breaking the layout loops, implement these guardrails inside your prototype from day one:

1. **Token Bucket Rate Limiter:** Build a simple memory-based dictionary or local Redis key structure inside FastAPI. Limit every workspace IP to a maximum of **3 ad generations per hour**.
2. **Strict Global Character Caps:** Clip the incoming text from websites before it hits your LLM context window. Ensure your voice script output length is strictly bound to **under 250 characters** per 15-second ad window to keep ElevenLabs token pricing predictable.
3. **Asset Fail-Safes:** If Fal.ai fails to generate a scene image due to prompt safety filters, write an immediate fallback exception code block that pulls the client’s original hero image scraped directly from their landing page. This prevents the entire render pipeline from crashing midway through a job.