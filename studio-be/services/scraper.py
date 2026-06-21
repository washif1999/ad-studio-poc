import httpx
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_url(url: str) -> str:
    """Scrapes the target URL and returns the clean text content quickly."""
    try:
        # Using httpx for fast async HTTP requests
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Mask as a standard browser to avoid basic blocks
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts, styles, and footers for clean text
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # Limit the output to roughly the first 10,000 characters.
            # This is highly efficient and saves LLM token costs & latency while getting core context.
            return text[:10000]
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return f"Failed to extract content from {url}. Ensure it is a valid, accessible website."
