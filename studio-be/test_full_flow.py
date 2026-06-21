import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

from main import generate_ad_pipeline

async def run():
    job_id = "test-job-id"
    url = "https://example.com"
    await generate_ad_pipeline(job_id, url)
    print("Done")

asyncio.run(run())
