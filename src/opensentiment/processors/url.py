from typing import Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
from ..utils.validation import validate_url

class URLProcessor:
    def __init__(self):
        self.timeout = 30
        
    async def fetch_content(self, url: str) -> Dict[str, Any]:
        """Fetch and process content from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=self.timeout) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                return {
                    "title": soup.title.string if soup.title else None,
                    "text": soup.get_text(strip=True),
                    "metadata": await self.extract_metadata(soup, url)
                }
                
    async def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from webpage"""
        return {
            "url": url,
            "domain": url.split('/')[2],
            "meta_description": soup.find("meta", {"name": "description"}),
            "publish_date": None  # Placeholder for date extraction
        } 